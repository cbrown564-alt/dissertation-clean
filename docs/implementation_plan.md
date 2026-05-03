# Comprehensive Implementation Plan

This plan builds from the repo's current contract-first state into a runnable
dissertation evidence pipeline for the revised research question:

> How do CLINES-inspired modular architecture, clinical extraction baselines,
> and model capacity affect correctness, evidence support, auditability, cost,
> latency, token use, and harness complexity in epilepsy clinic-letter
> extraction?

The implementation should no longer optimize for a single binary comparison
between direct prompting and a role-separated system. It should build an
architecture ladder, map clinical NLP baselines, and support frozen model-family
experiments.

The companion review in `docs/coding_agent_harness_literature_review.md`
extends this plan with a harness-native direction. The main implication is that
the system should treat the harness as part of the evaluated method, not as
incidental glue around prompts. Later phases should therefore make manifests,
typed workflow units, event traces, document tools, verifier gates, budget
policies, and cockpit visibility first-class outputs.

## Phase 0: Repo Readiness

Goal: make the existing foundation easy to run and hard to accidentally break.

Tasks:

- Add a tiny committed fixture dataset under `tests/fixtures/`.
- Ensure `pytest` is available through a documented dev setup.
- Add `README` commands for install, test, smoke run, summarize run.
- Confirm all schema, data, and evaluation tests pass from a fresh checkout.
- Add a lightweight CI command or local `scripts/check.py` if desired.

Files likely touched:

- `README.md`
- `pyproject.toml`
- `tests/fixtures/*.json`
- `tests/test_*.py`

Acceptance criteria:

- A new developer can install dev dependencies and run tests.
- Existing smoke metadata run works against a fixture.
- No LLM/provider dependency is needed for tests.

## Phase 1: Contract And Schema Hardening

Goal: strengthen the shared contract before adding baselines and harnesses.

Tasks:

- Add JSON serialization helpers for extraction payloads, not just run records.
- Add schema validation-style checks for required final payload keys.
- Add `architecture_family`, `model_registry_entry`, `complexity`, and
  `external_baseline` fields to run records.
- Add field coverage helpers for full contract, partial contract, unsupported
  fields, and `not_attempted` baseline fields.
- Add parse-validity metric helpers for component validity rates.
- Add helpers for evidence grades, field-family mapping, and literature-aligned
  field names.
- Make run-record `code_version` configurable from git commit when available.
- Add tests for payload serialization, coverage helpers, baseline mapping, and
  run-record metadata.

Files likely touched:

- `src/epilepsy_extraction/schemas/extraction.py`
- `src/epilepsy_extraction/schemas/contracts.py`
- `src/epilepsy_extraction/schemas/runs.py`
- `src/epilepsy_extraction/evaluation/mapping.py`
- `tests/test_schemas.py`
- `tests/test_evaluation_mapping.py`

Acceptance criteria:

- Every harness can emit the same payload shape or an explicitly mapped partial
  baseline payload.
- Missing, partial, failed, and not-attempted fields are represented
  consistently.
- Run records include reproducibility, model registry, architecture, budget,
  and complexity metadata in standard places.

## Phase 2: Model Registry And Provider Abstraction

Goal: define the boundary between harness logic and model calls, and make
model-family experiments reproducible.

Tasks:

- Add provider protocol/interface for chat/completion requests.
- Define provider request, response, usage, latency, cost, and error dataclasses.
- Add mock provider for tests.
- Add local JSON replay provider so old or captured outputs can be evaluated
  without calling an API.
- Add model registry loader and validator.
- Add candidate and frozen registry file locations.
- Add parse failure/recovery conventions.
- Keep closed-provider clients optional and outside core tests.

Files likely touched:

- `src/epilepsy_extraction/providers/base.py`
- `src/epilepsy_extraction/providers/mock.py`
- `src/epilepsy_extraction/providers/replay.py`
- `src/epilepsy_extraction/providers/__init__.py`
- `src/epilepsy_extraction/models/registry.py`
- `config/model_registry.candidate.yaml`
- `tests/test_providers.py`
- `tests/test_model_registry.py`

Acceptance criteria:

- Harnesses can call a provider without knowing whether it is mock, replay,
  local, or closed.
- Token, call, latency, and cost metadata flow into run records.
- A frozen model registry entry can be attached to a run.
- Tests do not require network or secrets.

## Phase 3: Prompt, Schema, And Mapping Assets

Goal: make prompts, output schemas, and baseline mapping rules versioned,
inspectable, and tied to run records.

Tasks:

- Add prompt directories for direct, evidence-contract, retrieval, and
  CLINES-inspired modular harnesses.
- Add final output schema description or JSON schema-like contract.
- Add baseline mapping specs for deterministic, ExECT-lite, and ExECTv2 outputs.
- Add prompt version IDs.
- Add loader utilities for prompt and mapping files.
- Store prompt path/version, schema version, and mapping version in run records.

Suggested structure:

```text
prompts/
  direct/
    full_contract_v1.md
    evidence_contract_v1.md
  retrieval/
    field_extractors_v1/
  clines_inspired/
    chunking_v1.md
    field_extractors_v1/
    verification_v1.md
schemas/
  final_extraction_v1.md or final_extraction_v1.json
mappings/
  exect_v2_mapping_v1.yaml
  exect_lite_mapping_v1.yaml
```

Acceptance criteria:

- Every LLM run records prompt version and schema version.
- Every external or partial baseline run records mapping version.
- Prompt and mapping changes are reviewable as normal files.
- Direct, retrieval, and modular systems share the same final schema.

## Phase 4: Clinical NLP Baselines

Goal: create reproducible floors and serious non-LLM comparators before LLM
architecture work.

Tasks:

- Implement `deterministic_baseline` harness.
- Implement `exect_lite_cleanroom_baseline` using independently authored rules
  based on published field definitions.
- Add an `exect_v2_external_baseline` adapter that can ingest ExECTv2 outputs
  when generated outside this repo.
- Document ExECTv2 setup assumptions, source repository, commit hash, GATE
  version, and licensing caveat.
- Ensure gold labels are reserved for evaluation and fixtures; no benchmark path
  may read gold labels as input.
- Emit valid mapped run records with `clinical_nlp_baseline` architecture
  family.

Files likely touched:

- `src/epilepsy_extraction/harnesses/deterministic.py`
- `src/epilepsy_extraction/harnesses/exect_lite.py`
- `src/epilepsy_extraction/harnesses/exect_v2_external.py`
- `src/epilepsy_extraction/harnesses/__init__.py`
- `scripts/run_experiment.py`
- `tests/test_baseline_harnesses.py`

Acceptance criteria:

- `python scripts/run_experiment.py dataset.json --harness deterministic_baseline --limit 5`
  writes a valid run record.
- ExECT-lite emits mapped partial/full outputs without copying ExECTv2 source
  logic.
- ExECTv2 external outputs can be mapped when available.
- Baseline field coverage distinguishes attempted, supported, and
  `not_attempted` fields.
- No benchmark path reads gold labels as input.

## Phase 5: Anchor Seizure-Frequency Harnesses ✓ COMPLETE

Goal: rebuild the compact reliability microcosm around the new architecture
ladder.

Tasks:

- Implement `direct_anchor`.
- Implement `retrieval_anchor`.
- Implement a separable CLINES-style anchor if useful.
- Implement self-consistency variants `anchor_sc3` and `anchor_sc5`.
- Reuse existing label parsing and metrics.
- Emit row-level predictions, evidence spans, confidence, warnings, and budget.
- Add replay/mock-provider tests for successful parse, invalid JSON, abstention,
  unsupported evidence, and retrieval recall loss.
- Timebox this phase as an infrastructure exercise so seizure frequency does
  not crowd out the full-contract architecture ladder.

Files likely touched:

- `src/epilepsy_extraction/harnesses/anchor.py`
- `src/epilepsy_extraction/retrieval/candidates.py`
- `src/epilepsy_extraction/evaluation/metrics.py`
- `scripts/run_experiment.py`
- `tests/test_anchor_harnesses.py`

Acceptance criteria:

- Anchor harnesses produce comparable run records.
- `summarize()` can generate anchor metrics from run rows.
- Self-consistency reports extra cost explicitly.
- Retrieval failures are visible as retrieval recall or candidate-span warnings.

## Phase 6: Direct Full-Contract LLM Baselines ✓ COMPLETE

Goal: create strong direct-prompt comparators.

Tasks:

- Implement `direct_full_contract`.
- Implement `direct_evidence_contract`.
- One provider call reads the letter and emits the final schema.
- Parse into `ExtractionPayload`.
- Validate field-family coverage and component parse validity.
- Preserve warnings, citations, confidence, invalid output state, and raw
  provider artifact.
- Add recovery policy for invalid/malformed output.

Files likely touched:

- `src/epilepsy_extraction/harnesses/direct_full_contract.py`
- `src/epilepsy_extraction/schemas/extraction.py`
- `tests/test_direct_full_contract.py`

Acceptance criteria:

- Direct harnesses emit the same final payload shape expected of retrieval and
  modular pipelines.
- Records field coverage for all core families.
- Invalid output is measurable by component, not only globally.
- Evidence-contract behavior is separately measurable from direct prompting.

## Phase 7: Retrieval-Plus-Field Extraction ✓ COMPLETE

Goal: test whether candidate-span selection and local-context extraction improve
output quality before the full modular pipeline.

Tasks:

- Implement document normalization and basic section detection.
- Implement candidate-span retrieval grouped by field family.
- Implement field-specific extractors over candidate spans plus local context.
- Preserve candidate-span artifacts, token counts, and retrieval warnings.
- Add recall-loss error tags when retrieved context appears insufficient.
- Aggregate field outputs into the shared final payload.

Files likely touched:

- `src/epilepsy_extraction/document/normalization.py`
- `src/epilepsy_extraction/document/sections.py`
- `src/epilepsy_extraction/retrieval/candidates.py`
- `src/epilepsy_extraction/harnesses/retrieval_field_extractors.py`
- `tests/test_retrieval.py`
- `tests/test_retrieval_field_extractors.py`

Acceptance criteria:

- Retrieval artifacts are preserved in `artifacts`.
- Field extractors emit schema-valid outputs using the shared final schema.
- Retrieval can be compared against direct prompting on matched rows.
- Candidate-span recall failures are observable and not collapsed into generic
  wrong-answer errors.

## Phase 8: CLINES-Inspired Modular Pipeline ✓ COMPLETE

Goal: implement the main revised architecture as a clinical modular pipeline,
not as a claimed CLINES replication.

Build modules in this order:

1. Document normalization and sectioning.
2. Semantic chunking and candidate-span retrieval.
3. Field-specific extraction.
4. Assertion, status, and temporality enrichment.
5. Normalization and value/unit handling.
6. Evidence verification.
7. Cross-chunk aggregation and schema adaptation.

Field extractors should cover:

- Seizure frequency and seizure freedom.
- Current medications.
- Investigations.
- Seizure type, semiology, and pattern modifiers.
- Epilepsy type and syndrome.

Files likely touched:

- `src/epilepsy_extraction/modules/chunking.py`
- `src/epilepsy_extraction/modules/field_extractors.py`
- `src/epilepsy_extraction/modules/status_temporality.py`
- `src/epilepsy_extraction/modules/normalization.py`
- `src/epilepsy_extraction/modules/verification.py`
- `src/epilepsy_extraction/modules/aggregation.py`
- `src/epilepsy_extraction/harnesses/clines_epilepsy_modular.py`
- `src/epilepsy_extraction/harnesses/clines_epilepsy_verified.py`
- `tests/test_modules.py`
- `tests/test_clines_epilepsy_modular.py`

Acceptance criteria:

- Modular final schema matches direct-prompt final schema.
- Intermediate artifacts are preserved for chunking, candidate spans,
  extraction, status/temporality, normalization, verification, and aggregation.
- Verifier grades more than quote presence.
- Aggregator does not create new clinical claims.
- The run record clearly labels this as `clines_inspired_modular`, not CLINES
  replication.

## Phase 9: Evaluation And Result Tables ✓ COMPLETE

Goal: turn runs into dissertation-ready evidence under the revised evaluation
contract.

Tasks:

- Generate architecture and harness coverage table.
- Generate baseline comparability table.
- Generate model registry table.
- Generate budget, latency, token, and complexity table.
- Generate component parse-validity table.
- Generate field-level correctness/adjudication table skeletons.
- Generate evidence-support table.
- Generate architecture ablation table.
- Generate model-family and model-tier table.
- Generate seizure-frequency anchor table.
- Generate self-consistency cost table.
- Generate harness-complexity tables that can later incorporate manifest
  version, event counts, module counts, repair attempts, verifier passes,
  escalation decisions, and artifact counts per row.
- Add CSV/JSON output under `results/tables/`.

Files likely touched:

- `scripts/summarize_results.py`
- `src/epilepsy_extraction/evaluation/tables.py`
- `src/epilepsy_extraction/evaluation/metrics.py`
- `tests/test_tables.py`

Acceptance criteria:

- Given one or more run records, scripts produce stable machine-readable tables.
- Tables follow the order in `docs/evaluation_contract.md`.
- Missing adjudication is explicit, not silently treated as zero.
- Architecture deltas can be computed on matched rows where available.
- Harness complexity is represented as evaluable data rather than prose-only
  commentary.

## Phase 10: Adjudication Workflow ✓ COMPLETE

Goal: support matched clinical review without blending adjudication into model
output.

Tasks:

- Add adjudication sheet generator.
- Include row ID, harness, architecture family, model registry entry, field
  family, emitted value, evidence, scores, error tags, and notes.
- Add adjudication importer.
- Add adjudication summary metrics.
- Keep adjudication files under `results/adjudication/`.
- Align error tags with `docs/evaluation_contract.md` and
  `docs/adjudication_protocol.md`.

Files likely touched:

- `src/epilepsy_extraction/evaluation/adjudication.py`
- `scripts/build_adjudication_sheet.py`
- `scripts/summarize_adjudication.py`
- `tests/test_adjudication.py`

Acceptance criteria:

- Matched architecture-ladder outputs can be exported for review.
- Completed adjudication can be re-imported.
- Error tags distinguish wrong value, wrong status, wrong temporality, wrong
  normalization, unsupported evidence, retrieval recall loss, aggregation
  conflict, and baseline mapping error.

## Phase 11: Model-Family Sensitivity Runs ✓ COMPLETE

Goal: evaluate whether architecture benefits change across open and closed
model families and model-size tiers.

Tasks:

- Freeze `config/model_registry.YYYY-MM-DD.yaml`.
- Run anchor smoke tests across candidate model entries.
- Select bounded small/medium/frontier model sets.
- Run selected architecture rungs across frozen model entries.
- Report model-family metrics, token use, cost, latency, parse stability, and
  evidence-supported correctness.
- Keep closed-provider and frontier runs bounded, especially on synthetic data.

Files likely touched:

- `config/model_registry.YYYY-MM-DD.yaml`
- `scripts/run_model_matrix.py`
- `scripts/summarize_results.py`
- `results/runs/*`
- `results/tables/model_family*.csv`

Acceptance criteria:

- Every canonical model run references a frozen registry entry.
- Results can compare model family, tier, architecture, budget, and evidence
  support.
- Moving aliases such as "latest" are not used in canonical result tables.
- Closed-provider sensitivity runs are clearly labelled and bounded.

## Phase 12: Generated Unified Cockpit ✓ COMPLETE

Goal: provide a compact, regularly regenerated visibility layer that preserves
the best qualities of the original unified document without recreating the old
dashboard sprawl.

The cockpit should be a supervisor/examiner-facing visual narrative, not just a
JSON dump. It should make the research arc legible at a glance: architecture
ladder, baselines, model registry, decisions, linked records, current claims,
uncertainties, timelines, example rows, and budget/performance tradeoffs.

Design reference screenshots and notes from the previous unified simplified
view are preserved in `docs/visibility_cockpit_reference/`. They should inspire
the interaction model and information hierarchy, while the clean repo rebuilds
the content model around benchmark comparison, wider field coverage, evidence
support, adjudication, and model registry governance.

Tasks:

- Expand `build_cockpit_data.py` into the source-backed data compiler for the
  cockpit.
- Generate `site/cockpit-data.json` from docs, run records, result tables,
  adjudication files, and decision notes.
- Add a small static `site/index.html` inspired by the original unified doc's
  editorial research-review style.
- Show research docs, run records, current canonical/supporting/archive runs,
  table summaries, and model registry snapshots.
- Include core visual views: architecture ladder, harness tradeoff surface,
  baseline comparability, model-family matrix, branch detail, linked decisions,
  session timeline, current-status claim panel, and source-letter/extracted
  output example view.
- Refactor the cockpit data model so it can ingest harness manifests, event-log
  summaries, skill/module versions, verifier-gate summaries, and
  harness-complexity tables when Phase 13 lands.
- Add a harness-native view that explains how a row moved through context
  construction, extraction, verification, aggregation, and adjudication export.
- Keep it generated, data-driven, and minimal enough to maintain.
- Treat `site/cockpit-data.json` as generated output by default. Commit the
  generator and source artifacts; commit generated snapshots only when they are
  intentionally used as review/reproducibility artifacts.

Files likely touched:

- `scripts/build_cockpit_data.py`
- `site/index.html`
- `site/cockpit-data.json`

Acceptance criteria:

- Cockpit is regenerated by a documented command, not hand-maintained.
- Cockpit loads generated JSON and links every visible claim back to docs,
  run records, tables, adjudication, model registry entries, or decision notes.
- It does not become a second source of truth.
- It only surfaces canonical/supporting/archive labels already present in run
  records.
- Harness-native displays link back to source manifests, event summaries, run
  records, and result tables rather than duplicating those facts in the site.

## Phase 13: Harness-Native Refactor ✓ COMPLETE

Goal: refactor the completed architecture ladder so every extraction system is
described and evaluated as an explicit clinical agent harness.

This phase incorporates the implementation backlog from
`docs/coding_agent_harness_literature_review.md`. It should be treated as a
methodological hardening phase, not a new claim that more agents are better.
The existing direct, retrieval, modular, verifier, model-matrix, adjudication,
and cockpit work should remain intact, but the metadata and orchestration
surfaces should become more explicit.

### 13.1 Harness Manifests ✓ COMPLETE

Tasks:

- Add versioned harness manifests under `config/harnesses/`.
- Capture harness ID, architecture family, allowed modules/tools, prompt
  versions, schema versions, provider/model registry entry, context policy,
  output contract, repair policy, verifier policy, aggregation policy, budget
  limits, gold-label isolation rules, and artifact retention policy.
- Add manifest loader and validator.
- Store manifest ID and manifest hash in run records.
- Update `scripts/run_experiment.py` and `scripts/run_model_matrix.py` so a run
  can resolve defaults from a manifest while still allowing explicit CLI
  overrides for experiments.

Files likely touched:

- `config/harnesses/*.yaml`
- `src/epilepsy_extraction/harnesses/manifest.py`
- `src/epilepsy_extraction/schemas/runs.py`
- `scripts/run_experiment.py`
- `scripts/run_model_matrix.py`
- `tests/test_harness_manifests.py`

Acceptance criteria:

- Every canonical harness run references a validated manifest.
- Prompt, schema, mapping, verifier, aggregation, and budget policies are no
  longer hidden in code-only conventions.
- Manifest changes are reviewable as normal dissertation-method changes.

### 13.2 Harness Event Logs ✓ COMPLETE

Tasks:

- Add a lightweight `HarnessEvent` schema for row-level traces.
- Use stable event types such as `context_built`, `provider_call_started`,
  `provider_call_finished`, `parse_attempted`, `parse_repaired`,
  `candidate_spans_selected`, `field_extraction_completed`,
  `verification_completed`, `aggregation_completed`, `budget_limit_hit`, and
  `warning_emitted`.
- Store PHI-safe event summaries by default; allow quote-bearing synthetic
  fixture events only when the dataset policy permits it.
- Add event summary helpers for counts, timings, warnings, repair attempts,
  verifier passes, and escalation decisions.
- Include event summary metadata in run records and result tables.

Files likely touched:

- `src/epilepsy_extraction/schemas/events.py`
- `src/epilepsy_extraction/schemas/runs.py`
- `src/epilepsy_extraction/evaluation/tables.py`
- `src/epilepsy_extraction/harnesses/*.py`
- `tests/test_harness_events.py`
- `tests/test_tables.py`

Acceptance criteria:

- Harness behavior is inspectable without reading raw provider artifacts.
- Event logs support row-level debugging, matched ablations, and cockpit
  visualization.
- Event logs do not leak gold labels or clinical secrets into model-visible
  context.

### 13.3 Skill-Like Field Workflow Units ✓ COMPLETE

Tasks:

- Package field extractors, verifier, normalizer, and aggregator as versioned
  workflow units with declared input/output contracts.
- Record workflow unit names and versions in artifacts.
- Add shared pre/post hooks for parse repair, deterministic normalization,
  evidence validation, and warning emission.
- Keep the implementation Python-native; do not introduce an external agent
  framework unless a later experiment explicitly justifies it.

Files likely touched:

- `src/epilepsy_extraction/modules/field_extractors.py`
- `src/epilepsy_extraction/modules/verification.py`
- `src/epilepsy_extraction/modules/normalization.py`
- `src/epilepsy_extraction/modules/aggregation.py`
- `src/epilepsy_extraction/modules/workflows.py`
- `tests/test_modules.py`

Acceptance criteria:

- Field-family behavior can be compared by workflow unit version.
- Adding a new clinical field requires a declared contract rather than an
  implicit prompt-only change.
- Workflow metadata flows into run artifacts and cockpit data.

### 13.4 Clinical-Document Interface ✓ COMPLETE

Tasks:

- Define bounded document tools for `get_sections`, `search_spans`,
  `get_span`, `quote_evidence`, `validate_payload`, and
  `compare_evidence_to_claim`.
- Route retrieval and modular harnesses through this interface where practical.
- Preserve direct full-letter prompting as a separate baseline that can bypass
  the interface.
- Add tests for section lookup, span windows, quote fidelity, and evidence
  locator stability.

Files likely touched:

- `src/epilepsy_extraction/document/interface.py`
- `src/epilepsy_extraction/document/sections.py`
- `src/epilepsy_extraction/retrieval/candidates.py`
- `src/epilepsy_extraction/harnesses/retrieval_field_extractors.py`
- `src/epilepsy_extraction/harnesses/clines_epilepsy_modular.py`
- `tests/test_document_interface.py`

Acceptance criteria:

- Retrieval and modular systems have a stable Clinical-Document Interface,
  analogous to a coding agent's Agent-Computer Interface.
- Evidence quotes can be traced back to deterministic locators.
- Direct and modular comparisons can explicitly report which systems used the
  document interface.

### 13.5 Verifier Gates And Escalation Policies ✓ COMPLETE

Tasks:

- Expand verifier artifacts to distinguish value support, status support,
  temporality support, normalization support, field-family placement, and
  known epilepsy edge-case checks.
- Add downgrade/removal policies for unsupported overclaims.
- Add budgeted model-escalation harness variants: cheap retrieval, stronger
  ambiguous extraction, verifier equal-or-stronger than extractor, and
  escalation only on low confidence, parse failure, or verifier disagreement.
- Keep escalation variants separate from canonical baseline runs.

Files likely touched:

- `src/epilepsy_extraction/modules/verification.py`
- `src/epilepsy_extraction/harnesses/clines_epilepsy_verified.py`
- `src/epilepsy_extraction/harnesses/escalation.py`
- `config/harnesses/*escalation*.yaml`
- `tests/test_clines_epilepsy_modular.py`
- `tests/test_escalation_harnesses.py`

Acceptance criteria:

- Verifier performance can be evaluated as its own intervention.
- Escalation decisions are visible in event logs and budget tables.
- Costed reliability variants never silently replace the strong direct,
  retrieval, or modular baselines.

### 13.6 External Harness Adapters ✓ COMPLETE

Tasks:

- Define an `ExternalClinicalAgentAdapter` boundary for sandboxed outputs from
  CLI or framework agents.
- Normalize adapter outputs into `ExtractionPayload`, `HarnessEvent` summaries,
  and raw artifact references.
- Treat Claude Code, Codex, Pi, Flue, OpenHands, Gemini CLI, Aider, and
  harness adapters as possible future runners, not canonical clinical
  comparators by default.
- Add replay fixtures for external adapter outputs before attempting live
  subprocess runs.

Files likely touched:

- `src/epilepsy_extraction/harnesses/external_adapter.py`
- `src/epilepsy_extraction/providers/replay.py`
- `tests/fixtures/external_harness_outputs/*.json`
- `tests/test_external_harness_adapter.py`

Acceptance criteria:

- External harness outputs can be evaluated without changing the final schema.
- Live external-agent runs remain optional and non-canonical unless separately
  approved and sandboxed.
- The repo can compare local harnesses and external harness outputs through a
  common event/run contract.

### 13.7 Cockpit Refactor For Harness Visibility ✓ COMPLETE

Tasks:

- Update `scripts/build_cockpit_data.py` to ingest harness manifests, event-log
  summaries, workflow versions, verifier-gate summaries, escalation decisions,
  and harness-complexity tables.
- Add cockpit panels for harness manifest lineage, row-level event timelines,
  verifier gates, escalation/cost decisions, and workflow-unit versions.
- Keep `site/index.html` generated-data-driven; do not make the cockpit a
  hand-maintained source of truth.
- Add tests or smoke checks that the cockpit compiler handles old run records
  without harness-native fields and new run records with manifest/event data.

Files likely touched:

- `scripts/build_cockpit_data.py`
- `site/index.html`
- `site/cockpit-data.json`
- `tests/test_scripts.py`

Acceptance criteria:

- The cockpit can explain not only which harness won, but how a harness reached
  its output.
- Older run records degrade gracefully with missing manifest/event data.
- Harness-native claims visible in the cockpit link back to manifests, run
  records, event summaries, tables, or docs.

### 13.8 Evaluation Contract Update ✓ COMPLETE

Tasks:

- Update `docs/evaluation_contract.md` to define harness manifests,
  event traces, verifier-gate metrics, escalation metrics, and
  harness-complexity reporting.
- Update `docs/experiment_protocol.md` so matched runs specify whether
  manifests, event logs, document tools, verifier gates, and escalation policies
  are active.
- Update `docs/adjudication_protocol.md` only where event traces or verifier
  gates affect reviewer-facing artifacts.

Files likely touched:

- `docs/evaluation_contract.md`
- `docs/experiment_protocol.md`
- `docs/adjudication_protocol.md`

Acceptance criteria:

- Harness-native metadata has a documented evaluation meaning.
- New complexity and trace metrics are not confused with clinical correctness.
- Human adjudication remains independent from model-generated claims.

## Recommended Build Order

1. Phase 0: repo readiness.
2. Phase 1: contract and schema hardening.
3. Phase 2: model registry and provider abstraction.
4. Phase 3: prompt, schema, and mapping assets.
5. Phase 4: clinical NLP baselines.
6. Phase 5: anchor seizure-frequency harnesses.
7. Phase 6: direct full-contract LLM baselines.
8. Phase 7: retrieval-plus-field extraction.
9. Phase 8: CLINES-inspired modular pipeline.
10. Phase 9: evaluation and result tables.
11. Phase 10: adjudication workflow.
12. Phase 11: model-family sensitivity runs.
13. Phase 12: cockpit.
14. Phase 13: harness-native refactor.

The anchor harnesses still come before the full-contract systems. They are
smaller, they exercise provider calls and run metadata, and they expose the
awkward parts of parsing, invalid output handling, evidence spans, retrieval,
and budget accounting before those problems get multiplied across all field
families. Clinical NLP baselines should also come early so the project does not
accidentally optimize only against LLM comparators.

Phase 13 comes after the first complete architecture ladder because it refactors
what has already been learned into a more explicit harness contract. It should
not invalidate earlier runs; instead, it should allow older records to remain
readable while newer records expose manifests, event traces, verifier gates,
workflow versions, and cockpit-level harness visibility.
