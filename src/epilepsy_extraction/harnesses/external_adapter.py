from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from epilepsy_extraction.schemas import (
    CORE_FIELD_FAMILIES,
    ExtractionPayload,
    FinalExtraction,
    event_dicts,
    failed_component_coverage,
    field_coverage,
    harness_event,
    summarize_harness_events,
)
from epilepsy_extraction.schemas.contracts import ArchitectureFamily


@dataclass(frozen=True)
class ExternalClinicalAgentAdapter:
    adapter_id: str
    runner_name: str
    runner_version: str = ""
    canonical_comparator: bool = False

    def normalize_output(
        self,
        raw_output: dict[str, Any],
        *,
        row_id: str,
        artifact_ref: str = "",
    ) -> dict[str, Any]:
        payload = _payload_from_external(raw_output, self.adapter_id)
        events = [
            harness_event(
                "context_built",
                row_id,
                1,
                component="external_adapter",
                summary="External harness output loaded from sandbox artifact",
                metrics={"artifact_ref": artifact_ref},
            ),
            harness_event(
                "parse_attempted",
                row_id,
                2,
                component="external_adapter",
                summary="External output normalized into ExtractionPayload",
                metrics={"valid": not payload.invalid_output},
                warnings=payload.warnings,
            ),
        ]
        return {
            "adapter": {
                "adapter_id": self.adapter_id,
                "runner_name": self.runner_name,
                "runner_version": self.runner_version,
                "canonical_comparator": self.canonical_comparator,
            },
            "payload": payload.to_dict(),
            "harness_events": event_dicts(events),
            "event_summary": summarize_harness_events(events),
            "raw_artifact_ref": artifact_ref,
            "architecture_family": ArchitectureFamily.COSTED_RELIABILITY_VARIANT.value,
        }


def load_external_adapter_output(path: str | Path, adapter: ExternalClinicalAgentAdapter | None = None) -> dict[str, Any]:
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    adapter = adapter or ExternalClinicalAgentAdapter(
        adapter_id=str(raw.get("adapter_id") or "external_replay"),
        runner_name=str(raw.get("runner_name") or raw.get("runner") or "external"),
        runner_version=str(raw.get("runner_version") or ""),
        canonical_comparator=bool(raw.get("canonical_comparator", False)),
    )
    row_id = str(raw.get("row_id") or raw.get("source_row_id") or "")
    return adapter.normalize_output(raw, row_id=row_id, artifact_ref=str(path))


def _payload_from_external(raw_output: dict[str, Any], adapter_id: str) -> ExtractionPayload:
    warnings = [str(warning) for warning in raw_output.get("warnings", [])]
    final_raw = raw_output.get("payload", {}).get("final") if isinstance(raw_output.get("payload"), dict) else None
    final_raw = final_raw or raw_output.get("final") or raw_output.get("extraction") or {}
    invalid_output = not isinstance(final_raw, dict) or not final_raw
    if invalid_output:
        warnings.append("external_output_missing_final_payload")
        final_raw = {}

    final = FinalExtraction(
        seizure_frequency=final_raw.get("seizure_frequency", {}) if isinstance(final_raw, dict) else {},
        current_medications=final_raw.get("current_medications", []) if isinstance(final_raw, dict) else [],
        investigations=final_raw.get("investigations", []) if isinstance(final_raw, dict) else [],
        seizure_types=final_raw.get("seizure_types", []) if isinstance(final_raw, dict) else [],
        seizure_features=final_raw.get("seizure_features", []) if isinstance(final_raw, dict) else [],
        seizure_pattern_modifiers=final_raw.get("seizure_pattern_modifiers", []) if isinstance(final_raw, dict) else [],
        epilepsy_type=final_raw.get("epilepsy_type") if isinstance(final_raw, dict) else None,
        epilepsy_syndrome=final_raw.get("epilepsy_syndrome") if isinstance(final_raw, dict) else None,
        citations=final_raw.get("citations", []) if isinstance(final_raw, dict) else [],
        confidence=final_raw.get("confidence", {}) if isinstance(final_raw, dict) else {},
        warnings=final_raw.get("warnings", warnings) if isinstance(final_raw, dict) else warnings,
    )
    coverage = raw_output.get("field_coverage")
    if not isinstance(coverage, dict):
        coverage = failed_component_coverage(CORE_FIELD_FAMILIES) if invalid_output else field_coverage(implemented=CORE_FIELD_FAMILIES)
    return ExtractionPayload(
        pipeline_id=adapter_id,
        final=final,
        field_coverage=coverage,
        artifacts={"external_raw_keys": sorted(raw_output.keys())},
        invalid_output=invalid_output,
        warnings=warnings,
        metadata={"external_runner": raw_output.get("runner_name") or raw_output.get("runner", "")},
    )
