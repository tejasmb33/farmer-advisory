import json

import llm

CASE = dict(language='Kannada', crop='Tomato', region='Mandya', season='Kharif',
            stage='Flowering', soil='Red soil', question='ಟೊಮೇಟೊ ಎಲೆಗಳಲ್ಲಿ ಕಂದು ಕಲೆಗಳಿವೆ')
ADVICE = dict(problem='ಎಲೆಗಳಲ್ಲಿ ಕಲೆಗಳಿವೆ', cause='ಕಾರಣ ಇನ್ನೂ ಖಚಿತವಾಗಿಲ್ಲ',
              steps=['ಎಲೆಗಳ ಎರಡೂ ಬದಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ'], prevent='ಹೊಲವನ್ನು ಸ್ವಚ್ಛವಾಗಿಡಿ',
              expert='ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ', follow_up='ಕಲೆಗಳು ಯಾವಾಗ ಆರಂಭವಾದವು?')


def test_kannada_invalid_response_retries_and_counts_both_attempts(monkeypatch):
    calls = []
    def fake_ollama(url, model, system, user, cap, *, structured=False):
        calls.append((cap, structured))
        if len(calls) == 1:
            return dict(text='{"problem":', input_tokens=100, output_tokens=1800, seconds=1, stop_reason='end_turn')
        return dict(text=json.dumps(ADVICE, ensure_ascii=False), input_tokens=100, output_tokens=400,
                    seconds=1, stop_reason='end_turn')
    monkeypatch.setattr(llm, 'call_ollama', fake_ollama)
    result = llm.run_advisory(CASE, 'V10', mode='ollama', model='local')
    assert calls == [(1800, True), (2400, True)]
    assert result['advice'] == ADVICE and not result['truncated'] and result['format_ok']
    assert result['retry_count'] == 1
    assert (result['input_tokens'], result['output_tokens'], result['total_tokens']) == (200, 2200, 2400)


def test_truncated_answer_is_not_automatically_retried(monkeypatch):
    monkeypatch.setattr(llm, 'call_ollama', lambda *args, **kwargs: dict(
        text='{"problem":', input_tokens=10, output_tokens=20, seconds=1, stop_reason='max_tokens'))
    result = llm.run_advisory(CASE, 'V10', mode='ollama', model='local')
    assert result['truncated'] and not result['format_ok'] and result['advice'] is None
    assert result['retry_count'] == 0 and len(result['calls']) == 1
