# Praxis and llm-d-sc proof matrix

| ID | Discipline | Capability | Red evidence | Green requirement | Status |
|---|---|---|---|---|---|
| CDD-001 | CDD/TDD | Parse versioned ranked evidence | `ModuleNotFoundError: proof_layer` | Valid evidence preserves labels, scores, and revisions | Green |
| CDD-002 | CDD/TDD | Preserve routing authority boundary | No contract enforcement | Route or endpoint fields are rejected | Green |
| CBT-001 | CBT/BDD | Shadow classification | No shadow-mode implementation | Evidence is recorded and the baseline route is unchanged | Green |
| CBT-002 | CBT/BDD | Policy-owned semantic routing | No policy implementation | Complexity and sensitivity map to deterministic approved routes | Green |
| CBT-003 | CBT/BDD | Explicit abstention fallback | No fallback implementation | ABSTAIN preserves baseline route and records its reason | Green |
| EDD-001 | EDD | Classification quality corpus | Not yet measured | Meet per-label precision/recall thresholds on curated IT prompts | Planned |
| CBT-004 | CBT | Transparent Praxis proxy | Direct-only baseline; no gateway path | Real Praxis proxy returns a behaviorally identical status and JSON response | Green |
| CBT-005 | CBT | Live llm-d-sc gRPC adapter | Not yet implemented | Adapter validates revisions, status, ordering, and timeout behavior | Planned |
| NFR-001 | CBT | Added latency | Not yet measured | Record p50/p95 overhead separately for proxy and classifier | Planned |

## Red run

Command:

```text
UV_PROJECT_ENVIRONMENT=.venv312 uv run --python 3.12 pytest -q test/test_praxis_semantic_policy.py
```

Observed result before implementation:

```text
ModuleNotFoundError: No module named 'proof_layer'
```

The default `uv run` selected Python 3.14 and exposed an unrelated existing
dependency compatibility issue (`pydantic-core`/PyO3 supports through Python
3.13). Proof commands therefore pin Python 3.12, matching this repository's
declared runtime requirement.

## Transparent Praxis proxy run

Praxis AI source revision:

```text
praxis-proxy/ai d40e8e4af127ec235145cc8915d97489fc4d7640
```

The release binary was built from source and run with
`proof/praxis/transparent-proxy.yaml`. The deterministic backend was invoked
once directly and once through Praxis. Both calls returned HTTP 200 and the
same complete OpenAI-compatible JSON body, including model, content, finish
reason, and token usage.

```json
{
  "status": "pass",
  "model": "baseline-model",
  "content": "transparent-proxy-proof",
  "total_tokens": 7
}
```
