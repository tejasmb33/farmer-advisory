import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from farm_options import CROPS, DISTRICTS


def test_districts_and_crops_include_custom_option():
    assert len(DISTRICTS) == len(set(DISTRICTS)) == 31
    assert {'Bengaluru South', 'Vijayanagara', 'Mandya'} <= set(DISTRICTS)
    assert {'Rice', 'Coffee', 'Arecanut', 'Other'} <= set(CROPS)


def test_voice_transcript_and_custom_crop_reach_advice(monkeypatch):
    import httpx
    import llm
    import streamlit.components.v1 as components

    monkeypatch.setattr(httpx, 'get', lambda *a, **kw: (_ for _ in ()).throw(httpx.ConnectError('offline')))
    transcript = {'session': 'first-utterance', 'sequence': 1, 'text': 'The leaves'}
    monkeypatch.setattr(components, 'declare_component', lambda *a, **kw:
                        lambda **args: transcript.copy()
                        if args['key'].startswith('ask') else None)
    seen = {}

    def fake_ollama(url, model, system, user, cap, *, structured=False):
        seen['payload'] = json.loads(user)
        text = json.dumps(dict(problem='spots', cause='uncertain', steps=['check'],
                               prevent='monitor', expert='consult expert', follow_up=''))
        return dict(text=text, input_tokens=100, output_tokens=30, seconds=.1, stop_reason='end_turn')

    monkeypatch.setattr(llm, 'call_ollama', fake_ollama)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
    assert not app.exception
    assert app.text_area(key='askqEnglishCustom question').value == 'The leaves'
    transcript.update(sequence=2, text='The leaves have brown spots')
    app.run()
    assert app.text_area(key='askqEnglishCustom question').value == 'The leaves have brown spots'
    app.selectbox(key='askcrop').select('Other').run()
    app.text_input(key='askcustom_crop').set_value('Medicinal herb').run()
    app.selectbox(key='askregion').select('Vijayanagara').run()
    assert app.text_area(key='askqEnglishCustom question').value == 'The leaves have brown spots'
    app.button(key='asksubmit').click().run()
    assert not app.exception
    assert seen['payload']['question'] == 'The leaves have brown spots'
    assert seen['payload']['context']['crop'] == 'Medicinal herb'
    assert seen['payload']['context']['region'] == 'Vijayanagara'
