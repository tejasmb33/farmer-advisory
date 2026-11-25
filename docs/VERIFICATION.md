# Verification at delivery

- 19 automated tests passed on Python 3.12.
- Streamlit AppTest exercised initial rendering, Kannada fixture generation, unsafe-example comparison, empty input validation and live-mode missing-model handling.
- Mock-provider tests verified V9 two-call usage/cost aggregation, translation input, English one-call behavior, temperature/model consistency, truncation propagation, V10 output cap and compact schema validation.
- Scoring tests verified V5-relative savings, missing-price behavior, rejection of demo/incomplete scores, matched query populations, mixed models and invalid token totals.
- Batch tests verified successful-record resume, changed-setting rejection and exclusion of offline records from blind research scoring.
- Separate offline CLI smoke run completed 36 records (18 queries × V5/V10). Repeating the command added no duplicate records. These are interface fixtures, not measured results.
- Python source compilation passed.

No live API requests or agricultural/language expert reviews were performed. No empirical savings, advice accuracy or translation-quality findings are claimed. Browser-level screenshot/visual review was not performed; the available UI verification used Streamlit's interactive testing framework.

The environment denied creation of the requested /codex/.../output directory. The working source remains in /workspace/farmer-advisory. A source archive was prepared under /workspace/work without environments, credentials, caches or generated experiment records.
