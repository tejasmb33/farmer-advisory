"""Farmwise — multilingual prompt engineering workbench."""
import os
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from prompts import VERSIONS, FIELDS, build_prompt, library_hash, stable_prefix
from llm import run_advisory, count_ollama_tokens
from demo import HEADINGS, DISCLAIMER
from i18n import translate
from farm_options import CROPS, districts_for_language
from question_languages import LANGUAGES, translate_question

st.set_page_config(page_title=translate('Farmwise · Advisory Lab', st.session_state.get('ui_language', 'English')),page_icon='🌱',layout='wide')

ui_language = st.sidebar.selectbox("Language / ಭಾಷೆ / भाषा", ["English", "Kannada", "Hindi"],
    format_func=lambda value: {"English": "English", "Kannada": "ಕನ್ನಡ", "Hindi": "हिन्दी"}[value], key="ui_language")
t = lambda text: translate(text, ui_language)
if st.session_state.get('_previous_ui_language') != ui_language:
    for prefix in ('ask', 'compare'):
        st.session_state[prefix+'lang'] = ui_language
    st.session_state['_previous_ui_language'] = ui_language

load_dotenv()
ROOT=Path(__file__).parent
speech_input = components.declare_component('farmwise_speech_input', path=str(ROOT / 'speech_input'))
FIELD_LABELS={'crop':'Crop','region':'District','season':'Season','stage':'Growth stage','soil':'Soil, if known','regional_profile':'Regional note'}
TOPIC_LABELS={'pest':'Pests','disease':'Disease','nutrient':'Nutrients','water':'Water','weather':'Weather','harvest':'Harvest and storage'}
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&family=Noto+Sans+Kannada:wght@400;500;600;700&display=swap');

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

html, body, [class*="css"], .stApp {
  font-family: 'DM Sans', 'Noto Sans Kannada', sans-serif;
  color: #132a1c;
}
.stApp {
  background: linear-gradient(135deg, #eef7ef 0%, #f5faf6 48%, #fcf8ec 100%);
}
h1, h2, h3, h4 {
  font-family: 'Manrope', 'Noto Sans Kannada', sans-serif !important;
  letter-spacing: -0.03em;
  color: #0f2e1d !important;
}
h1 {
  font-size: 3rem !important;
  line-height: 1.12 !important;
  font-weight: 800 !important;
  background: linear-gradient(120deg, #0f3d26 0%, #1f7347 55%, #b88214 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Main area text contrast */
.stApp p, .stApp li, .stApp label, .stApp span,
[data-testid="stWidgetLabel"] p,
[data-testid="stMarkdownContainer"] p {
  color: #132a1c;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: #3f5e4b !important;
  font-size: 0.87rem !important;
}

/* Rich Emerald Forest Sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #103322 0%, #184931 55%, #123926 100%);
  border-right: 3px solid #eab338;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: #f2faf4 !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: #bde0c8 !important;
}
[data-testid="stSidebar"] hr {
  border-color: rgba(234, 179, 56, 0.35) !important;
}
/* Keep sidebar inputs bright & legible */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] input {
  background-color: #ffffff !important;
  color: #132a1c !important;
  border-color: #8cc2a1 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {
  color: #132a1c !important;
}
[data-testid="stSidebar"] .brand {
  font-size: 1.75rem;
  font-weight: 800;
  color: #ffffff !important;
  letter-spacing: -0.04em;
}
[data-testid="stSidebar"] .caption {
  font-size: 0.76rem;
  color: #f6cb63 !important;
  font-weight: 700;
  letter-spacing: 0.12em;
}
[data-testid="stSidebar"] .badge {
  display: inline-block;
  background: rgba(246, 203, 99, 0.18);
  color: #fde192 !important;
  border: 1px solid rgba(246, 203, 99, 0.5);
  padding: 6px 13px;
  border-radius: 30px;
  font-size: 0.76rem;
  font-weight: 600;
  margin-bottom: 8px;
}

/* Elevated Form Card */
[data-testid="stForm"] {
  background: #ffffff;
  border: 1px solid #cce3d2;
  border-top: 4px solid #1f7a4c;
  border-radius: 18px;
  padding: 26px !important;
  box-shadow: 0 12px 32px rgba(18, 66, 40, 0.08);
  animation: fadeInUp 0.35s ease-out;
}

/* Inputs, selectboxes, textareas in main area */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
textarea {
  background-color: #f7fbf8 !important;
  border: 1.5px solid #c2dcc9 !important;
  color: #132a1c !important;
  border-radius: 11px !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}
[data-baseweb="select"] > div:hover,
textarea:hover {
  border-color: #1f7a4c !important;
  background-color: #ffffff !important;
}

/* Vibrant Primary CTA Button */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
  background: linear-gradient(135deg, #18633d 0%, #228753 55%, #2ea063 100%) !important;
  color: #ffffff !important;
  border: 0 !important;
  border-radius: 12px !important;
  padding: 0.72rem 1.4rem !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  letter-spacing: 0.02em;
  box-shadow: 0 6px 18px rgba(24, 99, 61, 0.32);
  transition: transform 0.16s ease, box-shadow 0.16s ease, filter 0.16s ease;
}
/* Place the speech control inside the question textarea without covering text. */
.st-key-askquestion_area, .st-key-comparequestion_area { position: relative; }
.st-key-askquestion_area [data-testid="stElementContainer"]:has(iframe[title*="farmwise_speech_input"]),
.st-key-comparequestion_area [data-testid="stElementContainer"]:has(iframe[title*="farmwise_speech_input"]) {
  position: absolute; top: 32px; right: 8px; width: 44px !important; z-index: 2;
}
.st-key-askquestion_area textarea, .st-key-comparequestion_area textarea { padding-right: 56px !important; }
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(24, 99, 61, 0.4);
  filter: brightness(1.06);
}
.stButton > button[kind="primary"] p,
.stFormSubmitButton > button[kind="primary"] p {
  color: #ffffff !important;
}

/* Colorful Metric Cards */
[data-testid="stMetric"] {
  background: linear-gradient(180deg, #ffffff 0%, #f8fcf9 100%);
  border: 1px solid #cfe3d4;
  border-left: 5px solid #1f7a4c;
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 6px 16px rgba(18, 66, 40, 0.06);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(18, 66, 40, 0.12);
}
[data-testid="stMetricLabel"] p { color: #3d634d !important; font-weight: 700 !important; }
[data-testid="stMetricValue"] {
  font-family: 'Manrope', 'Noto Sans Kannada', sans-serif;
  font-size: 1.8rem !important;
  color: #103d25 !important;
  font-weight: 800 !important;
}

/* Colorful Pill Tabs */
[data-testid="stTabs"] [role="tablist"] {
  gap: 10px;
  background: #e1efe4;
  padding: 6px;
  border-radius: 14px;
  border: 1px solid #c6dfc9;
}
[data-testid="stTabs"] button {
  font-size: 0.95rem !important;
  font-weight: 600 !important;
  color: #214d35 !important;
  border-radius: 10px !important;
  padding: 8px 16px !important;
  border: none !important;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.15s ease;
}
[data-testid="stTabs"] button:hover {
  background-color: #cfe6d4 !important;
  color: #0f2e1d !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  background: linear-gradient(135deg, #18633d 0%, #248653 100%) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(24, 99, 61, 0.28);
}
[data-testid="stTabs"] button[aria-selected="true"] p {
  color: #ffffff !important;
}

/* Layout & Hero Components */
.block-container { max-width: 1320px; padding-top: 2rem; padding-bottom: 3rem; }
.kicker {
  display: inline-block;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: #ffffff !important;
  background: linear-gradient(90deg, #18633d 0%, #278a57 100%);
  padding: 6px 14px;
  border-radius: 999px;
  margin-bottom: 14px;
  box-shadow: 0 4px 12px rgba(24, 99, 61, 0.2);
}
.intro { font-size: 1.08rem; color: #355442 !important; max-width: 650px; line-height: 1.65; }
.hero {
  background: linear-gradient(135deg, #165937 0%, #21784b 60%, #2b915b 100%);
  border-radius: 20px;
  padding: 24px 28px;
  border: 2px solid #eab338;
  margin: 8px 0 20px 0;
  box-shadow: 0 12px 28px rgba(22, 89, 55, 0.22);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.hero:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 34px rgba(22, 89, 55, 0.3);
}
.hero h3 { color: #ffffff !important; margin: 8px 0 6px 0 !important; }
.hero p { color: #e1f5e8 !important; margin-bottom: 0; font-size: 0.95rem; }

/* A calmer, more readable workspace */
.stApp { background: #f5f7f1; }
[data-testid="stHeader"] { background: rgba(245,247,241,.94); }
[data-testid="stSidebar"] { background: #153b2c; border-right: 1px solid #315a43; }
[data-testid="stSidebar"] .brand { font-size: 1.9rem; }
[data-testid="stSidebar"] .caption { color: #d9bd77 !important; letter-spacing: .14em; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #c1d7c7 !important; line-height: 1.6; }
.block-container { max-width: 1220px; padding-top: 3.5rem; padding-bottom: 4rem; }
h1 { font-size: clamp(2.5rem, 4vw, 3.6rem) !important; letter-spacing: -.055em; }
h2, h3 { letter-spacing: -.035em; }
.kicker { background: #e5efe2; color: #386548 !important; box-shadow: none; padding: 8px 14px; }
.intro { color: #526b59 !important; font-size: 1.08rem; }
.hero { background: #245c40; border: 1px solid #3e7855; border-radius: 24px; padding: 28px; box-shadow: 0 14px 32px rgba(31,76,49,.14); }
.hero h3 { color: #fff !important; }
.hero p { color: #e4f1e4 !important; line-height: 1.6; }
[data-testid="stForm"] { border: 1px solid #dce8d9; border-top: 1px solid #dce8d9; border-radius: 20px; padding: 28px !important; box-shadow: 0 12px 36px rgba(35,70,43,.06); }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea { background: #fff !important; border: 1px solid #cbdacb !important; border-radius: 10px !important; }
[data-testid="stTabs"] [role="tablist"] { background: #e9f0e5; border: 1px solid #dae6d8; border-radius: 15px; padding: 6px; gap: 4px; flex-wrap: wrap; }
[data-testid="stTabs"] button { padding: 10px 16px !important; }
[data-testid="stTabs"] button[aria-selected="true"] { background: #245c40 !important; box-shadow: 0 3px 10px rgba(36,92,64,.18); }
[data-testid="stMetric"] { border-left: 1px solid #dce8d9; box-shadow: 0 8px 24px rgba(35,70,43,.06); }
@media (max-width: 640px) {
  .block-container { padding-top: 2rem; }
  [data-testid="stForm"] { padding: 18px !important; }
  [data-testid="stTabs"] button { padding: 8px 10px !important; }
}

/* Farmwise workspace */
.stApp {
  background: radial-gradient(ellipse at 85% 0%, #e8efdc 0%, transparent 38%), #f8f8f2;
}
[data-testid="stHeader"] { background: rgba(248, 248, 242, .92); }
[data-testid="stSidebar"] {
  background: linear-gradient(165deg, #173c2c 0%, #102f23 100%);
  border-right: 1px solid #315a43;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 1rem; }
[data-testid="stSidebar"] .brand { font-family: 'Manrope', sans-serif; font-size: 1.85rem; }
[data-testid="stSidebar"] .caption { font-size: .65rem; letter-spacing: .16em; }
[data-testid="stSidebar"] hr { border-color: rgba(218, 206, 157, .22) !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div {
  border: 1px solid #789885 !important;
  border-radius: 10px !important;
}
.block-container { max-width: 1260px; padding-top: 3.4rem; }
h1 {
  background: none;
  -webkit-text-fill-color: #163e2c;
  color: #163e2c !important;
  font-size: clamp(2.8rem, 4.4vw, 4.3rem) !important;
  line-height: 1.05 !important;
  letter-spacing: -.06em;
  max-width: 720px;
}
h2 { font-weight: 700 !important; }
.kicker {
  color: #376849 !important;
  background: #e5eedf;
  border: 1px solid #d4e4d0;
  font-size: .68rem;
  letter-spacing: .12em;
  padding: 8px 13px;
  margin-bottom: 8px;
}
.intro { max-width: 600px; color: #526b59 !important; line-height: 1.7; }
.hero {
  position: relative;
  overflow: hidden;
  min-height: 230px;
  padding: 27px 26px;
  background: linear-gradient(145deg, #245e40, #173e2d);
  border: 1px solid #417650;
  border-radius: 22px;
  box-shadow: 0 15px 32px rgba(32, 72, 46, .16);
}
.hero::after {
  content: '';
  position: absolute;
  width: 170px;
  height: 170px;
  right: -65px;
  bottom: -75px;
  border: 25px solid rgba(215, 229, 171, .12);
  border-radius: 50%;
}
.hero h3 { color: #fff !important; font-size: 1.45rem !important; line-height: 1.2; }
.hero p { color: #deebd9 !important; }
[data-testid="stAlert"] { border-radius: 13px; }
[data-testid="stTabs"] [role="tablist"] {
  gap: 5px;
  background: #eaf0e5;
  border: 1px solid #dce8d9;
  padding: 6px;
  border-radius: 15px;
}
[data-testid="stTabs"] button {
  min-height: 44px;
  font-size: .9rem !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  background: #245c40 !important;
  box-shadow: 0 3px 9px rgba(23, 60, 44, .2);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
[data-testid="stForm"] {
  background: #fff;
  border: 1px solid #e0e9dc;
  border-radius: 20px;
  box-shadow: 0 12px 40px rgba(38, 74, 47, .07);
}
[data-testid="stWidgetLabel"] p { font-weight: 600; font-size: .86rem; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea {
  border-color: #d3dfd1 !important;
  box-shadow: none;
}
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"] > div:focus-within, textarea:focus {
  border-color: #3d8056 !important;
  box-shadow: 0 0 0 3px rgba(61, 128, 86, .14) !important;
}
.stFormSubmitButton > button[kind="primary"] {
  background: #245f40 !important;
  min-height: 48px;
  box-shadow: 0 5px 14px rgba(36, 95, 64, .2);
}
@media (max-width: 640px) {
  .block-container { padding-top: 2rem; }
  h1 { font-size: 2.7rem !important; }
  .hero { min-height: 0; }
  [data-testid="stTabs"] [role="tablist"] { overflow-x: auto; flex-wrap: nowrap; }
}
</style>''',unsafe_allow_html=True)

with st.sidebar:
    st.markdown(t('<div class="brand">🌱 farmwise</div><p class="caption">MULTILINGUAL ADVISORY LAB</p>'),unsafe_allow_html=True)
    st.divider()
    st.markdown(t('**Your workspace**'))
    st.caption(t('Prompt engineering for practical farm advice. Three languages. Twelve approaches.'))
    mode='ollama'
    ollama_url=os.getenv('OLLAMA_BASE_URL','http://localhost:11434')
    api_key=None;price_in=None;price_out=None;price_date=''
    model=os.getenv('OLLAMA_MODEL','')
    if not model:
        try:
            import httpx
            tags_resp=httpx.get(f"{ollama_url.rstrip('/')}/api/tags",timeout=2.0)
            if tags_resp.status_code==200:
                models=[m['name'] for m in tags_resp.json().get('models',[]) if m.get('name')]
                if models: model=models[0]
        except Exception:
            pass
    if not model:
        model='llama3.2'
    st.divider()
    st.markdown(t('**Built for Karnataka**'))
    st.caption(t('31 districts · many crops')+'\n\n'+t('English')+' · ಕನ್ನಡ · '+t('Hindi'))
    st.caption(t('Local research prototype. Runs locally via Ollama with no automatic disk storage of questions.'))

st.markdown(t('<div class="kicker">SMALLER PROMPTS. THOUGHTFUL ADVICE.</div>'),unsafe_allow_html=True)
left,right=st.columns([3,1])
with left:
    st.title(t('Better advice.\nFewer tokens.'))
    st.markdown(t('<p class="intro">Explore how prompt design changes farm advice across languages — and measure what it costs.</p>'),unsafe_allow_html=True)
with right:
    st.markdown(t('<div class="hero"><span style="font-size:2.5rem">🌾</span><h3>Rooted in context.</h3><p>Designed for local questions.<br>Measured with care.</p></div>'),unsafe_allow_html=True)

advisory,compare,library,gaptab=st.tabs([t('🌿  Ask an adviser'),t('⇄  Compare prompts'),t('⌘  Prompt library'),t('🔤  Language gap')])


def display_frame(frame):
    return frame.map(lambda value:t(value) if isinstance(value,str) else value).rename(columns=t)


def case_form(prefix, comparison=False):
    tests=pd.read_csv(ROOT/'data/test_queries.csv',keep_default_na=False)
    lang=st.selectbox(t('Response language'),['English','Kannada','Hindi'],key=prefix+'lang',format_func=t)
    examples=tests[tests.language==lang]
    category=st.selectbox(t('Start with an example'), ['Custom question']+list(examples.category),key=prefix+'example',format_func=lambda s:t(s) if ui_language in ('Kannada', 'Hindi') else s.replace('_',' ').capitalize())
    example=examples[examples.category==category]
    default=example.iloc[0].question if not example.empty else ''
    with st.container(border=True):
        a,b,c=st.columns(3)
        crop=a.selectbox(t('Crop'),CROPS,key=prefix+'crop',format_func=t)
        districts=districts_for_language(ui_language)
        region=b.selectbox(t('District'),districts,index=districts.index('Mandya'),key=prefix+'region',format_func=t)
        season=c.selectbox(t('Season'),['Kharif','Rabi','Summer'],key=prefix+'season',format_func=t)
        if crop == 'Other':
            crop=st.text_input(t('Enter your crop'),max_chars=100,key=prefix+'custom_crop').strip()
        a,b=st.columns(2)
        stage=a.selectbox(t('Growth stage'),['Vegetative','Seedling','Flowering','Fruiting','Harvest'],key=prefix+'stage',format_func=t)
        soil=b.selectbox(t('Soil, if known'),['Unknown','Red soil','Black soil','Sandy loam','Clay loam'],key=prefix+'soil',format_func=t)
        question_key=prefix+'q'+lang+category
        if question_key not in st.session_state:
            st.session_state[question_key]=default
        with st.container(key=prefix+'question_area'):
            voice=speech_input(
                locale={'English':'en-IN', 'Kannada':'kn-IN', 'Hindi':'hi-IN'}[lang],
                start_label=t('🎙️ Speak your question'), stop_label=t('⏹ Stop listening'),
                listening=t('Listening… speak in the selected response language.'),
                unsupported=t('Speech recognition is unavailable in this browser. You can type your question.'),
                error=t('Microphone or speech recognition failed. Check permission and try again.'),
                key=prefix+'voice'+lang+category, default=None)
            last_voice_key=question_key+'_last_voice'
            if isinstance(voice, dict) and voice.get('session') and isinstance(voice.get('sequence'), int):
                previous=st.session_state.get(last_voice_key, {})
                current=st.session_state[question_key]
                if previous.get('session') != voice['session']:
                    previous={'session':voice['session'], 'sequence':0, 'inserted':'', 'editable':True}
                if voice['sequence'] > previous['sequence']:
                    inserted=previous['inserted']
                    if inserted and not current.endswith(inserted):
                        previous['editable']=False
                    if previous['editable']:
                        base=current[:-len(inserted)] if inserted else current
                        spoken=str(voice.get('text', '')).strip()
                        updated=(base.rstrip()+' '+spoken).strip()[:4000]
                        st.session_state[question_key]=updated
                        previous['inserted']=updated[len(base.rstrip()):].strip() if base.strip() else updated
                    previous['sequence']=voice['sequence']
                    st.session_state[last_voice_key]=previous
            question=st.text_area(t('What is happening in your field?'),max_chars=4000,height=105,
                                  placeholder=t('Describe symptoms, when they began, and how many plants are affected.'),key=question_key)
        st.caption(t('Speech recognition is provided by your browser and may send audio to its speech service.'))
        if comparison:
            a,b=st.columns(2)
            first=a.selectbox(t('Reference prompt'),list(VERSIONS),index=5,format_func=lambda v:f'{v} · {t(VERSIONS[v])}',key=prefix+'v1')
            second=b.selectbox(t('Compare with'),list(VERSIONS),index=10,format_func=lambda v:f'{v} · {t(VERSIONS[v])}',key=prefix+'v2')
            versions=[first,second]
        else:
            versions=[st.selectbox(t('Prompt approach'),list(VERSIONS),index=10,format_func=lambda v:f'{v} · {t(VERSIONS[v])}',key=prefix+'v')]
        submitted=st.button(t('Compare advice') if comparison else t('Generate advice'),type='primary',width='stretch',key=prefix+'submit')
    return submitted,dict(language=lang,crop=crop,region=region,season=season,stage=stage,soil=soil,question=question),versions


def execute(prefix,submitted,case,versions):
    if not submitted:return
    st.session_state.pop(prefix+'result',None)
    if not case['crop']:
        st.warning(t('Enter your crop before continuing.'));return
    if not case['question'].strip():
        st.warning(t('Describe a crop problem or choose an example first.'));return
    if len(set(versions))!=len(versions):
        st.warning(t('Choose two different prompt versions.'));return
    responses=[]
    with st.spinner(t('Preparing advice…') if mode=='demo' else t('Requesting advice and collecting exact usage…')):
        for version in versions:
            try:
                result=run_advisory(case,version,mode=mode,model=model,api_key=api_key,price_in=price_in,price_out=price_out,ollama_url=ollama_url)
                result['price_date']=price_date
                responses.append(result)
            except Exception as exc:
                if isinstance(exc,ValueError): st.error(t(str(exc)))
                else: st.error(t('Ollama request failed. Make sure Ollama is running and the model is pulled.') + f' ({type(exc).__name__})')
                break
    if responses:
        st.session_state[prefix+'result']={'case':case,'responses':responses}


def render_result(result):
    st.markdown(f"### {result['version']} · {t(VERSIONS[result['version']])}")
    if result['mode']=='demo':st.caption(t('Prewritten offline example · not model output'))
    if result.get('truncated'):st.error(t('The answer was cut off and cannot be used. Please try again or use another model.'))
    if result.get('format_required') and not result.get('format_ok'):
        st.warning(t('The model could not produce a complete structured answer. Please try again or use another model.'))
    if result.get('retry_count'):
        st.caption(t('The first response was incomplete or invalid, so the app retried. Token counts include both attempts.'))
    if int(result['version'][1:])<4 and result['mode'] in ('live','ollama'):
        st.warning(t('Research baseline: this version has limited safety instructions. Review output before use.'))
    if result['advice'] and not result.get('truncated'):
        st.warning(t('AI-generated advice can be inaccurate. Confirm it with a local agriculture officer or KVK before acting.'))
    with st.container(border=True):
        if result['advice'] and not result.get('truncated'):
            for key,heading in zip(FIELDS,HEADINGS[result['language']]):
                content=result['advice'][key]
                if not content:continue
                st.markdown('**'+heading+'**')
                if isinstance(content,list):
                    for item in content: st.write('• '+item)
                else:st.write(content)
        elif not result.get('format_required') and not result.get('truncated'):
            st.write(result['text'])
    a,b,c=st.columns(3)
    a.metric(t('Input tokens'),result['input_tokens'] if result['input_tokens'] is not None else '—')
    b.metric(t('Output tokens'),result['output_tokens'] if result['output_tokens'] is not None else '—')
    c.metric(t('Total tokens'),result['total_tokens'] if result['total_tokens'] is not None else '—')
    cost=result.get('cost_usd')
    st.caption(t('Cost')+f": {'$'+format(cost,'.6f') if cost is not None else t('not measured / pricing not configured')} · "+t('Time')+f": {str(result['seconds'])+' '+t('s') if result['seconds'] is not None else t('not measured')} · "+t('Calls')+f": {len(result['calls'])}")
    report=result.get('context_report')
    if report and report['mode']=='selective':
        topics=', '.join(t(TOPIC_LABELS[x]) for x in report['topics']) if report['topics'] else t('none recognised')
        sent=', '.join(t(FIELD_LABELS[f]) for f in report['fields_sent']) or '—'
        held=', '.join(t(FIELD_LABELS[f]) for f in report['fields_withheld']) or '—'
        st.caption('🎯 '+t('Query-aware context')+f' · {t("Topics detected")}: {topics} · {t("Sent")}: {sent} · {t("Withheld")}: {held}'+(' · '+t('conservative fallback') if report['fallback'] else ''))
    if result['mode']=='live' and (result['version']=='V11' or result.get('cache_write_tokens') or result.get('cache_read_tokens')):
        a,b,c=st.columns(3)
        a.metric(t('Cache write tokens'),result['cache_write_tokens']);b.metric(t('Cache read tokens'),result['cache_read_tokens'])
        c.metric(t('Cost-weighted input tokens'),f"{result['cost_weighted_input_tokens']:.0f}",help=t('Uncached + cache writes and reads at their price multiples. Caching lowers this, not the raw token count.'))
        if result['version']=='V11':
            if not result.get('cache_enabled'):st.info(t('Control run: the same guide was sent without a cache marker.'))
            elif not (result['cache_write_tokens'] or result['cache_read_tokens']):st.warning(t('No cache activity detected. The guide may be shorter than the model minimum cacheable length. Check the usage fields before claiming caching savings.'))
            elif result['cache_read_tokens']==0:st.caption(t('This request wrote the cache. Run again within the cache lifetime (5 minutes by default) to see cache reads.'))
    st.caption(DISCLAIMER[result['language']])



def show_saved(prefix):
    bundle=st.session_state.get(prefix+'result')
    if not bundle:return
    st.divider()
    case=bundle['case'];responses=bundle['responses']
    st.caption(f"{t('Result snapshot')} · {t(case['crop'])} · {t(case['region'])} · {t(case['language'])} · {t('Offline demo' if responses[0]['mode']=='demo' else ('Local Ollama' if responses[0]['mode']=='ollama' else 'Live API'))}")
    st.write(case['question'])
    if len(responses)==2:
        first,second=responses
        valid=all(not r.get('truncated') and (not r.get('format_required') or r.get('format_ok')) for r in responses)
        if valid and first['total_tokens'] and second['total_tokens'] is not None:
            savings=(1-second['total_tokens']/first['total_tokens'])*100
            st.metric(t('Token reduction vs reference'),f'{savings:.1f}%',help=t('Negative values mean the comparison consumed more tokens. Quality requires independent human scoring.'))
        else:st.caption(t('Token reduction is unavailable when usage is missing or an answer failed.'))
        for column,result in zip(st.columns(2),responses):
            with column:render_result(result)
    else:render_result(responses[0])

with advisory:
    st.subheader(t('A little context goes a long way.'))
    st.caption(t('Tell the adviser about your crop. Your question stays in this session.'))
    submitted,ask_case,versions=case_form('ask')
    execute('ask',submitted,ask_case,versions);show_saved('ask')

with compare:
    st.subheader(t('Same question. Different prompt.'))
    st.caption(t('Compare two prompt approaches using the same model and temperature. Token counts include any retries.'))
    submitted,case,versions=case_form('compare',True)
    execute('compare',submitted,case,versions);show_saved('compare')

with library:
    st.subheader(t('Twelve versions. One research question.'))
    st.caption(t('How much can tokens be reduced while keeping quality and safety close to V5?'))
    st.dataframe(pd.DataFrame([{t('Version'):v,t('Technique'):t(name),t('Track'):t('Quality' if int(v[1:])<=5 else 'Efficiency')} for v,name in VERSIONS.items()]),hide_index=True,width='stretch')
    version=st.selectbox(t('Inspect a prompt'),list(VERSIONS),index=10)
    preview_questions={'Kannada':'ನನ್ನ ಟೊಮೇಟೊ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ. ಏನು ಮಾಡಬೇಕು?', 'Hindi':'मेरे टमाटर की पत्तियाँ पीली हो रही हैं। क्या करूँ?', 'English':'My tomato leaves are turning yellow. What should I do?'}
    preview_case=dict(language=ui_language,crop='Tomato',region='Mandya',season='Kharif',stage='Vegetative',soil='Unknown',question=preview_questions[ui_language])
    system,user=build_prompt(version,preview_case)
    prefix=stable_prefix(version)
    if prefix:
        st.markdown(t('**Stable cached prefix**')); st.code(prefix,language=None)
    st.markdown(t('**System prompt**'));st.code(system or t('(No system prompt: V0 baseline)'),language=None)
    st.markdown(t('**User message · example**'));st.code(user,language='json' if version!='V0' else None)
    st.caption(t('For local Ollama V10 and V11, the app also requests brief fields and one or two steps.'))
    st.caption(t('V9 generates compact English advice, then translates for Kannada/Hindi. Both calls count. V7, V10 and V11 send only the context fields relevant to the question (query-aware selective context), with a conservative fallback when no topic is recognised. V10 is a combined treatment, so its effect cannot be attributed to one technique. V11 adds a stable guide to V10 and marks it cacheable.'))
    st.code(t('Library + context SHA-256: ')+library_hash(),language=None)

with gaptab:
    st.subheader(t('Compare your question across languages'))
    st.caption(t('Use the current question from Ask an adviser. Ollama translates it so you can review the wording before comparing input tokens.'))
    question=ask_case['question'].strip()
    source=st.selectbox(t('Language of your question'), LANGUAGES,
                        index=LANGUAGES.index(ask_case['language']), format_func=t, key='gap_source')
    if not question:
        st.info(t('Enter a question in Ask an adviser first.'))
    else:
        st.markdown(t('**Your question**'))
        st.write(question)
        signature=(question,source,model,ollama_url)
        if st.button(t('Translate question'),key='gap_translate'):
            st.session_state.pop('gap_question_result',None)
            st.session_state.pop('gap_translations',None)
            try:
                with st.spinner(t('Translating your question with Ollama...')):
                    translations=translate_question(question,source,model,ollama_url)
                st.session_state['gap_translations']={'signature':signature}
                for language in LANGUAGES:
                    st.session_state['gap_text_'+language]=translations[language]
            except ValueError as exc:
                st.error(t(str(exc)))
            except Exception as exc:
                st.error(t('Ollama request failed. Make sure Ollama is running and the model is pulled.')+f' ({type(exc).__name__})')
        prepared=st.session_state.get('gap_translations')
        if prepared and prepared['signature']==signature:
            st.caption(t('These are machine translations. Review and correct them before counting; the original question is shown unchanged.'))
            texts={}
            for language in LANGUAGES:
                if language == source:
                    texts[language]=question
                    st.markdown('**'+t(language)+' ('+t('original')+')**')
                    st.write(question)
                else:
                    texts[language]=st.text_area(t(language),key='gap_text_'+language,max_chars=4000,height=85)
            comparison_signature=(signature,tuple(texts[language].strip() for language in LANGUAGES))
            if st.button(t('Count question tokens'),key='gapbtn'):
                st.session_state.pop('gap_question_result',None)
                if any(not texts[language].strip() for language in LANGUAGES):
                    st.warning(t('Each translation must contain text before counting.'))
                else:
                    try:
                        with st.spinner(t('Counting tokens with Ollama...')):
                            counts={language:count_ollama_tokens(ollama_url,model,texts[language].strip()) for language in LANGUAGES}
                        if any(count <= 0 for count in counts.values()):
                            raise ValueError('Ollama did not return a valid token count.')
                        st.session_state['gap_question_result']={'signature':comparison_signature,'counts':counts}
                    except ValueError as exc:
                        st.error(t(str(exc)))
                    except Exception as exc:
                        st.error(t('Ollama request failed. Make sure Ollama is running and the model is pulled.')+f' ({type(exc).__name__})')
            result=st.session_state.get('gap_question_result')
            if result and result['signature']==comparison_signature:
                counts=result['counts']
                table=pd.DataFrame([{'language':t(language),'input_tokens':counts[language],
                                     'ratio_to_english':round(counts[language]/counts['English'],2)} for language in LANGUAGES])
                st.caption(t('Counts are for one user message per language, including Ollama message formatting. They exclude the advisory prompt, model response, and translation calls.'))
                st.dataframe(display_frame(table),hide_index=True,width='stretch')
                st.caption(t('Results depend on the selected model and the reviewed translations; they do not establish a general language-wide token cost.'))
        elif prepared:
            st.info(t('The question, its language, or the model changed. Translate again to compare the current question.'))

st.divider()
st.caption(t('FARMWISE  /  Prompt engineering research prototype  ·  English / ಕನ್ನಡ / हिन्दी'))
