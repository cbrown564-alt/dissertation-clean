"""
Auto-adjudicate seizure_frequency rows using gold labels from the synthetic dataset.

Comparison strategy (in order):
  1. If emitted value is null/empty/unknown → score=0
  2. If parse_label succeeds on both emitted and gold → compare pragmatic classes
  3. Otherwise → LLM judge (GPT-5.4-mini) to assess semantic equivalence

Non-SF rows are passed through with reference_value filled but score left blank
(pending human review).

Usage:
  python scripts/auto_adjudicate.py \\
    --adjudication results/adjudication/architecture_ladder_n25_real_provider_2026_05_08.csv \\
    --dataset data/synthetic_data_subset_1500.json \\
    --output results/adjudication/architecture_ladder_n25_real_provider_2026_05_08_adjudicated.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epilepsy_extraction.data import load_synthetic_subset
from epilepsy_extraction.evaluation import parse_label
from epilepsy_extraction.providers import OpenAIProvider
from epilepsy_extraction.providers.base import ProviderMessage, ProviderRequest

_JUDGE_MODEL = "gpt-5.4-mini-2026-03-17"
_NULL_VALUES = {"", "null", "none", "unknown", "not stated", "not reported", "not documented"}

_JUDGE_SYSTEM = (
    "You are a clinical adjudicator comparing a model's extracted seizure frequency "
    "against a gold standard label. Reply with JSON only: "
    '{"score": "1"|"0.5"|"0", "note": "<one sentence reason>"}. '
    "Score 1 = semantically equivalent, 0.5 = partially correct (right order of magnitude "
    "but wrong specifics), 0 = wrong or cannot be evaluated."
)


def _is_null(value: str) -> bool:
    return value.strip().lower() in _NULL_VALUES or value.strip().startswith("{")


def _rule_compare(emitted: str, gold: str) -> tuple[str, str] | None:
    """Return (score, note) if both labels parse cleanly, else None."""
    try:
        gold_p = parse_label(gold)
        emitted_p = parse_label(emitted)
    except Exception:
        return None
    if gold_p.pragmatic_class == "UNK" or emitted_p.pragmatic_class == "UNK":
        return None
    if gold_p.pragmatic_class == emitted_p.pragmatic_class:
        return "1", f"pragmatic class match ({gold_p.pragmatic_class})"
    return "0", f"pragmatic mismatch: extracted={emitted_p.pragmatic_class} gold={gold_p.pragmatic_class}"


def _llm_judge(emitted: str, gold: str, provider: OpenAIProvider) -> tuple[str, str]:
    prompt = (
        f"Gold label: {gold}\n"
        f"Extracted value: {emitted}\n"
        "Do these describe the same seizure frequency?"
    )
    req = ProviderRequest(
        messages=[
            ProviderMessage(role="system", content=_JUDGE_SYSTEM),
            ProviderMessage(role="user", content=prompt),
        ],
        model=_JUDGE_MODEL,
        temperature=0.0,
        response_format="json",
    )
    resp = provider.complete(req)
    if not resp.ok:
        return "0", f"judge_error: {resp.error.type}"
    try:
        data = json.loads(resp.content)
        return str(data.get("score", "0")), str(data.get("note", ""))
    except Exception:
        return "0", "judge_parse_error"


def adjudicate_sf_row(
    emitted: str,
    gold: str,
    provider: OpenAIProvider,
) -> tuple[str, str, str]:
    """Return (reference_value, value_score, adjudicator_note)."""
    if _is_null(emitted):
        return gold, "0", "null or missing extraction"
    rule = _rule_compare(emitted, gold)
    if rule is not None:
        return gold, rule[0], rule[1]
    score, note = _llm_judge(emitted, gold, provider)
    return gold, score, f"llm_judge: {note}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adjudication", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default=_JUDGE_MODEL)
    args = parser.parse_args()

    # Build gold label index
    records = load_synthetic_subset(args.dataset)
    gold_index: dict[str, str] = {str(r.row_id): r.gold_label for r in records}

    provider = OpenAIProvider()

    with open(args.adjudication, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) if rows else []

    total_sf = sum(1 for r in rows if r["field_family"] == "seizure_frequency")
    done = 0

    output_rows = []
    for row in rows:
        row = dict(row)
        if row["field_family"] == "seizure_frequency":
            gold = gold_index.get(str(row["row_id"]), "")
            if gold:
                ref, score, note = adjudicate_sf_row(row["emitted_value"], gold, provider)
                row["reference_value"] = ref
                row["value_score"] = score
                row["adjudicator_note"] = note
            done += 1
            if done % 25 == 0:
                print(f"  SF adjudicated: {done}/{total_sf}", file=sys.stderr)
        output_rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    sf_scored = sum(1 for r in output_rows if r["field_family"] == "seizure_frequency" and r.get("value_score"))
    print(json.dumps({
        "output": str(args.output),
        "total_rows": len(output_rows),
        "sf_rows_adjudicated": sf_scored,
        "other_rows_passthrough": len(output_rows) - total_sf,
    }, indent=2))


if __name__ == "__main__":
    main()
