from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Iterable

from epilepsy_extraction.assets import load_prompt, load_schema
from epilepsy_extraction.evaluation import parse_label, parse_validity_summary
from epilepsy_extraction.providers import (
    ChatProvider,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    budget_from_provider_responses,
)
from epilepsy_extraction.schemas import (
    CORE_FIELD_FAMILIES,
    DatasetSlice,
    ExtractionPayload,
    FinalExtraction,
    GoldRecord,
    RunRecord,
    event_dicts,
    failed_component_coverage,
    field_coverage,
    harness_event,
    summarize_harness_events,
    validate_final_payload_keys,
)
from epilepsy_extraction.schemas.contracts import ArchitectureFamily, FieldFamily


FIELD_TO_FINAL_KEYS = {
    FieldFamily.SEIZURE_FREQUENCY: ("seizure_frequency",),
    FieldFamily.CURRENT_MEDICATIONS: ("current_medications",),
    FieldFamily.INVESTIGATIONS: ("investigations",),
    FieldFamily.SEIZURE_CLASSIFICATION: (
        "seizure_types",
        "seizure_features",
        "seizure_pattern_modifiers",
    ),
    FieldFamily.EPILEPSY_CLASSIFICATION: ("epilepsy_type", "epilepsy_syndrome"),
}


def run_direct_full_contract(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    provider: ChatProvider,
    *,
    model: str = "mock-model",
    temperature: float = 0.0,
) -> RunRecord:
    prompt = load_prompt("full_contract_single")
    schema = load_schema("final_extraction")
    record_list = list(records)
    rows: list[dict[str, Any]] = []
    responses: list[ProviderResponse] = []
    parse_results: list[tuple[str, bool]] = []
    run_coverage = field_coverage(implemented=CORE_FIELD_FAMILIES)
    events = []

    for record in record_list:
        row_events = [
            harness_event(
                "context_built",
                record.row_id,
                1,
                component="full_contract_prompt",
                summary="Full letter and final schema assembled for direct extraction",
            ),
            harness_event(
                "provider_call_started",
                record.row_id,
                2,
                component="direct_full_contract",
                summary="Provider call requested final extraction payload",
            ),
        ]
        response = _call_provider(provider, prompt.content, schema.content, record.letter, model, temperature)
        row_events.append(
            harness_event(
                "provider_call_finished",
                record.row_id,
                3,
                component="direct_full_contract",
                summary="Provider call completed",
                metrics={
                    "ok": response.ok,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "latency_ms": response.latency_ms,
                },
                error=response.error.type if response.error else "",
            )
        )
        responses.append(response)
        payload, component_validity = _payload_from_response(response, record)
        row_events.append(
            harness_event(
                "parse_attempted",
                record.row_id,
                4,
                component="final_output",
                summary="Provider JSON parsed into final extraction payload",
                metrics={"valid": not payload.invalid_output},
                warnings=payload.warnings,
            )
        )
        parse_results.extend(component_validity)
        if payload.invalid_output:
            run_coverage = failed_component_coverage(CORE_FIELD_FAMILIES)
            row_events.append(
                harness_event(
                    "warning_emitted",
                    record.row_id,
                    5,
                    component="final_output",
                    summary="Direct full-contract payload was invalid or incomplete",
                    warnings=payload.warnings,
                )
            )
        events.extend(row_events)
        rows.append(
            {
                "row_id": record.row_id,
                "source_row_index": record.source_row_index,
                "payload": payload.to_dict(),
                "provider_response": asdict(response),
                "harness_events": event_dicts(row_events),
            }
        )

    return RunRecord(
        run_id=run_id,
        harness="direct_full_contract",
        schema_version=schema.version,
        dataset=dataset,
        model=model,
        provider=provider.provider_name,
        temperature=temperature,
        prompt_version=prompt.version,
        code_version=code_version,
        budget=budget_from_provider_responses(responses, rows=len(record_list)),
        field_coverage=run_coverage,
        rows=rows,
        parse_validity=parse_validity_summary(parse_results),
        artifact_paths={"prompt": prompt.path, "schema": schema.path},
        architecture_family=ArchitectureFamily.DIRECT_LLM.value,
        harness_events=event_dicts(events),
        event_summary=summarize_harness_events(events),
    )


def run_single_prompt_full_contract(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    provider: ChatProvider,
    *,
    model: str = "mock-model",
    temperature: float = 0.0,
) -> RunRecord:
    return run_direct_full_contract(
        records,
        dataset,
        run_id,
        code_version,
        provider,
        model=model,
        temperature=temperature,
    )


def _call_provider(
    provider: ChatProvider,
    prompt: str,
    schema: dict[str, Any],
    letter: str,
    model: str,
    temperature: float,
) -> ProviderResponse:
    return provider.complete(
        ProviderRequest(
            messages=[
                ProviderMessage(
                    role="user",
                    content=f"{prompt}\n\nFinal schema:\n{json.dumps(schema, sort_keys=True)}\n\nClinic letter:\n{letter}",
                )
            ],
            model=model,
            temperature=temperature,
            response_format="json",
            metadata={
                "prompt_id": "full_contract_single",
                "schema_id": "final_extraction",
            },
        )
    )


def _payload_from_response(
    response: ProviderResponse,
    record: GoldRecord,
) -> tuple[ExtractionPayload, list[tuple[str, bool]]]:
    warnings: list[str] = []
    if not response.ok:
        warnings.append("provider_error")
        return _invalid_payload(record, warnings), _failed_validity()

    try:
        decoded = json.loads(response.content)
    except json.JSONDecodeError:
        warnings.append("invalid_json")
        return _invalid_payload(record, warnings), _failed_validity()

    final_data = decoded.get("final", decoded)
    try:
        validate_final_payload_keys(final_data)
    except (TypeError, ValueError) as exc:
        warnings.append(str(exc))
        return _invalid_payload(record, warnings, raw=decoded), _failed_validity()

    final = FinalExtraction(**{key: final_data[key] for key in FinalExtraction().to_dict()})
    component_validity = _component_validity(final)
    invalid_output = not all(valid for _, valid in component_validity)
    payload_warnings = [str(warning) for warning in final.warnings] + warnings
    return (
        ExtractionPayload(
            pipeline_id="direct_full_contract",
            final=final,
            field_coverage=field_coverage(implemented=CORE_FIELD_FAMILIES),
            artifacts={"raw_provider": decoded},
            invalid_output=invalid_output,
            warnings=payload_warnings,
            metadata={"source_row_index": record.source_row_index},
        ),
        component_validity,
    )


def _invalid_payload(
    record: GoldRecord,
    warnings: list[str],
    raw: dict[str, Any] | None = None,
) -> ExtractionPayload:
    return ExtractionPayload(
        pipeline_id="direct_full_contract",
        final=FinalExtraction(warnings=warnings),
        field_coverage=failed_component_coverage(CORE_FIELD_FAMILIES),
        artifacts={"raw_provider": raw} if raw is not None else {},
        invalid_output=True,
        warnings=warnings,
        metadata={"source_row_index": record.source_row_index},
    )


def _component_validity(final: FinalExtraction) -> list[tuple[str, bool]]:
    validity = [("final_output", True)]
    for field_family in FIELD_TO_FINAL_KEYS:
        if field_family == FieldFamily.SEIZURE_FREQUENCY:
            if not isinstance(final.seizure_frequency, dict):
                validity.append((field_family.value, False))
            else:
                value = final.seizure_frequency.get("value") or final.seizure_frequency.get("label")
                validity.append((field_family.value, bool(value and parse_label(str(value)).monthly_rate is not None)))
        elif field_family == FieldFamily.CURRENT_MEDICATIONS:
            validity.append((field_family.value, isinstance(final.current_medications, list)))
        elif field_family == FieldFamily.INVESTIGATIONS:
            validity.append((field_family.value, isinstance(final.investigations, list)))
        elif field_family == FieldFamily.SEIZURE_CLASSIFICATION:
            validity.append(
                (
                    field_family.value,
                    all(
                        isinstance(value, list)
                        for value in (
                            final.seizure_types,
                            final.seizure_features,
                            final.seizure_pattern_modifiers,
                        )
                    ),
                )
            )
        elif field_family == FieldFamily.EPILEPSY_CLASSIFICATION:
            validity.append(
                (
                    field_family.value,
                    all(
                        value is None or isinstance(value, dict)
                        for value in (final.epilepsy_type, final.epilepsy_syndrome)
                    ),
                )
            )
    return validity


def _failed_validity() -> list[tuple[str, bool]]:
    return [("final_output", False)] + [(field.value, False) for field in CORE_FIELD_FAMILIES]
