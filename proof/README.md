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
- Live loopback gRPC proof for the pinned llm-d-sc wire contract
- Versioned IT semantic corpus and per-label quality/latency scorer

The policy implementation is a local executable specification. It is not yet
wired into the quickstart's Agent Service, Llama Stack provider, or Helm chart.
The first real-model shadow run failed the quality gate, so enforcement remains
deliberately disabled.

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

## Live llm-d-sc adapter proof

The pinned `Classify` protobuf is stored in `proof/contracts/classify.proto`.
The adapter owns one long-lived channel, applies a deadline to every call,
normalizes successful responses through the route-free evidence contract, and
returns explicit `UNAVAILABLE` evidence for gRPC failures.

```bash
UV_PROJECT_ENVIRONMENT=.venv312 \
  uv run --python 3.12 pytest -q test/test_llmd_sc_client.py
```

This test starts a real loopback gRPC server; it does not require a model or a
cluster. The committed generated bindings make the test reproducible without
requiring `protoc` at test time.

## Semantic quality evaluation

`proof/corpus/it-semantic-v1.jsonl` is a candidate expert-review corpus for the
IT domain. It covers complexity and sensitivity separately. Its labels must be
reviewed before they are treated as ground truth.

Predictions use one JSON object per line with `id`, `predicted` (a label or
`null` for abstention), and `latency_ms`. Score them with:

```bash
UV_PROJECT_ENVIRONMENT=.venv312 uv run --python 3.12 \
  python proof/harness/score_semantic_predictions.py predictions.jsonl
```

The command exits nonzero unless every expected label reaches both the default
0.80 precision and 0.80 recall threshold. It also reports abstention rate and
p50/p95 classifier latency.

The first real-model run is preserved in
`proof/evidence/it-semantic-live-2026-09-14.jsonl`. Against the candidate corpus:

- complexity: 3/8 correct (37.5%), p50 12.12 ms, p95 14.17 ms
- sensitivity: 6/10 correct (60%), p50 10.03 ms, p95 11.44 ms
- abstention: 0% for both classifiers

Both classifiers correctly failed the 0.80 per-label precision/recall gate.
These are local Apple ARM64 timings, not cluster capacity measurements. The run
also exposed and corrected a proof-policy mismatch: upstream sensitivity uses
`CONFIDENTIAL`, `REGULATED`, and `NEVER_EGRESS`, not `RESTRICTED`.

## Next red/green slices

1. Obtain domain-owner review of the candidate IT corpus labels.
2. Tune IT-specific anchors or classifier artifacts in a separate experiment.
3. Repeat the shadow run until the quality gate passes without hiding abstentions.
4. Connect only validated evidence to a Praxis routing policy.
5. Run existing quickstart evaluations through the transparent gateway.

The upstream llm-d-sc schema and gRPC suites have also been run locally. On
Apple ARM64 they require `protoc` and an explicit Rust 1.96.1 toolchain; the
machine's default Rust 1.90 toolchain cannot compile Candle's FP16 NEON path.
