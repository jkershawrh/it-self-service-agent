"""Provider-neutral contracts for optional semantic model routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Mapping, Protocol


@dataclass(frozen=True)
class ClassificationRequest:
    request_id: str
    text: str
    taxonomy_revision: str


class ClassifierAdapter(Protocol):
    """Produce evidence only; classifiers never choose a model endpoint."""

    name: str

    async def classify(self, request: ClassificationRequest) -> Mapping[str, Any]: ...


class ModelGatewayAdapter(Protocol):
    """Invoke a logical model alias without exposing backend credentials."""

    name: str

    async def invoke(
        self, *, model_alias: str, payload: Mapping[str, Any]
    ) -> Any: ...


@dataclass(frozen=True)
class RoutingContext:
    model_alias: str
    mode: str
    provider: str
    audit: Mapping[str, Any]


async def classify_or_fallback(
    *,
    classifier: ClassifierAdapter,
    request: ClassificationRequest,
    baseline_alias: str,
    decide: Any,
) -> RoutingContext:
    """Normalize adapter failures into the existing safe model route."""

    try:
        evidence = await classifier.classify(request)
        decision = decide(evidence)
        return RoutingContext(
            model_alias=decision.route,
            mode=decision.decision_mode,
            provider=classifier.name,
            audit=decision.audit,
        )
    except Exception as exc:
        return RoutingContext(
            model_alias=baseline_alias,
            mode="fallback",
            provider=getattr(classifier, "name", "unknown"),
            audit={
                "semantic.fallback_reason": "classifier_error",
                "semantic.error_type": type(exc).__name__,
            },
        )

