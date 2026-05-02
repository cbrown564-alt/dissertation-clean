from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epilepsy_extraction.evaluation.adjudication import (
    read_adjudication_sheet,
    summarize_adjudication,
    write_adjudication_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a completed adjudication CSV.")
    parser.add_argument("adjudication_sheet", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    rows = read_adjudication_sheet(args.adjudication_sheet)
    summary = summarize_adjudication(rows)
    if args.output is not None:
        write_adjudication_summary(summary, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
