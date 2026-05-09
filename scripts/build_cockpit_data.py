from __future__ import annotations

import argparse
import csv
import json
from collections import Counter as _Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


try:
    import yaml as _yaml  # type: ignore[import]

    def _load_yaml(path: Path) -> dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return _yaml.safe_load(text) or {}
        except Exception as exc:  # noqa: BLE001
            return {"_error": str(exc)}

except ImportError:
    def _load_yaml(path: Path) -> dict[str, Any]:  # type: ignore[misc]
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return {"_error": f"pyyaml not installed and JSON parse failed: {exc}"}


ARCHITECTURE_LADDER: list[dict[str, Any]] = [
    {
        "step": 1,
        "family": "clinical_nlp_baseline",
        "label": "Clinical NLP Baselines",
        "colour": "teal",
        "description": (
            "Deterministic rule-based extraction, ExECT-inspired clean-room rules, "
            "and an external ExECTv2 adapter. Establishes reproducible floors before "
            "LLM comparison."
        ),
        "harnesses": [
            "deterministic_baseline",
            "exect_lite_cleanroom_baseline",
            "exect_v2_external",
        ],
    },
    {
        "step": 2,
        "family": "direct",
        "label": "Direct LLM Baselines",
        "colour": "blue",
        "description": (
            "Single provider call reads the full letter and emits the final schema. "
            "Full-contract and evidence-contract variants test whether requiring "
            "evidence citations changes output quality."
        ),
        "harnesses": ["direct_full_contract", "direct_evidence_contract"],
    },
    {
        "step": 3,
        "family": "retrieval",
        "label": "Retrieval + Field Extraction",
        "colour": "purple",
        "description": (
            "Candidate-span retrieval grouped by field family, then local-context "
            "extraction per field. Tests whether span selection and focused context "
            "improve output quality."
        ),
        "harnesses": ["retrieval_field_extractors"],
    },
    {
        "step": 4,
        "family": "clines_inspired_modular",
        "label": "CLINES-Inspired Modular Pipeline",
        "colour": "amber",
        "description": (
            "Full modular pipeline: sectioning, semantic chunking, field-specific "
            "extraction, assertion/status enrichment, normalization, evidence "
            "verification, and cross-chunk aggregation. Main proposed architecture."
        ),
        "harnesses": ["clines_epilepsy_modular", "clines_epilepsy_verified"],
    },
    {
        "step": 5,
        "family": "anchor",
        "label": "Seizure-Frequency Anchor",
        "colour": "green",
        "description": (
            "Microcosm anchor harnesses for seizure frequency across architecture "
            "families and model tiers. Self-consistency variants measure costed "
            "reliability gains."
        ),
        "harnesses": ["direct_anchor", "retrieval_anchor", "anchor_sc3", "anchor_sc5"],
    },
]

_FAMILY_TO_STEP = {entry["family"]: entry["step"] for entry in ARCHITECTURE_LADDER}

# Normalise run-record family names to ladder family keys
FAMILY_NORM: dict[str, str] = {
    "direct_llm":                 "direct",
    "retrieval_field_pipeline":   "retrieval",
    "costed_reliability_variant": "anchor",
}


def _normalize_family(family: str) -> str:
    return FAMILY_NORM.get(family, family)


FIELD_FAMILIES = [
    "seizure_frequency",
    "seizure_classification",
    "epilepsy_classification",
    "current_medications",
    "investigations",
    "associated_symptoms",
    "comorbidities",
    "rescue_medication",
    "other_therapies",
]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _load_csv(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            headers = list(reader.fieldnames or [])
            rows = list(reader)
        return {"headers": headers, "rows": rows}
    except FileNotFoundError:
        return {"headers": [], "rows": []}


def _manifest_summary(record: dict[str, Any]) -> dict[str, Any]:
    manifest = record.get("harness_manifest") or record.get("manifest") or {}
    complexity = record.get("complexity") if isinstance(record.get("complexity"), dict) else {}
    if not manifest and isinstance(complexity.get("manifest"), dict):
        manifest = complexity["manifest"]
    if not isinstance(manifest, dict):
        manifest = {}
    return {
        "id": manifest.get("id") or manifest.get("manifest_id") or record.get("manifest_id") or "",
        "hash": manifest.get("hash") or manifest.get("manifest_hash") or record.get("manifest_hash") or "",
        "source": manifest.get("source") or manifest.get("path") or manifest.get("source_path") or "",
        "architecture_family": manifest.get("architecture_family") or record.get("architecture_family") or "",
    }


def _event_log(record: dict[str, Any]) -> list[dict[str, Any]]:
    events = record.get("harness_events") or record.get("event_log") or []
    if not isinstance(events, list):
        return []
    return [event for event in events if isinstance(event, dict)]


def _event_summary(record: dict[str, Any]) -> dict[str, Any]:
    explicit = record.get("event_summary") or record.get("harness_event_summary")
    if isinstance(explicit, dict):
        return dict(explicit)
    events = _event_log(record)
    counts: dict[str, int] = {}
    for event in events:
        event_type = event.get("event_type") or event.get("type") or "unknown"
        counts[str(event_type)] = counts.get(str(event_type), 0) + 1
    return {
        "event_count": len(events),
        "event_type_counts": counts,
        "provider_calls": counts.get("provider_call_started", 0),
        "parse_repair_attempts": counts.get("parse_repaired", 0),
        "verifier_passes": counts.get("verification_completed", 0),
        "escalation_decisions": counts.get("escalation_decision", 0),
    }


def _count_sequence(value: Any, fallback: Any = "") -> int | str:
    if isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
        return len(value)
    if isinstance(value, int) or isinstance(value, float):
        return int(value)
    if isinstance(fallback, int) or isinstance(fallback, float):
        return int(fallback)
    return ""


def _run_summary(record: dict[str, Any]) -> dict[str, Any]:
    budget = record.get("budget") or {}
    metrics = record.get("metrics") or {}
    dataset = record.get("dataset") or {}
    fc = record.get("field_coverage") or {}
    family_raw = record.get("architecture_family", "")
    family     = _normalize_family(family_raw)
    complexity = record.get("complexity") if isinstance(record.get("complexity"), dict) else {}
    manifest = _manifest_summary(record)
    events = _event_summary(record)
    workflow_units = record.get("workflow_units") or complexity.get("workflow_units") or []
    verifier_gates = record.get("verifier_gates") or record.get("verification_gates") or {}
    escalation = record.get("escalation") or record.get("escalation_policy") or {}

    return {
        "run_id": record.get("run_id", ""),
        "harness": record.get("harness", ""),
        "architecture_family": family,
        "architecture_family_raw": family_raw,
        "ladder_step": _FAMILY_TO_STEP.get(family),
        "status": record.get("status", ""),
        "created_at": record.get("created_at", ""),
        "model": record.get("model", "none"),
        "model_registry_entry": record.get("model_registry_entry"),
        "provider": record.get("provider", ""),
        "external_baseline": record.get("external_baseline", False),
        "mapping_version": record.get("mapping_version"),
        "prompt_version": record.get("prompt_version"),
        "schema_version": record.get("schema_version"),
        "code_version": record.get("code_version"),
        "dataset_id": dataset.get("dataset_id", ""),
        "dataset_n": dataset.get("n", 0),
        "budget": {
            "input_tokens": budget.get("input_tokens", 0),
            "output_tokens": budget.get("output_tokens", 0),
            "total_tokens": budget.get("total_tokens", 0),
            "latency_ms": budget.get("latency_ms", 0),
            "llm_calls_per_row": budget.get("llm_calls_per_row", 0),
        },
        "metrics": {
            "exact_label_accuracy": metrics.get("exact_label_accuracy"),
            "monthly_rate_accuracy": metrics.get("monthly_rate_accuracy_tolerance_15pct"),
            "n": metrics.get("n"),
        },
        "field_coverage": fc,
        "field_coverage_counts": {
            "implemented": sum(1 for v in fc.values() if v == "implemented"),
            "partial": sum(1 for v in fc.values() if v == "partial"),
            "not_attempted": sum(1 for v in fc.values() if v == "not_attempted"),
        },
        "parse_validity": record.get("parse_validity") or {},
        "harness_manifest": manifest,
        "harness_events": events,
        "harness_complexity": {
            "modules_invoked": _count_sequence(
                complexity.get("modules"),
                complexity.get("modules_invoked"),
            ),
            "workflow_units": _count_sequence(
                workflow_units,
                complexity.get("workflow_units_invoked"),
            ),
            "event_count": events.get("event_count", 0),
            "provider_calls": events.get("provider_calls", 0),
            "parse_repair_attempts": events.get("parse_repair_attempts", 0),
            "verifier_passes": events.get("verifier_passes", 0),
            "escalation_decisions": events.get("escalation_decisions", 0),
            "intermediate_artifacts": len(record.get("artifact_paths") or {}),
            "status": "harness_native"
            if manifest.get("id") and events.get("event_count")
            else ("partial" if manifest.get("id") or events.get("event_count") or complexity else "legacy_or_not_reported"),
        },
        "workflow_units": workflow_units if isinstance(workflow_units, list) else [],
        "verifier_gates": verifier_gates if isinstance(verifier_gates, dict) else {},
        "escalation": escalation if isinstance(escalation, dict) else {},
        "warnings": record.get("warnings") or [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile cockpit data from docs, runs, result tables, and model registry.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("site/cockpit-data.json"))
    args = parser.parse_args()

    root = args.repo_root.resolve()

    docs: dict[str, str] = {
        key: _read_text(root / "docs" / fname)
        for key, fname in [
            ("research_question", "research_question.md"),
            ("architecture", "architecture.md"),
            ("evaluation_contract", "evaluation_contract.md"),
            ("adjudication_protocol", "adjudication_protocol.md"),
            ("experiment_protocol", "experiment_protocol.md"),
            ("model_registry_protocol", "model_registry_protocol.md"),
            ("implementation_plan", "implementation_plan.md"),
            ("coding_agent_harness_literature_review", "coding_agent_harness_literature_review.md"),
        ]
    }

    runs_dir = root / "results" / "runs"
    primary_runs: list[dict[str, Any]] = []
    matrix_runs:  list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("**/*.json")):
        is_matrix = len(path.relative_to(runs_dir).parts) > 1
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            summary = _run_summary(record)
            summary["is_matrix_run"] = is_matrix
            (matrix_runs if is_matrix else primary_runs).append(summary)
        except Exception:  # noqa: BLE001
            pass

    run_records = primary_runs + matrix_runs

    # Non-smoke primary runs + real-data supporting matrix runs for the cockpit register
    def _is_display(r: dict[str, Any]) -> bool:
        if r.get("status") in ("smoke",):
            return False
        if r.get("is_matrix_run"):
            bud = r.get("budget") or {}
            return isinstance(bud, dict) and int(bud.get("total_tokens", 0)) > 0
        return True

    display_register = [r for r in run_records if _is_display(r)]

    # Build harness→family map and load adjudicated accuracy from result table
    _harness_to_family: dict[str, str] = {}
    for step in ARCHITECTURE_LADDER:
        for h in step.get("harnesses", []):
            _harness_to_family[h] = step["family"]

    _table_accs: dict[str, list[float]] = {}  # family → list of accuracies from table
    _flc_path = root / "results" / "tables" / "field_level_correctness.csv"
    if _flc_path.exists():
        for row in _load_csv(_flc_path).get("rows", []):
            # Only use SF accuracy so best_accuracy reflects the primary outcome field
            if str(row.get("field_family", "")) != "seizure_frequency":
                continue
            acc_str = str(row.get("exact_label_accuracy") or "").strip()
            if not acc_str:
                continue
            try:
                acc = float(acc_str)
            except ValueError:
                continue
            harness = str(row.get("harness", ""))
            fam_key = _harness_to_family.get(harness) or str(row.get("architecture_family", ""))
            if fam_key:
                _table_accs.setdefault(fam_key, []).append(acc)

    # Per-family aggregated summaries
    family_summaries: dict[str, Any] = {}
    for step in ARCHITECTURE_LADDER:
        fam         = step["family"]
        fam_primary = [r for r in primary_runs if r["architecture_family"] == fam]
        fam_matrix  = [r for r in matrix_runs  if r["architecture_family"] == fam]
        non_smoke   = [r for r in fam_primary  if r.get("status") != "smoke"]
        accs = [
            r["metrics"]["exact_label_accuracy"]
            for r in non_smoke
            if (r.get("metrics") or {}).get("exact_label_accuracy") is not None
            and r.get("status") != "archive"
        ]
        # Supplement with adjudicated accuracies from result tables
        accs = accs + _table_accs.get(fam, [])
        agg_cov: dict[str, Any] = {}
        for field in FIELD_FAMILIES:
            statuses = [r["field_coverage"].get(field) for r in non_smoke if r.get("field_coverage")]
            if "implemented" in statuses:
                agg_cov[field] = "implemented"
            elif "partial" in statuses:
                agg_cov[field] = "partial"
            elif any(s is not None for s in statuses):
                agg_cov[field] = "not_attempted"
            else:
                agg_cov[field] = None
        family_summaries[fam] = {
            "family": fam,
            "step": step["step"],
            "label": step["label"],
            "colour": step["colour"],
            "description": step["description"],
            "harnesses": list(dict.fromkeys(r["harness"] for r in non_smoke if r.get("harness"))),
            "run_counts": {
                "supporting": sum(1 for r in fam_primary if r.get("status") == "supporting"),
                "archive":    sum(1 for r in fam_primary if r.get("status") == "archive"),
                "smoke":      sum(1 for r in fam_primary if r.get("status") == "smoke"),
                "matrix":     len(fam_matrix),
            },
            "best_accuracy": max(accs) if accs else None,
            "has_data": len(non_smoke) > 0 or len(fam_matrix) > 0,
            "aggregate_field_coverage": agg_cov,
        }

    sc = _Counter(r.get("status", "") for r in primary_runs)
    run_meta = {
        "primary_total": len(primary_runs),
        "matrix_total":  len(matrix_runs),
        "display_total": len(display_register),
        "by_status": dict(sc),
    }

    model_registry: dict[str, Any] = {}
    frozen_files = sorted((root / "config").glob("model_registry.????-??-??.yaml"))
    if frozen_files:
        entry = _load_yaml(frozen_files[-1])
        entry["_source"] = frozen_files[-1].name
        model_registry["frozen"] = entry
    candidate_path = root / "config" / "model_registry.candidate.yaml"
    if candidate_path.exists():
        model_registry["candidate"] = _load_yaml(candidate_path)

    harness_manifests: list[dict[str, Any]] = []
    manifests_dir = root / "config" / "harnesses"
    for path in sorted(manifests_dir.glob("*.yaml")) + sorted(manifests_dir.glob("*.yml")):
        manifest = _load_yaml(path)
        manifest["_source"] = str(path.relative_to(root))
        harness_manifests.append(manifest)

    result_tables: dict[str, Any] = {}
    for csv_path in sorted((root / "results" / "tables").glob("*.csv")):
        result_tables[csv_path.stem] = _load_csv(csv_path)

    adjudication: dict[str, Any] = {}
    for csv_path in sorted((root / "results" / "adjudication").glob("*.csv")):
        adjudication[csv_path.stem] = _load_csv(csv_path)

    payload: dict[str, Any] = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "architecture_ladder": ARCHITECTURE_LADDER,
        "field_families": FIELD_FAMILIES,
        "run_register": run_records,
        "display_register": display_register,
        "family_summaries": family_summaries,
        "run_meta": run_meta,
        "harness_manifests": harness_manifests,
        "model_registry": model_registry,
        "result_tables": result_tables,
        "adjudication": adjudication,
        "docs": docs,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    n_primary = len(primary_runs)
    n_matrix  = len(matrix_runs)
    n_display = len(display_register)
    print(
        f"Cockpit data written to {args.output}  "
        f"({n_primary} primary, {n_matrix} matrix, {n_display} display)"
    )


if __name__ == "__main__":
    main()
