# Research Question And Claims

## Primary Question

For structured epilepsy clinic-letter extraction, how do CLINES-inspired
modular architecture, clinical extraction baselines, and model capacity affect
clinical correctness, evidence support, auditability, cost, latency, token use,
and harness complexity?

## Study Position

The dissertation should no longer be framed as a simple test of whether
multi-agent extraction beats a single prompt. The literature suggests a wider
and more useful design space. Direct prompting can be strong, rule-based
epilepsy NLP systems such as ExECT are serious comparators, and modular
clinical pipelines such as CLINES suggest that chunking, normalization,
assertion/status handling, temporality, evidence grounding, and aggregation may
matter as much as the base model.

The project therefore evaluates architecture as an empirical variable. A
CLINES-inspired modular pipeline is the main proposed architecture, but its
components should be tested through ablations and compared against direct LLM
prompting and clinical NLP-style baselines.

## Extraction Target

The system reads an epilepsy clinic letter and extracts structured fields for:

- seizure frequency and seizure freedom;
- current anti-seizure medications;
- investigations and investigation results;
- seizure types, semiology features, and pattern modifiers;
- epilepsy type and epilepsy syndrome;
- evidence spans, confidence, warnings, and citations.

The target is structured, evidence-grounded clinical extraction. It is not
free-text summarisation.

## Hypotheses

### H1: Modular Clinical Architecture May Improve Evidence-Supported Extraction

A CLINES-inspired architecture may improve evidence support, status handling,
temporality, normalization, and auditability compared with direct prompting.
This is a hypothesis, not a premise.

### H2: Architecture Components Have Uneven Value

Chunking, candidate-span retrieval, field-specific extraction, assertion/status
classification, temporality resolution, evidence verification, and aggregation
should be evaluated as separable interventions. Some modules may improve one
field family while harming another through information loss or additional error
propagation.

### H3: Strong Direct Prompting Is A Necessary Comparator

Direct full-letter prompting may remain competitive, especially for shorter
letters and fields with simple surface forms. The direct baseline must use the
same final schema, evidence requirements, decoding controls, parse validation,
and adjudication rubric as modular pipelines.

### H4: Clinical NLP Baselines Establish The Real Floor

The alternative to LLM extraction is not "no system." ExECTv2, ExECT-inspired
clean-room rules, deterministic medication/date/frequency extractors, and
possibly machine-reading seizure-frequency baselines should be used to show
where LLMs genuinely add value and where conventional clinical NLP remains
competitive.

### H5: Model Capacity And Harness Complexity Trade Off

Larger or closed frontier models may reduce the need for complex harnesses,
while smaller open models may become competitive when supported by retrieval,
verification, and stricter schemas. Cost, token use, latency, parse stability,
and harness complexity are therefore outcomes, not footnotes.

### H6: Field Difficulty Is Uneven

Medication and investigation extraction may be less architecture-sensitive than
seizure-frequency temporality or seizure-type normalization. Results should be
reported by field family rather than only in aggregate.

## Core Comparisons

| Comparison | Purpose |
| --- | --- |
| Deterministic and ExECT-style baselines vs LLM systems | Establish reproducible clinical NLP floors. |
| Full-contract direct prompt vs evidence-required direct prompt | Tests whether an evidence contract alone changes output quality. |
| Direct prompt vs retrieval-plus-field extraction | Tests candidate-span selection and local-context extraction. |
| Direct prompt vs CLINES-inspired modular pipeline | Tests the full clinical modular architecture. |
| Modular pipeline with and without verifier | Tests whether explicit evidence/status verification adds value. |
| Architecture ladder across model families and sizes | Tests whether harness complexity or model capacity drives performance. |
| Self-consistency variants | Measures costed reliability gains, if budget allows. |

## Claims This Repo Should Support

- CLINES-inspired modularization did or did not improve field-level correctness,
  evidence support, status handling, temporality, or normalization compared with
  strong direct prompting.
- Specific architecture components helped, harmed, or had no measurable effect.
- ExECTv2 or ExECT-inspired baselines remain competitive for some structured
  epilepsy fields.
- Evidence support must be clinically adjudicated; evidence presence alone is
  insufficient.
- Reliability varies by clinical field family.
- Model family, model scale, cost, latency, token use, and harness complexity
  jointly influence the best practical system.
- Synthetic-only or closed-model sensitivity results are bounded evidence and
  do not prove clinical deployment readiness.

## Claims To Avoid

- Multi-agent or modular systems are categorically better than direct prompts.
- A stronger model makes architecture irrelevant.
- Schema-valid JSON implies clinical correctness.
- A quoted span automatically supports the extracted value.
- Synthetic-only frontier-model results prove real-clinical deployment
  readiness.
- A CLINES-inspired implementation is a direct CLINES replication unless the
  original code, prompts, and evaluation scripts are public and used.
- Visibility tooling is the dissertation contribution.

## Success Criteria

Another researcher should be able to:

1. run deterministic and ExECT-style clinical NLP baselines;
2. run fixed-slice direct-prompt LLM baselines;
3. run fixed-slice CLINES-inspired modular pipelines and ablations;
4. inspect intermediate artifacts for chunking, candidate spans, field outputs,
   verification, normalization, and aggregation;
5. evaluate outputs under the shared field contract;
6. adjudicate matched subsets using the clinical rubric;
7. compare model families and size tiers under frozen model registry entries;
8. reproduce result tables for correctness, evidence support, budget, latency,
   token use, and harness complexity;
9. understand which claims are supported, uncertain, or out of scope.
