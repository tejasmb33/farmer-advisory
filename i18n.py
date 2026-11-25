"""Presentation translations. Canonical experiment values remain unchanged."""
import json
from pathlib import Path

KANNADA = json.loads(Path(__file__).with_name('translations_kn.json').read_text(encoding='utf-8'))


def translate(text, language='English'):
    if language != 'Kannada' or not isinstance(text, str):
        return text
    if text in KANNADA:
        return KANNADA[text]
    if text.startswith('**') and text.endswith('**'):
        return '**' + translate(text[2:-2], language) + '**'
    if text.startswith('Do not combine experiments with different '):
        return 'ವಿಭಿನ್ನ ಸೆಟ್ಟಿಂಗ್‌ಗಳ ಪ್ರಯೋಗಗಳನ್ನು ಸೇರಿಸಬೇಡಿ: ' + translate(text.removeprefix('Do not combine experiments with different '), language)
    # HTML decorations retain their markup; translate the text nodes only.
    if '<' in text:
        import re
        return re.sub(r'(?<=>)[^<>]+(?=<)', lambda m: KANNADA.get(m[0], m[0]), text)
    return text


def localize_data(value, language):
    """Translate report presentation without changing source data or export schemas."""
    if isinstance(value, dict):
        return {translate(k, language): localize_data(v, language) for k, v in value.items()}
    if isinstance(value, list):
        return [localize_data(v, language) for v in value]
    return translate(value, language)
