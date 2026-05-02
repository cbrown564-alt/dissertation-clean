"""ExECT-lite cleanroom baseline harness.

Independently-authored rule-based extraction using published field definitions
from the ExECT/ExECTv2 literature. Does not use or copy ExECTv2 source code.
Covers seizure frequency, medications, seizure type, and epilepsy type.
All other fields are marked not_attempted.
"""
from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any, Iterable

from epilepsy_extraction.assets import load_mapping
from epilepsy_extraction.evaluation import evaluate_prediction, parse_label, parse_validity_summary, summarize
from epilepsy_extraction.schemas import (
    BudgetMetadata,
    DatasetSlice,
    EvidenceSpan,
    ExtractionPayload,
    FinalExtraction,
    GoldRecord,
    Prediction,
    RunRecord,
)
from epilepsy_extraction.schemas.contracts import (
    ArchitectureFamily,
    FieldCoverageStatus,
    FieldFamily,
    not_attempted_coverage,
)


# ── seizure-frequency patterns ────────────────────────────────────────────────

_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "twenty": 20,
}
_NUM = r"(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|multiple|several|few)"
_UNIT = r"(?:day|days|week|weeks|month|months|year|years)"

_SEIZURE_FREE = re.compile(
    r"seizure[- ]free(?:\s+for\s+(?P<count>" + _NUM + r")\s+(?P<unit>" + _UNIT + r"))?",
    re.IGNORECASE,
)
_FREQ_OVER_PERIOD = re.compile(
    r"(?P<count>" + _NUM + r")\s+(?:seizures?|events?|absences?|episodes?)\s+"
    r"(?:over|in|during)\s+(?:the\s+)?(?:last\s+)?(?P<period>" + _NUM + r")\s+(?P<unit>" + _UNIT + r")",
    re.IGNORECASE,
)
_FREQ_PER_UNIT = re.compile(
    r"(?P<count>" + _NUM + r")\s+(?:seizures?|events?|absences?|episodes?)?\s*"
    r"(?:times?\s+)?per\s+(?P<unit>day|week|month|year)",
    re.IGNORECASE,
)
_CLUSTER = re.compile(
    r"(?P<clusters>" + _NUM + r")\s+cluster[- ]days?\s+(?:per\s+)?(?:this\s+)?month.*?"
    r"(?P<count>" + _NUM + r")\s+(?:seizures?|per\s+cluster)",
    re.IGNORECASE | re.DOTALL,
)

# ── medication patterns ────────────────────────────────────────────────────────

_COMMON_ASMS = (
    "lamotrigine", "levetiracetam", "valproate", "sodium valproate",
    "carbamazepine", "oxcarbazepine", "phenytoin", "topiramate",
    "lacosamide", "zonisamide", "pregabalin", "gabapentin",
    "clobazam", "clonazepam", "ethosuximide", "perampanel",
    "brivaracetam", "eslicarbazepine", "cenobamate", "fenfluramine",
    "vigabatrin", "stiripentol", "rufinamide", "clobazam",
)
_MED_PATTERN = re.compile(
    r"(?P<name>" + "|".join(re.escape(m) for m in _COMMON_ASMS) + r")"
    r"(?:\s+(?P<dose>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|mmol))?"
    r"(?:\s+(?P<frequency>once|twice|three\s+times?|(?:\d+\s+times?))\s+(?:a\s+)?(?:daily|day|week|weekly|night|nightly|bd|tds|qds))?",
    re.IGNORECASE,
)

# ── investigation patterns ─────────────────────────────────────────────────────

_INVESTIGATION_TYPES = {
    "EEG": re.compile(r"\bEEG\b", re.IGNORECASE),
    "MRI": re.compile(r"\bMRI\b(?:\s+brain)?", re.IGNORECASE),
    "CT": re.compile(r"\bCT\s+(?:brain|head|scan)\b", re.IGNORECASE),
    "ECG": re.compile(r"\bECG\b", re.IGNORECASE),
    "blood": re.compile(r"\b(?:blood\s+test|FBC|U&E|LFT|TFT|AED\s+levels?)\b", re.IGNORECASE),
}
_RESULT_WORDS = re.compile(
    r"\b(?:normal|abnormal|showed?|showing|reported|revealed|demonstrated|pending|awaiting|unremarkable)\b",
    re.IGNORECASE,
)

# ── seizure-type patterns ──────────────────────────────────────────────────────

_SEIZURE_TYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("tonic-clonic", re.compile(r"\b(?:tonic[- ]clonic|grand\s+mal|GTCS|GTC)\b", re.IGNORECASE)),
    ("focal", re.compile(r"\b(?:focal|partial|complex\s+partial|simple\s+partial)\b", re.IGNORECASE)),
    ("absence", re.compile(r"\b(?:absence|petit\s+mal)\b", re.IGNORECASE)),
    ("myoclonic", re.compile(r"\bmyoclonic?\b", re.IGNORECASE)),
    ("tonic", re.compile(r"\btonic\s+seizure\b", re.IGNORECASE)),
    ("atonic", re.compile(r"\b(?:atonic|drop\s+attack)\b", re.IGNORECASE)),
    ("clonic", re.compile(r"\bclonic\s+seizure\b", re.IGNORECASE)),
    ("spasm", re.compile(r"\b(?:infantile\s+spasms?|epileptic\s+spasms?)\b", re.IGNORECASE)),
]

# ── epilepsy-type patterns ─────────────────────────────────────────────────────

_EPILEPSY_TYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("focal epilepsy", re.compile(r"\bfocal\s+epilepsy\b", re.IGNORECASE)),
    ("generalised epilepsy", re.compile(r"\b(?:general(?:is|iz)ed|idiopathic\s+general(?:is|iz)ed)\s+epilepsy\b", re.IGNORECASE)),
    ("temporal lobe epilepsy", re.compile(r"\btemporal\s+lobe\s+epilepsy\b", re.IGNORECASE)),
    ("frontal lobe epilepsy", re.compile(r"\bfrontal\s+lobe\s+epilepsy\b", re.IGNORECASE)),
    ("juvenile myoclonic epilepsy", re.compile(r"\bjuvenile\s+myoclonic\s+epilepsy\b|\bJME\b", re.IGNORECASE)),
    ("childhood absence epilepsy", re.compile(r"\bchildhood\s+absence\s+epilepsy\b|\bCAE\b", re.IGNORECASE)),
    ("Dravet syndrome", re.compile(r"\bDravet\s+syndrome\b|\bSCN1A\s+(?:related\s+)?epilepsy\b", re.IGNORECASE)),
    ("Lennox-Gastaut syndrome", re.compile(r"\bLennox[- ]Gastaut\s+syndrome\b|\bLGS\b", re.IGNORECASE)),
    ("West syndrome", re.compile(r"\bWest\s+syndrome\b", re.IGNORECASE)),
]


def run_exect_lite_baseline(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
) -> RunRecord:
    rows: list[dict[str, Any]] = []
    evaluation_rows = []
    parse_results: list[tuple[str, bool]] = []
    mapping = load_mapping("exect_lite")

    for record in records:
        extracted = _extract_all(record.letter)
        freq_prediction = extracted["freq_prediction"]
        parsed_ok = freq_prediction.parsed_monthly_rate is not None
        parse_results.append(("seizure_frequency", parsed_ok))
        evaluation = evaluate_prediction(record.source_row_index, record.gold_label, freq_prediction)
        evaluation_rows.append(evaluation)

        coverage = _build_coverage(extracted)
        payload = ExtractionPayload(
            pipeline_id="exect_lite_cleanroom_baseline",
            final=FinalExtraction(
                seizure_frequency={
                    "value": freq_prediction.label,
                    "parsed_monthly_rate": freq_prediction.parsed_monthly_rate,
                    "pragmatic_class": freq_prediction.pragmatic_class,
                    "purist_class": freq_prediction.purist_class,
                },
                current_medications=extracted["medications"],
                investigations=extracted["investigations"],
                seizure_types=extracted["seizure_types"],
                epilepsy_type=extracted["epilepsy_type"],
                citations=[asdict(span) for span in freq_prediction.evidence],
                confidence={"seizure_frequency": freq_prediction.confidence},
                warnings=freq_prediction.warnings,
            ),
            field_coverage=coverage,
            invalid_output=not parsed_ok,
            warnings=freq_prediction.warnings,
            metadata={"source_row_index": record.source_row_index},
        )
        rows.append(
            {
                "row_id": record.row_id,
                "source_row_index": record.source_row_index,
                "prediction": asdict(freq_prediction),
                "payload": payload.to_dict(),
                "evaluation": asdict(evaluation),
            }
        )

    return RunRecord(
        run_id=run_id,
        harness="exect_lite_cleanroom_baseline",
        schema_version="1.0.0",
        dataset=dataset,
        model="none",
        provider="deterministic",
        temperature=0.0,
        prompt_version="exect_lite_rules_v1",
        code_version=code_version,
        budget=BudgetMetadata(),
        field_coverage=_run_level_coverage(),
        metrics=summarize(evaluation_rows),
        rows=rows,
        parse_validity=parse_validity_summary(parse_results),
        warnings=["exect_lite_cleanroom_independently_authored"],
        architecture_family=ArchitectureFamily.CLINICAL_NLP_BASELINE.value,
        mapping_version=mapping.version,
    )


# ── extraction helpers ─────────────────────────────────────────────────────────

def _extract_all(letter: str) -> dict[str, Any]:
    freq_prediction = _extract_seizure_frequency(letter)
    return {
        "freq_prediction": freq_prediction,
        "medications": _extract_medications(letter),
        "investigations": _extract_investigations(letter),
        "seizure_types": _extract_seizure_types(letter),
        "epilepsy_type": _extract_epilepsy_type(letter),
    }


def _extract_seizure_frequency(letter: str) -> Prediction:
    # seizure-free check (highest priority)
    m = _SEIZURE_FREE.search(letter)
    if m:
        count_str = m.group("count")
        unit_str = m.group("unit")
        if count_str and unit_str:
            count = _parse_number(count_str)
            unit = _singular(unit_str)
            label = f"seizure free for {count:g} {unit}"
        else:
            label = "seizure free"
        return _make_freq_prediction(label, m.group(0), 0.7)

    # count over period
    m = _FREQ_OVER_PERIOD.search(letter)
    if m:
        count = _parse_number(m.group("count"))
        period = _parse_number(m.group("period"))
        unit = _singular(m.group("unit"))
        label = f"{count:g} per {period:g} {unit}" if period != 1 else f"{count:g} per {unit}"
        return _make_freq_prediction(label, m.group(0), 0.65)

    # per-unit rate
    m = _FREQ_PER_UNIT.search(letter)
    if m:
        count = _parse_number(m.group("count"))
        unit = m.group("unit").lower()
        label = f"{count:g} per {unit}"
        return _make_freq_prediction(label, m.group(0), 0.65)

    # cluster pattern
    m = _CLUSTER.search(letter)
    if m:
        clusters = _parse_number(m.group("clusters"))
        count = _parse_number(m.group("count"))
        label = f"{clusters:g} cluster per month, {count:g} per cluster"
        return _make_freq_prediction(label, m.group(0), 0.6)

    return Prediction(
        label="unknown",
        confidence=0.0,
        parsed_monthly_rate=parse_label("unknown").monthly_rate,
        pragmatic_class="UNK",
        purist_class="UNK",
        warnings=["no_frequency_pattern_matched"],
    )


def _make_freq_prediction(label: str, evidence: str, confidence: float) -> Prediction:
    parsed = parse_label(label)
    return Prediction(
        label=label,
        evidence=[EvidenceSpan(quote=evidence)],
        confidence=confidence,
        parsed_monthly_rate=parsed.monthly_rate,
        pragmatic_class=parsed.pragmatic_class,
        purist_class=parsed.purist_class,
        warnings=[],
    )


def _extract_medications(letter: str) -> list[dict[str, Any]]:
    results = []
    seen: set[str] = set()
    for m in _MED_PATTERN.finditer(letter):
        name = m.group("name").lower()
        if name in seen:
            continue
        seen.add(name)
        med: dict[str, Any] = {
            "name": m.group("name"),
            "dose": m.group("dose"),
            "unit": m.group("unit"),
            "frequency": m.group("frequency"),
            "evidence": m.group(0).strip(),
        }
        results.append(med)
    return results


def _extract_investigations(letter: str) -> list[dict[str, Any]]:
    results = []
    for inv_type, pattern in _INVESTIGATION_TYPES.items():
        m = pattern.search(letter)
        if m:
            start = max(0, m.start() - 60)
            end = min(len(letter), m.end() + 80)
            context = letter[start:end]
            result_match = _RESULT_WORDS.search(context)
            results.append(
                {
                    "type": inv_type,
                    "result_word": result_match.group(0) if result_match else None,
                    "evidence": m.group(0).strip(),
                }
            )
    return results


def _extract_seizure_types(letter: str) -> list[dict[str, Any]]:
    results = []
    for label, pattern in _SEIZURE_TYPE_PATTERNS:
        m = pattern.search(letter)
        if m:
            results.append({"type": label, "evidence": m.group(0).strip()})
    return results


def _extract_epilepsy_type(letter: str) -> dict[str, Any] | None:
    for label, pattern in _EPILEPSY_TYPE_PATTERNS:
        m = pattern.search(letter)
        if m:
            return {"type": label, "evidence": m.group(0).strip()}
    return None


def _build_coverage(extracted: dict[str, Any]) -> dict[str, str]:
    coverage = not_attempted_coverage()
    coverage[FieldFamily.SEIZURE_FREQUENCY.value] = FieldCoverageStatus.IMPLEMENTED.value
    coverage[FieldFamily.CURRENT_MEDICATIONS.value] = (
        FieldCoverageStatus.PARTIAL.value if extracted["medications"]
        else FieldCoverageStatus.NOT_ATTEMPTED.value
    )
    coverage[FieldFamily.INVESTIGATIONS.value] = (
        FieldCoverageStatus.PARTIAL.value if extracted["investigations"]
        else FieldCoverageStatus.NOT_ATTEMPTED.value
    )
    coverage[FieldFamily.SEIZURE_CLASSIFICATION.value] = (
        FieldCoverageStatus.PARTIAL.value if extracted["seizure_types"]
        else FieldCoverageStatus.NOT_ATTEMPTED.value
    )
    coverage[FieldFamily.EPILEPSY_CLASSIFICATION.value] = (
        FieldCoverageStatus.PARTIAL.value if extracted["epilepsy_type"] is not None
        else FieldCoverageStatus.NOT_ATTEMPTED.value
    )
    return coverage


def _run_level_coverage() -> dict[str, str]:
    coverage = not_attempted_coverage()
    coverage[FieldFamily.SEIZURE_FREQUENCY.value] = FieldCoverageStatus.IMPLEMENTED.value
    coverage[FieldFamily.CURRENT_MEDICATIONS.value] = FieldCoverageStatus.PARTIAL.value
    coverage[FieldFamily.INVESTIGATIONS.value] = FieldCoverageStatus.PARTIAL.value
    coverage[FieldFamily.SEIZURE_CLASSIFICATION.value] = FieldCoverageStatus.PARTIAL.value
    coverage[FieldFamily.EPILEPSY_CLASSIFICATION.value] = FieldCoverageStatus.PARTIAL.value
    return coverage


def _parse_number(value: str) -> float:
    value = value.lower().strip()
    if value in {"multiple", "several"}:
        return 3.0
    if value == "few":
        return 2.0
    if value in _NUMBER_WORDS:
        return float(_NUMBER_WORDS[value])
    return float(value)


def _singular(unit: str) -> str:
    unit = unit.lower()
    return unit.rstrip("s") if unit.endswith("s") and len(unit) > 3 else unit
