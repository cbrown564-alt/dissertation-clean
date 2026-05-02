from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epilepsy_extraction.evaluation.tables import build_result_tables, load_run_records, write_result_tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize run records and generate result tables.")
    parser.add_argument("run_record", type=Path, nargs="+")
    parser.add_argument(
        "--tables-dir",
        type=Path,
        default=None,
        help="Write Phase 9 JSON/CSV result tables to this directory.",
    )
    parser.add_argument(
        "--model-registry",
        type=Path,
        default=None,
        help="Optional model registry YAML used to populate model-family tables.",
    )
    args = parser.parse_args()

    records = load_run_records(args.run_record)
    if args.tables_dir is not None:
        tables = build_result_tables(records, model_registry_path=args.model_registry)
        written = write_result_tables(tables, args.tables_dir)
        summary = {
            "run_records": len(records),
            "tables_dir": str(args.tables_dir),
            "tables": sorted({path.stem for path in written}),
            "files_written": [str(path) for path in written],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    data = records[0]
    summary = {
        "run_id": data["run_id"],
        "harness": data["harness"],
        "status": data["status"],
        "n": data["dataset"]["n"],
        "provider": data["provider"],
        "model": data["model"],
        "warnings": data["warnings"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
