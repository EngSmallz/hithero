"""Minimal isolated backend for SvelteKit forum failure-state integration tests."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlparse(self.path).path
        if path == "/api/profile/":
            self.respond(
                200,
                {
                    "user_id": 42,
                    "user_role": "teacher",
                    "user_email": "forum-failure@example.test",
                },
            )
            return
        if path == "/forum/get_posts":
            self.respond(500, {"detail": "Forum list provider unavailable."})
            return
        if path == "/forum/get_post":
            self.respond(
                200,
                {
                    "id": 101,
                    "title": "Failure-boundary discussion",
                    "content": "The post remains visible when comments fail.",
                    "created_at": "2026-07-12T12:00:00",
                    "user_id": 42,
                    "upvote_count": 0,
                    "comment_count": 1,
                },
            )
            return
        if path == "/forum/comments/101/":
            self.respond(500, {"detail": "Comments provider unavailable."})
            return
        self.respond(404, {"detail": "Not found"})

    def respond(self, status: int, body: dict[str, object]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
