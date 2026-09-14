"""Deterministic OpenAI-compatible backend for transparent-proxy proof runs."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/v1/models":
            self._send(
                200,
                {
                    "object": "list",
                    "data": [{"id": "baseline-model", "object": "model"}],
                },
            )
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        length = int(self.headers.get("content-length", "0"))
        request = json.loads(self.rfile.read(length) or b"{}")
        if self.path != "/v1/chat/completions":
            self._send(404, {"error": "not found"})
            return
        self._send(
            200,
            {
                "id": "proof-chat-001",
                "object": "chat.completion",
                "model": request.get("model", "baseline-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "transparent-proxy-proof",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 3,
                    "total_tokens": 7,
                },
            },
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18081), Handler).serve_forever()
