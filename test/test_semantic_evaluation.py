"""EDD tests for semantic quality gates."""

import pytest

from proof_layer.evaluation import EvaluationRecord, evaluate


def test_report_scores_each_label_abstention_and_latency() -> None:
    report = evaluate(
        [
            EvaluationRecord("SIMPLE", "SIMPLE", 10),
            EvaluationRecord("SIMPLE", None, 20),
            EvaluationRecord("REASONING", "REASONING", 30),
            EvaluationRecord("REASONING", "SIMPLE", 40),
        ]
    )

    assert report.labels["SIMPLE"].precision == pytest.approx(0.5)
    assert report.labels["SIMPLE"].recall == pytest.approx(0.5)
    assert report.labels["REASONING"].precision == pytest.approx(1.0)
    assert report.labels["REASONING"].recall == pytest.approx(0.5)
    assert report.abstention_rate == pytest.approx(0.25)
    assert report.p50_latency_ms == pytest.approx(25)
    assert report.p95_latency_ms == pytest.approx(38.5)


def test_quality_gate_requires_every_expected_label_to_pass() -> None:
    report = evaluate(
        [
            EvaluationRecord("SIMPLE", "SIMPLE", 10),
            EvaluationRecord("REASONING", "SIMPLE", 10),
        ]
    )

    assert not report.meets(minimum_precision=0.8, minimum_recall=0.8)


def test_empty_evaluation_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        evaluate([])
