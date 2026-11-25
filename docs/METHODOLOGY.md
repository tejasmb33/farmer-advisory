# Study protocol

Research question: How much can token use be reduced across English, Kannada and Hindi while preserving quality and safety relative to V5?

## Treatments

V0 is question-only. V1 adds the Karnataka extension-officer role. V2 adds the full draft regional profile and crop/season/stage/soil. V3 adds the answer structure. V4 adds uncertainty, follow-up, simplicity and chemical safety rules. V5 adds the requested response language.

V6 rewrites the V5 system instructions compactly. V7 removes the general regional profile while retaining crop, district, season, stage and any known soil. This conservative fixed subset avoids English-only keyword filters, but is not a semantic relevance classifier. V8 asks for six compact JSON fields; the UI supplies translated headings. V9 generates those fields in English and translates the values for Kannada/Hindi, preserving keys and safety content. English V9 uses only the first call. V10 combines compression, selective context, compact output and direct target-language generation with a 100-word instruction and 700-token output cap. V10 uses direct generation rather than V9 because a best language strategy cannot be selected before experiments. Revisit this decision only in a new, separately frozen experiment after measuring V9.

The optimisation sequence has bundled changes; a V10 gain cannot be attributed to one technique. V5 is the intended quality reference, not a proven empirical ceiling. V11 caching is optional future work and is not implemented.

## Before collecting outputs

1. Record model ID, provider, pricing and verification date; freeze temperature 0.2.
2. Verify context and exact official source documents with a local agricultural reviewer. Document soil and climate uncertainty rather than inventing them.
3. Have fluent Kannada/Hindi speakers review all test questions and the 10 aligned language samples.
4. Freeze the rubric before looking at outputs. For multiple reviewers, reconcile assessments or predefine an aggregation policy.
5. Freeze prompts/context (library hash) and queries (file hash). Save the manifest.
6. Run matched cases across all versions; use three repeats for the consistency subset or the full dataset if budget permits.

## Measures

Input/output tokens are provider usage counts; V9 totals sum both requests. Latency sums request durations, including SDK retry time. USD/query = (input × input-price + output × output-price) / 1,000,000; USD/1,000 = query-cost × 1,000. Unknown pricing stays blank. Failed attempts can incur costs outside completed-result totals; audit provider billing separately.

For each output, human quality is the mean of accuracy, clarity, simplicity, completeness, safety and language quality (1–5). Efficiency = quality / total_tokens × 1,000. Mean metrics are grouped by version and language. Token savings = (1 − treatment_mean_tokens / V5_mean_tokens_for_same_language) × 100. Use matched query populations and repeats to avoid confounding. A negative saving is a token increase. Review safety individually, even if mean quality is high.

JSON format compliance is exact key/type validation for V8–V10. V0–V7 have no machine-readable schema contract, so compliance is not auto-scored. Truncation is recorded whenever any underlying request stops because of max_tokens. This detects provider cap truncation, not every semantically incomplete answer. The 100-word instruction may be violated; Indic word segmentation needs human review.

The separate language experiment counts one user message for each aligned snippet. Provider framing is included. Do not equate these input counts with output-token counts from generation, or assume an Indic token penalty before measuring.

## Analysis and interpretation

Export blind outputs and keep the mapping away from reviewers. Accuracy reviewers must cite actual official guidance, not just a portal. Kannada/Hindi quality requires fluent reviewers. Inspect all stress cases. Explain at least one failure and its practical implication. Report both human scores and format/truncation failures. State an acceptable quality/safety difference *before* inspecting results; do not claim equivalence from similar means alone. This small coursework study does not establish statistical non-inferiority or deployment safety.

Report charts: mean tokens/version, V5/V10 by language, quality-versus-tokens, efficiency/version. The UI produces all four views through the token grouped bars, summary table and trade-off/efficiency charts. Explain which measured technique helped and where safety/quality changed. Keep illustrative screenshots separate from empirical evidence.
