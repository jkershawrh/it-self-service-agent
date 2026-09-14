# Praxis and llm-d-sc local proof layer

This directory holds additive proof artifacts for evaluating Praxis AI and
llm-d-sc without changing the self-service agent's production deployment path.

## Current scope

- Normalized, versioned llm-d-sc evidence contract
- Explicit enforcement that classification never selects a route
- Shadow-mode evidence collection
- Deterministic gateway-owned complexity and sensitivity policy
- Abstention and unavailable fallbacks
- Real Praxis transparent-proxy equivalence test

The policy implementation is a local executable specification. It is not yet
wired into the quickstart's Agent Service, Llama Stack provider, or Helm chart.

## Contract and policy tests

Use Python 3.12 because the repository's pinned Pydantic/PyO3 dependency chain
does not currently build under the newer Python 3.14 selected by an unpinned
local `uv` invocation.

```bash
UV_PROJECT_ENVIRONMENT=.venv312 \
  uv run --python 3.12 pytest -q test/test_praxis_semantic_policy.py
```

## Transparent Praxis proxy proof

Build `praxis-proxy/ai` release `0.3.0`, then start the deterministic backend:

```bash
python3 proof/harness/mock_openai_backend.py
```

Start Praxis in another terminal, replacing `PRAXIS_SOURCE` with the checkout:

```bash
"${PRAXIS_SOURCE}/target/release/praxis-ai" \
  -c proof/praxis/transparent-proxy.yaml
```

Run the equivalence assertion:

```bash
python3 proof/harness/verify_transparent_proxy.py
```

The verifier fails unless the direct and proxied HTTP status and parsed JSON
responses are equal.

## Next red/green slices

1. Implement a live gRPC adapter for the llm-d-sc `Classify` contract.
2. Run classification in shadow mode against a curated IT prompt corpus.
3. Establish per-label precision/recall and abstention thresholds.
4. Connect validated evidence to a Praxis routing policy.
5. Run existing quickstart evaluations through the transparent gateway.
