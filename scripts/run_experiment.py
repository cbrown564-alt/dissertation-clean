from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.harnesses import (
    run_anchor_harness,
    run_deterministic_baseline,
    run_single_prompt_full_contract,
)
from epilepsy_extraction.providers import ReplayProvider
from epilepsy_extraction.schemas import BudgetMetadata, DatasetSlice, RunRecord, resolve_code_version, write_run_record


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
            "single_prompt_anchor",
            "multi_agent_anchor",
            "multi_agent_anchor_sc3",
            "multi_agent_anchor_sc5",
            "single_prompt_full_contract",
        ],
        default="metadata_smoke",
    )
    parser.add_argument("--run-id", default="smoke_fixed_slice")
    parser.add_argument("--output", type=Path, default=Path("results/runs/smoke_fixed_slice.json"))
    parser.add_argument("--code-version", default=None)
    parser.add_argument("--replay", type=Path, default=None)
    parser.add_argument("--model", default="mock-model")
    args = parser.parse_args()

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
    if args.harness == "deterministic_baseline":
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
            model=args.model,
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
            model=args.model,
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
    write_run_record(record, args.output)


if __name__ == "__main__":
    main()
