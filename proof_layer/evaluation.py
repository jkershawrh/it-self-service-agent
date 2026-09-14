"""Deterministic quality and latency scoring for semantic classifications."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Mapping


@dataclass(frozen=True)
class EvaluationRecord:
    expected: str
    predicted: str | None
    latency_ms: float


@dataclass(frozen=True)
class LabelMetrics:
    precision: float
    recall: float
    support: int


@dataclass(frozen=True)
class EvaluationReport:
    labels: Mapping[str, LabelMetrics]
    abstention_rate: float
    p50_latency_ms: float
    p95_latency_ms: float

    def meets(self, *, minimum_precision: float, minimum_recall: float) -> bool:
        return bool(self.labels) and all(
            metric.precision >= minimum_precision and metric.recall >= minimum_recall
            for metric in self.labels.values()
        )


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def evaluate(records: Iterable[EvaluationRecord]) -> EvaluationReport:
    rows = list(records)
    if not rows:
        raise ValueError("evaluation requires at least one record")
    if any(row.latency_ms < 0 for row in rows):
        raise ValueError("latency cannot be negative")

    labels = sorted({row.expected.upper() for row in rows})
    metrics: dict[str, LabelMetrics] = {}
    for label in labels:
        true_positive = sum(
            row.expected.upper() == label and (row.predicted or "").upper() == label
            for row in rows
        )
        predicted_positive = sum((row.predicted or "").upper() == label for row in rows)
        support = sum(row.expected.upper() == label for row in rows)
        metrics[label] = LabelMetrics(
            precision=(
                true_positive / predicted_positive if predicted_positive else 0.0
            ),
            recall=true_positive / support,
            support=support,
        )

    latencies = [row.latency_ms for row in rows]
    return EvaluationReport(
        labels=metrics,
        abstention_rate=sum(row.predicted is None for row in rows) / len(rows),
        p50_latency_ms=median(latencies),
        p95_latency_ms=_percentile(latencies, 0.95),
    )
