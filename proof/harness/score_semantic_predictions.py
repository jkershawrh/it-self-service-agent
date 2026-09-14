#!/usr/bin/env python3
"""Score JSONL predictions against the versioned IT semantic corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from proof_layer.evaluation import EvaluationRecord, evaluate


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("proof/corpus/it-semantic-v1.jsonl"),
    )
    parser.add_argument("--minimum-precision", type=float, default=0.80)
    parser.add_argument("--minimum-recall", type=float, default=0.80)
    parser.add_argument("--classifier")
    args = parser.parse_args()

    all_corpus_rows = load_jsonl(args.corpus)
    all_corpus_ids = {row["id"] for row in all_corpus_rows}
    corpus_rows = all_corpus_rows
    if args.classifier:
        corpus_rows = [
            row for row in corpus_rows if row["classifier_id"] == args.classifier
        ]
    corpus = {row["id"]: row for row in corpus_rows}
    predictions = load_jsonl(args.predictions)
    truly_unknown = sorted({row["id"] for row in predictions} - all_corpus_ids)
    if truly_unknown:
        raise SystemExit(f"unknown prediction IDs: {truly_unknown}")
    if args.classifier:
        predictions = [row for row in predictions if row["id"] in corpus]
    seen = {row["id"] for row in predictions}
    missing = sorted(set(corpus) - seen)
    unknown = sorted(seen - set(corpus))
    if missing or unknown:
        raise SystemExit(
            f"prediction IDs mismatch: missing={missing}, unknown={unknown}"
        )

    records = [
        EvaluationRecord(
            expected=corpus[row["id"]]["expected"],
            predicted=row.get("predicted"),
            latency_ms=float(row["latency_ms"]),
        )
        for row in predictions
    ]
    report = evaluate(records)
    result = {
        "labels": {
            label: {
                "precision": metric.precision,
                "recall": metric.recall,
                "support": metric.support,
            }
            for label, metric in report.labels.items()
        },
        "abstention_rate": report.abstention_rate,
        "p50_latency_ms": report.p50_latency_ms,
        "p95_latency_ms": report.p95_latency_ms,
        "quality_gate": report.meets(
            minimum_precision=args.minimum_precision,
            minimum_recall=args.minimum_recall,
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["quality_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
