# Farmwise — Token-Efficient Multilingual Farmer Advisory

A Python/Streamlit project implementing the supplied roadmap: prompt-only agricultural advice in English, Kannada and Hindi; V0–V10; exact provider token accounting; side-by-side comparison; and a reproducible human-scored evaluation workflow.

## MacBook quick start

Read `START_HERE_MAC.md`. After extracting the ZIP, open Terminal in this folder and run `bash run-mac.command`. Install Python 3.11 or 3.12 first. The launcher creates a new Mac-local virtual environment. Offline demo needs no API key.

## Run locally

Requires Python 3.11 or 3.12 and internet for installing dependencies. No API key is needed for the offline demonstration.

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. Select an example query and click **Generate advice**, or open **Compare prompts** to compare V5 and V10.

For the exact versions used during development on Python 3.12, install `requirements-lock.txt` instead. `requirements.txt` allows compatible updates. Run `python -m pytest -q` to verify the project.

## Enable live AI

Copy `.env.example` to `.env`. Set `ANTHROPIC_API_KEY` and an `ANTHROPIC_MODEL` available to your account. Restart Streamlit, then select **Live API**. An API key can also be entered in the password field for the current session. Keys are never included in run downloads or batch outputs.

The PDF's example model name is not assumed to be available. Check your account for a valid ID. Temperature is fixed at 0.2. V0–V9 use `max_tokens=1000`; V10 intentionally uses 700 plus a 100-word instruction. Indic text may still be truncated: the provider stop reason is recorded, not concealed. Word limits are instructions, not guaranteed enforcement.

For costs, enter current USD input/output prices per million tokens and the verification date in the sidebar, then confirm verification. Without verified pricing, costs remain unknown. The app does not assume that missing prices mean free usage.

### Offline demonstration

Offline mode uses prewritten generic advice in the selected language. It is identical across prompt versions and is not an AI experiment. Token, cost and latency measurements remain blank. Do not report fixture outputs as research results. The examples illustrate interface behavior, language rendering and basic safety/referral content; they do not diagnose the selected crop.

## What is included

| File | Purpose |
| --- | --- |
| `app.py` | Advisory UI, V5/V10 comparison, prompt inspection, result uploads and charts |
| `prompts.py` | V0–V10, context selection and SHA-256 fingerprints |
| `llm.py` | Anthropic calls, exact usage, costs, JSON validation and V9 translation accounting |
| `demo.py` | Clearly labelled offline multilingual fixtures |
| `evaluate.py` | Resumable batch runner, blind review export, summaries and language token counts |
| `data/context.json` | Draft regional profiles and source portals |
| `data/test_queries.csv` | 18 queries, six per language, including vague/unsafe/out-of-scope/injection cases |
| `data/language_samples.csv` | 10 aligned advice snippets in three languages |
| `data/rubric.json` | Six fixed human-scoring criteria |
| `docs/` | Methodology, report template, presentation outline, demo script and roadmap coverage |
| `tests/` | Mock-provider, accounting, schema, scoring and interactive Streamlit tests |

## Run the research study

First verify context against current local extension guidance, have fluent speakers review the Kannada/Hindi datasets, and freeze the rubric before examining model outputs. Record exact source documents and access dates. The bundled profiles and translations are draft material, not validated agronomic findings.

All live commands below make paid API requests. The full default batch contains 198 advisory runs (18 × 11). V9 adds a translation request for the 12 non-English cases, for 210 API requests without retries. A three-repeat run makes 630 API requests without retries. Start with anchor cases or fewer versions if needed.

```bash
# Optional offline pipeline smoke test; keep separate from measured data.
python evaluate.py run --mode demo --versions V5,V10 --output results/demo.csv

# Set model/key in .env before live work.
# Supply prices only after checking the provider's current pricing page.
python evaluate.py run --mode live --output results/outputs.csv
# Optional: --price-in <USD_PER_MTOK> --price-out <USD_PER_MTOK>
# For repeated trials: use --repeats 3 and a NEW output path.

python evaluate.py blind
# Give ONLY results/review/blind_scores.csv to reviewers.
# Keep private_mapping.csv separate so the version labels remain hidden.
# Reviewers fill every criterion with an integer 1–5 and add identity/references/notes.
python evaluate.py summarize

# Separate language-token study; uses provider count_tokens, not generated answers.
python evaluate.py language-gap
```

The batch runner records text, usage, format compliance for JSON versions, stop/truncation flags, per-call usage, time, model, temperature, hashes and UTC timestamps. It writes questions and outputs to disk only when you explicitly run the batch command. The manifest freezes prompt/context and query hashes, pricing, model and settings. Re-run the exact same command to resume successful records; use a new path if settings or inputs change. Interruptions during a CSV write can require removing the incomplete final row before resuming. If a V9 translation fails, no complete result is claimed; its already-billed first call is not included in successful-result totals. Provider retry billing and failed-call costs should be audited separately when reporting total study spend.

The summarizer rejects demo data, incomplete scores, duplicate keys and mismatched review mappings. It writes:

- `results/analysis/scored_outputs.csv`
- `results/analysis/summary.csv` — per version/language quality, safety, tokens, costs, efficiency and V5-relative savings
- `results/analysis/tradeoff.html` — standalone interactive chart

Upload live outputs, blind scores and the mapping in **Research desk** for token, trade-off and efficiency charts. Do not pool different model/settings experiments. Compare the same cases and repeats across versions. Averages can conceal safety failures; inspect individual unsafe, vague and injection cases.

### Language-token study

Each language sample is sent as a single user message to Anthropic's `count_tokens` endpoint. Counts include provider message framing and are labelled accordingly; they are not pure text-only tokenizer counts or generated-answer usage. The script reports average message tokens and each language's ratio to English. Treat unreviewed translations as preliminary. No language-token gap is assumed in advance.

## Limits and safety

This is an educational research prototype, not validated production agricultural advice. No image diagnosis, model training, live weather, exact pesticide dosage, large-scale retrieval or caching experiments are included. Prompts reduce risk but cannot guarantee safety. V0–V3 deliberately have fewer guardrails to preserve the research ladder; the interface flags these live baselines. Treat all results as unverified until reviewed by a qualified agriculture adviser and fluent speaker.

The UI retains the latest advisory and comparison in Streamlit session memory, and never automatically saves them to disk. Downloads are explicit. Do not enter sensitive personal data. Live queries are sent to Anthropic and are governed by its policies. SDK exception bodies are not printed to avoid exposing request information. Streamlit session memory is not durable storage or a production privacy guarantee.

No live API key was supplied during project creation. Automated tests use mocked provider responses and offline fixtures. Real quality, cost savings and language correctness still require the study and human review; no findings are fabricated.

## Deployment

This is a standard Python Streamlit server. For hosted use, deploy to Streamlit Community Cloud or a Python-capable server, put credentials in the host's secret settings, and use `streamlit run app.py --server.address 0.0.0.0`. Do not expose a credential-bearing instance to untrusted users without access controls and spending limits. The Sites static/Worker hosting format does not execute Python/Streamlit, so this project is supplied as a runnable source package.

### Interface language

Use **Language / ಭಾಷೆ** in the sidebar to switch between English and Kannada.
Switching also sets the response language for both advice forms; their existing
response-language selectors (including Hindi) remain available. Kannada labels,
options, messages, rubric, charts, and summary downloads use Unicode text.
Canonical experiment values, raw requests, JSON keys, source datasets, and prompt
source remain unchanged for inspection and evaluation compatibility.

Live requests apply a response-language instruction to V0–V10; V9 retains its
English-first translation workflow and two-call accounting. Prompt builders retain
the original research treatments. The experiment library hash also covers `llm.py`
so batches created before this delivery change cannot silently resume with changed
request instructions. Kannada typography uses Noto Sans Kannada with system font
fallbacks. Translations are maintained in `translations_kn.json`.
