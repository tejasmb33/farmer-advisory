from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import question_languages


def test_translation_preserves_original_and_validates_output(monkeypatch):
    monkeypatch.setattr(question_languages, 'call_ollama', lambda *args: {
        'text': '{"Kannada":"ಕೀಟಗಳಿವೆ", "Hindi":"कीड़े हैं"}', 'stop_reason': 'end_turn'})
    result = question_languages.translate_question('There are insects', 'English', 'model', 'http://local')
    assert result == {'English': 'There are insects', 'Kannada': 'ಕೀಟಗಳಿವೆ', 'Hindi': 'कीड़े हैं'}
    monkeypatch.setattr(question_languages, 'call_ollama', lambda *args: {'text': '{}', 'stop_reason': 'end_turn'})
    with pytest.raises(ValueError, match='valid translations'):
        question_languages.translate_question('There are insects', 'English', 'model', 'http://local')


def test_language_gap_compares_current_question_and_reviewed_translations(monkeypatch):
    import httpx
    import llm

    monkeypatch.setattr(httpx, 'get', lambda *a, **kw: (_ for _ in ()).throw(httpx.ConnectError('offline')))
    calls = []
    def translate(question, language, model, url):
        calls.append((question, language))
        return {'English': question, 'Kannada': 'ಕನ್ನಡ ಪ್ರಶ್ನೆ', 'Hindi': 'हिन्दी प्रश्न'}
    monkeypatch.setattr(question_languages, 'translate_question', translate)
    counted = []
    def count(url, model, text):
        counted.append(text)
        return {'Leaves are yellow': 10, 'ಕನ್ನಡ ಪ್ರಶ್ನೆ': 15, 'सुधारा हुआ प्रश्न': 12}[text]
    monkeypatch.setattr(llm, 'count_ollama_tokens', count)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
    app.text_area(key='askqEnglishCustom question').set_value('Leaves are yellow').run()
    app.button(key='gap_translate').click().run()
    assert not app.exception
    assert calls == [('Leaves are yellow', 'English')]
    app.text_area(key='gap_text_Hindi').set_value('सुधारा हुआ प्रश्न').run()
    app.button(key='gapbtn').click().run()
    assert not app.exception
    assert counted == ['Leaves are yellow', 'ಕನ್ನಡ ಪ್ರಶ್ನೆ', 'सुधारा हुआ प्रश्न']
    assert app.session_state['gap_question_result']['counts']['Hindi'] == 12
    app.text_area(key='askqEnglishCustom question').set_value('A different question').run()
    assert any('Translate again' in message.value for message in app.info)
    assert not any(button.key == 'gapbtn' for button in app.button)
