"""
Build letter-explorer-data.json for the cockpit letter explorer panel.

Extracts one representative letter (row_id 11118) with all available run
records' extracted fields, evidence quotes, pipeline events, and adjudication
scores, packed into a single JSON the browser can load on demand.

Usage:
  python scripts/build_letter_explorer_data.py \\
    --row-id 11118 \\
    --dataset data/synthetic_data_subset_1500.json \\
    --adjudication results/adjudication/architecture_ladder_n25_real_provider_2026_05_08_adjudicated.csv \\
    --adjudication results/adjudication/gpt55_verified_n25_2026_05_09_adjudicated.csv \\
    --output site/letter-explorer-data.json \\
    results/runs/model_family/architecture_ladder_n25_2026_05_08/*.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from epilepsy_extraction.data import load_synthetic_subset

_FIELD_ORDER = [
    "seizure_frequency",
    "current_medications",
    "investigations",
    "seizure_classification",
    "epilepsy_classification",
]

_FIELD_LABELS = {
    "seizure_frequency":     "Seizure Frequency",
    "current_medications":   "Current Medications",
    "investigations":        "Investigations",
    "seizure_classification":"Seizure Classification",
    "epilepsy_classification":"Epilepsy Classification",
}

_MODEL_SHORT = {
    "gpt-5.5-2026-04-23":       "GPT-5.5",
    "gpt-5.4-mini-2026-03-17":  "GPT-5.4 mini",
}

_HARNESS_LABELS = {
    "direct_full_contract":        "Direct (full contract)",
    "direct_evidence_contract":    "Direct (evidence contract)",
    "retrieval_field_extractors":  "Retrieval + field extraction",
    "clines_epilepsy_modular":     "Modular pipeline",
    "clines_epilepsy_verified":    "Modular + LLM verifier",
}

_STAGE_LABELS = {
    "context_built":            "Context built",
    "candidate_spans_selected": "Candidate spans selected",
    "provider_call_started":    "LLM call started",
    "provider_call_finished":   "LLM call finished",
    "parse_attempted":          "Output parsed",
    "verification_completed":   "Verification",
    "field_extraction_completed":"Field extraction done",
    "aggregation_completed":    "Aggregation",
    "warning_emitted":          "Warning",
    "budget_limit_hit":         "Budget limit hit",
}


def _extract_row(record: dict, row_id: str) -> dict | None:
    for row in record.get("rows", []):
        if str(row.get("row_id")) == str(row_id):
            return row
    return None


def _field_items(payload: dict) -> list[dict]:
    """Flatten final payload into list of {family, value, evidence, confidence, warnings}."""
    final = payload.get("final") or {}
    items = []

    def _add(family: str, value_obj):
        if value_obj is None:
            return
        if isinstance(value_obj, list):
            for v in value_obj:
                _add(family, v)
            return
        if isinstance(value_obj, dict):
            val = (value_obj.get("value") or value_obj.get("label") or
                   value_obj.get("name") or value_obj.get("type") or
                   value_obj.get("normalized_value") or "")
            if not val:
                val = None
            ev = value_obj.get("evidence") or ""
            if isinstance(ev, dict):
                ev = ev.get("quote", "")
            conf = value_obj.get("confidence")
            warn = value_obj.get("warnings") or []
        else:
            val = str(value_obj)
            ev = ""
            conf = None
            warn = []
        items.append({
            "family": family,
            "value": val,
            "evidence": str(ev) if ev else "",
            "confidence": conf,
            "warnings": warn,
        })

    sf = final.get("seizure_frequency")
    if sf:
        _add("seizure_frequency", sf)

    for med in (final.get("current_medications") or []):
        _add("current_medications", med)

    for inv in (final.get("investigations") or []):
        _add("investigations", inv)

    for st in (final.get("seizure_types") or []):
        _add("seizure_classification", st)
    for sf2 in (final.get("seizure_features") or []):
        _add("seizure_classification", sf2)
    for spm in (final.get("seizure_pattern_modifiers") or []):
        _add("seizure_classification", spm)

    for et in ([final.get("epilepsy_type")] if final.get("epilepsy_type") else []):
        _add("epilepsy_classification", et)
    for es in ([final.get("epilepsy_syndrome")] if final.get("epilepsy_syndrome") else []):
        _add("epilepsy_classification", es)

    return items


def _pipeline_stages(harness_events: list[dict]) -> list[dict]:
    """Summarise harness events into pipeline stage steps for display."""
    stages = []
    for ev in harness_events:
        etype = ev.get("event_type", "")
        label = _STAGE_LABELS.get(etype, etype)
        component = ev.get("component", "")
        metrics = ev.get("metrics") or {}
        summary = ev.get("summary", "")
        error = ev.get("error", "")
        warnings = ev.get("warnings") or []
        stages.append({
            "type": etype,
            "label": label,
            "component": component,
            "summary": summary,
            "metrics": metrics,
            "error": error,
            "warnings": warnings,
        })
    return stages


def _load_adjudication(paths: list[Path], row_id: str) -> dict[tuple[str, str, int], str]:
    """Return {(run_id, field_family, item_index): value_score}."""
    result: dict[tuple[str, str, int], str] = {}
    for path in paths:
        if not path.exists():
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if str(row.get("row_id")) != str(row_id):
                    continue
                key = (row["run_id"], row["field_family"], int(row.get("item_index", 0)))
                result[key] = row.get("value_score", "")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_records", type=Path, nargs="+")
    parser.add_argument("--row-id", default="11118")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path, action="append", default=None)
    parser.add_argument("--output", type=Path, default=Path("site/letter-explorer-data.json"))
    args = parser.parse_args()

    records_map = load_synthetic_subset(args.dataset)
    gold_record = next((r for r in records_map if str(r.row_id) == str(args.row_id)), None)
    if not gold_record:
        sys.exit(f"Row {args.row_id} not found in dataset")

    adj_scores = _load_adjudication(args.adjudication or [], args.row_id)

    runs_out = []
    for path in sorted(args.run_records):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Skip empty/failed runs
        budget = record.get("budget") or {}
        if int(budget.get("total_tokens", 0)) == 0:
            continue

        row = _extract_row(record, args.row_id)
        if not row:
            continue

        harness = record.get("harness", "")
        model = record.get("model", "")
        run_id = record.get("run_id", "")

        payload = row.get("payload") or {}
        items = _field_items(payload)

        # Attach adjudication scores
        family_counters: dict[str, int] = {}
        for item in items:
            fam = item["family"]
            idx = family_counters.get(fam, 0)
            family_counters[fam] = idx + 1
            score = adj_scores.get((run_id, fam, idx), "")
            item["score"] = score

        events = row.get("harness_events") or []
        pipeline = _pipeline_stages(events)

        runs_out.append({
            "run_id": run_id,
            "harness": harness,
            "harness_label": _HARNESS_LABELS.get(harness, harness),
            "model": model,
            "model_short": _MODEL_SHORT.get(model, model),
            "picker_label": f"{_MODEL_SHORT.get(model, model)} — {_HARNESS_LABELS.get(harness, harness)}",
            "budget": {
                "llm_calls_per_row": budget.get("llm_calls_per_row", 0),
                "total_tokens": budget.get("total_tokens", 0),
                "latency_ms": budget.get("latency_ms", 0),
                "estimated_cost_usd": budget.get("estimated_cost_usd", 0),
            },
            "fields": items,
            "pipeline": pipeline,
        })

    # Sort: GPT-5.5 first, then mini; within each model by harness complexity
    _harness_order = list(_HARNESS_LABELS.keys())
    runs_out.sort(key=lambda r: (
        0 if "5.5" in r["model"] else 1,
        _harness_order.index(r["harness"]) if r["harness"] in _harness_order else 99,
    ))

    output = {
        "row_id": args.row_id,
        "letter": gold_record.letter,
        "gold_label_sf": gold_record.gold_label,
        "field_order": _FIELD_ORDER,
        "field_labels": _FIELD_LABELS,
        "runs": runs_out,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "row_id": args.row_id,
        "runs": len(runs_out),
        "letter_chars": len(gold_record.letter),
    }, indent=2))


if __name__ == "__main__":
    main()
