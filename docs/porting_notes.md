# Porting Notes

## Purpose

The current dissertation repository is the exploration archive. This clean repo
should port durable contracts and mechanisms, not the chronology or full
artifact sprawl of the old repo.

## Port Directly Or Closely Adapt

### Evaluation And Clinical Contract

Source references:

- `docs/evaluation_contract.md`
- `docs/clinical_rubric_tightening_guidelines.md`
- `docs/mc3_field_subset.md`
- `src/epilepsy_agents/evaluation_contract.py`
- `src/epilepsy_agents/mc3.py`

Reason: these encode the field-family and adjudication logic that should be
foundational in the clean repo.

### Data Loading And Labels

Port or reimplement:

- dataset loader code;
- label parser;
- seizure-frequency normalization and metrics;
- data hash and row-filtering metadata.

Reason: reproducible fixed-slice evaluation is a durable strength of the
exploratory repo.

### Provider And Harness Infrastructure

Port or reimplement:

- local/closed provider abstraction;
- run metadata patterns;
- fixed-slice runner discipline;
- prompt/schema versioning patterns.

Reason: the clean repo still needs controlled, training-free experiments.

### h013 And Modular Architecture Ideas

Port the useful design ideas, but adapt them to the revised CLINES-inspired
architecture ladder:

- document sectioning and timeline extraction;
- candidate span and evidence-span artifacts;
- field-specific extraction;
- verification beyond quote presence;
- aggregation without inventing clinical facts;
- confidence/citation/warning output pattern.

Reason: this is the closest existing implementation of the older modular
research architecture, but it should now feed `retrieval_field_extractors`,
`clines_epilepsy_modular`, and `clines_epilepsy_verified` rather than define
the whole dissertation system.

### h012 Design Lesson

Port the lesson, not necessarily the code:

- separate seizure-frequency extraction from broader-field extraction where
  useful;
- compare task framing rather than assuming one joint prompt is best.
- use the lesson as part of model-family and architecture-sensitivity work.

### ExECT And Baseline Lessons

Port or recreate:

- deterministic clinical NLP floor;
- ExECT-lite clean-room baseline based on published field definitions;
- ExECTv2 external-output mapping if GATE outputs are generated separately.

Reason: the revised proposal needs serious clinical NLP baselines, not only LLM
comparators. Do not copy ExECTv2 rules or gazetteers into this repo unless
licensing is clarified.

### Model Registry Discipline

Port or implement:

- provider metadata capture;
- token/cost/latency accounting;
- exact model ID recording;
- frozen model registry snapshots for canonical runs.

Reason: latest-model comparisons must be reproducible and interpretable across
open and closed model families.

## Summarize, Do Not Maintain As Main Code

### h008

Summarize as the joint broader-field stress test.

Lessons:

- joint framing improved broader-field coverage;
- seizure-frequency performance degraded;
- guard/rubric work improved clinical support.

### h009, h010, h011

Summarize as rejected architecture probes.

Lessons:

- broader-only extraction collapsed in h009/h011;
- context injection did not restore coverage;
- anti-abstention language overcorrected in h010.

### h005

Summarize as a failed evidence-presence intervention.

Lesson:

- evidence strings are not the same as evidence support.

### Prompt Example Tuning

Summarize the example-heavy prompt regression.

Lesson:

- prompt interventions must be small, measured, and quickly rejected when they
  regress.

## Archive Or Leave Behind

Do not port these as active clean-repo components unless a specific dissertation
claim requires them:

- full Evidence Notebook static app;
- Pipeline Observatory product implementation;
- generated JS payloads for old dashboards;
- repeated run-log backfills;
- agent-local plugin and command scaffolding;
- frontend design experiments;
- state-machine workflow files;
- intermediate smoke runs;
- rejected harness implementations.

## Historical Evidence To Preserve

The clean repo can cite or summarize:

- `docs/repo_evolution_audit.md`, with corrected backwards interpretation;
- canonical `docs/run_logs/*`;
- `project_state/harnesses/README.md`;
- canonical `project_state/runs/*.json`;
- adjudication CSVs for h008/h012/h013 where relevant.

## Red Flags

Stop and reconsider if the clean repo starts accumulating:

- multiple dashboard apps;
- many manually synchronized state files;
- rejected harnesses as maintained code paths;
- results without data hash and slice metadata;
- evidence metrics that only check quote presence;
- field schemas that merge seizure type, semiology, and epilepsy diagnosis;
- production claims based only on synthetic frontier-model sensitivity.

## First Code-Port Batch

The first implementation batch should add only:

1. data loading and fixed-slice selection;
2. schema definitions for final payloads, evidence grades, field coverage, and
   run metadata;
3. architecture-family and model-registry metadata;
4. baseline mapping support;
5. run-record writing and deterministic metadata capture.

No LLM harness should become canonical until the contract and run metadata layer
exist.
