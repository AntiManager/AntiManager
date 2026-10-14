"""Tests for the feedback microservice (standard library unittest, no deps).

Run from the repository root:
    python -m unittest discover -s site/feedback/tests
"""

import json
import os
import socket
import sys
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402


class _StubTelegram(BaseHTTPRequestHandler):
    """Stand-in for api.telegram.org: records sendMessage calls, replies ok/fail."""

    calls = []
    ok = True

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8")
        _StubTelegram.calls.append((self.path, dict(urllib.parse.parse_qsl(body))))
        payload = json.dumps({"ok": _StubTelegram.ok}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class _StubServer:
    def __init__(self):
        self.httpd = HTTPServer(("127.0.0.1", 0), _StubTelegram)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


class _Service:
    def __init__(self, config):
        self.httpd = server.build_server(config)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


def _post(port, path, payload, headers=None):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        finally:
            exc.close()


def _get(port, path):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, exc.read().decode("utf-8")
        finally:
            exc.close()


def _post_raw(port, path, body):
    """POST an arbitrary raw body (already bytes) and return the status code."""
    request = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        try:
            return exc.code
        finally:
            exc.close()


def _post_headers_only(port, path, content_length):
    """Send a request advertising a huge Content-Length but no body, over a raw
    socket, so the server's size guard is exercised without transferring 16 KB."""
    head = (
        "POST %s HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
        "Content-Length: %d\r\nConnection: close\r\n\r\n" % (path, content_length)
    ).encode("ascii")
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall(head)
        raw = sock.recv(65536)
    return int(raw.split(b" ", 2)[1])


def _config(stub_port, **overrides):
    env = {
        "TELEGRAM_BOT_TOKEN": "TESTTOKEN",
        "TELEGRAM_CHAT_ID": "12345",
        "PORT": "0",
        "TELEGRAM_API_BASE": "http://127.0.0.1:%d" % stub_port,
        "RATE_LIMIT_MAX": "50",
        "RATE_LIMIT_WINDOW": "600",
    }
    env.update({k: str(v) for k, v in overrides.items()})
    return server.Config(env)


VALID = {"name": "Иван", "contact": "+7 900 000-00-00", "message": "Нужен аудит", "pack": "process", "consent": True, "website": ""}


class ValidateTests(unittest.TestCase):
    def test_valid_payload_is_normalised(self):
        data, error = server.validate(dict(VALID))
        self.assertIsNone(error)
        self.assertEqual(data["name"], "Иван")
        self.assertEqual(data["pack"], "process")

    def test_consent_is_required(self):
        bad = dict(VALID)
        bad["consent"] = False
        data, error = server.validate(bad)
        self.assertIsNone(data)
        self.assertIn("consent", error)

    def test_empty_message_is_rejected(self):
        bad = dict(VALID)
        bad["message"] = "   "
        data, _ = server.validate(bad)
        self.assertIsNone(data)

    def test_overlong_message_is_rejected(self):
        bad = dict(VALID)
        bad["message"] = "x" * (server.MAX_MESSAGE + 1)
        data, _ = server.validate(bad)
        self.assertIsNone(data)

    def test_unknown_pack_is_dropped_not_rejected(self):
        good = dict(VALID)
        good["pack"] = "whatever"
        data, error = server.validate(good)
        self.assertIsNone(error)
        self.assertEqual(data["pack"], "")


class FormatMessageTests(unittest.TestCase):
    def test_includes_fields_and_pack_label(self):
        data, _ = server.validate(dict(VALID))
        text = server.format_message(data)
        self.assertIn("Иван", text)
        self.assertIn("Проработка процессов", text)
        self.assertIn("Нужен аудит", text)

    def test_is_truncated_to_the_telegram_limit(self):
        data = {"name": "N", "contact": "C", "message": "m" * 5000, "pack": ""}
        self.assertLessEqual(len(server.format_message(data)), server.TELEGRAM_TEXT_LIMIT)


class RateLimiterTests(unittest.TestCase):
    def test_blocks_after_max_in_window(self):
        limiter = server.RateLimiter(max_events=2, window_seconds=600)
        self.assertTrue(limiter.allow("ip"))
        self.assertTrue(limiter.allow("ip"))
        self.assertFalse(limiter.allow("ip"))
        self.assertTrue(limiter.allow("other-ip"))


class EndpointTests(unittest.TestCase):
    def setUp(self):
        _StubTelegram.calls = []
        _StubTelegram.ok = True
        self.stub = _StubServer()
        self.stub.__enter__()

    def tearDown(self):
        self.stub.__exit__(None, None, None)

    def _start(self, **overrides):
        service = _Service(_config(self.stub.port, **overrides))
        service.__enter__()
        self.addCleanup(lambda: service.__exit__(None, None, None))
        return service.port

    def test_valid_submission_reaches_telegram(self):
        port = self._start()
        status, body = _post(port, "/api/feedback", dict(VALID), {"X-Real-IP": "10.0.0.1"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(len(_StubTelegram.calls), 1)
        path, fields = _StubTelegram.calls[0]
        self.assertIn("/botTESTTOKEN/sendMessage", path)
        self.assertEqual(fields["chat_id"], "12345")
        self.assertIn("Нужен аудит", fields["text"])

    def test_honeypot_is_dropped_silently(self):
        port = self._start()
        bot = dict(VALID)
        bot["website"] = "http://spam.example"
        status, body = _post(port, "/api/feedback", bot, {"X-Real-IP": "10.0.0.2"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(_StubTelegram.calls, [])

    def test_missing_consent_is_rejected(self):
        port = self._start()
        bad = dict(VALID)
        bad["consent"] = False
        status, _ = _post(port, "/api/feedback", bad, {"X-Real-IP": "10.0.0.3"})
        self.assertEqual(status, 400)

    def test_telegram_failure_returns_502(self):
        _StubTelegram.ok = False
        port = self._start()
        status, _ = _post(port, "/api/feedback", dict(VALID), {"X-Real-IP": "10.0.0.4"})
        self.assertEqual(status, 502)

    def test_rate_limit_returns_429(self):
        port = self._start(RATE_LIMIT_MAX=2)
        for _ in range(2):
            status, _ = _post(port, "/api/feedback", dict(VALID), {"X-Real-IP": "10.0.0.5"})
            self.assertEqual(status, 200)
        status, _ = _post(port, "/api/feedback", dict(VALID), {"X-Real-IP": "10.0.0.5"})
        self.assertEqual(status, 429)

    def test_get_on_feedback_is_method_not_allowed(self):
        port = self._start()
        status, _ = _get(port, "/api/feedback")
        self.assertEqual(status, 405)

    def test_healthz(self):
        port = self._start()
        status, body = _get(port, "/healthz")
        self.assertEqual(status, 200)
        self.assertIn("ok", body)

    def test_oversized_body_is_rejected(self):
        port = self._start()
        self.assertEqual(_post_headers_only(port, "/api/feedback", server.MAX_BODY + 1), 400)
        self.assertEqual(_StubTelegram.calls, [])

    def test_invalid_json_is_rejected(self):
        port = self._start()
        status = _post_raw(port, "/api/feedback", b"not json at all")
        self.assertEqual(status, 400)

    def test_non_object_payload_is_rejected(self):
        port = self._start()
        status = _post_raw(port, "/api/feedback", json.dumps([1, 2, 3]).encode("utf-8"))
        self.assertEqual(status, 400)

    def test_unknown_path_is_not_found(self):
        port = self._start()
        status = _post_raw(port, "/nope", json.dumps(dict(VALID)).encode("utf-8"))
        self.assertEqual(status, 404)

    def test_invalid_requests_do_not_consume_the_rate_limit(self):
        # The limiter is applied only after validation, so rejected (400) requests
        # must not use up an IP's budget.
        port = self._start(RATE_LIMIT_MAX=1)
        bad = dict(VALID)
        bad["consent"] = False
        for _ in range(3):
            status, _ = _post(port, "/api/feedback", bad, {"X-Real-IP": "10.0.0.9"})
            self.assertEqual(status, 400)
        status, _ = _post(port, "/api/feedback", dict(VALID), {"X-Real-IP": "10.0.0.9"})
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
