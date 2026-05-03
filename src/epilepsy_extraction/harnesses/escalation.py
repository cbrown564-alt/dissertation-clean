from __future__ import annotations

from typing import Iterable

from epilepsy_extraction.harnesses.direct_evidence_contract import run_direct_evidence_contract
from epilepsy_extraction.harnesses.retrieval_field_extractors import run_retrieval_field_extractors
from epilepsy_extraction.providers import ChatProvider
from epilepsy_extraction.schemas import (
    BudgetMetadata,
    DatasetSlice,
    GoldRecord,
    RunRecord,
    event_dicts,
    harness_event,
    summarize_harness_events,
)
from epilepsy_extraction.schemas.contracts import ArchitectureFamily


def run_budgeted_escalation_harness(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    cheap_provider: ChatProvider,
    strong_provider: ChatProvider,
    *,
    cheap_model: str = "mock-cheap",
    strong_model: str = "mock-strong",
    temperature: float = 0.0,
) -> RunRecord:
    """Costed reliability variant: retrieval first, direct evidence on ambiguity.

    This is intentionally a separate harness, not a replacement for the
    canonical direct, retrieval, or modular baselines.
    """
    record_list = list(records)
    cheap = run_retrieval_field_extractors(
        record_list,
        dataset,
        f"{run_id}_cheap_retrieval",
        code_version,
        cheap_provider,
        model=cheap_model,
        temperature=temperature,
    )
    should_escalate, reasons = _should_escalate(cheap)
    events = [
        harness_event(
            "escalation_decision",
            "run",
            1,
            component="budgeted_escalation_policy",
            summary="Escalation policy evaluated retrieval output",
            metrics={"escalated": should_escalate, "reasons": reasons},
            warnings=reasons,
        )
    ]

    if should_escalate:
        strong = run_direct_evidence_contract(
            record_list,
            dataset,
            f"{run_id}_strong_direct_evidence",
            code_version,
            strong_provider,
            model=strong_model,
            temperature=temperature,
        )
        budget = _sum_budgets(cheap.budget, strong.budget)
        rows = strong.rows
        field_coverage = strong.field_coverage
        parse_validity = strong.parse_validity
        metrics = strong.metrics
        artifact_paths = {
            "cheap_retrieval": cheap.run_id,
            "strong_direct_evidence": strong.run_id,
            **strong.artifact_paths,
        }
        model = f"{cheap_model}->{strong_model}"
        provider = f"{cheap.provider}->{strong.provider}"
    else:
        budget = cheap.budget
        rows = cheap.rows
        field_coverage = cheap.field_coverage
        parse_validity = cheap.parse_validity
        metrics = cheap.metrics
        artifact_paths = {"cheap_retrieval": cheap.run_id, **cheap.artifact_paths}
        model = cheap_model
        provider = cheap.provider

    all_events = events + _events_from_run(cheap)
    if should_escalate:
        all_events.extend(_events_from_run(strong))

    return RunRecord(
        run_id=run_id,
        harness="budgeted_escalation",
        schema_version=cheap.schema_version,
        dataset=dataset,
        model=model,
        provider=provider,
        temperature=temperature,
        prompt_version="retrieval_then_direct_evidence_v1",
        code_version=code_version,
        budget=budget,
        field_coverage=field_coverage,
        metrics=metrics,
        rows=rows,
        parse_validity=parse_validity,
        warnings=[f"escalation_reason:{reason}" for reason in reasons],
        artifact_paths=artifact_paths,
        architecture_family=ArchitectureFamily.COSTED_RELIABILITY_VARIANT.value,
        complexity={
            "modules": ["cheap_retrieval", "escalation_policy", "strong_direct_evidence"],
            "escalation_policy": {
                "escalate_on": ["parse_failure", "warning", "low_confidence"],
                "escalated": should_escalate,
                "reasons": reasons,
            },
        },
        harness_events=event_dicts(all_events),
        event_summary=summarize_harness_events(all_events),
    )


def _should_escalate(record: RunRecord) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if any(stats.get("valid_rate", 1.0) < 1.0 for stats in record.parse_validity.values()):
        reasons.append("parse_failure")
    if record.warnings:
        reasons.append("warning")
    for row in record.rows:
        payload = row.get("payload", {}) if isinstance(row, dict) else {}
        final = payload.get("final", {}) if isinstance(payload, dict) else {}
        confidence = final.get("confidence", {}) if isinstance(final, dict) else {}
        if isinstance(confidence, dict) and any(float(value or 0.0) < 0.5 for value in confidence.values()):
            reasons.append("low_confidence")
            break
    return bool(reasons), sorted(set(reasons))


def _sum_budgets(left: BudgetMetadata, right: BudgetMetadata) -> BudgetMetadata:
    return BudgetMetadata(
        llm_calls_per_row=left.llm_calls_per_row + right.llm_calls_per_row,
        input_tokens=left.input_tokens + right.input_tokens,
        output_tokens=left.output_tokens + right.output_tokens,
        total_tokens=left.total_tokens + right.total_tokens,
        latency_ms=left.latency_ms + right.latency_ms,
        estimated_cost_usd=left.estimated_cost_usd + right.estimated_cost_usd,
    )


def _events_from_run(record: RunRecord):
    events = []
    for index, event in enumerate(record.harness_events, start=2):
        if not isinstance(event, dict):
            continue
        events.append(
            harness_event(
                str(event.get("event_type", "warning_emitted")),
                str(event.get("row_id", "")),
                index,
                component=str(event.get("component", "")),
                summary=str(event.get("summary", "")),
                metrics=dict(event.get("metrics", {})) if isinstance(event.get("metrics"), dict) else {},
                warnings=list(event.get("warnings", [])) if isinstance(event.get("warnings"), list) else [],
                error=str(event.get("error", "")),
            )
        )
    return events
