import json
from types import SimpleNamespace
import pandas as pd
import pytest
from llm import run_advisory, parse_advice, price_cost
from prompts import VERSIONS,build_prompt
from evaluate import summarize_frames,CRITERIA

CASE=dict(language='Kannada',crop='Tomato',region='Mandya',season='Kharif',stage='Vegetative',soil='Unknown',question='ನನ್ನ ಸಸಿಗಳು ಸಾಯುತ್ತಿವೆ. ಏನು ಮಾಡಬೇಕು?')
ADVICE=dict(problem='Unknown',cause='Unconfirmed',steps=['Inspect'],prevent='Monitor',expert='Ask KVK',follow_up='When?')

def test_prompt_ladder_and_selective_context():
    assert build_prompt('V0',CASE)==('',CASE['question'])
    for version in VERSIONS:
        system,user=build_prompt(version,CASE)
        assert CASE['question'] in user
        if int(version[1:])>=4:
            assert 'dosage' in system and ('uncertainty' in system or 'uncertain' in system or 'cautious' in system)
    assert 'regional_profile' in json.loads(build_prompt('V6',CASE)[1])['context']
    assert 'regional_profile' not in json.loads(build_prompt('V7',CASE)[1])['context']
    assert 'Answer in English' in build_prompt('V9',CASE)[0]
    assert 'Maximum 100 words' in build_prompt('V10',CASE)[0]

@pytest.mark.parametrize('bad',[[],{'steps':'wrong'},dict(ADVICE,steps=[1]),dict(ADVICE,problem=2),dict(ADVICE,extra='x')])
def test_schema_rejects_invalid(bad):
    assert parse_advice(json.dumps(bad)) is None

def test_fenced_json_and_cost():
    assert parse_advice('```json\n'+json.dumps(ADVICE)+'\n```')==ADVICE
    assert price_cost(1000,200,3,15)==pytest.approx(.006)
    assert price_cost(1,1) is None

class FakeClient:
    def __init__(self):self.messages=self;self.requests=[]
    def create(self,**kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type='text',text=json.dumps(ADVICE))],
               usage=SimpleNamespace(input_tokens=100,output_tokens=40),stop_reason='max_tokens' if len(self.requests)==1 else 'end_turn')

def test_v9_does_not_translate_a_truncated_response():
    client=FakeClient()
    result=run_advisory(CASE,'V9',mode='live',model='test-model',client=client,price_in=3,price_out=15)
    assert result['total_tokens']==140 and result['input_tokens']==100 and len(result['calls'])==1
    assert result['truncated'] is True and result['format_ok'] is True
    assert result['cost_usd']==pytest.approx(.0009)
    assert all(c['temperature']==.2 and c['model']=='test-model' for c in client.requests)

def test_v9_english_one_call_and_v10_cap():
    client=FakeClient();run_advisory(dict(CASE,language='English'),'V9',mode='live',model='test',client=client)
    assert len(client.requests)==1
    run_advisory(CASE,'V10',mode='live',model='test',client=client)
    assert client.requests[-1]['max_tokens']==700

@pytest.mark.parametrize('lang',['English','Kannada','Hindi'])
def test_demo_never_claims_usage(lang):
    r=run_advisory(dict(CASE,language=lang),'V10')
    assert r['mode']=='demo' and r['total_tokens'] is None and r['cost_usd'] is None and r['calls']==[]

def frames():
    outputs=pd.DataFrame([dict(record_id=f'r{i}',mode='live',version=v,language='English',total_tokens=t,input_tokens=t-10,output_tokens=10,cost_usd=None,seconds=.5) for i,(v,t) in enumerate([('V5',100),('V10',60)])])
    mapping=pd.DataFrame([dict(blind_id=f'b{i}',record_id=f'r{i}') for i in range(2)])
    scores=pd.DataFrame([dict(blind_id=f'b{i}',**{c:4 for c in CRITERIA}) for i in range(2)])
    return outputs,scores,mapping

def test_summary_correct_savings_and_rejects_missing_scores():
    outputs,scores,mapping=frames()
    _,summary=summarize_frames(outputs,scores,mapping)
    assert summary.loc[summary.version=='V10','token_savings_pct'].iloc[0]==40
    assert summary.cost_usd.isna().all()
    scores.loc[0,'safety']=None
    with pytest.raises(ValueError):summarize_frames(outputs,scores,mapping)

def test_no_demo_or_partial_results_in_research():
    outputs,scores,mapping=frames();outputs.loc[0,'mode']='demo'
    with pytest.raises(ValueError):summarize_frames(outputs,scores,mapping)
    outputs,scores,mapping=frames()
    with pytest.raises(ValueError):summarize_frames(outputs,scores.iloc[:1],mapping)

def test_summary_rejects_mixed_model_and_wrong_token_sum():
    outputs,scores,mapping=frames();outputs['model']=['a','b']
    with pytest.raises(ValueError,match='different model'):summarize_frames(outputs,scores,mapping)
    outputs,scores,mapping=frames();outputs.loc[0,'total_tokens']=999
    with pytest.raises(ValueError,match='Token totals'):summarize_frames(outputs,scores,mapping)

def test_summary_requires_matched_case_populations():
    outputs,scores,mapping=frames();outputs['query_id']=['one','two'];outputs['repeat']=1
    with pytest.raises(ValueError,match='matched query'):summarize_frames(outputs,scores,mapping)


@pytest.mark.parametrize('version',list(VERSIONS))
@pytest.mark.parametrize('language',['English','Kannada'])
def test_live_language_contract_across_versions(version,language):
    client=FakeClient()
    # Exercise the translation path with a complete first response.
    client.requests.append({'placeholder': True})
    run_advisory(dict(CASE,language=language),version,mode='live',model='test',client=client)
    request=client.requests[-1]
    system = request['system']
    system_text = ' '.join(block['text'] for block in system) if isinstance(system, list) else system
    assert language in system_text
    if language=='Kannada':
        assert 'Kannada' in system_text
    if version=='V9' and language=='Kannada':
        assert len(client.requests)==3
    else:
        assert len(client.requests)==2


def test_unicode_report_translation():
    from i18n import translate,localize_data
    assert translate('Crop','Kannada')=='ಬೆಳೆ'
    assert translate('Crop','English')=='Crop'
    assert localize_data({'safety':'Unsafe or overconfident'},'Kannada')=={'ಸುರಕ್ಷತೆ':'ಅಸುರಕ್ಷಿತ ಅಥವಾ ಅತಿಯಾದ ಖಚಿತತೆ'}


def test_ollama_mode_accounting(monkeypatch):
    import httpx
    captured = []
    def fake_post(url, json=None, timeout=None):
        captured.append((url, json))
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {
                'message': {'content': '{"problem":"Leaf spot","cause":"Fungal","steps":["Remove leaves"],"prevent":"Spacing","expert":"Ask KVK","follow_up":"Any spots?"}'},
                'prompt_eval_count': 42,
                'eval_count': 18,
                'done_reason': 'stop',
            },
        )
    monkeypatch.setattr(httpx, 'post', fake_post)
    result = run_advisory(dict(CASE, language='English'), 'V10', mode='ollama', model='llama3.2', ollama_url='http://localhost:11434')
    assert result['mode'] == 'ollama'
    assert result['cost_usd'] == 0.0
    assert result['input_tokens'] == 42 and result['output_tokens'] == 18 and result['total_tokens'] == 60
    assert result['format_ok'] is True
    assert captured[0][0] == 'http://localhost:11434/api/chat'
    assert captured[0][1]['options']['num_predict'] == 700
