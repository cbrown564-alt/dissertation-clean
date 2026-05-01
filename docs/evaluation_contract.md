# Evaluation Contract

## Purpose

This document defines the evaluation vocabulary for the clean repo. Seizure
frequency remains the anchor task, but it must not decide whether broader
clinical extraction is valid. Each field family needs separate coverage,
validity, evidence-support, and correctness measures.

## Field Families

| Field family | Status | Required initially |
| --- | --- | --- |
| Seizure frequency | Core anchor | Yes |
| Current anti-seizure medications | Core | Yes |
| Investigations | Core | Yes |
| Seizure type, semiology, and pattern modifiers | Core, normalization-sensitive | Yes |
| Epilepsy type and syndrome | Core | Yes |
| Seizure freedom | Core subfield | Prefer explicit subfield |
| Most recent seizure | Future/subfield | Optional first pass |
| Rescue medication | Future/subfield | Optional first pass |
| Other therapies | Future | Optional first pass |
| Comorbidities | Future | Optional first pass |
| Associated symptoms | Future | Optional first pass |

Harnesses that do not emit all core field families must be labelled
`partial_contract`.

## Evaluation Layers

Evaluation happens in five layers:

1. Field implementation coverage.
2. Parse validity and recoverability.
3. Proxy coverage and support metrics.
4. Matched clinical adjudication.
5. Seizure-frequency anchor metrics.

## Component Validity Metrics

Run artifacts should expose component validity separately:

- `seizure_frequency_invalid_output_rate`
- `current_medication_invalid_output_rate`
- `seizure_classification_invalid_output_rate`
- `investigations_invalid_output_rate`
- `epilepsy_classification_invalid_output_rate`
- `broader_fields_invalid_output_rate`
- `full_contract_invalid_output_rate`
- `legacy_any_invalid_output_rate`

`legacy_any_invalid_output_rate` may exist for continuity, but dissertation
tables should prefer component validity and `full_contract_invalid_output_rate`.

## Correctness Axes

For non-empty model outputs, score these axes:

| Axis | Meaning |
| --- | --- |
| Value correctness | Did the model identify the right clinical entity or concept? |
| Status correctness | Did it preserve current, historical, planned, pending, conditional, absent, or uncertain status? |
| Temporality correctness | Did it preserve the relevant time anchor or currentness? |
| Normalization correctness | Did it map the raw phrase to a defensible schema label? |
| Evidence support | Does the cited span support value, status, temporality, and normalization? |

Schema validity is not clinical correctness.

## Evidence Grades

| Grade | Definition |
| --- | --- |
| `exact_span` | Shortest or near-shortest span directly supports the output. |
| `overlapping_span` | Span overlaps the decisive wording but includes extra text. |
| `section_level` | Right section, but not decisive wording. |
| `wrong_temporal_status` | Evidence supports the entity but not the claimed status or time anchor. |
| `unsupported` | Evidence does not support the output. |
| `missing_evidence` | Non-empty output has no usable evidence. |

Full evidence credit requires `exact_span` or `overlapping_span`.

## Budget Metrics

Every run should report:

- number of LLM calls per row;
- mean input tokens;
- mean output tokens;
- mean total tokens;
- mean latency;
- model/provider;
- temperature and sampling settings;
- prompt/schema version;
- fixed data slice and data hash.

Budget is part of the result, not a footnote.

## Minimum Result Tables

The clean repo should generate:

- harness coverage table;
- matched-budget comparison table;
- field-level correctness table;
- evidence-support table;
- seizure-frequency anchor table;
- self-consistency cost table;
- adjudication error-category table.

## Reporting Order

Final result tables should be ordered as:

1. field implementation coverage;
2. call/token budget;
3. component parse validity;
4. proxy coverage/support;
5. matched adjudication;
6. seizure-frequency anchor metrics;
7. failure categories and uncertainty.
