# Proposal Decision Map

## Purpose

This document records the current dissertation direction after the literature
review. It treats the earlier role-separated extraction idea as a useful first
draft, but not as the final research frame.

The revised proposal should evaluate how clinical extraction architecture,
clinical NLP baselines, and model capacity interact when extracting structured,
evidence-grounded epilepsy information from clinic letters.

## Revised Dissertation Spine

The central contribution is a controlled evaluation of epilepsy clinic-letter
extraction systems across:

- clinical NLP baselines;
- direct LLM prompting;
- evidence-required direct prompting;
- retrieval-plus-field extraction;
- CLINES-inspired modular extraction;
- verifier and self-consistency variants;
- contemporary open and closed model families.

The study should report not only correctness, but evidence support, status and
temporality handling, normalization quality, parse validity, cost, latency,
token use, and harness complexity.

## Key Decisions

| Decision | Options | Literature Pressure | Recommended Position |
| --- | --- | --- | --- |
| Main frame | Multi-agent vs single prompt; clinical architecture comparison | Fang warns direct extraction can be strong; CLINES supports modular clinical decomposition | Use architecture/model/cost tradeoff study as the main frame |
| Modular architecture | Generic role agents; CLINES-inspired clinical modules | CLINES decomposes chunking, entity extraction, normalization, dates, attributes, and aggregation | Build a CLINES-inspired epilepsy pipeline |
| Baselines | LLM-only; deterministic; ExECTv2; ExECT-lite; machine-reading | ExECT and Xie are serious prior approaches | Include deterministic and ExECT-style baselines; use ExECTv2 externally if feasible |
| ExECT replication | Directly run public ExECTv2; clean-room approximation | ExECTv2 code and synthetic data are public, but repo has no explicit license | Run as external baseline; build separate clean-room ExECT-lite if needed |
| CLINES replication | Direct replication; inspired implementation | CLINES code/prompts promised at publication but not currently public | Do not claim replication; implement a CLINES-inspired architecture |
| Model strategy | One model; open only; closed only; model-family matrix | Recent studies show model choice and harness design both matter | Freeze a model registry covering open/closed, small/medium/large tiers |
| Output representation | Numeric targets; categories; clinical-status objects | Holgate and Gan show representation shapes performance | Use structured clinical-status objects with evidence and warnings |
| Evidence | Optional citation; required span; verifier-graded support | Evidence is useful only when it supports value/status/time/normalization | Require evidence and adjudicate support quality |
| Budget | Footnote; matched budget only; costed intervention | Modular pipelines cost more; model tiers differ sharply | Report calls, tokens, latency, and cost as primary outcomes |
| Synthetic data | Development only; main evidence; sensitivity | Synthetic letters improve reproducibility but bound clinical claims | Use synthetic data for development and reproducible benchmarks; bound clinical claims |

## Proposed Architecture Ladder

| Rung | Name | Description | Primary Question |
| --- | --- | --- | --- |
| 0 | `deterministic_baseline` | Simple rules for obvious dates, medication strings, seizure-frequency phrases, and investigation mentions | What is the reproducible floor? |
| 1 | `exect_v2_external_baseline` | Run public ExECTv2 GATE application where technically and legally feasible | How does a published epilepsy NLP system perform on shared synthetic letters? |
| 2 | `exect_lite_cleanroom_baseline` | Locally implemented rules based on published field definitions, not copied JAPE/gazetteers | What can transparent epilepsy rules achieve? |
| 3 | `direct_full_contract` | One LLM call emits the full schema | How strong is direct prompting? |
| 4 | `direct_evidence_contract` | Direct prompt with stricter evidence and abstention requirements | Does the evidence contract alone help? |
| 5 | `retrieval_field_extractors` | Candidate span retrieval plus field-specific extraction | Does local-context extraction improve value/evidence quality? |
| 6 | `clines_epilepsy_modular` | Chunking, extraction, status/temporality, normalization, evidence grading, aggregation | Does clinical modularization help? |
| 7 | `clines_epilepsy_verified` | Modular pipeline with explicit verifier and downgrade policy | Does verification improve supported outputs? |
| 8 | `costed_reliability_variants` | Self-consistency, stronger verifier, or model escalation | What reliability gains justify extra cost? |

## Model-Family Matrix

Model names change quickly, so the proposal should commit to families and tiers,
then freeze exact snapshots shortly before experiments.

| Tier | Open model families | Closed model families | Purpose |
| --- | --- | --- | --- |
| Small / cheap | Phi, Gemma, Qwen, Llama, DeepSeek small/flash variants | GPT mini/nano class, Claude Haiku/Sonnet-small class | Low-cost and privacy-conscious extraction |
| Medium | Qwen, Llama, Gemma, DeepSeek mid/pro variants | GPT mid-tier, Claude Sonnet class | Practical quality/cost tradeoff |
| Large / frontier | Qwen MoE/large, Llama large, Gemma large, DeepSeek Pro | GPT frontier, Claude Opus class | Upper-bound performance and architecture sensitivity |

Exact model IDs, release dates, pricing, context windows, backends,
quantization, and decoding settings belong in the model registry.

## Formal Proposal Claim

The proposal should claim:

> This dissertation evaluates a CLINES-inspired modular LLM harness for
> epilepsy clinic-letter extraction, benchmarking it against clinical
> NLP-style baselines and direct LLM prompting across contemporary open and
> closed model families. The study measures not only extraction correctness,
> but evidence support, temporality, normalization, schema validity, cost,
> latency, token use, and harness complexity.

## Boundaries

- Do not call the modular pipeline a CLINES replication unless the CLINES code,
  prompts, annotations, and evaluation scripts are public and actually used.
- Do not import ExECTv2 source logic into this repo unless licensing is
  clarified.
- Do not treat synthetic-only results as clinical deployment evidence.
- Do not let frontier-model sensitivity runs become the main evidence spine.
- Do not collapse all fields into a single aggregate score.
