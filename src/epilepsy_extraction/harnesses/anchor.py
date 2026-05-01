from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from typing import Any, Iterable, Literal

from epilepsy_extraction.assets import load_prompt
from epilepsy_extraction.evaluation import evaluate_prediction, parse_label, parse_validity_summary, summarize
from epilepsy_extraction.providers import (
    ChatProvider,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    budget_from_provider_responses,
)
from epilepsy_extraction.schemas import (
    DatasetSlice,
    EvidenceSpan,
    ExtractionPayload,
    FinalExtraction,
    GoldRecord,
    Prediction,
    RunRecord,
    field_coverage,
)
from epilepsy_extraction.schemas.contracts import FieldFamily


AnchorHarnessName = Literal[
    "single_prompt_anchor",
    "multi_agent_anchor",
    "multi_agent_anchor_sc3",
    "multi_agent_anchor_sc5",
]


def run_anchor_harness(
    records: Iterable[GoldRecord],
    dataset: DatasetSlice,
    run_id: str,
    code_version: str,
    provider: ChatProvider,
    *,
    harness: AnchorHarnessName,
    model: str = "mock-model",
    temperature: float = 0.0,
) -> RunRecord:
    rows: list[dict[str, Any]] = []
    evaluation_rows = []
    parse_results: list[tuple[str, bool]] = []
    responses: list[ProviderResponse] = []
    record_list = list(records)

    for record in record_list:
        prediction, row_responses = _predict_anchor(record.letter, provider, harness, model, temperature)
        responses.extend(row_responses)
        parsed_ok = prediction.parsed_monthly_rate is not None
        parse_results.append(("seizure_frequency", parsed_ok))
        evaluation = evaluate_prediction(record.source_row_index, record.gold_label, prediction)
        evaluation_rows.append(evaluation)
        payload = _payload_from_prediction(prediction, harness, record)
        rows.append(
            {
                "row_id": record.row_id,
                "source_row_index": record.source_row_index,
                "prediction": asdict(prediction),
                "payload": payload.to_dict(),
                "evaluation": asdict(evaluation),
                "provider_responses": [asdict(response) for response in row_responses],
            }
        )

    prompt = _prompt_for_harness(harness)
    return RunRecord(
        run_id=run_id,
        harness=harness,
        schema_version="1.0.0",
        dataset=dataset,
        model=model,
        provider=provider.provider_name,
        temperature=temperature,
        prompt_version=prompt.version,
        code_version=code_version,
        budget=budget_from_provider_responses(responses, rows=len(record_list)),
        field_coverage=field_coverage(implemented=[FieldFamily.SEIZURE_FREQUENCY]),
        metrics=summarize(evaluation_rows),
        rows=rows,
        parse_validity=parse_validity_summary(parse_results),
        artifact_paths={"prompt": prompt.path},
    )


def _predict_anchor(
    letter: str,
    provider: ChatProvider,
    harness: AnchorHarnessName,
    model: str,
    temperature: float,
) -> tuple[Prediction, list[ProviderResponse]]:
    if harness == "single_prompt_anchor":
        response = _call_provider(provider, "anchor_single", letter, model, temperature)
        return _prediction_from_response(response, letter), [response]

    if harness == "multi_agent_anchor":
        extractor = _call_provider(provider, "anchor_multi_extractor", letter, model, temperature)
        verifier = _call_provider(
            provider,
            "anchor_multi_verifier",
            letter,
            model,
            temperature,
            context=extractor.content,
        )
        return _prediction_from_response(verifier, letter), [extractor, verifier]

    samples = 3 if harness == "multi_agent_anchor_sc3" else 5
    sample_predictions: list[Prediction] = []
    responses: list[ProviderResponse] = []
    for _ in range(samples):
        response = _call_provider(provider, "anchor_single", letter, model, temperature)
        responses.append(response)
        sample_predictions.append(_prediction_from_response(response, letter))
    return _majority_prediction(sample_predictions), responses


def _call_provider(
    provider: ChatProvider,
    prompt_id: str,
    letter: str,
    model: str,
    temperature: float,
    *,
    context: str | None = None,
) -> ProviderResponse:
    prompt = load_prompt(prompt_id)
    content = f"{prompt.content}\n\nClinic letter:\n{letter}"
    if context:
        content = f"{content}\n\nPrior agent output:\n{context}"
    return provider.complete(
        ProviderRequest(
            messages=[ProviderMessage(role="user", content=content)],
            model=model,
            temperature=temperature,
            response_format="json",
            metadata={"prompt_id": prompt_id, "prompt_version": prompt.version},
        )
    )


def _prediction_from_response(response: ProviderResponse, letter: str) -> Prediction:
    if not response.ok:
        return _invalid_prediction(["provider_error"])
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        return _invalid_prediction(["invalid_json"])

    label = str(data.get("label") or "unknown")
    evidence = str(data.get("evidence") or "")
    warnings = [str(warning) for warning in data.get("warnings", [])]
    if label.strip().lower() in {"", "abstain", "unknown"}:
        label = "unknown"
        warnings.append("abstained_or_unknown")
    if evidence and evidence not in letter:
        warnings.append("unsupported_evidence")
    parsed = parse_label(label)
    return Prediction(
        label=label,
        evidence=[EvidenceSpan(quote=evidence)] if evidence else [],
        confidence=float(data.get("confidence", 0.0) or 0.0),
        parsed_monthly_rate=parsed.monthly_rate,
        pragmatic_class=parsed.pragmatic_class,
        purist_class=parsed.purist_class,
        warnings=warnings,
        metadata={"provider": response.provider, "model": response.model},
    )


def _invalid_prediction(warnings: list[str]) -> Prediction:
    return Prediction(
        label="unknown",
        confidence=0.0,
        parsed_monthly_rate=parse_label("unknown").monthly_rate,
        pragmatic_class="UNK",
        purist_class="UNK",
        warnings=warnings,
    )


def _majority_prediction(predictions: list[Prediction]) -> Prediction:
    counts = Counter(prediction.label for prediction in predictions)
    label, _ = counts.most_common(1)[0]
    winner = next(prediction for prediction in predictions if prediction.label == label)
    return Prediction(
        label=winner.label,
        evidence=winner.evidence,
        confidence=sum(prediction.confidence for prediction in predictions if prediction.label == label)
        / counts[label],
        parsed_monthly_rate=winner.parsed_monthly_rate,
        pragmatic_class=winner.pragmatic_class,
        purist_class=winner.purist_class,
        warnings=winner.warnings + [f"self_consistency_samples={len(predictions)}"],
        metadata={"vote_counts": dict(counts)},
    )


def _payload_from_prediction(prediction: Prediction, harness: str, record: GoldRecord) -> ExtractionPayload:
    return ExtractionPayload(
        pipeline_id=harness,
        final=FinalExtraction(
            seizure_frequency={
                "value": prediction.label,
                "parsed_monthly_rate": prediction.parsed_monthly_rate,
                "pragmatic_class": prediction.pragmatic_class,
                "purist_class": prediction.purist_class,
            },
            citations=[asdict(span) for span in prediction.evidence],
            confidence={"seizure_frequency": prediction.confidence},
            warnings=prediction.warnings,
        ),
        field_coverage=field_coverage(implemented=[FieldFamily.SEIZURE_FREQUENCY]),
        invalid_output=prediction.parsed_monthly_rate is None,
        warnings=prediction.warnings,
        metadata={"source_row_index": record.source_row_index},
    )


def _prompt_for_harness(harness: AnchorHarnessName):
    if harness == "multi_agent_anchor":
        return load_prompt("anchor_multi_verifier")
    return load_prompt("anchor_single")
