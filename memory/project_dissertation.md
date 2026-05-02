---
name: Dissertation Pipeline Project State
description: Epilepsy extraction dissertation — phase completion status, architecture overview, and key design decisions
type: project
---

Research question: How do CLINES-inspired modular architecture, clinical extraction baselines, and model capacity affect correctness, evidence support, auditability, cost, latency, token use, and harness complexity in epilepsy clinic-letter extraction?

## Phase completion (as of 2026-05-02)

Phases 0–8 are complete. The next phase is Phase 9 (Evaluation And Result Tables).

- Phase 0: Repo readiness ✓
- Phase 1: Contract and schema hardening ✓
- Phase 2: Model registry and provider abstraction ✓
- Phase 3: Prompt, schema, and mapping assets ✓
- Phase 4: Clinical NLP baselines ✓
- Phase 5: Anchor seizure-frequency harnesses ✓
- Phase 6: Direct full-contract LLM baselines ✓
- Phase 7: Retrieval-plus-field extraction ✓
- Phase 8: CLINES-inspired modular pipeline ✓

## Architecture ladder (harnesses implemented)

- `deterministic_baseline` — no LLM, regex rules
- `exect_lite_cleanroom_baseline` — cleanroom ExECT-lite rules
- `exect_v2_external_baseline` — adapter for external ExECTv2 outputs
- `single_prompt_anchor` / `retrieval_anchor` / `multi_agent_anchor` / `*_sc3` / `*_sc5` — seizure-frequency anchor
- `direct_full_contract` / `single_prompt_full_contract` — direct single-call full extraction
- `direct_evidence_contract` — direct with evidence-contract prompt
- `retrieval_field_extractors` — regex retrieval + per-family extraction
- `clines_epilepsy_modular` — section-aware chunking, per-family extraction, deterministic status/norm/verification, aggregation
- `clines_epilepsy_verified` — same + one provider-backed verification call per row

## Key module locations

- `src/epilepsy_extraction/modules/` — Phase 8 modules: chunking, field_extractors, status_temporality, normalization, verification, aggregation
- `src/epilepsy_extraction/harnesses/` — all harnesses
- `src/epilepsy_extraction/schemas/` — contracts, extraction, runs
- `src/epilepsy_extraction/providers/` — base, mock, replay
- `src/epilepsy_extraction/evaluation/` — metrics, mapping, labels
- `prompts/clines_inspired/` — field_extractor_v1.md, verification_v1.md

## Test suite

152 tests, all passing. No LLM/network dependency for tests (mock/replay providers).

**Why:** Phase 9 needs evaluation table generation from run records; see docs/evaluation_contract.md for the required table list.
**How to apply:** When implementing Phase 9, generate tables from run records in results/ using summarize_results.py.
