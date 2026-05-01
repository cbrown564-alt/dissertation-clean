# Research Question And Claims

## Primary Question

Can a training-free, role-separated multi-agent extraction system improve the
reliability, auditability, and evidence support of structured epilepsy-letter
extraction compared with a single-prompt extractor under controlled budget
constraints?

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

### H1: Role Separation Improves Auditability

A role-separated pipeline should make extraction decisions easier to inspect
because intermediate artifacts expose candidate spans, field-specific outputs,
verification decisions, aggregation warnings, confidence, and citation metadata.
This may hold even when aggregate accuracy is similar.

### H2: Role Separation May Improve Reliability, But Not Automatically

Multi-agent decomposition is a testable intervention, not an assumed win. The
clean repo should report where role separation helps, where it is parity, and
where it harms performance.

### H3: Evidence Requirements Help Only When Support Is Scored

Evidence strings alone are insufficient. Evidence must support the extracted
value, clinical status, temporality, and normalization.

### H4: Self-Consistency Is A Costed Reliability Intervention

Self-consistency should be reported as a budget/reliability tradeoff, not as a
free improvement.

### H5: Field Difficulty Is Uneven

Medication and investigation extraction may be more reliable than seizure-type
normalization or seizure-frequency temporality. Results should be reported by
field family rather than only in aggregate.

## Core Comparisons

| Comparison | Purpose |
| --- | --- |
| Full-contract single prompt vs full-contract role-separated pipeline | Main test of the research question. |
| Role-separated pipeline with and without strong verification | Tests whether verification adds reliability beyond architecture. |
| Deterministic baseline vs LLM extractors | Establishes a reproducible floor. |
| Self-consistency k=3/k=5 vs one-pass extraction | Measures costed reliability gain. |
| Local model vs frontier model on synthetic-only data | Sensitivity analysis, not deployment evidence. |

## Claims This Repo Should Support

- Under matched or explicitly costed budget, role separation did or did not
  improve field-level correctness compared with single-prompt extraction.
- Role separation improved auditability by exposing candidate spans,
  verification warnings, and confidence/citation metadata.
- Evidence support must be clinically adjudicated; evidence presence alone is
  insufficient.
- Reliability varies by clinical field family.
- Self-consistency improves some metrics only at explicit cost.
- The system remains training-free and synthetic-data-safe unless governed
  real-data access is separately approved.

## Claims To Avoid

- Multi-agent systems are categorically better than single prompts.
- Schema-valid JSON implies clinical correctness.
- A quoted span automatically supports the extracted value.
- Synthetic-only frontier-model results prove real-clinical deployment
  readiness.
- Visibility tooling is the dissertation contribution.

## Success Criteria

Another researcher should be able to:

1. run a fixed-slice single-prompt baseline;
2. run a fixed-slice role-separated multi-agent pipeline;
3. inspect intermediate role artifacts;
4. evaluate outputs under the field contract;
5. adjudicate a matched subset using the clinical rubric;
6. reproduce result tables and visibility cockpit summaries;
7. understand which claims are supported, uncertain, or out of scope.
