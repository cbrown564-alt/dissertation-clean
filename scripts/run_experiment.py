from __future__ import annotations

import argparse
from pathlib import Path

from epilepsy_extraction.data import compute_file_sha256, load_synthetic_subset, select_fixed_slice
from epilepsy_extraction.schemas import BudgetMetadata, DatasetSlice, RunRecord, write_run_record


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a metadata-only smoke run for a fixed synthetic slice.",
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--run-id", default="smoke_fixed_slice")
    parser.add_argument("--output", type=Path, default=Path("results/runs/smoke_fixed_slice.json"))
    args = parser.parse_args()

    records = load_synthetic_subset(args.dataset)
    selected = select_fixed_slice(records, limit=args.limit)
    row_ids = [record.row_id for record in selected]

    record = RunRecord(
        run_id=args.run_id,
        harness="metadata_smoke",
        schema_version="1.0.0",
        dataset=DatasetSlice(
            dataset_id=args.dataset.stem,
            dataset_path=str(args.dataset),
            data_hash=compute_file_sha256(args.dataset),
            row_ids=row_ids,
            inclusion_criteria=f"row_ok_only=true; limit={args.limit}",
        ),
        model="none",
        provider="deterministic",
        temperature=0.0,
        prompt_version="none",
        code_version="uncommitted",
        budget=BudgetMetadata(),
        warnings=["metadata_only_run_no_extraction"],
    )
    write_run_record(record, args.output)


if __name__ == "__main__":
    main()
