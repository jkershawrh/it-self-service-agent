"""Live loopback gRPC tests for the llm-d-sc adapter."""

from concurrent import futures
from contextlib import contextmanager
from typing import Iterator

import grpc

from proof_layer.generated import classify_pb2, classify_pb2_grpc
from proof_layer.llmd_sc_client import ClassificationRequest, LlmdScClient


class Classifier(classify_pb2_grpc.ClassifyServicer):
    def Classify(self, request, context):  # noqa: N802, ANN001, ANN201
        return classify_pb2.ClassifyResponse(
            request_id=request.request_id,
            classifier_id="complexity",
            model_revision="model-v1",
            tokenizer_revision="tokenizer-v1",
            taxonomy_revision="it-proof-v1",
            status=classify_pb2.OK,
            ranked=[
                classify_pb2.RankedSignal(label="REASONING", score=0.91),
                classify_pb2.RankedSignal(label="SIMPLE", score=0.12),
            ],
        )


@contextmanager
def classifier_server() -> Iterator[str]:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    classify_pb2_grpc.add_ClassifyServicer_to_server(Classifier(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    try:
        yield f"127.0.0.1:{port}"
    finally:
        server.stop(grace=None).wait()


def request() -> ClassificationRequest:
    return ClassificationRequest(
        request_id="req-live-1",
        session_id="session-1",
        context="Diagnose a recurring production outage across services.",
        signals=("complexity",),
    )


def test_live_grpc_round_trip_normalizes_versioned_evidence() -> None:
    with classifier_server() as target, LlmdScClient(target) as client:
        evidence = client.classify(request())

    assert evidence.request_id == "req-live-1"
    assert evidence.status == "OK"
    assert evidence.top_label == "REASONING"
    assert evidence.taxonomy_revision == "it-proof-v1"


def test_unreachable_classifier_returns_explicit_unavailable_evidence() -> None:
    with LlmdScClient("127.0.0.1:1", timeout_seconds=0.05) as client:
        evidence = client.classify(request())

    assert evidence.status == "UNAVAILABLE"
    assert evidence.request_id == "req-live-1"
    assert evidence.ranked == ()
