"""Reproducible batch runs, blind human scoring, summaries and language counts."""
import argparse
import csv
import hashlib
import json
import os
import random
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from llm import run_advisory
from prompts import VERSIONS, library_hash

ROOT = Path(__file__).parent
CRITERIA = ['accuracy','clarity','simplicity','completeness','safety','language_quality']

def write_csv(df, path):
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False,encoding='utf-8-sig')

def run_batch(args):
    tests = pd.read_csv(args.queries,keep_default_na=False)
    selected = args.versions.split(',')
    if any(v not in VERSIONS for v in selected): raise ValueError('Invalid version')
    if tests['id'].duplicated().any(): raise ValueError('Query IDs must be unique')
    if args.repeats < 1: raise ValueError('repeats must be positive')
    output = Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    manifest = dict(mode=args.mode, model=args.model if args.mode=='live' else 'offline fixture',
        temperature=0.2, library_hash=library_hash(), repeats=args.repeats, versions=selected,
        price_input=args.price_in,price_output=args.price_out,price_date=os.getenv('PRICE_DATE'),
        query_sha256=hashlib.sha256(Path(args.queries).read_bytes()).hexdigest())
    manifest_path = output.with_suffix('.manifest.json')
    if output.exists() and not manifest_path.exists(): raise ValueError('Existing outputs have no manifest; choose a new path')
    if manifest_path.exists():
        previous=json.loads(manifest_path.read_text())
        if previous['settings'] != manifest: raise ValueError('Run settings changed; choose a new output path')
    else:
        manifest_path.write_text(json.dumps({'settings':manifest,'started_utc':datetime.now(timezone.utc).isoformat()},indent=2))
    existing = pd.read_csv(output,keep_default_na=False) if output.exists() else pd.DataFrame()
    done = set(existing['record_id']) if not existing.empty else set()
    failures = 0
    for case in tests.to_dict('records'):
        for version in selected:
            for repeat in range(1,args.repeats+1):
                rid = f"{case['id']}-{version}-{repeat}"
                if rid in done: continue
                try:
                    result = run_advisory(case,version,mode=args.mode,model=args.model,
                                          price_in=args.price_in,price_out=args.price_out)
                    row = dict(result, record_id=rid,query_id=case['id'], repeat=repeat,
                               question=case['question'],category=case.get('category',''),price_date=os.getenv('PRICE_DATE',''))
                    for field in ('calls','advice'): row[field]=json.dumps(row[field],ensure_ascii=False)
                    frame=pd.DataFrame([row])
                    frame.to_csv(output,mode='a',header=not output.exists(),index=False,encoding='utf-8')
                    done.add(rid)
                    print('Done', rid,flush=True)
                except Exception as exc:
                    failures += 1
                    # Do not print provider exceptions, which can contain request details.
                    print('Failed',rid,type(exc).__name__, '— rerun to resume.',flush=True)
    if failures: raise SystemExit(f'{failures} calls failed. Successful records were retained.')

def blind_export(args):
    df=pd.read_csv(args.input,keep_default_na=False)
    if (df['mode']!='live').any(): raise ValueError('Blind scoring accepts live outputs only')
    rows=df.to_dict('records');random.Random(args.seed).shuffle(rows)
    mapping=[];blind=[]
    for i,row in enumerate(rows,1):
        bid=f'B{i:04}'
        mapping.append(dict(blind_id=bid,record_id=row['record_id']))
        blind.append(dict(blind_id=bid,language=row['language'],question=row['question'],output=row['text'],
                          **{c:'' for c in CRITERIA},reviewer='',reference='',notes=''))
    target=Path(args.directory);target.mkdir(parents=True,exist_ok=True)
    write_csv(pd.DataFrame(mapping),target/'private_mapping.csv')
    write_csv(pd.DataFrame(blind),target/'blind_scores.csv')
    print('Give only blind_scores.csv to reviewers; keep private_mapping.csv private.')

def summarize_frames(outputs, scores, mapping):
    outputs, scores, mapping = outputs.copy(), scores.copy(), mapping.copy()
    if (outputs['mode']!='live').any(): raise ValueError('Demo outputs cannot be used as measured results')
    for frame,key in ((outputs,'record_id'),(scores,'blind_id'),(mapping,'blind_id')):
        if frame[key].duplicated().any(): raise ValueError('Duplicate scoring/output keys')
    if mapping['record_id'].duplicated().any(): raise ValueError('Duplicate record mapping')
    for c in CRITERIA:
        scores[c]=pd.to_numeric(scores[c],errors='coerce')
        if scores[c].isna().any() or not scores[c].between(1,5).all() or not (scores[c]%1==0).all():
            raise ValueError('All six criteria require integer human scores from 1 to 5')
    if set(scores.blind_id)!=set(mapping.blind_id) or set(mapping.record_id)!=set(outputs.record_id):
        raise ValueError('Scores, mapping and outputs must cover exactly the same records')
    df=outputs.merge(mapping,on='record_id',validate='one_to_one').merge(scores,on='blind_id',validate='one_to_one')
    for column in ('input_tokens','output_tokens','seconds'):
        df[column]=pd.to_numeric(df[column],errors='raise')
        if df[column].isna().any() or (df[column]<0).any(): raise ValueError('Invalid usage or latency')
    for column in ('model','temperature','library_hash'):
        if column in df and df[column].nunique(dropna=False)!=1:
            raise ValueError('Do not combine experiments with different '+column)
    if 'query_id' in df and 'repeat' in df:
        populations=[set(zip(group.query_id,group.repeat)) for _,group in df.groupby('version')]
        if populations and any(population!=populations[0] for population in populations):
            raise ValueError('Versions must contain matched query IDs and repeats')
    df['quality']=df[CRITERIA].mean(axis=1)
    df['total_tokens']=pd.to_numeric(df['total_tokens'],errors='raise')
    if df.total_tokens.isna().any() or (df.total_tokens<=0).any(): raise ValueError('Token totals must be positive')
    if not (df.total_tokens==df.input_tokens+df.output_tokens).all(): raise ValueError('Token totals do not match input plus output')
    df['efficiency']=df.quality/df.total_tokens*1000
    df['cost_usd']=pd.to_numeric(df.cost_usd,errors='coerce')
    if (df.cost_usd.dropna()<0).any(): raise ValueError('Costs cannot be negative')
    grouped=df.groupby(['version','language'],sort=False)[CRITERIA+['quality','input_tokens','output_tokens','total_tokens','cost_usd','seconds','efficiency']].mean().reset_index()
    complete_costs=df.groupby(['version','language']).cost_usd.agg(lambda values: values.mean() if values.notna().all() else float('nan')).reset_index(name='complete_cost')
    grouped=grouped.merge(complete_costs,on=['version','language'])
    grouped['cost_usd']=grouped.pop('complete_cost')
    counts=df.groupby(['version','language']).size().reset_index(name='n_outputs')
    grouped=grouped.merge(counts,on=['version','language'])
    for flag in ('truncated','format_ok'):
        if flag in df:
            values=df[flag].astype(str).str.lower().map({'true':1.0,'false':0.0})
            rates=df.assign(_flag=values).groupby(['version','language'])._flag.mean().reset_index(name=flag+'_rate')
            grouped=grouped.merge(rates,on=['version','language'])
    grouped['cost_per_1000_queries']=grouped.cost_usd*1000
    # Baselines are matched by language, not pooled across languages.
    baseline=grouped[grouped.version=='V5'][['language','total_tokens']].rename(columns={'total_tokens':'v5_tokens'})
    grouped=grouped.merge(baseline,on='language',how='left')
    grouped['token_savings_pct']=(1-grouped.total_tokens/grouped.v5_tokens)*100
    return df,grouped

def summarize(args):
    df,grouped=summarize_frames(pd.read_csv(args.input),pd.read_csv(args.scores),pd.read_csv(args.mapping))
    target=Path(args.directory);target.mkdir(parents=True,exist_ok=True)
    write_csv(df,target/'scored_outputs.csv');write_csv(grouped,target/'summary.csv')
    import altair as alt
    chart=alt.Chart(grouped).mark_circle(size=110).encode(x=alt.X('total_tokens:Q',title='Mean total tokens'),
        y=alt.Y('quality:Q',scale=alt.Scale(domain=[1,5]),title='Mean human quality score'),color='version:N',shape='language:N',tooltip=['version','language','total_tokens','quality','safety'])
    chart.save(str(target/'tradeoff.html'))
    print('Saved summaries and interactive trade-off chart.')

def language_gap(args):
    import anthropic
    if not args.model: raise ValueError('Set a valid model ID')
    client=anthropic.Anthropic(timeout=60,max_retries=2)
    samples=pd.read_csv(args.samples)
    if samples.duplicated(['id','language']).any(): raise ValueError('Duplicate language sample')
    groups=samples.groupby('id').language.agg(set)
    if any(langs != {'English','Kannada','Hindi'} for langs in groups): raise ValueError('Each sample needs all three languages')
    rows=[]
    # Absolute message counts include provider framing; report framing explicitly.
    for row in samples.to_dict('records'):
        counted=client.messages.count_tokens(model=args.model,messages=[{'role':'user','content':row['text']}])
        rows.append(dict(row,input_tokens=counted.input_tokens,model=args.model,count_scope='Single user message including provider framing',timestamp=datetime.now(timezone.utc).isoformat()))
    df=pd.DataFrame(rows);write_csv(df,args.output)
    summary=df.groupby('language').input_tokens.mean().to_frame('mean_message_tokens')
    summary['ratio_to_english']=summary.mean_message_tokens/summary.loc['English','mean_message_tokens']
    write_csv(summary.reset_index(),Path(args.output).with_suffix('.summary.csv'))

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run');run.set_defaults(func=run_batch)
    run.add_argument('--queries',default=str(ROOT/'data/test_queries.csv'))
    run.add_argument('--output',default=str(ROOT/'results/outputs.csv'))
    run.add_argument('--mode',choices=['demo','live'],default='demo')
    run.add_argument('--model',default=os.getenv('ANTHROPIC_MODEL',''))
    run.add_argument('--versions',default=','.join(VERSIONS));run.add_argument('--repeats',type=int,default=1)
    run.add_argument('--price-in',type=float,default=None);run.add_argument('--price-out',type=float,default=None)
    blind=sub.add_parser('blind');blind.set_defaults(func=blind_export)
    blind.add_argument('--input',default=str(ROOT/'results/outputs.csv'));blind.add_argument('--directory',default=str(ROOT/'results/review'));blind.add_argument('--seed',type=int,default=42)
    report=sub.add_parser('summarize');report.set_defaults(func=summarize)
    report.add_argument('--input',default=str(ROOT/'results/outputs.csv'))
    report.add_argument('--scores',default=str(ROOT/'results/review/blind_scores.csv'))
    report.add_argument('--mapping',default=str(ROOT/'results/review/private_mapping.csv'))
    report.add_argument('--directory',default=str(ROOT/'results/analysis'))
    gap=sub.add_parser('language-gap');gap.set_defaults(func=language_gap)
    gap.add_argument('--model',default=os.getenv('ANTHROPIC_MODEL',''));gap.add_argument('--samples',default=str(ROOT/'data/language_samples.csv'));gap.add_argument('--output',default=str(ROOT/'results/language_gap.csv'))
    args=parser.parse_args();args.func(args)

if __name__=='__main__': main()
