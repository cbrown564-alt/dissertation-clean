"""
Run a model-family sensitivity matrix.

Each (model_entry, harness) pair produces a separate run record in --output-dir.
Deterministic harnesses run once regardless of model entries (no provider needed).
Provider-backed harnesses run once per selected model entry.

Usage:
  python scripts/run_model_matrix.py \\
    --registry config/model_registry.2026-05-02.yaml \\
    --dataset data/synthetic/epilepsy_letters.json \\
    --harnesses single_prompt_anchor,direct_full_contract \\
    --tiers frontier,small \\
    --limit 5 \\
    --output-dir results/runs/matrix/

Provider options:
  --provider mock      MockProvider — no API calls, safe for smoke tests (default)
  --provider replay    ReplayProvider — requires --replay PATH to saved responses
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import (
    attach_manifest_to_run,
    default_manifest_path,
    load_harness_manifest,
    run_anchor_harness,
    run_budgeted_escalation_harness,
    run_clines_epilepsy_modular,
    run_clines_epilepsy_verified,
    run_deterministic_baseline,
    run_direct_evidence_contract,
    run_direct_full_contract,
    run_exect_lite_baseline,
    run_retrieval_field_extractors,
    run_single_prompt_full_contract,
)
from epilepsy_extraction.harnesses.manifest import HarnessManifest
from epilepsy_extraction.models.registry import ModelRegistryEntry, load_registry, validate_registry
from epilepsy_extraction.providers import MockProvider, ReplayProvider
from epilepsy_extraction.schemas import DatasetSlice, RunRecord, resolve_code_version, write_run_record


DETERMINISTIC_HARNESSES: frozenset[str] = frozenset({"deterministic_baseline", "exect_lite_cleanroom_baseline"})

PROVIDER_BACKED_HARNESSES: frozenset[str] = frozenset({
    "single_prompt_anchor",
    "retrieval_anchor",
    "multi_agent_anchor",
    "multi_agent_anchor_sc3",
    "multi_agent_anchor_sc5",
    "direct_full_contract",
    "single_prompt_full_contract",
    "direct_evidence_contract",
    "retrieval_field_extractors",
    "clines_epilepsy_modular",
    "clines_epilepsy_verified",
    "budgeted_escalation",
})

ALL_HARNESSES: frozenset[str] = DETERMINISTIC_HARNESSES | PROVIDER_BACKED_HARNESSES

_MOCK_ANCHOR_RESPONSE = (
    '{"label":"2 per month","evidence":"two seizures per month","confidence":0.9,"warnings":[]}'
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a model × harness matrix using a frozen model registry."
    )
    parser.add_argument("--registry", type=Path, required=True, help="Model registry YAML (frozen recommended)")
    parser.add_argument("--dataset", type=Path, required=True, help="Input dataset JSON")
    parser.add_argument(
        "--harnesses",
        default="single_prompt_anchor,direct_full_contract",
        help="Comma-separated harness names (default: single_prompt_anchor,direct_full_contract)",
    )
    parser.add_argument("--tiers", default="", help="Comma-separated tier filter (empty = all)")
    parser.add_argument("--model-ids", default="", help="Comma-separated model ID filter (empty = all)")
    parser.add_argument("--limit", type=int, default=5, help="Max rows per run (safety bound)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/runs/matrix"),
        help="Directory for output run records",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "replay"],
        default="mock",
        help="Provider type for LLM calls (default: mock)",
    )
    parser.add_argument("--replay", type=Path, default=None, help="Replay file (required if --provider=replay)")
    parser.add_argument("--dry-run", action="store_true", help="Print the run plan and exit without executing")
    parser.add_argument(
        "--allow-unfrozen",
        action="store_true",
        help="Proceed even if the registry frozen_at field is not set",
    )
    parser.add_argument("--code-version", default=None, help="Override code version string")
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=Path("config/harnesses"),
        help="Directory containing <harness>.yaml manifests (default: config/harnesses)",
    )
    args = parser.parse_args()

    entries = _load_and_validate_registry(args.registry, allow_unfrozen=args.allow_unfrozen)

    harnesses = [h.strip() for h in args.harnesses.split(",") if h.strip()]
    unknown = [h for h in harnesses if h not in ALL_HARNESSES]
    if unknown:
        raise SystemExit(f"Unknown harnesses: {unknown}. Available: {sorted(ALL_HARNESSES)}")

    tier_filter = {t.strip() for t in args.tiers.split(",") if t.strip()} or None
    model_id_filter = {m.strip() for m in args.model_ids.split(",") if m.strip()} or None
    plan = build_plan(entries, harnesses, tier_filter, model_id_filter)

    manifests = _load_manifests(harnesses, args.manifest_dir)

    if args.dry_run:
        print(json.dumps(
            {"plan": _plan_as_list(plan, manifests), "total_runs": len(plan)},
            indent=2,
            sort_keys=True,
        ))
        return

    code_version = resolve_code_version(args.code_version, cwd=Path.cwd(), fallback="uncommitted")
    all_records = load_synthetic_subset(args.dataset)
    selected = select_fixed_slice(all_records, limit=args.limit)
    dataset = DatasetSlice(
        dataset_id=args.dataset.stem,
        dataset_path=str(args.dataset),
        data_hash=compute_file_sha256(args.dataset),
        row_ids=[r.row_id for r in selected],
        inclusion_criteria=f"row_ok_only=true; limit={args.limit}",
    )

    results: list[dict[str, Any]] = []
    for entry, harness in plan:
        run_id = _run_id(entry, harness)
        output_path = args.output_dir / f"{run_id}.json"
        provider = _make_provider(args.provider, args.replay)
        record = _dispatch(harness, entry, selected, dataset, run_id, code_version, provider)
        if entry is not None and not record.model_registry_entry:
            record = replace(record, model_registry_entry=entry.model_id)
        record = attach_manifest_to_run(record, manifests.get(harness))
        write_run_record(record, output_path)
        results.append({
            "run_id": run_id,
            "harness": harness,
            "model": entry.model_id if entry else "none",
            "tier": entry.tier if entry else "none",
            "registry_provider": entry.provider if entry else "deterministic",
            "model_registry_entry": record.model_registry_entry or "",
            "output": str(output_path),
        })

    print(json.dumps({"runs": len(results), "results": results}, indent=2, sort_keys=True))


def build_plan(
    entries: list[ModelRegistryEntry],
    harnesses: list[str],
    tier_filter: set[str] | None,
    model_id_filter: set[str] | None,
) -> list[tuple[ModelRegistryEntry | None, str]]:
    """Return list of (registry_entry, harness) pairs to execute."""
    filtered = entries
    if tier_filter:
        filtered = [e for e in filtered if e.tier in tier_filter]
    if model_id_filter:
        filtered = [e for e in filtered if e.model_id in model_id_filter]

    plan: list[tuple[ModelRegistryEntry | None, str]] = []
    for harness in harnesses:
        if harness in DETERMINISTIC_HARNESSES:
            plan.append((None, harness))
        else:
            for entry in filtered:
                plan.append((entry, harness))
    return plan


def _load_and_validate_registry(path: Path, allow_unfrozen: bool = False) -> list[ModelRegistryEntry]:
    entries = load_registry(path)
    errors = validate_registry(entries)
    if errors:
        raise SystemExit("Registry validation errors:\n" + "\n".join(f"  {e}" for e in errors))
    frozen_at = _extract_frozen_at(path.read_text(encoding="utf-8"))
    if not frozen_at:
        msg = f"Registry {path} has no frozen_at date. Use --allow-unfrozen to proceed anyway."
        if not allow_unfrozen:
            raise SystemExit(msg)
        print(f"WARNING: {msg}", file=sys.stderr)
    return entries


def _extract_frozen_at(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("frozen_at:"):
            return stripped.split(":", 1)[1].strip().strip("'\"")
    return ""


def _run_id(entry: ModelRegistryEntry | None, harness: str) -> str:
    model_part = _safe_id(entry.model_id) if entry else "deterministic"
    return f"matrix_{model_part}_{harness}"


def _safe_id(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", text)


def _load_manifests(harnesses: list[str], manifest_dir: Path) -> dict[str, HarnessManifest]:
    manifests: dict[str, HarnessManifest] = {}
    for harness in harnesses:
        path = manifest_dir / f"{harness}.yaml"
        if not path.exists():
            path = default_manifest_path(harness, Path.cwd())
        if not path.exists():
            continue
        manifest = load_harness_manifest(path)
        if manifest.harness_id != harness:
            raise SystemExit(f"Manifest {path} is for harness {manifest.harness_id!r}, not {harness!r}")
        manifests[harness] = manifest
    return manifests


def _plan_as_list(
    plan: list[tuple[ModelRegistryEntry | None, str]],
    manifests: dict[str, HarnessManifest] | None = None,
) -> list[dict[str, str]]:
    manifests = manifests or {}
    return [
        {
            "harness": harness,
            "model": entry.model_id if entry else "none",
            "tier": entry.tier if entry else "none",
            "manifest_id": manifests[harness].manifest_id if harness in manifests else "",
        }
        for entry, harness in plan
    ]


def _make_provider(provider_name: str, replay_path: Path | None):
    if provider_name == "replay":
        if replay_path is None:
            raise SystemExit("--replay PATH is required when --provider=replay")
        return ReplayProvider(replay_path)
    return MockProvider(responses=[_MOCK_ANCHOR_RESPONSE] * 500)


def _dispatch(
    harness: str,
    entry: ModelRegistryEntry | None,
    records: list,
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    provider,
) -> RunRecord:
    model = entry.model_id if entry else "none"
    if harness in ("single_prompt_anchor", "retrieval_anchor", "multi_agent_anchor",
                   "multi_agent_anchor_sc3", "multi_agent_anchor_sc5"):
        return run_anchor_harness(records, dataset, run_id, code_version, provider, harness=harness, model=model)
    if harness == "deterministic_baseline":
        return run_deterministic_baseline(records, dataset, run_id, code_version)
    if harness == "exect_lite_cleanroom_baseline":
        return run_exect_lite_baseline(records, dataset, run_id, code_version)
    if harness == "direct_full_contract":
        return run_direct_full_contract(records, dataset, run_id, code_version, provider, model=model)
    if harness == "single_prompt_full_contract":
        return run_single_prompt_full_contract(records, dataset, run_id, code_version, provider, model=model)
    if harness == "direct_evidence_contract":
        return run_direct_evidence_contract(records, dataset, run_id, code_version, provider, model=model)
    if harness == "retrieval_field_extractors":
        return run_retrieval_field_extractors(records, dataset, run_id, code_version, provider, model=model)
    if harness == "clines_epilepsy_modular":
        return run_clines_epilepsy_modular(records, dataset, run_id, code_version, provider, model=model)
    if harness == "clines_epilepsy_verified":
        return run_clines_epilepsy_verified(records, dataset, run_id, code_version, provider, model=model)
    if harness == "budgeted_escalation":
        return run_budgeted_escalation_harness(
            records,
            dataset,
            run_id,
            code_version,
            provider,
            provider,
            cheap_model=model,
            strong_model=model,
        )
    raise ValueError(f"Unknown harness: {harness!r}")


if __name__ == "__main__":
    main()
