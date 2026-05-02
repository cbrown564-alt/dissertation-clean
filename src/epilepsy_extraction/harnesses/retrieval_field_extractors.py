from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Iterable

from epilepsy_extraction.assets import load_prompt, load_schema
from epilepsy_extraction.evaluation import parse_validity_summary
from epilepsy_extraction.providers import (
    ChatProvider,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    budget_from_provider_responses,
)
from epilepsy_extraction.retrieval.candidates import build_retrieval_context
from epilepsy_extraction.schemas import (
    CORE_FIELD_FAMILIES,
    DatasetSlice,
    ExtractionPayload,
    FinalExtraction,
    GoldRecord,
    RunRecord,
    failed_component_coverage,
    field_coverage,
)
from epilepsy_extraction.schemas.contracts import ArchitectureFamily, FieldFamily


FIELD_FAMILY_KEYS: dict[FieldFamily, list[str]] = {
    FieldFamily.SEIZURE_FREQUENCY: ["seizure_frequency"],
    FieldFamily.CURRENT_MEDICATIONS: ["current_medications"],
    FieldFamily.INVESTIGATIONS: ["investigations"],
    FieldFamily.SEIZURE_CLASSIFICATION: ["seizure_types", "seizure_features", "seizure_pattern_modifiers"],
    FieldFamily.EPILEPSY_CLASSIFICATION: ["epilepsy_type", "epilepsy_syndrome"],
}


def run_retrieval_field_extractors(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    provider: ChatProvider,
    *,
    model: str = "mock-model",
    temperature: float = 0.0,
) -> RunRecord:
    prompt = load_prompt("retrieval_field_extractor")
    schema = load_schema("final_extraction")
    record_list = list(records)
    rows: list[dict[str, Any]] = []
    all_responses: list[ProviderResponse] = []
    parse_results: list[tuple[str, bool]] = []
    run_coverage = field_coverage(implemented=CORE_FIELD_FAMILIES)

    for record in record_list:
        row_responses: list[ProviderResponse] = []
        field_results: dict[FieldFamily, dict[str, Any]] = {}
        row_artifacts: dict[str, Any] = {}
        row_warnings: list[str] = []

        for family in CORE_FIELD_FAMILIES:
            context, span_artifacts, retrieval_warnings = build_retrieval_context(record.letter, family)
            row_warnings.extend(retrieval_warnings)
            row_artifacts[family.value] = {
                "candidate_spans": span_artifacts,
                "warnings": retrieval_warnings,
            }

            response = _call_provider(
                provider,
                prompt.content,
                schema.content,
                family,
                context,
                record.letter,
                model,
                temperature,
            )
            row_responses.append(response)

            field_data, validity = _parse_field_response(response, family)
            field_results[family] = field_data
            parse_results.extend(validity)

        final, any_invalid = _aggregate_fields(field_results)
        if any_invalid:
            run_coverage = failed_component_coverage(CORE_FIELD_FAMILIES)

        payload = ExtractionPayload(
            pipeline_id="retrieval_field_extractors",
            final=final,
            field_coverage=(
                field_coverage(implemented=CORE_FIELD_FAMILIES)
                if not any_invalid
                else failed_component_coverage(CORE_FIELD_FAMILIES)
            ),
            artifacts=row_artifacts,
            invalid_output=any_invalid,
            warnings=row_warnings,
            metadata={"source_row_index": record.source_row_index},
        )

        all_responses.extend(row_responses)
        rows.append(
            {
                "row_id": record.row_id,
                "source_row_index": record.source_row_index,
                "payload": payload.to_dict(),
                "retrieval_artifacts": row_artifacts,
                "provider_responses": [asdict(r) for r in row_responses],
            }
        )

    return RunRecord(
        run_id=run_id,
        harness="retrieval_field_extractors",
        schema_version=schema.version,
        dataset=dataset,
        model=model,
        provider=provider.provider_name,
        temperature=temperature,
        prompt_version=prompt.version,
        code_version=code_version,
        budget=budget_from_provider_responses(all_responses, rows=len(record_list)),
        field_coverage=run_coverage,
        rows=rows,
        parse_validity=parse_validity_summary(parse_results),
        artifact_paths={"prompt": prompt.path, "schema": schema.path},
        architecture_family=ArchitectureFamily.RETRIEVAL_FIELD_PIPELINE.value,
    )


def _call_provider(
    provider: ChatProvider,
    prompt_text: str,
    schema: dict[str, Any],
    family: FieldFamily,
    context: str,
    letter: str,
    model: str,
    temperature: float,
) -> ProviderResponse:
    keys = FIELD_FAMILY_KEYS[family]
    field_schema = {k: schema.get(k, {}) for k in keys}
    content = (
        f"{prompt_text}\n\n"
        f"Field family: {family.value}\n"
        f"Target fields: {', '.join(keys)}\n"
        f"Field schema: {json.dumps(field_schema, sort_keys=True)}\n\n"
        f"Retrieved context:\n{context}\n\n"
        f"Full clinic letter (for reference):\n{letter}"
    )
    return provider.complete(
        ProviderRequest(
            messages=[ProviderMessage(role="user", content=content)],
            model=model,
            temperature=temperature,
            response_format="json",
            metadata={"prompt_id": "retrieval_field_extractor", "field_family": family.value},
        )
    )


def _parse_field_response(
    response: ProviderResponse,
    family: FieldFamily,
) -> tuple[dict[str, Any], list[tuple[str, bool]]]:
    if not response.ok:
        return {}, [(family.value, False)]
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        return {}, [(family.value, False)]
    keys = FIELD_FAMILY_KEYS[family]
    parsed = {k: data[k] for k in keys if k in data}
    return parsed, [(family.value, bool(parsed))]


def _aggregate_fields(
    field_results: dict[FieldFamily, dict[str, Any]],
) -> tuple[FinalExtraction, bool]:
    merged: dict[str, Any] = {}
    any_invalid = False
    for family, data in field_results.items():
        if not data:
            any_invalid = True
        merged.update(data)

    return (
        FinalExtraction(
            seizure_frequency=merged.get("seizure_frequency", {}),
            current_medications=merged.get("current_medications", []),
            investigations=merged.get("investigations", []),
            seizure_types=merged.get("seizure_types", []),
            seizure_features=merged.get("seizure_features", []),
            seizure_pattern_modifiers=merged.get("seizure_pattern_modifiers", []),
            epilepsy_type=merged.get("epilepsy_type"),
            epilepsy_syndrome=merged.get("epilepsy_syndrome"),
            citations=merged.get("citations", []),
            confidence=merged.get("confidence", {}),
            warnings=merged.get("warnings", []),
        ),
        any_invalid,
    )
