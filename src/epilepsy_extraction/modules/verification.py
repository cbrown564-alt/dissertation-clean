from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from epilepsy_extraction.schemas.contracts import EvidenceGrade


@dataclass(frozen=True)
class EvidenceVerificationResult:
    grade: EvidenceGrade
    matched_span: str | None = None
    notes: list[str] = field(default_factory=list)


def verify_evidence_deterministic(
    claimed_value: str,
    evidence_quote: str | None,
    context: str,
) -> EvidenceVerificationResult:
    """Check whether the evidence_quote appears in context, grading the match quality."""
    if not evidence_quote:
        return EvidenceVerificationResult(
            grade=EvidenceGrade.MISSING_EVIDENCE,
            notes=["no_evidence_quote"],
        )
    if evidence_quote.lower() in context.lower():
        return EvidenceVerificationResult(
            grade=EvidenceGrade.EXACT_SPAN,
            matched_span=evidence_quote,
        )
    words = set(re.findall(r"\w+", evidence_quote.lower()))
    context_words = set(re.findall(r"\w+", context.lower()))
    overlap = words & context_words
    if words and len(overlap) / len(words) >= 0.6:
        return EvidenceVerificationResult(
            grade=EvidenceGrade.OVERLAPPING_SPAN,
            matched_span=evidence_quote,
            notes=["fuzzy_match"],
        )
    if claimed_value and claimed_value.lower() in context.lower():
        return EvidenceVerificationResult(
            grade=EvidenceGrade.SECTION_LEVEL,
            notes=["value_found_but_quote_not_matched"],
        )
    return EvidenceVerificationResult(
        grade=EvidenceGrade.UNSUPPORTED,
        notes=["evidence_not_found_in_context"],
    )


def verify_field_extraction(
    field_data: dict[str, Any],
    context: str,
) -> tuple[dict[str, Any], list[EvidenceVerificationResult]]:
    """Verify citation evidence for a field extraction result.

    Returns (artifact_dict, results) where artifact_dict records grades per
    citation. The original field_data is not mutated.
    """
    citations = field_data.get("citations", [])
    if not citations:
        return {"grade": EvidenceGrade.MISSING_EVIDENCE.value, "citations_checked": 0}, []

    results: list[EvidenceVerificationResult] = []
    annotated: list[dict[str, Any]] = []
    for citation in citations:
        quote = citation.get("quote") if isinstance(citation, dict) else str(citation)
        value_candidates = [str(v) for v in field_data.values() if isinstance(v, (str, int, float))]
        claimed = value_candidates[0] if value_candidates else ""
        result = verify_evidence_deterministic(claimed, quote, context)
        results.append(result)
        entry: dict[str, Any] = {"quote": quote, "grade": result.grade.value}
        if result.notes:
            entry["notes"] = result.notes
        annotated.append(entry)

    grades = [r.grade for r in results]
    grade_order = list(EvidenceGrade)
    best_grade = min(grades, key=lambda g: grade_order.index(g))
    return {
        "grade": best_grade.value,
        "citations_checked": len(results),
        "citation_grades": annotated,
    }, results
