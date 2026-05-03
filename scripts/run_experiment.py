from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    load_exect_v2_outputs,
    run_exect_lite_baseline,
    run_exect_v2_external_baseline,
    run_retrieval_field_extractors,
    run_single_prompt_full_contract,
)
from epilepsy_extraction.providers import ReplayProvider
from epilepsy_extraction.schemas import BudgetMetadata, DatasetSlice, RunRecord, RunStatus, resolve_code_version, write_run_record


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a metadata-only smoke run for a fixed synthetic slice.",
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument(
        "--harness",
        choices=[
            "metadata_smoke",
            "deterministic_baseline",
            "exect_lite_cleanroom_baseline",
            "exect_v2_external_baseline",
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
        ],
        default="metadata_smoke",
    )
    parser.add_argument("--run-id", default="smoke_fixed_slice")
    parser.add_argument("--output", type=Path, default=Path("results/runs/smoke_fixed_slice.json"))
    parser.add_argument("--code-version", default=None)
    parser.add_argument(
        "--status",
        choices=[item.value for item in RunStatus],
        default=RunStatus.SMOKE.value,
        help="Evidence status label written to the run record.",
    )
    parser.add_argument("--replay", type=Path, default=None)
    parser.add_argument(
        "--exect-v2-output",
        type=Path,
        default=None,
        help="Pre-generated ExECTv2 JSON output for exect_v2_external_baseline.",
    )
    parser.add_argument("--exect-v2-source-commit", default="")
    parser.add_argument("--exect-v2-gate-version", default="")
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--model-registry-entry",
        default=None,
        help="Frozen model registry entry ID to attach to the run record.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Harness manifest path. Defaults to config/harnesses/<harness>.yaml when present.",
    )
    args = parser.parse_args()

    manifest_path = args.manifest or default_manifest_path(args.harness, Path.cwd())
    if args.manifest is not None and not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    manifest = load_harness_manifest(manifest_path) if manifest_path.exists() else None
    if manifest is not None and manifest.harness_id != args.harness:
        raise SystemExit(
            f"Manifest {manifest_path} is for harness {manifest.harness_id!r}, not {args.harness!r}"
        )
    model = args.model or (manifest.model_registry_entry if manifest and manifest.model_registry_entry else "mock-model")

    records = load_synthetic_subset(args.dataset)
    selected = select_fixed_slice(records, limit=args.limit)
    row_ids = [record.row_id for record in selected]

    dataset = DatasetSlice(
        dataset_id=args.dataset.stem,
        dataset_path=str(args.dataset),
        data_hash=compute_file_sha256(args.dataset),
        row_ids=row_ids,
        inclusion_criteria=f"row_ok_only=true; limit={args.limit}",
    )

    code_version = resolve_code_version(args.code_version, cwd=Path.cwd(), fallback="uncommitted")
    if args.harness == "exect_lite_cleanroom_baseline":
        record = run_exect_lite_baseline(selected, dataset, args.run_id, code_version)
    elif args.harness == "exect_v2_external_baseline":
        if args.exect_v2_output is None:
            raise SystemExit("--exect-v2-output is required for exect_v2_external_baseline")
        record = run_exect_v2_external_baseline(
            selected,
            dataset,
            args.run_id,
            code_version,
            load_exect_v2_outputs(args.exect_v2_output),
            source_commit=args.exect_v2_source_commit,
            gate_version=args.exect_v2_gate_version,
        )
    elif args.harness == "deterministic_baseline":
        record = run_deterministic_baseline(selected, dataset, args.run_id, code_version)
    elif args.harness.endswith("_anchor") or "_anchor_sc" in args.harness:
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed anchor harnesses")
        record = run_anchor_harness(
            selected,
            dataset,
            args.run_id,
            code_version,
            ReplayProvider(args.replay),
            harness=args.harness,
            model=model,
        )
    elif args.harness == "direct_full_contract":
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed full-contract harnesses")
        record = run_direct_full_contract(
            selected,
            dataset,
            args.run_id,
            code_version,
            ReplayProvider(args.replay),
            model=model,
        )
    elif args.harness == "single_prompt_full_contract":
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed full-contract harnesses")
        record = run_single_prompt_full_contract(
            selected,
            dataset,
            args.run_id,
            code_version,
            ReplayProvider(args.replay),
            model=model,
        )
    elif args.harness == "direct_evidence_contract":
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed harnesses")
        record = run_direct_evidence_contract(
            selected,
            dataset,
            args.run_id,
            code_version,
            ReplayProvider(args.replay),
            model=model,
        )
    elif args.harness == "retrieval_field_extractors":
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed harnesses")
        record = run_retrieval_field_extractors(
            selected,
            dataset,
            args.run_id,
            code_version,
            ReplayProvider(args.replay),
            model=model,
        )
    elif args.harness == "clines_epilepsy_modular":
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed harnesses")
        record = run_clines_epilepsy_modular(
            selected,
            dataset,
            args.run_id,
            code_version,
            ReplayProvider(args.replay),
            model=model,
        )
    elif args.harness == "clines_epilepsy_verified":
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed harnesses")
        record = run_clines_epilepsy_verified(
            selected,
            dataset,
            args.run_id,
            code_version,
            ReplayProvider(args.replay),
            model=model,
        )
    elif args.harness == "budgeted_escalation":
        if args.replay is None:
            raise SystemExit("--replay is required for provider-backed harnesses")
        provider = ReplayProvider(args.replay)
        record = run_budgeted_escalation_harness(
            selected,
            dataset,
            args.run_id,
            code_version,
            provider,
            provider,
            cheap_model=model,
            strong_model=model,
        )
    else:
        record = RunRecord(
            run_id=args.run_id,
            harness="metadata_smoke",
            schema_version="1.0.0",
            dataset=dataset,
            model="none",
            provider="deterministic",
            temperature=0.0,
            prompt_version="none",
            code_version=code_version,
            budget=BudgetMetadata(),
            warnings=["metadata_only_run_no_extraction"],
        )
    if record.status.value != args.status or args.model_registry_entry:
        from dataclasses import replace

        record = replace(
            record,
            status=RunStatus(args.status),
            model_registry_entry=args.model_registry_entry or record.model_registry_entry,
        )
    record = attach_manifest_to_run(record, manifest)
    write_run_record(record, args.output)


if __name__ == "__main__":
    main()
