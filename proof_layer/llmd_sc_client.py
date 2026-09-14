"""Typed gRPC adapter for the pinned llm-d-sc Classify contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import grpc

from proof_layer.generated import classify_pb2, classify_pb2_grpc
from proof_layer.semantic_policy import SemanticEvidence


@dataclass(frozen=True)
class ClassificationRequest:
    request_id: str
    session_id: str
    context: str
    signals: Sequence[str]


class LlmdScClient:
    """Long-lived llm-d-sc client with bounded calls and normalized results."""

    def __init__(self, target: str, *, timeout_seconds: float = 1.0) -> None:
        if not target.strip():
            raise ValueError("llm-d-sc target must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout_seconds = timeout_seconds
        self._channel = grpc.insecure_channel(target)
        self._stub = classify_pb2_grpc.ClassifyStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def classify(self, request: ClassificationRequest) -> SemanticEvidence:
        wire_request = classify_pb2.ClassifyRequest(  # type: ignore[attr-defined]
            request_id=request.request_id,
            session_id=request.session_id,
            context=request.context,
            signals=request.signals,
        )
        try:
            response = self._stub.Classify(
                wire_request,
                timeout=self._timeout_seconds,
            )
        except grpc.RpcError:
            return SemanticEvidence.from_mapping(
                {
                    "request_id": request.request_id,
                    "classifier_id": "llm-d-sc",
                    "model_revision": "unavailable",
                    "tokenizer_revision": "unavailable",
                    "taxonomy_revision": "unavailable",
                    "status": "UNAVAILABLE",
                    "ranked": [],
                }
            )

        status = classify_pb2.ClassificationStatus.Name(  # type: ignore[attr-defined]
            response.status
        )
        return SemanticEvidence.from_mapping(
            {
                "request_id": response.request_id,
                "classifier_id": response.classifier_id,
                "model_revision": response.model_revision,
                "tokenizer_revision": response.tokenizer_revision,
                "taxonomy_revision": response.taxonomy_revision,
                "status": status,
                "ranked": [
                    {"label": signal.label, "score": signal.score}
                    for signal in response.ranked
                ],
            }
        )

    def __enter__(self) -> "LlmdScClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
