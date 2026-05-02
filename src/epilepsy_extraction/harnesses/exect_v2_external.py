"""ExECTv2 external baseline adapter harness.

Ingests pre-generated ExECTv2 GATE pipeline outputs and maps them to the shared
final extraction schema. ExECTv2 must be run externally; this harness only adapts
its output for evaluation purposes.

Expected input format: a JSON file with a list of row objects keyed by row_id,
each containing ExECTv2 annotation fields. See mapping spec in
mappings/exect_v2_mapping_v1.yaml.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from epilepsy_extraction.assets import load_mapping
from epilepsy_extraction.evaluation import evaluate_prediction, parse_validity_summary, summarize
from epilepsy_extraction.schemas import (
    BudgetMetadata,
    DatasetSlice,
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
from epilepsy_extraction.evaluation.labels import parse_label


EXECT_V2_SOURCE_NOTE = (
    "ExECTv2 outputs were generated externally. "
    "Record the source repository commit hash, GATE version, and date of generation "
    "in the run record notes before treating this run as canonical."
)


def load_exect_v2_outputs(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load a pre-generated ExECTv2 output file.

    Expects JSON with structure: {"rows": [{"row_id": "1", ...}, ...]}.
    Returns a dict mapping row_id → row data.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("rows", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"ExECTv2 output at {path} must contain a list of rows")
    return {str(row["row_id"]): row for row in rows if "row_id" in row}


def run_exect_v2_external_baseline(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    exect_v2_outputs: dict[str, dict[str, Any]],
    *,
    source_commit: str = "",
    gate_version: str = "",
) -> RunRecord:
    rows: list[dict[str, Any]] = []
    evaluation_rows = []
    parse_results: list[tuple[str, bool]] = []
    mapping = load_mapping("exect_v2")
    warnings: list[str] = [EXECT_V2_SOURCE_NOTE]
    if source_commit:
        warnings.append(f"exect_v2_source_commit={source_commit}")
    if gate_version:
        warnings.append(f"exect_v2_gate_version={gate_version}")

    for record in records:
        raw_row = exect_v2_outputs.get(record.row_id, {})
        missing_row = not raw_row
        if missing_row:
            warnings.append(f"exect_v2_missing_row={record.row_id}")

        freq_prediction, freq_ok = _map_seizure_frequency(raw_row)
        parse_results.append(("seizure_frequency", freq_ok))
        evaluation = evaluate_prediction(record.source_row_index, record.gold_label, freq_prediction)
        evaluation_rows.append(evaluation)

        payload = _build_payload(freq_prediction, raw_row, record, missing_row)
        rows.append(
            {
                "row_id": record.row_id,
                "source_row_index": record.source_row_index,
                "prediction": asdict(freq_prediction),
                "payload": payload.to_dict(),
                "evaluation": asdict(evaluation),
                "exect_v2_raw": raw_row,
            }
        )

    return RunRecord(
        run_id=run_id,
        harness="exect_v2_external_baseline",
        schema_version="1.0.0",
        dataset=dataset,
        model="none",
        provider="exect_v2_external",
        temperature=0.0,
        prompt_version="exect_v2_external_v1",
        code_version=code_version,
        budget=BudgetMetadata(),
        field_coverage=_run_level_coverage(),
        metrics=summarize(evaluation_rows),
        rows=rows,
        parse_validity=parse_validity_summary(parse_results),
        warnings=warnings,
        architecture_family=ArchitectureFamily.CLINICAL_NLP_BASELINE.value,
        external_baseline=True,
        mapping_version=mapping.version,
    )


def _map_seizure_frequency(raw: dict[str, Any]) -> tuple[Prediction, bool]:
    value = str(raw.get("SeizureFrequency", "") or "").strip()
    if not value:
        return Prediction(
            label="unknown",
            confidence=0.0,
            parsed_monthly_rate=parse_label("unknown").monthly_rate,
            pragmatic_class="UNK",
            purist_class="UNK",
            warnings=["exect_v2_no_seizure_frequency"],
        ), False
    parsed = parse_label(value)
    return Prediction(
        label=value,
        confidence=0.8,
        parsed_monthly_rate=parsed.monthly_rate,
        pragmatic_class=parsed.pragmatic_class,
        purist_class=parsed.purist_class,
        warnings=[],
        metadata={"source": "exect_v2_SeizureFrequency"},
    ), parsed.monthly_rate is not None


def _build_payload(
    freq_prediction: Prediction,
    raw: dict[str, Any],
    record: GoldRecord,
    missing_row: bool,
) -> ExtractionPayload:
    medications = _map_medications(raw)
    investigations = _map_investigations(raw)
    seizure_types = _map_seizure_types(raw)
    epilepsy_type = _map_epilepsy_type(raw)
    epilepsy_syndrome = _map_epilepsy_syndrome(raw)
    coverage = _row_coverage(medications, investigations, seizure_types, epilepsy_type)

    return ExtractionPayload(
        pipeline_id="exect_v2_external_baseline",
        final=FinalExtraction(
            seizure_frequency={
                "value": freq_prediction.label,
                "parsed_monthly_rate": freq_prediction.parsed_monthly_rate,
                "pragmatic_class": freq_prediction.pragmatic_class,
                "purist_class": freq_prediction.purist_class,
            },
            current_medications=medications,
            investigations=investigations,
            seizure_types=seizure_types,
            epilepsy_type=epilepsy_type,
            epilepsy_syndrome=epilepsy_syndrome,
            citations=[],
            confidence={"seizure_frequency": freq_prediction.confidence},
            warnings=["exect_v2_missing_row"] if missing_row else [],
        ),
        field_coverage=coverage,
        invalid_output=missing_row,
        warnings=["exect_v2_missing_row"] if missing_row else [],
        metadata={"source_row_index": record.source_row_index, "exect_v2_row_available": not missing_row},
        artifacts={"exect_v2_raw": raw},
    )


def _map_medications(raw: dict[str, Any]) -> list[dict[str, Any]]:
    meds = raw.get("Medication", [])
    if not meds:
        return []
    if isinstance(meds, str):
        meds = [{"name": meds}]
    return [{"name": str(m.get("name", m) if isinstance(m, dict) else m)} for m in meds]


def _map_investigations(raw: dict[str, Any]) -> list[dict[str, Any]]:
    invs = raw.get("Investigation", [])
    if not invs:
        return []
    if isinstance(invs, str):
        invs = [{"type": invs}]
    return [{"type": str(i.get("type", i) if isinstance(i, dict) else i)} for i in invs]


def _map_seizure_types(raw: dict[str, Any]) -> list[dict[str, Any]]:
    types = raw.get("SeizureType", [])
    if not types:
        return []
    if isinstance(types, str):
        types = [types]
    return [{"type": str(t)} for t in types]


def _map_epilepsy_type(raw: dict[str, Any]) -> dict[str, Any] | None:
    value = raw.get("EpilepsyType") or raw.get("EpilepsyDiagnosis")
    if not value:
        return None
    return {"type": str(value)}


def _map_epilepsy_syndrome(raw: dict[str, Any]) -> dict[str, Any] | None:
    value = raw.get("EpilepsySyndrome")
    if not value:
        return None
    return {"syndrome": str(value)}


def _row_coverage(
    medications: list[Any],
    investigations: list[Any],
    seizure_types: list[Any],
    epilepsy_type: dict[str, Any] | None,
) -> dict[str, str]:
    coverage = not_attempted_coverage()
    coverage[FieldFamily.SEIZURE_FREQUENCY.value] = FieldCoverageStatus.IMPLEMENTED.value
    if medications:
        coverage[FieldFamily.CURRENT_MEDICATIONS.value] = FieldCoverageStatus.IMPLEMENTED.value
    if investigations:
        coverage[FieldFamily.INVESTIGATIONS.value] = FieldCoverageStatus.IMPLEMENTED.value
    if seizure_types:
        coverage[FieldFamily.SEIZURE_CLASSIFICATION.value] = FieldCoverageStatus.IMPLEMENTED.value
    if epilepsy_type:
        coverage[FieldFamily.EPILEPSY_CLASSIFICATION.value] = FieldCoverageStatus.PARTIAL.value
    return coverage


def _run_level_coverage() -> dict[str, str]:
    coverage = not_attempted_coverage()
    coverage[FieldFamily.SEIZURE_FREQUENCY.value] = FieldCoverageStatus.IMPLEMENTED.value
    coverage[FieldFamily.CURRENT_MEDICATIONS.value] = FieldCoverageStatus.IMPLEMENTED.value
    coverage[FieldFamily.INVESTIGATIONS.value] = FieldCoverageStatus.IMPLEMENTED.value
    coverage[FieldFamily.SEIZURE_CLASSIFICATION.value] = FieldCoverageStatus.IMPLEMENTED.value
    coverage[FieldFamily.EPILEPSY_CLASSIFICATION.value] = FieldCoverageStatus.PARTIAL.value
    return coverage
