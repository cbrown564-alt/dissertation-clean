from __future__ import annotations

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
    ProviderResponse,
    budget_from_provider_responses,
)
from epilepsy_extraction.schemas import (
    CORE_FIELD_FAMILIES,
    DatasetSlice,
    ExtractionPayload,
    GoldRecord,
    RunRecord,
    failed_component_coverage,
    field_coverage,
)
from epilepsy_extraction.schemas.contracts import ArchitectureFamily, FieldFamily


def run_clines_epilepsy_modular(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    provider: ChatProvider,
    *,
    model: str = "mock-model",
    temperature: float = 0.0,
) -> RunRecord:
    """CLINES-inspired modular extraction pipeline.

    Per row:
      1. Normalise letter text.
      2. Chunk by sections.
      3. For each field family: select relevant chunks, extract, annotate
         status/temporality, normalise values, verify evidence (deterministic).
      4. Aggregate across families into FinalExtraction.

    Makes len(CORE_FIELD_FAMILIES) provider calls per row.
    Architecture family: clines_inspired_modular.
    """
    prompt = load_prompt("clines_field_extractor")
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
                provider, prompt.content, schema.content, family, context, model, temperature
            )
            if result.response:
                row_responses.append(result.response)
            parse_results.append((family.value, result.valid))

            # Deterministic post-processing (stored in artifacts, not final payload)
            _, status_ann = annotate_status(result.data, context)
            verification_artifact, _ = verify_field_extraction(result.data, context)

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
                "verification": verification_artifact,
                "frequency_normalization": freq_norm,
                "parse_valid": result.valid,
                "warnings": result.warnings,
            }
            field_data[family] = result.data

        agg = aggregate_field_results(field_data)
        if agg.any_invalid:
            run_coverage = failed_component_coverage(CORE_FIELD_FAMILIES)

        payload = ExtractionPayload(
            pipeline_id="clines_epilepsy_modular",
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
        harness="clines_epilepsy_modular",
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
        architecture_family=ArchitectureFamily.CLINES_INSPIRED_MODULAR.value,
        complexity={
            "modules": [
                "chunking",
                "field_extractors",
                "status_temporality",
                "normalization",
                "verification_deterministic",
                "aggregation",
            ]
        },
    )
