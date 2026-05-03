# Experiment Protocol

## Purpose

Experiments should be small, comparable, and reproducible. The clean repo should
answer the revised research question with fixed slices, explicit budgets,
architecture ablations, model registry entries, and machine-readable run
records.

The main comparison is no longer a binary single-prompt versus multi-agent
test. The study should evaluate an architecture ladder: clinical NLP baselines,
direct LLM prompting, evidence-required prompting, retrieval-plus-extraction,
CLINES-inspired modular extraction, verification variants, and costed
reliability interventions.

## Harness Names

Use descriptive clean harness names rather than inheriting every exploratory
`h00x` name.

| Clean harness | Historical reference | Purpose |
| --- | --- | --- |
| `deterministic_baseline` | `h001`/`h002` | Reproducible rule floor. |
| `exect_v2_external_baseline` | new | Published epilepsy NLP comparator, run as external GATE baseline where feasible. |
| `exect_lite_cleanroom_baseline` | new | Transparent local epilepsy-rule baseline written from published definitions. |
| `single_prompt_anchor` | `h003` | Seizure-frequency direct-prompt anchor. |
| `retrieval_anchor` | new / `h004` reference | Candidate-span seizure-frequency anchor. |
| `multi_agent_anchor` | new | Compact separable anchor with extraction and verification roles. |
| `multi_agent_anchor_sc3` | `h006` | Self-consistency k=3 on anchor task. |
| `multi_agent_anchor_sc5` | `h007` | Self-consistency k=5 on anchor task. |
| `direct_full_contract` | new | Full-schema direct-prompt comparator. |
| `single_prompt_full_contract` | transitional alias | Alias around the same direct full-contract implementation. |
| `direct_evidence_contract` | new | Full-schema direct prompt with stricter evidence and abstention contract. |
| `retrieval_field_extractors` | new | Candidate retrieval plus field-specific extraction. |
| `clines_epilepsy_modular` | `h013` reference | Main CLINES-inspired modular system. |
| `clines_epilepsy_verified` | new | Modular system with explicit verifier/downgrade pass. |
| `budgeted_escalation` | new | Costed reliability variant: cheap retrieval first, stronger direct evidence extraction when policy triggers. |
| `model_family_sensitivity` | `h012` reference | Bounded model-family and model-capacity sensitivity runs. |

## Required Harness Families

### Clinical NLP Baselines

Purpose:

- establish reproducible non-LLM floors;
- avoid comparing LLM systems against a straw man;
- identify fields where conventional rules remain competitive.

Required baselines:

- `deterministic_baseline`;
- `exect_lite_cleanroom_baseline`;
- `exect_v2_external_baseline`, if GATE setup and licensing constraints allow
  external execution.

ExECTv2 should be treated as an external baseline unless licensing is clarified.
Record repository URL, commit hash, GATE version, input documents, output
mapping, and validation scripts used. Do not copy ExECTv2 source logic into
this repo without permission.

### Direct LLM Baselines

`direct_full_contract` is one LLM call that reads the letter and emits the full
output schema.

`direct_evidence_contract` uses the same direct architecture but stricter
evidence, abstention, and warning requirements.

Requirements:

- same final schema as modular pipelines;
- evidence spans required;
- invalid-output recovery logged;
- field-family validity metrics emitted;
- call/token/latency/cost metadata emitted.

### Retrieval-Plus-Field Extraction

This harness tests whether candidate-span retrieval and field-specific local
context improve output quality before adopting the full modular pipeline.

Requirements:

- candidate span artifact;
- field-family extractor outputs;
- evidence spans;
- recall-loss warnings where candidate spans appear incomplete;
- same final schema as direct and modular systems.

### CLINES-Inspired Modular Pipeline

This is the clean implementation of the revised research architecture.

Requirements:

- document normalization and sectioning artifact;
- semantic chunking or candidate-span artifact;
- field extractor artifacts;
- status/temporality artifact;
- normalization artifact, where implemented;
- verification artifact for `clines_epilepsy_verified`;
- aggregation artifact;
- final schema identical to the direct-prompt baseline;
- explicit call/token/latency/cost budget.

Do not label this as a CLINES replication unless the original CLINES code,
prompts, annotations, and evaluation scripts are public and used.

### Anchor Seizure-Frequency Harnesses

Keep the anchor-task line as a compact reliability microcosm:

- single-prompt anchor;
- retrieval anchor;
- compact multi-role anchor;
- self-consistency k=3;
- self-consistency k=5.

Purpose:

- preserve a controlled reliability study;
- stress-test temporality and ambiguity;
- show whether self-consistency is worth its cost;
- keep a low-cost place to test new model families before full-contract runs.

### Model-Family Sensitivity Harnesses

Sensitivity runs should answer specific questions:

- does a stronger model reduce the benefit of modular architecture?
- do smaller open models benefit more from retrieval and verification?
- which models are cost-efficient per evidence-supported extraction?
- do frontier closed models improve correctness enough to justify cost or
  governance constraints?

Closed-provider sensitivity runs on synthetic data must not become the main
clinical evidence spine.

## Fixed-Slice Discipline

Every experiment should specify:

- dataset path;
- data hash;
- row inclusion criteria;
- row order;
- `n`;
- row IDs;
- random seed, if sampling;
- model registry entry ID;
- model/provider/backend;
- prompt/schema version;
- run timestamp;
- code version or commit hash;
- external baseline version or commit hash, if applicable.

Comparisons should use matched rows whenever possible.

## Model Registry Discipline

Experiments must use frozen model registry entries rather than vague labels such
as "latest GPT" or "latest Qwen." Each entry should identify the exact model ID,
provider, release date or snapshot date, context window, pricing source,
inference backend, quantization, decoding settings, and hardware.

Latest-release scouting can happen before the freeze date, but canonical runs
must use frozen entries.

## Budget And Complexity Metrics

For architecture comparisons, define budget explicitly:

- same call count where possible;
- same maximum token budget where meaningful;
- deliberately unequal budgets reported as part of the intervention.

Do not compare a one-call baseline against a multi-call modular pipeline without
making call count, token use, latency, cost, and harness complexity central to
interpretation.

Every run should emit:

- number of LLM calls per row;
- mean input tokens;
- mean output tokens;
- mean total tokens;
- latency;
- estimated cost;
- parse repair count;
- number of modules invoked;
- number and size of intermediate artifacts;
- external tool/runtime requirements.

## Run Record Contract

Each run record should include:

- `run_id`;
- `harness`;
- `architecture_family`;
- `schema_version`;
- `field_coverage`;
- `dataset`;
- `slice`;
- `model_registry_entry`;
- `model`;
- `provider`;
- `backend`;
- `budget`;
- `complexity`;
- `metrics`;
- `rows`;
- `parse_validity`;
- `warnings`;
- `artifact_paths`;
- path to prompt/schema definitions;
- path to model registry snapshot;
- path to adjudication if available.

For harness-native runs, also include:

- `manifest_id` and `manifest_hash`;
- `harness_events` and `event_summary`;
- workflow-unit names and versions;
- document-interface use, if active;
- verifier-gate summaries;
- escalation policy and decision reasons;
- raw artifact references for external adapters.

Matched runs should state whether manifests, event logs, document tools,
verifier gates, and escalation policies were active. A direct full-letter
baseline may legitimately set document-interface use to false; retrieval and
modular runs should use the Clinical-Document Interface where practical.

Escalation variants must be named separately, for example
`budgeted_escalation`, and reported as `costed_reliability_variant`. They should
not overwrite or relabel the strong direct, retrieval, or modular baselines.
External harness outputs should first be replay fixtures through an
`ExternalClinicalAgentAdapter`; live subprocess or framework-agent runs require
separate sandbox approval and are non-canonical until promoted.

## Evidence-Production Order

After implementation, produce evidence in this order:

1. Choose the dataset slice and confirm row IDs, data hash, and inclusion
   criteria.
2. Freeze or select the model registry snapshot for the run set.
3. Run no-provider baselines first: `deterministic_baseline` and
   `exect_lite_cleanroom_baseline`.
4. Run anchor smoke checks against replay or mock providers before spending on
   full-contract calls.
5. Run the matched architecture ladder on the same rows and frozen model entry:
   `direct_full_contract`, `direct_evidence_contract`,
   `retrieval_field_extractors`, `clines_epilepsy_modular`, and
   `clines_epilepsy_verified`.
6. Run bounded costed reliability variants such as `multi_agent_anchor_sc3`,
   `multi_agent_anchor_sc5`, and `budgeted_escalation` only as supporting
   interventions.
7. Run `scripts/summarize_results.py` with `--tables-dir` and the frozen model
   registry.
8. Export matched adjudication sheets for the architecture-ladder runs.
9. Import/summarize adjudication after review.
10. Regenerate cockpit data from the run records, tables, adjudication files,
    manifests, and docs.

## Promotion Gates

Before a harness becomes canonical:

1. one-row smoke validates output shape;
2. small fixed-slice run validates parse stability;
3. `n=25` or `n=50` matched run gives preliminary metrics;
4. matched adjudication confirms value/status/temporality/normalization/evidence
   correctness;
5. budget and complexity metrics are complete;
6. only then promote to canonical result.

## Minimum Dissertation Experiment Set

The repo should produce:

1. deterministic baseline run;
2. ExECT-lite clean-room baseline run;
3. ExECTv2 external baseline run if feasible;
4. seizure-frequency anchor direct vs retrieval/modular run;
5. anchor self-consistency run;
6. direct full-contract run;
7. direct evidence-contract run;
8. retrieval-plus-field-extraction run;
9. CLINES-inspired modular run;
10. CLINES-inspired verified run;
11. matched adjudication for the full-contract architecture ladder;
12. model-family sensitivity runs across frozen open and closed model entries;
13. optional frontier sensitivity run on synthetic data only;
14. optional costed reliability runs such as `budgeted_escalation`, clearly
    reported as supporting variants;
15. optional external-adapter replay runs, clearly labelled non-canonical
    unless separately promoted.

## Result Families

Maintain simple structured outputs for:

- harness coverage;
- baseline comparison;
- architecture ablation ladder;
- model-family and model-tier comparison;
- budget, latency, token, and complexity comparison;
- anchor reliability results;
- clinical adjudication results;
- evidence-support results;
- sensitivity results.

Use `canonical`, `supporting`, and `archive` labels so the visibility cockpit
loads only the evidence that supports final claims by default.
