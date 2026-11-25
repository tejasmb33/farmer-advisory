"""Farmwise — multilingual prompt engineering workbench."""
import io
import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt
from dotenv import load_dotenv
from prompts import VERSIONS, FIELDS, build_prompt, library_hash
from llm import run_advisory
from demo import HEADINGS, DISCLAIMER
from evaluate import summarize_frames, CRITERIA
from i18n import translate, localize_data

st.set_page_config(page_title=translate('Farmwise · Advisory Lab', st.session_state.get('ui_language', 'English')),page_icon='🌱',layout='wide')

ui_language = st.sidebar.selectbox("Language / ಭಾಷೆ", ["English", "Kannada"],
    format_func=lambda value: {"English": "English", "Kannada": "ಕನ್ನಡ"}[value], key="ui_language")
t = lambda text: translate(text, ui_language)
if st.session_state.get('_previous_ui_language') != ui_language:
    for prefix in ('ask', 'compare'):
        st.session_state[prefix+'lang'] = ui_language
    st.session_state['_previous_ui_language'] = ui_language

load_dotenv()
ROOT=Path(__file__).parent
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&family=Noto+Sans+Kannada:wght@400;500;600;700&display=swap');
html,body,[class*="css"],.stApp{font-family:'DM Sans','Noto Sans Kannada',sans-serif}
.stApp{background:#f7f8f3;color:#20382b}
h1,h2,h3{font-family:'Manrope','Noto Sans Kannada',sans-serif!important;letter-spacing:-.035em}
h1{font-size:3.1rem!important;line-height:1.1!important}
[data-testid="stSidebar"]{background:#eef1e8;border-right:1px solid #dfe5d8}
[data-testid="stMetric"]{background:white;border:1px solid #e0e6d9;border-radius:12px;padding:15px}
[data-testid="stMetricLabel"]{color:#667461}
[data-testid="stMetricValue"]{font-family:'Manrope','Noto Sans Kannada',sans-serif;font-size:1.7rem}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:#245a3d;border:0;border-radius:8px}
.block-container{max-width:1320px;padding-top:2rem;padding-bottom:3rem}
.kicker{font-size:.74rem;font-weight:700;letter-spacing:.16em;color:#56815b;margin-bottom:16px}
.intro{font-size:1.1rem;color:#677460;max-width:650px;line-height:1.6}
.hero{background:#eaf0df;border-radius:18px;padding:26px 30px;border:1px solid #dce6cf;margin:20px 0}
.hero p{color:#55704d;margin-bottom:0}
.brand{font-size:1.6rem;font-weight:800;color:#245a3d;letter-spacing:-.06em}
.caption{font-size:.8rem;color:#7b8674}
.badge{display:inline-block;background:#e6edde;color:#3a643d;padding:5px 12px;border-radius:30px;font-size:.75rem;font-weight:600}
[data-testid="stTabs"] button{font-size:.95rem}
</style>''',unsafe_allow_html=True)

with st.sidebar:
    st.markdown(t('<div class="brand">🌱 farmwise</div><p class="caption">MULTILINGUAL ADVISORY LAB</p>'),unsafe_allow_html=True)
    st.divider()
    st.markdown(t('**Your workspace**'))
    st.caption(t('Prompt engineering for practical farm advice. Three languages. Eleven approaches.'))
    mode_label=st.radio(t('Connection'),['Offline demo','Live API'],format_func=t,help=t('Offline fixtures do not use AI or produce token measurements.'))
    mode='demo' if mode_label=='Offline demo' else 'live'
    model=os.getenv('ANTHROPIC_MODEL','')
    api_key=None;price_in=None;price_out=None;price_date=''
    if mode=='live':
        model=st.text_input(t('Anthropic model ID'),value=model,placeholder=t('An available model ID from your account'))
        api_key=st.text_input(t('API key (optional if set in .env)'),type='password',help=t('Held in this session only; never exported.')) or None
        with st.expander(t('Token pricing · USD')):
            st.caption(t('Enter current prices per million tokens from the provider pricing page.'))
            pi=st.number_input(t('Input / million'),min_value=0.0,value=float(os.getenv('PRICE_INPUT_MTOK') or 0),format='%.4f')
            po=st.number_input(t('Output / million'),min_value=0.0,value=float(os.getenv('PRICE_OUTPUT_MTOK') or 0),format='%.4f')
            price_date=st.text_input(t('Pricing verified date'),value=os.getenv('PRICE_DATE',''),placeholder=t('YYYY-MM-DD'))
            verified=st.checkbox(t('I have verified these prices'))
            if verified and price_date.strip(): price_in,price_out=pi,po
    st.divider()
    st.markdown(t('**Built for Karnataka**'))
    st.caption(t('6 crops · 4 districts')+'\n\n'+t('English')+' · ಕನ್ನಡ · '+t('Hindi'))
    st.markdown(t('<div class="badge">Prompt-only · no model training</div>'),unsafe_allow_html=True)
    st.caption(t('Local research prototype. No automatic disk storage of questions. API requests are subject to provider data policies.'))

st.markdown(t('<div class="kicker">SMALLER PROMPTS. THOUGHTFUL ADVICE.</div>'),unsafe_allow_html=True)
left,right=st.columns([3,1])
with left:
    st.title(t('Better advice.\nFewer tokens.'))
    st.markdown(t('<p class="intro">Explore how prompt design changes farm advice across languages — and measure what it costs.</p>'),unsafe_allow_html=True)
with right:
    st.markdown(t('<div class="hero"><span style="font-size:2.5rem">🌾</span><h3>Rooted in context.</h3><p>Designed for local questions.<br>Measured with care.</p></div>'),unsafe_allow_html=True)
if mode=='demo':
    st.info(t('OFFLINE DEMO · Prewritten examples, identical across prompt versions. No API calls, measured tokens, costs or quality scores.'))
else:
    st.caption(t('LIVE API · Usage comes directly from the provider. Running a comparison makes separate paid requests.'))

advisory,compare,library,research=st.tabs([t('🌿  Ask an adviser'),t('⇄  Compare prompts'),t('⌘  Prompt library'),t('▥  Research desk')])


def display_frame(frame):
    return frame.map(lambda value:t(value) if isinstance(value,str) else value).rename(columns=t)


def case_form(prefix, comparison=False):
    tests=pd.read_csv(ROOT/'data/test_queries.csv',keep_default_na=False)
    lang=st.selectbox(t('Response language'),['English','Kannada','Hindi'],key=prefix+'lang',format_func=t)
    examples=tests[tests.language==lang]
    category=st.selectbox(t('Start with an example'), ['Custom question']+list(examples.category),key=prefix+'example',format_func=lambda s:t(s) if ui_language=='Kannada' else s.replace('_',' ').capitalize())
    example=examples[examples.category==category]
    default=example.iloc[0].question if not example.empty else ''
    with st.form(prefix+'form'):
        a,b,c=st.columns(3)
        crop=a.selectbox(t('Crop'),['Tomato','Rice','Ragi','Sugarcane','Cotton','Maize'],key=prefix+'crop',format_func=t)
        region=b.selectbox(t('District'),['Mandya','Mysuru','Dharwad','Raichur'],key=prefix+'region',format_func=t)
        season=c.selectbox(t('Season'),['Kharif','Rabi','Summer'],key=prefix+'season',format_func=t)
        a,b=st.columns(2)
        stage=a.selectbox(t('Growth stage'),['Vegetative','Seedling','Flowering','Fruiting','Harvest'],key=prefix+'stage',format_func=t)
        soil=b.selectbox(t('Soil, if known'),['Unknown','Red soil','Black soil','Sandy loam','Clay loam'],key=prefix+'soil',format_func=t)
        question=st.text_area(t('What is happening in your field?'),value=default,max_chars=4000,height=105,
                              placeholder=t('Describe symptoms, when they began, and how many plants are affected.'),key=prefix+'q'+lang+category)
        if comparison:
            a,b=st.columns(2)
            first=a.selectbox(t('Reference prompt'),list(VERSIONS),index=5,format_func=lambda v:f'{v} · {t(VERSIONS[v])}',key=prefix+'v1')
            second=b.selectbox(t('Compare with'),list(VERSIONS),index=10,format_func=lambda v:f'{v} · {t(VERSIONS[v])}',key=prefix+'v2')
            versions=[first,second]
        else:
            versions=[st.selectbox(t('Prompt approach'),list(VERSIONS),index=10,format_func=lambda v:f'{v} · {t(VERSIONS[v])}',key=prefix+'v')]
        submitted=st.form_submit_button(t('Compare advice') if comparison else t('Generate advice'),type='primary',use_container_width=True)
    return submitted,dict(language=lang,crop=crop,region=region,season=season,stage=stage,soil=soil,question=question),versions


def execute(prefix,submitted,case,versions):
    if not submitted:return
    st.session_state.pop(prefix+'result',None)
    if not case['question'].strip():
        st.warning(t('Describe a crop problem or choose an example first.'));return
    if len(set(versions))!=len(versions):
        st.warning(t('Choose two different prompt versions.'));return
    responses=[]
    with st.spinner(t('Preparing advice…') if mode=='demo' else t('Requesting advice and collecting exact usage…')):
        for version in versions:
            try:
                result=run_advisory(case,version,mode=mode,model=model,api_key=api_key,price_in=price_in,price_out=price_out)
                result['price_date']=price_date
                responses.append(result)
            except Exception as exc:
                if isinstance(exc,ValueError): st.error(t(str(exc)))
                else: st.error(t('API request failed. Check credentials, model access, network and provider quota. No usage is claimed for this failed request.') + f' ({type(exc).__name__})')
                break
    if responses:
        st.session_state[prefix+'result']={'case':case,'responses':responses}


def render_result(result):
    st.markdown(f"### {result['version']} · {t(VERSIONS[result['version']])}")
    if result['mode']=='demo':st.caption(t('Prewritten offline example · not model output'))
    if result.get('truncated'):st.error(t('Output hit its token cap. Treat this as a truncation failure; review the incomplete advice.'))
    if result.get('format_required') and not result.get('format_ok'):
        st.warning(t('Compact JSON failed schema validation. Raw output is shown and the format failure is retained.'))
    if int(result['version'][1:])<4 and result['mode']=='live':
        st.warning(t('Research baseline: this version has limited safety instructions. Review output before use.'))
    with st.container(border=True):
        if result['advice']:
            for key,heading in zip(FIELDS,HEADINGS[result['language']]):
                content=result['advice'][key]
                if not content:continue
                st.markdown('**'+heading+'**')
                if isinstance(content,list):
                    for item in content: st.write('• '+item)
                else:st.write(content)
        else: st.write(result['text'])
    a,b,c=st.columns(3)
    a.metric(t('Input tokens'),result['input_tokens'] if result['input_tokens'] is not None else '—')
    b.metric(t('Output tokens'),result['output_tokens'] if result['output_tokens'] is not None else '—')
    c.metric(t('Total tokens'),result['total_tokens'] if result['total_tokens'] is not None else '—')
    cost=result.get('cost_usd')
    st.caption(t('Cost')+f": {'$'+format(cost,'.6f') if cost is not None else t('not measured / pricing not configured')} · "+t('Time')+f": {str(result['seconds'])+' '+t('s') if result['seconds'] is not None else t('not measured')} · "+t('Calls')+f": {len(result['calls'])}")
    st.caption(DISCLAIMER[result['language']])
    with st.expander(t('Inspect raw response and request usage')):
        st.code(result['text'],language='json' if result['advice'] else None)
        st.json({k:v for k,v in result.items() if k not in ('text','advice')})


def show_saved(prefix):
    bundle=st.session_state.get(prefix+'result')
    if not bundle:return
    st.divider()
    case=bundle['case'];responses=bundle['responses']
    st.caption(f"{t('Result snapshot')} · {t(case['crop'])} · {t(case['region'])} · {t(case['language'])} · {t('Offline demo' if responses[0]['mode']=='demo' else 'Live API')}")
    st.write(case['question'])
    if len(responses)==2:
        first,second=responses
        if first['total_tokens'] and second['total_tokens'] is not None:
            savings=(1-second['total_tokens']/first['total_tokens'])*100
            st.metric(t('Token reduction vs reference'),f'{savings:.1f}%',help=t('Negative values mean the comparison consumed more tokens. Quality requires independent human scoring.'))
        else:st.caption(t('Token reduction is unavailable in offline demo mode.'))
        for column,result in zip(st.columns(2),responses):
            with column:render_result(result)
    else:render_result(responses[0])
    st.download_button(t('Download this run · JSON'),json.dumps(bundle,ensure_ascii=False,indent=2),file_name='farmwise-run.json',mime='application/json',key=prefix+'download')

with advisory:
    st.subheader(t('A little context goes a long way.'))
    st.caption(t('Tell the adviser about your crop. Your question stays in this session unless you download it.'))
    submitted,case,versions=case_form('ask')
    execute('ask',submitted,case,versions);show_saved('ask')

with compare:
    st.subheader(t('Same question. Different prompt.'))
    st.caption(t('Compare the quality ceiling with a compact approach. Model and temperature stay the same; V10 intentionally uses a lower output cap.'))
    submitted,case,versions=case_form('compare',True)
    execute('compare',submitted,case,versions);show_saved('compare')

with library:
    st.subheader(t('Eleven versions. One research question.'))
    st.caption(t('How much can tokens be reduced while keeping quality and safety close to V5?'))
    st.dataframe(pd.DataFrame([{t('Version'):v,t('Technique'):t(name),t('Track'):t('Quality' if int(v[1:])<=5 else 'Efficiency')} for v,name in VERSIONS.items()]),hide_index=True,use_container_width=True)
    version=st.selectbox(t('Inspect a prompt'),list(VERSIONS),index=10)
    preview_case=dict(language=ui_language,crop='Tomato',region='Mandya',season='Kharif',stage='Vegetative',soil='Unknown',question=('ನನ್ನ ಟೊಮೇಟೊ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ. ಏನು ಮಾಡಬೇಕು?' if ui_language=='Kannada' else 'My tomato leaves are turning yellow. What should I do?'))
    system,user=build_prompt(version,preview_case)
    st.markdown(t('**System prompt**'));st.code(system or t('(No system prompt: V0 baseline)'),language=None)
    st.markdown(t('**User message · example**'));st.code(user,language='json' if version!='V0' else None)
    st.caption(t('V9 generates compact English advice, then translates for Kannada/Hindi. Both calls count. V7 uses a conservative context subset for all three languages. V10 is a combined treatment, so its effect cannot be attributed to one technique.'))
    st.code(t('Library + context SHA-256: ')+library_hash(),language=None)

with research:
    st.subheader(t('Evidence before conclusions.'))
    st.caption(t('A ready-to-run study kit. Real token savings and quality findings appear only after live calls and human review.'))
    a,b,c=st.columns(3)
    a.metric(t('Test queries'),'18');b.metric(t('Prompt versions'),'11');c.metric(t('Rubric criteria'),'6')
    st.markdown(t('**1 · Prepare the study**'))
    a,b,c=st.columns(3)
    a.download_button(t('Test queries · CSV'),(ROOT/'data/test_queries.csv').read_bytes(),'test_queries.csv','text/csv')
    b.download_button(t('Language samples · CSV'),(ROOT/'data/language_samples.csv').read_bytes(),'language_samples.csv','text/csv')
    c.download_button(t('Quality rubric · JSON'),json.dumps(localize_data(json.loads((ROOT/'data/rubric.json').read_text(encoding='utf-8')),ui_language),ensure_ascii=False,indent=2),'rubric.json','application/json')
    st.warning(t('Context, test translations and language samples are drafts pending local agronomic and fluent-speaker verification. They are not verified agricultural sources.'))
    st.markdown(t('**2 · Run, blind and score**'))
    st.code('python evaluate.py run --mode live --output results/outputs.csv\npython evaluate.py blind\n# Human reviewers fill every rubric score in results/review/blind_scores.csv\npython evaluate.py summarize\npython evaluate.py language-gap',language='bash')
    st.caption(t('Batch runner resumes successful records, rejects changed settings and freezes prompt/context and query hashes. Default batch: 198 advisory runs; V9 translation adds calls. Three repeats produce 594 runs. These are paid calls.'))
    st.markdown(t('**3 · Explore your reviewed results**'))
    a,b,c=st.columns(3)
    outputs=a.file_uploader(t('Live outputs CSV'),type='csv')
    scores=b.file_uploader(t('Completed blind scores CSV'),type='csv')
    mapping=c.file_uploader(t('Private mapping CSV'),type='csv')
    if outputs and scores and mapping:
        try:
            scored,summary=summarize_frames(pd.read_csv(outputs),pd.read_csv(scores),pd.read_csv(mapping))
            languages=st.multiselect(t('Include languages'),sorted(summary.language.unique()),default=sorted(summary.language.unique()),format_func=t)
            filtered=summary[summary.language.isin(languages)]
            chart_data=filtered.copy()
            chart_data['language']=chart_data['language'].map(t)
            token_chart=alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=3,cornerRadiusTopRight=3).encode(x=alt.X('version:N',sort=list(VERSIONS),title=t('version')),y=alt.Y('total_tokens:Q',title=t('Mean total tokens')),color=alt.Color('language:N',title=t('language')),xOffset='language:N',tooltip=[alt.Tooltip(k,title=t(k)) for k in ('version','language','total_tokens')])
            st.altair_chart(token_chart,use_container_width=True)
            tradeoff=alt.Chart(chart_data).mark_circle(size=130).encode(x=alt.X('total_tokens:Q',title=t('Mean total tokens')),y=alt.Y('quality:Q',scale=alt.Scale(domain=[1,5]),title=t('Mean human quality score')),color=alt.Color('version:N',title=t('version')),shape=alt.Shape('language:N',title=t('language')),tooltip=[alt.Tooltip(k,title=t(k)) for k in ('version','language','quality','safety','efficiency')])
            st.altair_chart(tradeoff,use_container_width=True)
            st.altair_chart(alt.Chart(chart_data).mark_bar().encode(x=alt.X('version:N',sort=list(VERSIONS),title=t('version')),y=alt.Y('efficiency:Q',title=t('Quality points per 1,000 tokens')),color=alt.Color('language:N',title=t('language')),xOffset='language:N'),use_container_width=True)
            st.dataframe(display_frame(filtered),hide_index=True,use_container_width=True)
            st.download_button(t('Download summary CSV'),display_frame(summary).to_csv(index=False).encode('utf-8-sig'),'summary.csv','text/csv')
            st.caption(t('Review individual safety and truncation failures alongside these averages. Scores are human assessments, not proof of clinical or agronomic correctness.'))
        except Exception as exc:st.error(t('Results could not be validated: ')+t(str(exc)))
    else:
        st.markdown(t('<div class="hero"><h3>Your evidence belongs here.</h3><p>Upload live outputs, completed blind scores and their private mapping to see token, quality and efficiency charts.</p></div>'),unsafe_allow_html=True)
    with st.expander(t('Rubric and source verification')):
        st.json(localize_data(json.loads((ROOT/'data/rubric.json').read_text(encoding='utf-8')),ui_language))
        for ref in json.loads((ROOT/'data/context.json').read_text())['reference_portals']:
            st.link_button(t(ref['title']),ref['url'])
        st.caption(t('Reference portals are starting points. Record the exact advisory document, access date and reviewer used for each accuracy judgment.'))

st.divider()
st.caption(t('FARMWISE  /  Prompt engineering research prototype  ·  English / ಕನ್ನಡ / हिन्दी  ·  No model training'))
