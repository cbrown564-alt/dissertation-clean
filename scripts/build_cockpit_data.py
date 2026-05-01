from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a minimal cockpit data payload from docs and run records.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("site/cockpit-data.json"))
    args = parser.parse_args()

    root = args.repo_root
    runs = sorted((root / "results" / "runs").glob("**/*.json"))
    payload = {
        "research_question": str(root / "docs" / "research_question.md"),
        "evaluation_contract": str(root / "docs" / "evaluation_contract.md"),
        "adjudication_protocol": str(root / "docs" / "adjudication_protocol.md"),
        "architecture": str(root / "docs" / "architecture.md"),
        "run_records": [str(path) for path in runs],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
