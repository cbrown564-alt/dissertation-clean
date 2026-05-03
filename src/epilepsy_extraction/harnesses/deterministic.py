from __future__ import annotations

import re
from dataclasses import asdict
from typing import Iterable

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
    event_dicts,
    field_coverage,
    harness_event,
    summarize_harness_events,
)
from epilepsy_extraction.schemas.contracts import FieldFamily


NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twelve": 12,
}

NUMBER = r"multiple|\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|twelve"


def run_deterministic_baseline(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
) -> RunRecord:
    rows: list[dict[str, object]] = []
    evaluation_rows = []
    parse_results: list[tuple[str, bool]] = []
    events = []

    for record in records:
        row_events = [
            harness_event(
                "context_built",
                record.row_id,
                1,
                component="deterministic_rules",
                summary="Full letter made available to deterministic rules",
            )
        ]
        prediction = predict_seizure_frequency(record.letter)
        parsed_ok = prediction.parsed_monthly_rate is not None
        parse_results.append(("seizure_frequency", parsed_ok))
        row_events.append(
            harness_event(
                "parse_attempted",
                record.row_id,
                2,
                component="seizure_frequency",
                summary="Rule output parsed as seizure-frequency label",
                metrics={"valid": parsed_ok},
                warnings=prediction.warnings,
            )
        )
        row_events.append(
            harness_event(
                "field_extraction_completed",
                record.row_id,
                3,
                component="seizure_frequency",
                summary="Deterministic seizure-frequency extraction completed",
                metrics={"valid": parsed_ok, "confidence": prediction.confidence},
                warnings=prediction.warnings,
            )
        )
        if prediction.warnings:
            row_events.append(
                harness_event(
                    "warning_emitted",
                    record.row_id,
                    4,
                    component="seizure_frequency",
                    summary="Deterministic extraction emitted warnings",
                    warnings=prediction.warnings,
                )
            )
        events.extend(row_events)
        evaluation = evaluate_prediction(record.source_row_index, record.gold_label, prediction)
        evaluation_rows.append(evaluation)

        payload = ExtractionPayload(
            pipeline_id="deterministic_baseline",
            final=FinalExtraction(
                seizure_frequency={
                    "value": prediction.label,
                    "parsed_monthly_rate": prediction.parsed_monthly_rate,
                    "pragmatic_class": prediction.pragmatic_class,
                    "purist_class": prediction.purist_class,
                },
                citations=[asdict(span) for span in prediction.evidence],
                confidence={"seizure_frequency": prediction.confidence},
                warnings=prediction.warnings,
            ),
            field_coverage=field_coverage(implemented=[FieldFamily.SEIZURE_FREQUENCY]),
            invalid_output=not parsed_ok,
            warnings=prediction.warnings,
            metadata={"source_row_index": record.source_row_index},
        )
        rows.append(
            {
                "row_id": record.row_id,
                "source_row_index": record.source_row_index,
                "prediction": asdict(prediction),
                "payload": payload.to_dict(),
                "evaluation": asdict(evaluation),
                "harness_events": event_dicts(row_events),
            }
        )

    return RunRecord(
        run_id=run_id,
        harness="deterministic_baseline",
        schema_version="1.0.0",
        dataset=dataset,
        model="none",
        provider="deterministic",
        temperature=0.0,
        prompt_version="rules_v1",
        code_version=code_version,
        budget=BudgetMetadata(),
        field_coverage=field_coverage(implemented=[FieldFamily.SEIZURE_FREQUENCY]),
        metrics=summarize(evaluation_rows),
        rows=rows,
        parse_validity=parse_validity_summary(parse_results),
        warnings=["deterministic_rules_use_letter_text_only"],
        harness_events=event_dicts(events),
        event_summary=summarize_harness_events(events),
    )


def predict_seizure_frequency(letter: str) -> Prediction:
    candidates = list(_candidate_predictions(letter))
    if not candidates:
        return _prediction("unknown", letter[:120], 0.0, ["no_deterministic_frequency_match"])

    candidates.sort(key=lambda item: item[0], reverse=True)
    _, label, evidence = candidates[0]
    return _prediction(label, evidence, 0.6, [])


def _candidate_predictions(letter: str) -> Iterable[tuple[float, str, str]]:
    for match in re.finditer(
        rf"seizure[- ]free for (?P<count>{NUMBER}) (?P<unit>month|months|year|years)",
        letter,
        flags=re.IGNORECASE,
    ):
        count = _number(match.group("count"))
        unit = _singular(match.group("unit"))
        yield 0.0, f"seizure free for {count:g} {unit}", match.group(0)

    for match in re.finditer(
        rf"cluster days (?P<clusters>{NUMBER}) this month; typically (?P<count>{NUMBER}) seizures",
        letter,
        flags=re.IGNORECASE,
    ):
        clusters = _number(match.group("clusters"))
        count = _number(match.group("count"))
        label = f"{clusters:g} cluster per month, {count:g} per cluster"
        yield _monthly_rate(label), label, match.group(0)

    for match in re.finditer(
        rf"(?P<count>{NUMBER}) (?:seizures?|events?|absences?) (?:over|in|during) (?:the )?(?:last )?(?P<period>{NUMBER}) (?P<unit>month|months|year|years)",
        letter,
        flags=re.IGNORECASE,
    ):
        count = _number(match.group("count"))
        period = _number(match.group("period"))
        unit = _singular(match.group("unit"))
        label = f"{count:g} per {period:g} {unit}"
        yield _monthly_rate(label), label, match.group(0)

    for match in re.finditer(
        rf"(?P<count>{NUMBER}) (?:seizures?|events?|absences?)? ?(?:times )?per (?P<unit>day|week|month|year)",
        letter,
        flags=re.IGNORECASE,
    ):
        count = _number(match.group("count"))
        unit = _singular(match.group("unit"))
        label = f"{count:g} per {unit}"
        yield _monthly_rate(label), label, match.group(0)


def _prediction(label: str, evidence: str, confidence: float, warnings: list[str]) -> Prediction:
    parsed = parse_label(label)
    return Prediction(
        label=label,
        evidence=[EvidenceSpan(quote=evidence)] if evidence else [],
        confidence=confidence,
        parsed_monthly_rate=parsed.monthly_rate,
        pragmatic_class=parsed.pragmatic_class,
        purist_class=parsed.purist_class,
        warnings=warnings,
    )


def _monthly_rate(label: str) -> float:
    return parse_label(label).monthly_rate or 0.0


def _number(value: str) -> float:
    value = value.lower()
    if value == "multiple":
        return 3.0
    if value in NUMBER_WORDS:
        return float(NUMBER_WORDS[value])
    return float(value)


def _singular(unit: str) -> str:
    return unit.lower().rstrip("s")
