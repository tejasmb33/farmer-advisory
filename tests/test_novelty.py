"""Tests for the novelty features: query-aware context, V11 caching accounting, language gap."""
import json
from types import SimpleNamespace
import pandas as pd
import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from evaluate import (gap_summary, load_language_samples, measure_language_gap, proxy_summary,
                      summarize_frames, CRITERIA)
from llm import run_advisory, price_cost
from prompts import (VERSIONS, build_prompt, context_report, detect_topics, route_context, stable_prefix,
                     library_hash)

BASE = dict(language='English', crop='Tomato', region='Mandya', season='Kharif', stage='Vegetative', soil='Unknown')
ADVICE = dict(problem='p', cause='c', steps=['s'], prevent='v', expert='Ask KVK', follow_up='')
APP = Path(__file__).resolve().parents[1] / 'app.py'

@pytest.fixture(autouse=True)
def isolate_app_connections(monkeypatch):
    import httpx
    def offline(*args, **kwargs):
        raise httpx.ConnectError('offline test')
    monkeypatch.setattr(httpx, 'get', offline)
    monkeypatch.setenv('ANTHROPIC_MODEL', '')



def case(question, **extra):
    return dict(BASE, question=question, **extra)


# ---------------- query-aware selective context ----------------
@pytest.mark.parametrize('question,topic', [
    ('Insects are eating my cotton leaves', 'pest'),
    ('There are brown spots and blight on leaves', 'disease'),
    ('Which fertiliser should I add, the plants look pale', 'nutrient'),
    ('How often should I irrigate? The field is dry', 'water'),
    ('Heavy rain and hail damaged the crop', 'weather'),
    ('How do I store the grain after harvest', 'harvest'),
    ('ನನ್ನ ಬೆಳೆಗೆ ಕೀಟ ಬಂದಿದೆ', 'pest'),
    ('ಎಲೆಗಳ ಮೇಲೆ ಚುಕ್ಕೆ ಮತ್ತು ರೋಗ', 'disease'),
    ('ಗೊಬ್ಬರ ಯಾವಾಗ ಹಾಕಬೇಕು', 'nutrient'),
    ('ಗದ್ದೆಗೆ ನೀರು ಸಾಕಾಗುತ್ತಿದೆಯೇ', 'water'),
    ('ಮಳೆಯಿಂದ ಬೆಳೆ ಹಾಳಾಯಿತು', 'weather'),
    ('मेरी फसल में कीड़े लग गए हैं', 'pest'),
    ('पत्तियों पर फफूंद और धब्बे हैं', 'disease'),
    ('खाद कब डालनी चाहिए', 'nutrient'),
    ('खेत में सिंचाई कब करें', 'water'),
    ('कटाई के बाद भंडारण कैसे करें', 'harvest'),
])
def test_topics_detected_in_three_languages(question, topic):
    assert topic in detect_topics(question)


def test_english_word_start_matching_avoids_false_positives():
    assert 'disease' not in detect_topics('Please protect my field')  # 'rot' inside 'protect'
    assert detect_topics('The plants are rotting') == ['disease']


def test_pest_question_sends_only_pest_fields():
    ctx, report = route_context(case('Insects are eating the leaves', soil='Red soil'))
    assert set(ctx) == {'crop', 'stage', 'season'}
    assert 'soil' in report['fields_withheld'] and 'regional_profile' in report['fields_withheld']
    assert report['topics'] == ['pest'] and not report['fallback']


def test_nutrient_question_adds_soil_only_when_known():
    ctx, _ = route_context(case('Which fertiliser should I add?', soil='Red soil'))
    assert ctx['soil'] == 'Red soil' and 'region' not in ctx
    ctx, report = route_context(case('Which fertiliser should I add?'))
    assert 'soil' not in ctx and 'soil' in report['fields_withheld']


def test_water_question_adds_regional_note_not_status_banner():
    ctx, _ = route_context(case('How often should I irrigate?'))
    assert 'regional_profile' in ctx and 'water' in ctx['regional_profile']
    assert 'profile_status' not in ctx


def test_ambiguous_symptom_widens_selection_instead_of_guessing():
    topics = detect_topics('My leaves are turning yellow')
    assert {'disease', 'nutrient', 'water'} <= set(topics)
    ctx, _ = route_context(case('My leaves are turning yellow'))
    assert {'crop', 'stage', 'season', 'region', 'regional_profile'} <= set(ctx)


def test_unrecognised_question_falls_back_to_conservative_subset():
    ctx, report = route_context(case('My plants are dying. What should I do?'))
    assert report['fallback'] and set(ctx) == {'crop', 'region', 'season', 'stage'}


def test_selective_context_is_smaller_than_full_context():
    c = case('Insects are eating the leaves')
    v6 = build_prompt('V6', c)[1]
    v7 = build_prompt('V7', c)[1]
    assert len(v7) < len(v6)
    assert 'regional_profile' not in json.loads(v7)['context']
    assert 'profile_status' in json.loads(v6)['context']


def test_context_report_per_version():
    c = case('Insects are eating the leaves')
    assert context_report('V0', c)['mode'] == 'none'
    assert context_report('V5', c)['mode'] == 'full'
    for version in ('V7', 'V10', 'V11'):
        assert context_report(version, c)['mode'] == 'selective'


def test_safety_rules_are_never_reduced_by_routing():
    for version in ('V7', 'V10', 'V11'):
        system = build_prompt(version, case('Insects are eating the leaves'))[0]
        assert 'dosage' in system and 'local KVK' in system


# ---------------- V11 caching ----------------
class UsageClient:
    def __init__(self, **usage):
        self.messages = self; self.requests = []
        self.usage = dict(input_tokens=20, output_tokens=40, **usage)

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type='text', text=json.dumps(ADVICE))],
                               usage=SimpleNamespace(**self.usage), stop_reason='end_turn')


def test_handbook_is_substantial_and_hashed():
    text = stable_prefix('V11')
    assert len(text) > 6000 and stable_prefix('V10') == ''
    assert 'no verified agronomic facts' in text.lower()


def test_v11_system_text_matches_v10_so_only_the_guide_differs():
    c = case('Insects are eating the leaves')
    assert build_prompt('V11', c) == build_prompt('V10', c)


def test_v11_marks_guide_cacheable_and_keeps_variable_part_uncached():
    client = UsageClient()
    run_advisory(case('Insects are eating the leaves'), 'V11', mode='live', model='m', client=client)
    system = client.requests[-1]['system']
    assert isinstance(system, list) and system[0]['cache_control'] == {'type': 'ephemeral'}
    assert system[0]['text'] == stable_prefix('V11')
    assert 'cache_control' not in system[1] and 'English' in system[1]['text']
    assert client.requests[-1]['max_tokens'] == 700


def test_v11_control_run_sends_same_words_without_cache_marker():
    client = UsageClient()
    result = run_advisory(case('Insects are eating the leaves'), 'V11', mode='live', model='m', client=client, cache=False)
    system = client.requests[-1]['system']
    assert isinstance(system, str) and system.startswith(stable_prefix('V11')) and 'English' in system
    assert result['cache_enabled'] is False


def test_other_versions_never_use_the_cache():
    client = UsageClient()
    for version in ('V5', 'V10'):
        result = run_advisory(case('Insects are eating the leaves'), version, mode='live', model='m', client=client)
        assert isinstance(client.requests[-1]['system'], str) and result['cache_enabled'] is False


def test_cache_write_usage_is_added_to_total_input_and_billed_at_write_rate():
    client = UsageClient(cache_creation_input_tokens=1000, cache_read_input_tokens=0)
    r = run_advisory(case('Insects are eating the leaves'), 'V11', mode='live', model='m', client=client,
                     price_in=2, price_out=10)
    assert r['input_tokens'] == 1020 and r['uncached_input_tokens'] == 20 and r['cache_write_tokens'] == 1000
    assert r['total_tokens'] == 1060 and r['input_tokens'] + r['output_tokens'] == r['total_tokens']
    assert r['cost_weighted_input_tokens'] == pytest.approx(20 + 1000 * 1.25)
    assert r['cost_usd'] == pytest.approx((20 * 2 + 1000 * 2 * 1.25 + 40 * 10) / 1e6)


def test_cache_read_is_cheap_in_cost_but_not_in_raw_tokens():
    write = run_advisory(case('Insects are eating the leaves'), 'V11', mode='live', model='m', price_in=2, price_out=10,
                         client=UsageClient(cache_creation_input_tokens=1000, cache_read_input_tokens=0))
    read = run_advisory(case('Insects are eating the leaves'), 'V11', mode='live', model='m', price_in=2, price_out=10,
                        client=UsageClient(cache_creation_input_tokens=0, cache_read_input_tokens=1000))
    assert read['total_tokens'] == write['total_tokens']          # raw tokens unchanged
    assert read['cost_usd'] < write['cost_usd'] / 4               # output tokens dilute the saving; input cost falls ~10x
    assert read['cost_weighted_input_tokens'] == pytest.approx(20 + 1000 * 0.1)
    assert read['cost_weighted_input_tokens'] < write['cost_weighted_input_tokens'] / 10


def test_model_specific_read_multiplier_is_configurable():
    r = run_advisory(case('Insects are eating the leaves'), 'V11', mode='live', model='m', price_in=2, price_out=10,
                     client=UsageClient(cache_read_input_tokens=1000), cache_read_mult=0.05)
    assert r['cost_weighted_input_tokens'] == pytest.approx(20 + 50)


def test_price_cost_backward_compatible_and_validates():
    assert price_cost(1000, 200, 3, 15) == pytest.approx(.006)
    assert price_cost(1, 1) is None
    with pytest.raises(ValueError):
        price_cost(1, 1, 1, 1, read_mult=-1)


def test_demo_mode_reports_context_but_no_usage():
    r = run_advisory(case('Insects are eating the leaves'), 'V11')
    assert r['context_report']['mode'] == 'selective' and r['total_tokens'] is None
    assert r['cache_read_tokens'] is None and r['cost_weighted_input_tokens'] is None


def test_library_hash_changes_when_guide_changes(tmp_path, monkeypatch):
    import prompts
    before = library_hash()
    guide = prompts.ROOT / 'data/handbook.md'
    original = guide.read_bytes()
    try:
        guide.write_bytes(original + b'\nextra')
        assert library_hash() != before
    finally:
        guide.write_bytes(original)
    assert library_hash() == before


def test_summary_adds_weighted_tokens_when_cache_columns_present():
    rows, maps, scores = [], [], []
    for i, (v, inp, w, r_, cw) in enumerate([('V5', 100, 0, 0, 100.0), ('V11', 600, 0, 500, 150.0)]):
        rows.append(dict(record_id=f'r{i}', mode='live', version=v, language='English', input_tokens=inp, output_tokens=10,
                         total_tokens=inp + 10, cost_usd=None, seconds=.5, cache_write_tokens=w, cache_read_tokens=r_,
                         cost_weighted_input_tokens=cw))
        maps.append(dict(blind_id=f'b{i}', record_id=f'r{i}'))
        scores.append(dict(blind_id=f'b{i}', **{c: 4 for c in CRITERIA}))
    _, summary = summarize_frames(pd.DataFrame(rows), pd.DataFrame(scores), pd.DataFrame(maps))
    v11 = summary[summary.version == 'V11'].iloc[0]
    assert v11.total_tokens > 100 * 1.0 + 10                      # raw tokens went UP (long guide)
    assert v11.weighted_tokens == pytest.approx(160)
    assert v11.weighted_savings_pct == pytest.approx((1 - 160 / 110) * 100)


# ---------------- language gap ----------------
def test_language_samples_load_and_validate():
    samples = load_language_samples()
    assert set(samples.language) == {'English', 'Kannada', 'Hindi'}
    bad = samples[~((samples.id == samples.id.iloc[0]) & (samples.language == 'Hindi'))]
    bad_path = Path(__file__).parent / '_bad_samples.csv'
    try:
        bad.to_csv(bad_path, index=False)
        with pytest.raises(ValueError, match='all three languages'):
            load_language_samples(bad_path)
    finally:
        bad_path.unlink(missing_ok=True)


def test_proxy_summary_is_real_and_english_is_baseline():
    proxy = proxy_summary(load_language_samples())
    english = proxy[proxy.language == 'English'].iloc[0]
    assert english.chars_ratio_to_english == pytest.approx(1) and english.bytes_ratio_to_english == pytest.approx(1)
    kannada = proxy[proxy.language == 'Kannada'].iloc[0]
    assert kannada.bytes_ratio_to_english > 1                    # Kannada uses 3 bytes per character in UTF-8


def test_measure_language_gap_with_fake_counter():
    samples = load_language_samples()
    factor = {'English': 1, 'Kannada': 4, 'Hindi': 3}
    lookup = {row['text']: factor[row['language']] * 10 for row in samples.to_dict('records')}
    rows, summary = measure_language_gap(samples, lambda text: lookup[text], 'test-model')
    assert len(rows) == len(samples) and (rows.model == 'test-model').all()
    ratios = dict(zip(summary.language, summary.ratio_to_english))
    assert ratios['English'] == 1 and ratios['Kannada'] == pytest.approx(4) and ratios['Hindi'] == pytest.approx(3)


def test_gap_summary_ratio():
    df = pd.DataFrame(dict(language=['English', 'Kannada'], v=[10, 25]))
    assert gap_summary(df, 'v').set_index('language').ratio_to_english['Kannada'] == pytest.approx(2.5)


# ---------------- app ----------------
def test_app_shows_query_aware_context_and_v11_in_demo():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    at.radio[0].set_value('Offline demo').run()
    assert not at.exception
    at.selectbox(key='askexample').select('unsafe').run()
    at.selectbox(key='askv').select('V11')      # form widgets are applied on submit, so no run() in between
    at.button[0].click().run()
    assert not at.exception
    result = at.session_state['askresult']['responses'][0]
    assert result['version'] == 'V11' and result['context_report']['mode'] == 'selective'
    assert any('Query-aware context' in str(c.value) for c in at.caption)


def test_app_language_gap_tab_offline_and_live_gating():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    at.radio[0].set_value('Offline demo').run()
    assert not at.exception
    assert any('Language gap' in tab.label for tab in at.tabs)
    assert any('Switch to Live API' in str(i.value) for i in at.info)
    at.radio[0].set_value('Live API').run()
    assert not at.exception
    assert any(b.key == 'gapbtn' for b in at.button)
    at.button(key='gapbtn').click().run()
    assert any('model ID' in e.value for e in at.error)


def test_app_kannada_ui_new_strings_translated():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    at.radio[0].set_value('Offline demo').run()
    at.selectbox(key='ui_language').select('Kannada').run()
    assert not at.exception
    assert any('ಭಾಷಾ ಅಂತರ' in tab.label for tab in at.tabs)


def test_versions_include_v11():
    assert 'V11' in VERSIONS and len(VERSIONS) == 12


def test_ollama_v11_sends_guide_without_claiming_cache(monkeypatch):
    import llm
    seen = {}
    def fake_ollama(url, model, system, user, cap, *, structured=False):
        seen.update(system=system, cap=cap)
        return dict(text=json.dumps(ADVICE), input_tokens=100, output_tokens=20, seconds=0.1, stop_reason='end_turn')
    monkeypatch.setattr(llm, 'call_ollama', fake_ollama)
    result = run_advisory(case('Insects are eating leaves'), 'V11', mode='ollama', model='local')
    assert seen['system'].startswith(stable_prefix('V11'))
    assert seen['cap'] == 700 and result['mode'] == 'ollama'
    assert result['cache_enabled'] is False and result['cache_read_tokens'] == 0
    assert result['total_tokens'] == 120 and result['cost_usd'] == 0
