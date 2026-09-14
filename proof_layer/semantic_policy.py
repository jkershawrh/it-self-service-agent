"""Normalized llm-d-sc evidence and a deterministic gateway policy.

This module is deliberately independent from the agent workflow.  It models the
contract between a semantic signal producer and a policy-owning AI gateway so
the integration can be proven locally before it is wired into Helm or runtime
code.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping, Sequence


class ContractError(ValueError):
    """Raised when semantic evidence violates the normalized contract."""


@dataclass(frozen=True)
class RankedSignal:
    label: str
    score: float


@dataclass(frozen=True)
class SemanticEvidence:
    request_id: str
    classifier_id: str
    model_revision: str
    tokenizer_revision: str
    taxonomy_revision: str
    status: str
    ranked: tuple[RankedSignal, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SemanticEvidence":
        forbidden = {"route", "endpoint", "target", "final_route"}.intersection(payload)
        if forbidden:
            raise ContractError(
                "llm-d-sc evidence must not select a route; found "
                + ", ".join(sorted(forbidden))
            )

        required = (
            "request_id",
            "classifier_id",
            "model_revision",
            "tokenizer_revision",
            "taxonomy_revision",
            "status",
            "ranked",
        )
        missing = [name for name in required if name not in payload]
        if missing:
            raise ContractError("missing required fields: " + ", ".join(missing))

        status = str(payload["status"]).upper()
        if status not in {"OK", "ABSTAIN", "UNAVAILABLE"}:
            raise ContractError(f"unsupported classifier status: {status}")

        ranked_value = payload["ranked"]
        if not isinstance(ranked_value, Sequence) or isinstance(
            ranked_value, (str, bytes)
        ):
            raise ContractError("ranked must be an array")

        ranked: list[RankedSignal] = []
        for item in ranked_value:
            if not isinstance(item, Mapping):
                raise ContractError("each ranked entry must be an object")
            label = str(item.get("label", "")).strip().upper()
            try:
                score = float(item["score"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ContractError(
                    "each ranked entry requires a numeric score"
                ) from exc
            if not label or not isfinite(score):
                raise ContractError("ranked labels must be non-empty and scores finite")
            ranked.append(RankedSignal(label=label, score=score))

        if status == "OK" and not ranked:
            raise ContractError("OK classifier evidence requires ranked signals")
        if any(a.score < b.score for a, b in zip(ranked, ranked[1:])):
            raise ContractError("ranked signals must be sorted by descending score")

        text_fields = {name: str(payload[name]).strip() for name in required[:-2]}
        empty = [name for name, value in text_fields.items() if not value]
        if empty:
            raise ContractError("empty required fields: " + ", ".join(empty))

        return cls(
            **text_fields,
            status=status,
            ranked=tuple(ranked),
        )

    @property
    def top_label(self) -> str | None:
        return self.ranked[0].label if self.ranked else None

    @property
    def margin(self) -> float | None:
        if not self.ranked:
            return None
        if len(self.ranked) == 1:
            return self.ranked[0].score
        return self.ranked[0].score - self.ranked[1].score

    def audit_fields(self) -> dict[str, str | float | None]:
        return {
            "semantic.request_id": self.request_id,
            "semantic.classifier_id": self.classifier_id,
            "semantic.model_revision": self.model_revision,
            "semantic.tokenizer_revision": self.tokenizer_revision,
            "semantic.taxonomy_revision": self.taxonomy_revision,
            "semantic.status": self.status,
            "semantic.top_label": self.top_label,
            "semantic.margin": self.margin,
        }


@dataclass(frozen=True)
class PolicyDecision:
    route: str
    decision_mode: str
    audit: Mapping[str, str | float | None]


@dataclass(frozen=True)
class RoutingPolicy:
    routes: Mapping[tuple[str, str], str]

    @classmethod
    def default(cls) -> "RoutingPolicy":
        return cls(
            routes={
                ("complexity", "SIMPLE"): "economical-model",
                ("complexity", "MEDIUM"): "baseline-model",
                ("complexity", "COMPLEX"): "advanced-model",
                ("complexity", "REASONING"): "advanced-model",
                ("sensitivity", "CONFIDENTIAL"): "private-model",
                ("sensitivity", "REGULATED"): "private-model",
                ("sensitivity", "NEVER_EGRESS"): "private-model",
            }
        )

    def decide(
        self, *, current_route: str, evidence: SemanticEvidence
    ) -> PolicyDecision:
        audit = evidence.audit_fields()
        if evidence.status != "OK":
            audit["semantic.fallback_reason"] = (
                "classifier_abstained"
                if evidence.status == "ABSTAIN"
                else "classifier_unavailable"
            )
            return PolicyDecision(current_route, "fallback", audit)

        route = self.routes.get(
            (evidence.classifier_id.lower(), evidence.top_label or ""),
            current_route,
        )
        if route == current_route:
            audit["semantic.fallback_reason"] = "no_matching_policy"
        return PolicyDecision(route, "enforced", audit)


def apply_shadow_classification(
    *, current_route: str, payload: Mapping[str, Any]
) -> PolicyDecision:
    """Record validated semantic evidence without changing model selection."""

    evidence = SemanticEvidence.from_mapping(payload)
    return PolicyDecision(current_route, "shadow", evidence.audit_fields())
