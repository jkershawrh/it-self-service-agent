"""Contract and capability tests for the Praxis + llm-d-sc proof layer."""

import pytest

from proof_layer.semantic_policy import (
    ContractError,
    RoutingPolicy,
    SemanticEvidence,
    apply_shadow_classification,
)


def evidence_payload(*, label: str = "SIMPLE", status: str = "OK") -> dict:
    return {
        "request_id": "req-123",
        "classifier_id": "complexity",
        "model_revision": "model-v1",
        "tokenizer_revision": "tokenizer-v1",
        "taxonomy_revision": "scr-default-anchors-v1",
        "status": status,
        "ranked": [
            {"label": label, "score": 0.91},
            {"label": "COMPLEX", "score": 0.42},
        ],
    }


def test_llmd_sc_contract_preserves_versioned_ranked_evidence() -> None:
    evidence = SemanticEvidence.from_mapping(evidence_payload())

    assert evidence.top_label == "SIMPLE"
    assert evidence.margin == pytest.approx(0.49)
    assert evidence.taxonomy_revision == "scr-default-anchors-v1"


def test_classifier_contract_must_not_contain_a_route() -> None:
    payload = evidence_payload()
    payload["route"] = "advanced-model"

    with pytest.raises(ContractError, match="must not select a route"):
        SemanticEvidence.from_mapping(payload)


def test_shadow_mode_records_evidence_without_changing_route() -> None:
    result = apply_shadow_classification(
        current_route="baseline-model",
        payload=evidence_payload(label="REASONING"),
    )

    assert result.route == "baseline-model"
    assert result.decision_mode == "shadow"
    assert result.audit["semantic.top_label"] == "REASONING"


@pytest.mark.parametrize(
    ("classifier_id", "label", "expected_route"),
    [
        ("complexity", "SIMPLE", "economical-model"),
        ("complexity", "REASONING", "advanced-model"),
        ("sensitivity", "CONFIDENTIAL", "private-model"),
        ("sensitivity", "REGULATED", "private-model"),
        ("sensitivity", "NEVER_EGRESS", "private-model"),
    ],
)
def test_gateway_policy_owns_the_route(
    classifier_id: str, label: str, expected_route: str
) -> None:
    payload = evidence_payload(label=label)
    payload["classifier_id"] = classifier_id

    result = RoutingPolicy.default().decide(
        current_route="baseline-model",
        evidence=SemanticEvidence.from_mapping(payload),
    )

    assert result.route == expected_route
    assert result.decision_mode == "enforced"


def test_abstention_uses_documented_safe_fallback() -> None:
    payload = evidence_payload(status="ABSTAIN")
    payload["ranked"] = []

    result = RoutingPolicy.default().decide(
        current_route="baseline-model",
        evidence=SemanticEvidence.from_mapping(payload),
    )

    assert result.route == "baseline-model"
    assert result.audit["semantic.fallback_reason"] == "classifier_abstained"
