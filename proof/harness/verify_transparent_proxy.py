"""Compare direct and Praxis-proxied OpenAI responses for equivalence."""

from __future__ import annotations

import json
import sys
import urllib.request


PAYLOAD = json.dumps(
    {
        "model": "baseline-model",
        "messages": [{"role": "user", "content": "I need a laptop refresh"}],
    }
).encode()


def invoke(url: str) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=PAYLOAD,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.load(response)


direct = invoke("http://127.0.0.1:18081/v1/chat/completions")
proxied = invoke("http://127.0.0.1:18080/v1/chat/completions")

if direct != proxied:
    print(json.dumps({"direct": direct, "proxied": proxied}, indent=2))
    sys.exit("transparent proxy changed the observable response")

print(json.dumps({"status": "pass", "direct": direct, "proxied": proxied}, indent=2))
