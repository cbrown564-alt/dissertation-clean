from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Iterable

from epilepsy_extraction.assets import load_prompt, load_schema
from epilepsy_extraction.document.normalization import normalize_letter
from epilepsy_extraction.evaluation import parse_validity_summary
from epilepsy_extraction.modules.aggregation import aggregate_field_results
from epilepsy_extraction.modules.chunking import chunk_letter, select_chunks_for_family
from epilepsy_extraction.modules.field_extractors import extract_field_family
from epilepsy_extraction.modules.normalization import enrich_seizure_frequency
from epilepsy_extraction.modules.status_temporality import annotate_status
from epilepsy_extraction.modules.verification import verify_field_extraction
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
    failed_component_coverage,
    field_coverage,
)
from epilepsy_extraction.schemas.contracts import ArchitectureFamily, FieldFamily


def run_clines_epilepsy_verified(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    provider: ChatProvider,
    *,
    model: str = "mock-model",
    temperature: float = 0.0,
) -> RunRecord:
    """CLINES-inspired modular pipeline with provider-backed evidence verification.

    Extends clines_epilepsy_modular by adding one additional provider call per
    row that reviews the aggregated extraction against the original letter and
    returns evidence grades beyond simple quote presence.

    Makes len(CORE_FIELD_FAMILIES) + 1 provider calls per row.
    Architecture family: clines_inspired_modular.
    """
    extraction_prompt = load_prompt("clines_field_extractor")
    verification_prompt = load_prompt("clines_verifier")
    schema = load_schema("final_extraction")
    record_list = list(records)
    rows: list[dict[str, Any]] = []
    all_responses: list[ProviderResponse] = []
    parse_results: list[tuple[str, bool]] = []
    run_coverage = field_coverage(implemented=CORE_FIELD_FAMILIES)

    for record in record_list:
        letter_norm = normalize_letter(record.letter)
        chunks = chunk_letter(letter_norm)

        row_responses: list[ProviderResponse] = []
        field_data: dict[FieldFamily, dict[str, Any]] = {}
        row_artifacts: dict[str, Any] = {
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "source_section": c.source_section,
                    "token_estimate": c.token_estimate,
                }
                for c in chunks
            ]
        }

        for family in CORE_FIELD_FAMILIES:
            selected, selection_warnings = select_chunks_for_family(chunks, family)
            context = "\n---\n".join(c.text for c in selected)

            result = extract_field_family(
                provider, extraction_prompt.content, schema.content, family, context, model, temperature
            )
            if result.response:
                row_responses.append(result.response)
            parse_results.append((family.value, result.valid))

            _, status_ann = annotate_status(result.data, context)
            det_verification, _ = verify_field_extraction(result.data, context)

            freq_norm = {}
            if family == FieldFamily.SEIZURE_FREQUENCY and result.data:
                freq_norm = enrich_seizure_frequency(
                    result.data.get("seizure_frequency", {})
                )

            row_artifacts[family.value] = {
                "selected_chunk_ids": [c.chunk_id for c in selected],
                "selection_warnings": selection_warnings,
                "status_annotation": {
                    "status": status_ann.status,
                    "confidence": status_ann.confidence,
                    "evidence_phrase": status_ann.evidence_phrase,
                },
                "verification_deterministic": det_verification,
                "frequency_normalization": freq_norm,
                "parse_valid": result.valid,
                "warnings": result.warnings,
            }
            field_data[family] = result.data

        agg = aggregate_field_results(field_data)
        if agg.any_invalid:
            run_coverage = failed_component_coverage(CORE_FIELD_FAMILIES)

        # Provider-backed verification pass
        verification_response, verification_artifact = _run_verification(
            provider,
            verification_prompt.content,
            agg.final,
            letter_norm,
            model,
            temperature,
        )
        if verification_response:
            row_responses.append(verification_response)
        row_artifacts["provider_verification"] = verification_artifact
        parse_results.append(("verification", verification_artifact.get("parse_valid", False)))

        payload = ExtractionPayload(
            pipeline_id="clines_epilepsy_verified",
            final=agg.final,
            field_coverage=(
                field_coverage(implemented=CORE_FIELD_FAMILIES)
                if not agg.any_invalid
                else failed_component_coverage(CORE_FIELD_FAMILIES)
            ),
            artifacts=row_artifacts,
            invalid_output=agg.any_invalid,
            warnings=agg.warnings,
            metadata={
                "source_row_index": record.source_row_index,
                "aggregation_conflicts": agg.conflicts,
                "verification_overall_confidence": verification_artifact.get("overall_confidence"),
            },
        )

        all_responses.extend(row_responses)
        rows.append(
            {
                "row_id": record.row_id,
                "source_row_index": record.source_row_index,
                "payload": payload.to_dict(),
                "modular_artifacts": row_artifacts,
                "provider_responses": [asdict(r) for r in row_responses],
            }
        )

    return RunRecord(
        run_id=run_id,
        harness="clines_epilepsy_verified",
        schema_version=schema.version,
        dataset=dataset,
        model=model,
        provider=provider.provider_name,
        temperature=temperature,
        prompt_version=extraction_prompt.version,
        code_version=code_version,
        budget=budget_from_provider_responses(all_responses, rows=len(record_list)),
        field_coverage=run_coverage,
        rows=rows,
        parse_validity=parse_validity_summary(parse_results),
        artifact_paths={
            "extraction_prompt": extraction_prompt.path,
            "verification_prompt": verification_prompt.path,
            "schema": schema.path,
        },
        architecture_family=ArchitectureFamily.CLINES_INSPIRED_MODULAR.value,
        complexity={
            "modules": [
                "chunking",
                "field_extractors",
                "status_temporality",
                "normalization",
                "verification_deterministic",
                "verification_provider",
                "aggregation",
            ]
        },
    )


def _run_verification(
    provider: ChatProvider,
    prompt_text: str,
    final: FinalExtraction,
    letter: str,
    model: str,
    temperature: float,
) -> tuple[ProviderResponse | None, dict[str, Any]]:
    """Call provider to verify evidence support for the aggregated extraction."""
    extraction_summary = json.dumps(final.to_dict(), indent=2, sort_keys=True)
    content = (
        f"{prompt_text}\n\n"
        f"Extracted output:\n{extraction_summary}\n\n"
        f"Original clinic letter:\n{letter}"
    )
    response = provider.complete(
        ProviderRequest(
            messages=[ProviderMessage(role="user", content=content)],
            model=model,
            temperature=temperature,
            response_format="json",
            metadata={"prompt_id": "clines_verifier"},
        )
    )
    if not response.ok:
        return response, {"parse_valid": False, "error": "provider_error"}
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        return response, {"parse_valid": False, "error": "json_parse_error"}
    return response, {
        "parse_valid": True,
        "verifications": data.get("verifications", {}),
        "overall_confidence": data.get("overall_confidence"),
        "warnings": data.get("warnings", []),
    }
