# Novelty: where each claim lives in the application

Each row of the proposal's novelty section, the code that implements it, how to show it in the demo, and what you may and may not claim.

| Novelty claim (proposal) | Implemented in | Show it in the demo | Claim only after |
|---|---|---|---|
| Token-aware prompt design for Indic languages | `evaluate.py` (`load_language_samples`, `proxy_summary`, `measure_language_gap`), **Language gap** tab | Offline proxy table, then live token counts per language and the ratio to English | Running the live count and having a fluent speaker review the samples |
| Selective context injection (query-relevant fields only) | `prompts.py` (`TOPIC_TERMS`, `TOPIC_FIELDS`, `route_context`), used by V7, V10, V11; context line in every result | Ask an insect question, then a fertiliser question: the **Sent / Withheld** fields change | Measuring V7 versus V6 tokens and quality in the live study |
| Compact structured output with app-side rendering | V8, V10, V11 return six JSON fields; `app.py` renders the localised headings (`demo.HEADINGS`) | Show raw JSON in *Inspect raw response* next to the rendered card | Comparing output tokens of V8 versus V5 live |
| Output language strategy comparison | V9 (English first, then translate) versus V10 direct generation; both calls counted | Compare V9 and V10 on a Kannada question | Live scores and token totals for both |
| Prompt compression, length control and caching as separate versions | V6 (compression), V10 (length cap), V11 (cached guide) | V10 versus V11 twice within five minutes; read the cache metrics | Seeing non-zero cache reads in the usage fields |
| Quality versus token trade-off | `summarize_frames`, Research desk charts, `tradeoff.html`, weighted-token chart | Upload scored results and show the trade-off chart | Completing human blind scoring |
| Live token and cost panel with side-by-side mode | `app.py` (`render_result`, Compare prompts) | Compare prompts tab | Entering verified prices and date |

## Design decisions worth explaining to evaluators

1. **Routing widens rather than guesses.** Ambiguous words such as *yellow* activate several topics, and an unrecognised question falls back to a fixed subset. The safety rules live in the system prompt and are never reduced by routing.
2. **The router is a transparent keyword lexicon**, not a classifier. That is a deliberate, auditable choice. Report its misses honestly and treat the Kannada and Hindi term lists as drafts for fluent-speaker review.
3. **Caching saves cost, not tokens.** The provider's `input_tokens` excludes cached tokens, so the app sums uncached, written and read tokens into `input_tokens` (keeping totals honest) and reports `cost_weighted_input_tokens` separately.
4. **V11 is not a free lunch.** It adds a roughly 2,000-token guide to every request. It only pays off when requests repeat inside the cache lifetime and the guide reaches the model's minimum cacheable length. Compare V10, V11 and the V11 control run (caching switched off in the sidebar, or `--no-cache` in the batch) to separate the effect of the guide from the effect of caching.
5. **Honest negative results are acceptable.** If V11 is more expensive than V10 on your data, report that and explain why.

## Not claimed

No token or cost saving is claimed anywhere in the code or documents. All savings must come from your own live runs. Offline numbers in the app (character and byte counts, request sizes) are proxies and must be labelled as such.

## Local Ollama integration

Ollama remains the default connection. V11 sends the same guide locally, but does not request Anthropic prompt caching or report cache savings. The live token-counting feature and cache controls require the Live API connection; the offline language character and byte proxies are available in every mode.
