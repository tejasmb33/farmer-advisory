from pathlib import Path

import httpx
from streamlit.testing.v1 import AppTest

from farm_options import DISTRICTS, districts_for_language
from i18n import translate


def test_all_districts_have_localized_names_and_order():
    assert districts_for_language('English') == sorted(DISTRICTS, key=str.casefold)
    for language, script_start, script_end in [('Kannada', 0x0C80, 0x0CFF), ('Hindi', 0x0900, 0x097F)]:
        ordered = districts_for_language(language)
        assert len(ordered) == len(DISTRICTS) == 31
        assert set(ordered) == set(DISTRICTS)
        assert ordered[:4] == ['Udupi', 'Uttara Kannada', 'Kalaburagi', 'Kodagu']
        for district in ordered:
            name = translate(district, language)
            assert name != district
            assert any(script_start <= ord(char) <= script_end for char in name)


def test_district_is_preserved_when_interface_language_changes(monkeypatch):
    def offline(*args, **kwargs):
        raise httpx.ConnectError('offline test')
    monkeypatch.setattr(httpx, 'get', offline)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
    assert app.selectbox(key='askregion').value == 'Mandya'
    app.selectbox(key='askregion').select('Vijayanagara').run()
    for language, translated in [('Kannada', 'ವಿಜಯನಗರ'), ('Hindi', 'विजयनगर'), ('English', 'Vijayanagara')]:
        app.selectbox(key='ui_language').select(language).run()
        assert not app.exception
        assert app.selectbox(key='askregion').value == 'Vijayanagara'
        assert translated in app.selectbox(key='askregion').options
        assert len(app.selectbox(key='askregion').options) == 31
