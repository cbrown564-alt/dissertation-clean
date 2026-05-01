# Experiment Protocol

## Purpose

Experiments should be small, comparable, and reproducible. The clean repo should
answer the research question with fixed slices, explicit budgets, and
machine-readable run records.

## Harness Names

Use descriptive clean harness names rather than inheriting every exploratory
`h00x` name.

| Clean harness | Historical reference | Purpose |
| --- | --- | --- |
| `deterministic_baseline` | `h001`/`h002` | Reproducible floor. |
| `single_prompt_anchor` | `h003` | Seizure-frequency anchor baseline. |
| `multi_agent_anchor` | `h004` | Role-separated anchor comparator. |
| `multi_agent_anchor_sc3` | `h006` | Self-consistency k=3. |
| `multi_agent_anchor_sc5` | `h007` | Self-consistency k=5. |
| `single_prompt_full_contract` | new | Full-schema single-prompt comparator. |
| `multi_agent_full_contract` | `h013` reference | Main role-separated system. |
| `medium_sensitivity` | `h012` | Optional bounded sensitivity harness. |

## Required Harnesses

### Full-Contract Single-Prompt Baseline

One LLM call reads the letter and emits the full output schema.

Purpose:

- main baseline against the role-separated system;
- tests whether architecture adds reliability beyond a strong direct prompt.

Requirements:

- same final schema as the multi-agent pipeline;
- evidence spans required;
- invalid-output recovery logged;
- field-family validity metrics emitted;
- budget metadata emitted.

### Full-Contract Role-Separated Multi-Agent Pipeline

This is the clean implementation of the original research idea.

Requirements:

- section/timeline artifact;
- field extractor artifacts;
- verification artifact;
- aggregation artifact;
- final schema identical to the single-prompt baseline;
- explicit call/token budget.

### Anchor Seizure-Frequency Harnesses

Keep the anchor-task line as a compact reliability microcosm:

- single-prompt anchor;
- role-separated anchor;
- self-consistency k=3;
- self-consistency k=5.

Purpose:

- preserve a controlled reliability study;
- show same-budget role separation may be parity;
- show self-consistency as a costed reliability intervention.

### Sensitivity Harnesses

Sensitivity runs are optional and bounded. They should answer specific questions
such as whether a stronger model changes conclusions or whether task framing
affects broader-field utility.

Closed-provider sensitivity runs are synthetic-only and must not become the main
evidence spine.

## Fixed-Slice Discipline

Every experiment should specify:

- dataset path;
- data hash;
- row inclusion criteria;
- row order;
- `n`;
- row IDs;
- random seed, if sampling;
- model/provider;
- prompt/schema version;
- run timestamp;
- code version or commit hash.

Comparisons should use matched rows whenever possible.

## Budget Matching

For single-prompt vs multi-agent comparison, define budget explicitly:

- same call count where possible;
- same maximum token budget; or
- deliberately unequal budgets reported as an intervention.

Do not compare a one-call baseline against a multi-call role pipeline without
making the budget difference central to interpretation.

Recommended primary comparisons:

1. one-call full-contract single prompt vs one-call constrained role variant, if
   feasible;
2. one-call full-contract single prompt vs production multi-agent with budget
   reported;
3. production multi-agent vs self-consistency or verifier variants as costed
   improvements.

## Run Record Contract

Each run record should include:

- `run_id`;
- `harness`;
- `schema_version`;
- `field_coverage`;
- `dataset`;
- `slice`;
- `model`;
- `provider`;
- `budget`;
- `metrics`;
- `rows`;
- `parse_validity`;
- `warnings`;
- `artifact_paths`;
- path to prompt/schema definitions;
- path to adjudication if available.

## Promotion Gates

Before a harness becomes canonical:

1. one-row smoke validates output shape;
2. small fixed-slice run validates parse stability;
3. `n=25` or `n=50` matched run gives preliminary metrics;
4. matched adjudication confirms value/status/evidence correctness;
5. only then promote to canonical result.

## Minimum Dissertation Experiment Set

The repo should produce:

1. deterministic baseline run;
2. anchor single-prompt vs anchor multi-agent run;
3. anchor self-consistency run;
4. full-contract single-prompt run;
5. full-contract multi-agent run;
6. matched adjudication for the full-contract comparison;
7. optional h012/frontier sensitivity run on synthetic data only.

## Result Families

Maintain simple structured outputs for:

- harness coverage;
- anchor reliability results;
- full-contract comparison;
- clinical adjudication results;
- sensitivity results.

Use `canonical`, `supporting`, and `archive` labels so the visibility cockpit
loads only the evidence that supports final claims by default.
