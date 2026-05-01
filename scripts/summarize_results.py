from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize run-record metadata.")
    parser.add_argument("run_record", type=Path)
    args = parser.parse_args()

    data = json.loads(args.run_record.read_text(encoding="utf-8"))
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
