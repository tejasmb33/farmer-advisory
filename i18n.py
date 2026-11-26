"""Presentation translations. Canonical experiment values remain unchanged."""
import json
from pathlib import Path

KANNADA = json.loads(Path(__file__).with_name('translations_kn.json').read_text(encoding='utf-8'))
HINDI = json.loads(Path(__file__).with_name('translations_hi.json').read_text(encoding='utf-8'))


def translate(text, language='English'):
    if language not in ('Kannada', 'Hindi') or not isinstance(text, str):
        return text
    translations = KANNADA if language == 'Kannada' else HINDI
    if text in translations:
        return translations[text]
    if text.startswith('**') and text.endswith('**'):
        return '**' + translate(text[2:-2], language) + '**'
    if language == 'Kannada' and text.startswith('Do not combine experiments with different '):
        return 'ವಿಭಿನ್ನ ಸೆಟ್ಟಿಂಗ್‌ಗಳ ಪ್ರಯೋಗಗಳನ್ನು ಸೇರಿಸಬೇಡಿ: ' + translate(text.removeprefix('Do not combine experiments with different '), language)
    # HTML decorations retain their markup; translate the text nodes only.
    if '<' in text:
        import re
        return re.sub(r'(?<=>)[^<>]+(?=<)', lambda m: translations.get(m[0], m[0]), text)
    return text


def localize_data(value, language):
    """Translate report presentation without changing source data or export schemas."""
    if isinstance(value, dict):
        return {translate(k, language): localize_data(v, language) for k, v in value.items()}
    if isinstance(value, list):
        return [localize_data(v, language) for v in value]
    return translate(value, language)
