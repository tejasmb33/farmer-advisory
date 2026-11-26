import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_hindi_interface_and_advice(monkeypatch):
    import httpx
    import llm

    def offline(*args, **kwargs):
        raise httpx.ConnectError('offline test')

    def fake_ollama(url, model, system, user, cap, *, structured=False):
        assert 'Hindi' in system
        return dict(text=json.dumps(dict(problem='पत्तियाँ पीली हैं', cause='कारण स्पष्ट नहीं',
                                         steps=['पौधों की जाँच करें'], prevent='निगरानी करें',
                                         expert='कृषि विशेषज्ञ से पूछें', follow_up=''), ensure_ascii=False),
                    input_tokens=100, output_tokens=30, seconds=0.1, stop_reason='end_turn')

    monkeypatch.setattr(httpx, 'get', offline)
    monkeypatch.setattr(llm, 'call_ollama', fake_ollama)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
    app.selectbox(key='ui_language').select('Hindi').run()
    assert not app.exception
    assert app.tabs[0].label == '🌿  सलाह लें'
    assert app.selectbox(key='askcrop').label == 'फसल'
    assert app.selectbox(key='asklang').value == 'Hindi'
    app.selectbox(key='askexample').select('vague').run()
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state['askresult']['responses'][0]['language'] == 'Hindi'
    assert any('पत्तियाँ पीली हैं' in str(element.value) for element in app.markdown)
    app.selectbox(key='ui_language').select('English').run()
    assert app.selectbox(key='asklang').value == 'English'
