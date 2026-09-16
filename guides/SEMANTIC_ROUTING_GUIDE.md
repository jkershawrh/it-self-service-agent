# Conservative semantic routing

This optional quickstart extension demonstrates a narrow, explainable routing
policy without changing the existing agent workflow:

```text
SIMPLE with a validated margin -> economical model
everything else               -> existing baseline model
```

It is an experimental learning path, not a production-readiness claim. The
default quickstart remains unchanged and semantic routing is disabled unless an
operator explicitly enables and completes the extension.

## Interchangeable integration points

The quickstart does not require a particular classifier or AI gateway. A
`ClassifierAdapter` translates llm-d-sc, vLLM Semantic Router, rules, or a
future classifier into versioned evidence. A separate `ModelGatewayAdapter`
sends the selected logical model alias through LlamaStack, Praxis, RACMaaS, or
another compatible gateway.

Classify the original user turn once and carry its `RoutingContext` through the
LangGraph state. Internal agent prompts should not be classified independently,
because that could change models partway through one workflow. The contracts
live in `proof_layer/adapters.py`; runtime wiring remains opt-in.

## Component responsibilities

```text
Agent / Llama Stack request
          |
          v
semantic policy adapter -----> llm-d-sc gRPC
          |                     returns ranked evidence only
          | model alias
          v
        Praxis
          | applies route and fallback policy
          v
 RACMaaS economical or baseline model
```

- **llm-d-sc** produces versioned semantic evidence. It does not select an
  endpoint.
- **The policy adapter** accepts only `SIMPLE` evidence above a configured
  margin. Unavailable, malformed, weak, or non-simple evidence resolves to the
  baseline alias.
- **Praxis** maps the resulting alias to an operator-configured RACMaaS backend
  and owns the final route.
- **RACMaaS** performs inference. Credentials are injected from a Secret and
  are never placed in learner commands, Helm values, or rendered documentation.

Praxis supports routing on a model value promoted from an OpenAI request body.
llm-d-sc exposes a separate gRPC `Classify` contract, so these components do not
connect directly. The adapter is a required boundary, not optional glue.

## Learner scope

Keep the learner exercise to three requests:

1. A clearly routine request may use the economical model.
2. A diagnostic or planning request uses the baseline model.
3. An ambiguous request or classifier failure demonstrates baseline fallback.

The learner observes the semantic label, margin, policy outcome, selected model
alias, and fallback reason. Anchor authoring, model training, and threshold
tuning remain maintainer activities under `proof/`.

## Configuration contract

Start from `helm/values-semantic-routing.yaml`. The overlay intentionally ships
disabled and contains no endpoint, model ID, or credential. Before enabling it,
the environment owner must provide:

- the approved Praxis image and configuration;
- the approved llm-d-sc image and pinned model artifact;
- an economical RACMaaS model ID;
- the existing baseline RACMaaS model ID;
- the RACMaaS API base URL; and
- a Secret containing the tenant-scoped API key.

The observed `0.45` margin is recorded only as an experimental starting point.
It was discovered on eight prompts and must not be treated as a validated
threshold. Until an independent corpus validates a threshold, run the adapter
in `shadow` mode.

## Activation gates

Do not enable model switching until all of these are true:

- the baseline route works when llm-d-sc is unavailable;
- malformed evidence cannot select the economical model;
- only `SIMPLE` can select the economical model;
- the threshold is calibrated on a development corpus;
- an untouched test corpus shows no accepted complex-to-economical routes;
- secrets are sourced only from an OpenShift Secret; and
- the original quickstart regression suite passes through the baseline route.

The local contracts, test corpus, raw evidence, and red/green matrix are in
`proof/README.md`. They explain why this extension uses asymmetric fallback.
