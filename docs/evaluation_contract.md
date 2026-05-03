# Evaluation Contract

## Purpose

This document defines the evaluation vocabulary for the clean repo after the
literature-review pivot. Seizure frequency remains the anchor task, but the
main study now evaluates clinical extraction systems across architecture
families, clinical NLP baselines, model families, model size tiers, and
operating profiles.

The evaluation must therefore answer more than "which model is most accurate?"
It should show how architecture, model capacity, evidence requirements,
normalization, cost, latency, token use, and harness complexity influence the
quality of structured epilepsy-letter extraction.

## Evaluation Units

Results should be reportable at four levels:

| Unit | Meaning |
| --- | --- |
| Row / letter | One clinic letter or synthetic letter. |
| Field family | A clinically coherent output group such as medications or seizure frequency. |
| Item | One extracted clinical claim, such as a medication, investigation result, seizure type, or frequency statement. |
| Architecture run | A fixed harness/model/dataset-slice combination. |

Do not rely on a single aggregate score. Aggregate metrics can be useful only
after field-family and item-level results are visible.

## Architecture Families

Every run should declare one architecture family:

| Family | Example harnesses | Evaluation role |
| --- | --- | --- |
| `clinical_nlp_baseline` | `deterministic_baseline`, `exect_lite_cleanroom_baseline`, `exect_v2_external_baseline` | Non-LLM and epilepsy-specific baseline floor. |
| `direct_llm` | `direct_full_contract`, `direct_evidence_contract` | Strong full-letter LLM comparator. |
| `retrieval_field_pipeline` | `retrieval_field_extractors`, `retrieval_anchor` | Candidate-span and local-context extraction ablation. |
| `clines_inspired_modular` | `clines_epilepsy_modular`, `clines_epilepsy_verified` | Main clinical modular architecture. |
| `costed_reliability_variant` | self-consistency, stronger verifier, model escalation | Costed reliability or sensitivity intervention. |

Baseline outputs may be partial. Their coverage must be explicit rather than
penalized as if they attempted the full contract.

## Field Families

| Field family | Status | Required initially |
| --- | --- | --- |
| Seizure frequency | Core anchor | Yes |
| Seizure freedom | Core subfield | Yes, as explicit subfield where possible |
| Current anti-seizure medications | Core | Yes |
| Investigations | Core | Yes |
| Seizure type, semiology, and pattern modifiers | Core, normalization-sensitive | Yes |
| Epilepsy type and syndrome | Core | Yes |
| Most recent seizure | Future/subfield | Optional first pass |
| Rescue medication | Future/subfield | Optional first pass |
| Other therapies | Future | Optional first pass |
| Comorbidities | Future | Optional first pass |
| Associated symptoms | Future | Optional first pass |

Harnesses that do not emit all core field families must be labelled
`partial_contract`. External baselines such as ExECTv2 may be mapped onto the
nearest supported field families and reported with explicit `field_coverage`.

## Literature Alignment

The field families should remain aligned with prior epilepsy and clinical IE
literature where possible. This makes the proposal easier to defend and helps
separate direct comparisons from new-field extensions.

| Proposed field family | Prior literature alignment | Evaluation implication |
| --- | --- | --- |
| Seizure frequency | ExECT/ExECTv2; Xie et al.; Holgate et al.; Gan et al. | Core anchor. Report fine-grained and pragmatic labels where possible, plus status, temporality, ambiguity, and evidence support. |
| Seizure freedom | Xie et al.; Gan et al.; seizure-frequency annotation schemes | Treat as explicit subfield, not merely a frequency category, because "no tonic-clonic seizures" may not imply global seizure freedom. |
| Most recent seizure / date of last seizure | Xie et al.; Gan et al. | Optional first-pass subfield, but important for temporality evaluation and future machine-reading comparison. |
| Current anti-seizure medications | ExECT/ExECTv2 prescriptions; Fang et al.; i2b2 medication lineage | Core field. Score currentness, drug name, dose, unit, frequency, planned changes, and evidence separately where supported. |
| Investigations | ExECT CT/MRI/EEG; ExECTv2 EEG/CT/MRI results; CLINES tests/labs/procedures | Core field. Score investigation type, result, status, temporality, and normal/abnormal/pending normalization. |
| Seizure type and classification | ExECT focal/generalized seizure categories; ExECTv2 seizure type; Fang et al. | Core normalization-sensitive field. Report raw mention and normalized label to avoid overclaiming. |
| Semiology features and pattern modifiers | Partially covered by Fang associated symptoms; not fully covered by ExECTv2 public annotation scope | Include as core only where the schema can preserve raw evidence and uncertainty; report separately from seizure-type labels. |
| Epilepsy type and syndrome | ExECT epilepsy diagnosis/type; ExECTv2 diagnosis/type/syndrome; Fang et al. | Core field. Score diagnosis/type/syndrome and diagnostic certainty separately. |
| Epilepsy cause / etiology | ExECTv2 epilepsy cause | Optional extension unless proposal scope expands; useful for ExECTv2 mapping. |
| Age/onset/when diagnosed | ExECTv2 onset and when diagnosed | Optional extension; useful for temporality stress testing but not required for first full contract. |
| Birth history and patient history | ExECTv2 annotation set | Out of initial scope unless needed for ExECTv2 baseline completeness; report as not attempted rather than false negative. |
| Associated symptoms | Fang et al. | Optional or supporting field; may overlap with semiology and should be mapped carefully. |
| Generic concepts, assertions, values/units, dates | CLINES | Architectural inspiration rather than epilepsy-field target; use for status, temporality, normalization, and value/unit evaluation axes. |

When a previous paper uses a different representation, evaluate alignment at
the nearest defensible level. For example, ExECT focal/generalized seizure
outputs can be mapped to seizure classification, while Holgate-style
seizure-frequency categories can be mapped to pragmatic frequency labels.
Fields that prior systems did not attempt should be marked `not_attempted`.

## Evaluation Layers

Evaluation happens in nine layers:

1. Architecture and field implementation coverage.
2. Baseline output mapping and comparability.
3. Parse validity and recoverability.
4. Proxy coverage and evidence presence.
5. Matched clinical adjudication.
6. Evidence-support grading.
7. Architecture ablation effects.
8. Model-family and model-tier effects.
9. Budget, latency, token use, and harness complexity.

Layered reporting matters because schema-valid, evidence-present outputs can
still be clinically wrong.

## Coverage Metrics

Report coverage separately from correctness.

Required coverage metrics:

- `attempted_field_families`;
- `supported_field_families`;
- `partial_contract`;
- `rows_attempted`;
- `rows_with_any_output`;
- `rows_with_field_family_output`;
- `items_emitted_by_field_family`;
- `abstention_rate_by_field_family`;
- `external_baseline_mapped_fields`, where applicable.

For baselines that do not attempt a field, report `not_attempted`, not false
negative.

## Parse Validity Metrics

Run artifacts should expose component validity separately:

- `seizure_frequency_invalid_output_rate`;
- `seizure_freedom_invalid_output_rate`;
- `current_medication_invalid_output_rate`;
- `seizure_classification_invalid_output_rate`;
- `investigations_invalid_output_rate`;
- `epilepsy_classification_invalid_output_rate`;
- `broader_fields_invalid_output_rate`;
- `full_contract_invalid_output_rate`;
- `repair_attempt_rate`;
- `repair_success_rate`;
- `legacy_any_invalid_output_rate`.

`legacy_any_invalid_output_rate` may exist for continuity, but dissertation
tables should prefer component validity and `full_contract_invalid_output_rate`.

## Correctness Axes

For non-empty outputs, score these axes:

| Axis | Meaning |
| --- | --- |
| Value correctness | Did the system identify the right clinical entity or concept? |
| Status correctness | Did it preserve current, historical, planned, pending, conditional, absent, or uncertain status? |
| Temporality correctness | Did it preserve the relevant time anchor or currentness? |
| Normalization correctness | Did it map the raw phrase to a defensible schema label or code? |
| Evidence support | Does the cited span support value, status, temporality, and normalization? |
| Field placement | Was the item assigned to the right field family? |
| Completeness | Did the system miss clinically relevant items within a field family it attempted? |

Schema validity is not clinical correctness.

## Evidence Grades

| Grade | Definition |
| --- | --- |
| `exact_span` | Shortest or near-shortest span directly supports the output. |
| `overlapping_span` | Span overlaps the decisive wording but includes extra text. |
| `section_level` | Right section, but not decisive wording. |
| `wrong_temporal_status` | Evidence supports the entity but not the claimed status or time anchor. |
| `wrong_normalization` | Evidence supports a raw mention but not the normalized label or code. |
| `unsupported` | Evidence does not support the output. |
| `missing_evidence` | Non-empty output has no usable evidence. |
| `not_applicable` | Baseline or field does not provide evidence spans. |

Full evidence credit requires `exact_span` or `overlapping_span`.

For systems without evidence spans, report value correctness separately and mark
evidence support as `not_applicable` rather than silently treating it as
unsupported.

## Baseline Comparability

Clinical NLP baselines may emit different output structures from LLM harnesses.
Each baseline needs a mapping layer:

- source field name;
- mapped field family;
- mapped item value;
- mapped status, if available;
- mapped temporality, if available;
- mapped normalization, if available;
- mapped evidence span or `not_applicable`;
- mapping warnings.

Report baseline limitations explicitly:

- fields not attempted;
- evidence not available;
- normalization not available;
- status or temporality not available;
- external runtime requirements;
- license or reproducibility constraints.

## Architecture Ablation Metrics

Architecture comparisons should be reported as deltas against matched rows and
matched model registry entries where possible.

Recommended ablation metrics:

- direct prompt to evidence-contract delta;
- direct prompt to retrieval-field pipeline delta;
- retrieval-field pipeline to CLINES-inspired modular delta;
- modular to verified modular delta;
- one-pass to self-consistency delta;
- small-model direct to small-model modular delta;
- frontier-model direct to frontier-model modular delta.

For each delta, report:

- field-family correctness change;
- evidence-support change;
- abstention change;
- parse-validity change;
- token/cost/latency change;
- warning and error-category change.

## Model-Family Metrics

Model comparisons must use frozen model registry entries.

Report:

- model registry entry ID;
- family;
- exact model ID;
- tier;
- provider/backend;
- context window;
- decoding settings;
- local hardware or API pricing;
- field-family metrics;
- evidence-supported correctness;
- parse validity;
- cost per row;
- latency per row;
- cost per valid output;
- cost per evidence-supported item;
- cost per correctly adjudicated item.

Avoid reporting only generic model family names such as "GPT", "Claude", or
"Qwen" in result tables.

## Budget And Complexity Metrics

Every run should report:

- number of LLM calls per row;
- mean input tokens;
- mean output tokens;
- mean total tokens;
- mean latency;
- estimated cost;
- model/provider/backend;
- temperature and sampling settings;
- prompt/schema version;
- fixed data slice and data hash;
- number of modules invoked;
- number of intermediate artifacts;
- external tools required;
- local hardware where applicable.

Harness complexity is part of the result. A modular pipeline that improves
evidence support at much higher cost should be interpreted as a tradeoff, not a
simple win.

## Harness-Native Metrics

Phase 13 adds explicit harness metadata. These metrics describe how a system
operated; they are not clinical correctness scores.

Every canonical harness run should reference:

- `manifest_id`;
- `manifest_hash`;
- allowed modules and workflow units;
- prompt, schema, verifier, aggregation, repair, context, and budget policies;
- gold-label isolation and artifact-retention policy.

Harness event traces should be PHI-safe summaries unless the row is a synthetic
fixture explicitly permitted to carry quotes. Report:

- total event count;
- event counts by type;
- provider calls;
- parse attempts and repairs;
- verifier passes;
- escalation decisions;
- warnings and errors;
- quote-bearing event count.

Workflow units should be versioned and reported separately from prompts. A field
extractor, deterministic normalizer, verifier, and aggregator can change even
when the final schema stays fixed. Workflow-unit metrics support method
auditing and ablation; they should not be interpreted as value correctness.

Verifier-gate metrics should distinguish:

- value support;
- status support;
- temporality support;
- normalization support;
- field-family placement;
- epilepsy edge-case checks.

Escalation metrics should report the trigger reason, stronger model used,
additional call/token/cost burden, and whether escalation was invoked because
of low confidence, parse failure, verifier disagreement, or unsupported
evidence. Escalation variants remain `costed_reliability_variant` runs and must
not silently replace canonical direct, retrieval, or modular baselines.

The Clinical-Document Interface should be reported when used. Document-interface
metrics include section lookup, candidate-span search, deterministic locators,
quote fidelity, payload validation, and evidence-to-claim comparison. Direct
full-letter prompting may bypass this interface and should remain labelled as
such.

External harness adapters should be reported as adapter-normalized outputs.
Claude Code, Codex, Pi, Flue, OpenHands, Gemini CLI, Aider, and similar future
runners are not canonical clinical comparators by default. They become
comparable only after their outputs are normalized into `ExtractionPayload`,
event summaries, raw artifact references, and explicit sandbox/version
metadata.

## Error Categories

Adjudication should tag errors using stable categories:

- `missed_item`;
- `spurious_item`;
- `wrong_value`;
- `wrong_status`;
- `wrong_temporality`;
- `wrong_normalization`;
- `wrong_field_family`;
- `unsupported_evidence`;
- `overbroad_evidence`;
- `missing_evidence`;
- `parse_or_schema_error`;
- `retrieval_recall_loss`;
- `aggregation_conflict`;
- `baseline_mapping_error`.

These categories should support architecture-specific error analysis. For
example, retrieval recall loss should be separable from field-extractor failure.

## Minimum Result Tables

The clean repo should generate:

- architecture and harness coverage table;
- baseline comparability table;
- model registry table;
- budget, latency, token, and complexity table;
- parse-validity table;
- field-level correctness table;
- evidence-support table;
- architecture ablation table;
- model-family and model-tier table;
- seizure-frequency anchor table;
- self-consistency cost table;
- adjudication error-category table.

## Reporting Order

Final result tables should be ordered as:

1. architecture and field implementation coverage;
2. baseline comparability;
3. model registry and run configuration;
4. budget, latency, token use, and harness complexity;
5. component parse validity;
6. proxy coverage and evidence presence;
7. matched clinical adjudication;
8. evidence-support grading;
9. architecture ablations;
10. model-family and model-tier comparisons;
11. seizure-frequency anchor metrics;
12. failure categories and uncertainty.
