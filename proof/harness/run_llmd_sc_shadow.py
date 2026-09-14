#!/usr/bin/env python3
"""Run one llm-d-sc instance against its slice of the IT proof corpus."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path

from proof_layer.llmd_sc_client import ClassificationRequest, LlmdScClient


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--classifier", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("proof/corpus/it-semantic-v1.jsonl"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    args = parser.parse_args()

    rows = [
        row
        for row in load_jsonl(args.corpus)
        if row["classifier_id"] == args.classifier
    ]
    if not rows:
        raise SystemExit(f"no corpus rows for classifier {args.classifier!r}")

    results = []
    with LlmdScClient(args.target, timeout_seconds=args.timeout_seconds) as client:
        for row in rows:
            started = time.perf_counter()
            evidence = client.classify(
                ClassificationRequest(
                    request_id=str(uuid.uuid4()),
                    session_id="it-semantic-shadow-v1",
                    context=row["prompt"],
                    signals=(args.classifier,),
                )
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if evidence.classifier_id != args.classifier:
                raise SystemExit(
                    f"expected classifier {args.classifier!r}, "
                    f"received {evidence.classifier_id!r}"
                )
            results.append(
                {
                    "id": row["id"],
                    "predicted": (
                        evidence.top_label if evidence.status == "OK" else None
                    ),
                    "latency_ms": round(latency_ms, 3),
                    "status": evidence.status,
                    "margin": evidence.margin,
                    "model_revision": evidence.model_revision,
                    "taxonomy_revision": evidence.taxonomy_revision,
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for result in results:
            stream.write(json.dumps(result, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
