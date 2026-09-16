from proof_layer.adapters import ClassificationRequest, classify_or_fallback


class BrokenClassifier:
    name = "candidate"

    async def classify(self, request):
        raise TimeoutError("unavailable")


async def test_classifier_failure_preserves_existing_route():
    result = await classify_or_fallback(
        classifier=BrokenClassifier(),
        request=ClassificationRequest("r1", "help", "taxonomy-v1"),
        baseline_alias="existing-model",
        decide=lambda evidence: None,
    )

    assert result.model_alias == "existing-model"
    assert result.mode == "fallback"
    assert result.audit["semantic.error_type"] == "TimeoutError"
