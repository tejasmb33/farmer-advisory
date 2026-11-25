from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'

def test_app_demo_and_compare():
    at=AppTest.from_file(str(APP),default_timeout=20).run()
    assert not at.exception
    # Exercise example loading, form submission, multilingual advice and comparison.
    at.selectbox(key='asklang').select('Kannada').run()
    at.selectbox(key='askexample').select('vague').run()
    at.button[0].click().run()
    assert not at.exception
    result=at.session_state['askresult']
    assert result['responses'][0]['language']=='Kannada'
    assert result['responses'][0]['total_tokens'] is None
    at.selectbox(key='compareexample').select('unsafe').run()
    at.button[1].click().run()
    assert not at.exception
    assert len(at.session_state['compareresult']['responses'])==2
    assert all(r['total_tokens'] is None for r in at.session_state['compareresult']['responses'])

def test_empty_query_and_live_settings():
    at=AppTest.from_file(str(APP),default_timeout=20).run()
    at.button[0].click().run()
    assert any('Describe a crop problem' in w.value for w in at.warning)
    at.radio[0].set_value('Live API').run()
    assert not at.exception
    at.selectbox(key='askexample').select('symptoms').run()
    at.button[0].click().run()
    assert any('model ID' in e.value for e in at.error)


def test_kannada_interface_and_switch_back():
    at=AppTest.from_file(str(APP),default_timeout=20).run()
    at.selectbox(key='ui_language').select('Kannada').run()
    assert not at.exception
    assert at.tabs[0].label == '🌿  ಕೃಷಿ ಸಲಹೆ ಪಡೆಯಿರಿ'
    assert at.selectbox(key='askcrop').label == 'ಬೆಳೆ'
    assert 'ಟೊಮೇಟೊ' in at.selectbox(key='askcrop').options
    assert at.selectbox(key='asklang').value == 'Kannada'
    at.button[0].click().run()
    assert any('ಮೊದಲು' in w.value for w in at.warning)
    at.selectbox(key='askexample').select('vague').run()
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state['askresult']['responses'][0]['language']=='Kannada'
    assert any('ಬೆಳೆಯ' in str(m.value) for m in at.markdown)
    at.selectbox(key='compareexample').select('unsafe').run()
    at.button[1].click().run()
    assert not at.exception
    assert len(at.session_state['compareresult']['responses']) == 2
    at.selectbox(key='ui_language').select('English').run()
    assert not at.exception
    assert at.tabs[0].label == '🌿  Ask an adviser'
    assert at.selectbox(key='asklang').value == 'English'
