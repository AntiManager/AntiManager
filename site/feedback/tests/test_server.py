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
    def __init__(self, config, challenge=None, global_limiter=None):
        self.httpd = server.build_server(
            config, challenge=challenge, global_limiter=global_limiter)
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


def _post_form(port, path, fields, headers=None):
    """POST an application/x-www-form-urlencoded body (the no-JS browser path).

    Returns (status, body_text, content_type).
    """
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8"), response.headers.get("Content-Type")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, exc.read().decode("utf-8"), exc.headers.get("Content-Type")
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
        "GLOBAL_RATE_LIMIT_MAX": "500",
        "GLOBAL_RATE_LIMIT_WINDOW": "3600",
    }
    env.update({k: str(v) for k, v in overrides.items()})
    return server.Config(env)


def _challenge(config, bits=8, min_fill=0.0):
    """A challenge with a trivial difficulty so tests stay fast."""
    return server.Challenge(config.challenge_secret, bits, min_fill=min_fill)


def _solve(item):
    """Return the submitted proof fields for an issued challenge."""
    nonce = 0
    while not server.leading_zero_bits("%s:%s" % (item["challenge"], nonce), item["bits"]):
        nonce += 1
    return {
        "challenge": item["challenge"],
        "challenge_bits": item["bits"],
        "challenge_issued": item["issued"],
        "challenge_signature": item["signature"],
        "challenge_nonce": str(nonce),
    }


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

    def test_audit_pack_is_accepted(self):
        good = dict(VALID)
        good["pack"] = "audit"
        data, error = server.validate(good)
        self.assertIsNone(error)
        self.assertEqual(data["pack"], "audit")


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

    def test_audit_pack_label_is_formatted(self):
        data, _ = server.validate(dict(VALID, pack="audit"))
        self.assertIn("Полный чек-лист ПС (120 критериев)", server.format_message(data))

    def test_documents_pack_is_accepted(self):
        data, error = server.validate(dict(VALID, pack="documents"))
        self.assertIsNone(error)
        self.assertEqual(data["pack"], "documents")
        self.assertIn("Типовые документы производственной системы",
                      server.format_message(data))


class RateLimiterTests(unittest.TestCase):
    def test_blocks_after_max_in_window(self):
        limiter = server.RateLimiter(max_events=2, window_seconds=600)
        self.assertTrue(limiter.allow("ip"))
        self.assertTrue(limiter.allow("ip"))
        self.assertFalse(limiter.allow("ip"))
        self.assertTrue(limiter.allow("other-ip"))


class ChallengeTests(unittest.TestCase):
    def setUp(self):
        self.secret = b"test-secret"
        self.challenge = server.Challenge(self.secret, bits=8, min_fill=0.0)

    def test_issue_then_verify_succeeds(self):
        item = self.challenge.issue()
        ok, issued, reason = self.challenge.verify(_solve(item))
        self.assertTrue(ok)
        self.assertIsNone(reason)
        self.assertEqual(issued, item["issued"])

    def test_wrong_nonce_is_bad_pow(self):
        item = self.challenge.issue()
        proof = _solve(item)
        proof["challenge_nonce"] = "0"
        ok, _issued, reason = self.challenge.verify(proof)
        self.assertFalse(ok)
        self.assertEqual(reason, "bad_pow")

    def test_tampered_signature_is_rejected(self):
        item = self.challenge.issue()
        proof = _solve(item)
        proof["challenge_signature"] = "0" * 64
        ok, _issued, reason = self.challenge.verify(proof)
        self.assertFalse(ok)
        self.assertEqual(reason, "bad_challenge")

    def test_non_ascii_signature_is_rejected_not_crashing(self):
        item = self.challenge.issue()
        proof = _solve(item)
        proof["challenge_signature"] = "подпись"
        ok, _issued, reason = self.challenge.verify(proof)
        self.assertFalse(ok)
        self.assertEqual(reason, "bad_challenge")

    def test_challenge_cannot_be_rewritten_with_another_issue_time(self):
        # The issue time is inside the HMAC, so a bot cannot backdate it to
        # defeat the fill-time trap.
        item = self.challenge.issue()
        proof = _solve(item)
        proof["challenge_issued"] = int(proof["challenge_issued"]) - 600
        ok, _issued, reason = self.challenge.verify(proof)
        self.assertFalse(ok)
        self.assertEqual(reason, "bad_challenge")

    def test_expired_challenge_is_stale(self):
        item = self.challenge.issue(now=1000)
        proof = _solve(item)
        ok, _issued, reason = self.challenge.verify(proof, now=1000 + server.CHALLENGE_TTL + 1)
        self.assertFalse(ok)
        self.assertEqual(reason, "stale_challenge")

    def test_instant_submission_is_too_fast(self):
        slow = server.Challenge(self.secret, bits=8, min_fill=2.0)
        item = slow.issue(now=1000)
        ok, _issued, reason = slow.verify(_solve(item), now=1000.5)
        self.assertTrue(ok)
        self.assertEqual(reason, "too_fast")

    def test_human_speed_submission_passes(self):
        slow = server.Challenge(self.secret, bits=8, min_fill=2.0)
        item = slow.issue(now=1000)
        ok, _issued, reason = slow.verify(_solve(item), now=1010)
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_replay_is_rejected(self):
        item = self.challenge.issue()
        proof = _solve(item)
        self.assertTrue(self.challenge.verify(proof)[0])
        ok, _issued, reason = self.challenge.verify(proof)
        self.assertFalse(ok)
        self.assertEqual(reason, "replay")

    def test_missing_fields_is_no_challenge(self):
        ok, _issued, reason = self.challenge.verify({"name": "x"})
        self.assertFalse(ok)
        self.assertEqual(reason, "no_challenge")


class SuspicionTests(unittest.TestCase):
    SPAM = {
        "name": "RobertMal",
        "contact": "aveyekoha655@gmail.com",
        "message": "Hi, ego volo scire vestri pretium.",
        "pack": "",
    }
    LEAD = {
        "name": "Иван",
        "contact": "+7 900 000-00-00",
        "message": "Нужен аудит производственных процессов на двух площадках.",
        "pack": "audit",
    }

    def test_observed_spam_is_quarantined(self):
        reasons = server.suspicion(dict(self.SPAM), has_challenge=True)
        self.assertIn("latin_only", reasons)
        self.assertIn("price_probe", reasons)
        self.assertIn("random_mailbox", reasons)
        self.assertTrue(server.is_quarantine(reasons))

    def test_ordinary_lead_is_delivered(self):
        reasons = server.suspicion(dict(self.LEAD), has_challenge=True)
        self.assertEqual(reasons, [])
        self.assertFalse(server.is_quarantine(reasons))

    def test_lead_without_challenge_is_still_delivered(self):
        # The no-JS path: a plausible Cyrillic request must not be quarantined
        # just because it carries no proof of work.
        reasons = server.suspicion(dict(self.LEAD), has_challenge=False)
        self.assertEqual(reasons, ["no_challenge"])
        self.assertFalse(server.is_quarantine(reasons))

    def test_latin_name_with_cyrillic_message_is_fine(self):
        data = dict(self.LEAD, name="Ivan")
        reasons = server.suspicion(data, has_challenge=True)
        self.assertEqual(reasons, ["latin_name"])
        self.assertFalse(server.is_quarantine(reasons))

    def test_link_in_message_quarantines(self):
        data = dict(self.LEAD, message="Смотрите https://spam.example/promo — это вам поможет")
        reasons = server.suspicion(data, has_challenge=True)
        self.assertIn("link_in_message", reasons)
        self.assertTrue(server.is_quarantine(reasons))


class EndpointTests(unittest.TestCase):
    def setUp(self):
        _StubTelegram.calls = []
        _StubTelegram.ok = True
        self.stub = _StubServer()
        self.stub.__enter__()

    def tearDown(self):
        self.stub.__exit__(None, None, None)

    def _start(self, challenge=None, **overrides):
        config = _config(self.stub.port, **overrides)
        service = _Service(config, challenge=challenge or _challenge(config))
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


class ChallengeEndpointTests(unittest.TestCase):
    def setUp(self):
        _StubTelegram.calls = []
        _StubTelegram.ok = True
        self.stub = _StubServer()
        self.stub.__enter__()

    def tearDown(self):
        self.stub.__exit__(None, None, None)

    def _start(self, challenge=None, **overrides):
        config = _config(self.stub.port, **overrides)
        service = _Service(config, challenge=challenge or _challenge(config))
        service.__enter__()
        self.addCleanup(lambda: service.__exit__(None, None, None))
        return config, service.port

    def _issue(self, port):
        status, body = _get(port, "/api/feedback/challenge")
        self.assertEqual(status, 200)
        return json.loads(body)

    def test_challenge_endpoint_returns_signed_material(self):
        _config_obj, port = self._start()
        item = self._issue(port)
        self.assertEqual(len(item["challenge"]), 32)
        self.assertEqual(item["bits"], 8)
        self.assertIsInstance(item["issued"], int)
        self.assertEqual(len(item["signature"]), 64)

    def test_valid_proof_is_delivered(self):
        _config_obj, port = self._start()
        proof = _solve(self._issue(port))
        payload = dict(VALID, **proof)
        status, body = _post(port, "/api/feedback", payload, {"X-Real-IP": "10.0.1.1"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(len(_StubTelegram.calls), 1)
        self.assertNotIn("Возможно спам", _StubTelegram.calls[0][1]["text"])

    def test_instant_proof_is_dropped_silently(self):
        config = _config(self.stub.port)
        slow = server.Challenge(config.challenge_secret, bits=8, min_fill=2.0)
        _config_obj, port = self._start(challenge=slow)
        proof = _solve(self._issue(port))
        status, body = _post(port, "/api/feedback", dict(VALID, **proof),
                             {"X-Real-IP": "10.0.1.2"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(_StubTelegram.calls, [])

    def test_spam_with_a_valid_proof_is_quarantined(self):
        _config_obj, port = self._start()
        proof = _solve(self._issue(port))
        spam = {
            "name": "RobertMal",
            "contact": "aveyekoha655@gmail.com",
            "message": "Hi, ego volo scire vestri pretium.",
            "pack": "",
            "consent": True,
        }
        status, _body = _post(port, "/api/feedback", dict(spam, **proof),
                              {"X-Real-IP": "10.0.1.3"})
        self.assertEqual(status, 200)
        self.assertEqual(len(_StubTelegram.calls), 1)
        text = _StubTelegram.calls[0][1]["text"]
        self.assertTrue(text.startswith("⚠️ Возможно спам"))
        self.assertIn("latin_only", text)

    def test_spam_without_a_challenge_is_quarantined(self):
        _config_obj, port = self._start()
        spam = {
            "name": "RobertMal",
            "contact": "aveyekoha655@gmail.com",
            "message": "Hi, ego volo scire vestri pretium.",
            "pack": "",
            "consent": True,
        }
        status, _body = _post(port, "/api/feedback", spam, {"X-Real-IP": "10.0.1.4"})
        self.assertEqual(status, 200)
        text = _StubTelegram.calls[0][1]["text"]
        self.assertTrue(text.startswith("⚠️ Возможно спам"))
        self.assertIn("no_challenge", text)

    def test_quarantine_chat_is_used_when_configured(self):
        _config_obj, port = self._start(TELEGRAM_QUARANTINE_CHAT_ID="-100999")
        spam = {
            "name": "RobertMal",
            "contact": "aveyekoha655@gmail.com",
            "message": "Hi, ego volo scire vestri pretium.",
            "pack": "",
            "consent": True,
        }
        _post(port, "/api/feedback", spam, {"X-Real-IP": "10.0.1.5"})
        self.assertEqual(_StubTelegram.calls[0][1]["chat_id"], "-100999")

    def test_global_limit_returns_429(self):
        _config_obj, port = self._start(GLOBAL_RATE_LIMIT_MAX="1")
        payload = dict(VALID)
        status, _ = _post(port, "/api/feedback", payload, {"X-Real-IP": "10.0.2.1"})
        self.assertEqual(status, 200)
        status, _ = _post(port, "/api/feedback", payload, {"X-Real-IP": "10.0.2.2"})
        self.assertEqual(status, 429)

    def test_honeypot_url_field_is_dropped(self):
        _config_obj, port = self._start()
        bot = dict(VALID, url="https://spam.example")
        status, _body = _post(port, "/api/feedback", bot, {"X-Real-IP": "10.0.2.3"})
        self.assertEqual(status, 200)
        self.assertEqual(_StubTelegram.calls, [])


class EndpointFlowTests(unittest.TestCase):
    """Remaining endpoint paths; reuses the EndpointTests fixture without
    re-collecting its test methods (inheritance would run them twice)."""

    setUp = EndpointTests.setUp
    tearDown = EndpointTests.tearDown
    _start = EndpointTests._start

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

    def test_no_js_form_submission_delivers_and_returns_html(self):
        # A browser with JavaScript off posts the form natively; the checkbox is
        # sent as "consent=on" and the response should be an HTML page, not JSON.
        port = self._start()
        fields = {"name": "Иван", "contact": "+7 900 000-00-00", "message": "Нужен аудит", "pack": "process", "consent": "on"}
        status, body, ctype = _post_form(port, "/api/feedback", fields,
                                         {"X-Real-IP": "10.0.0.7", "Accept": "text/html,application/xhtml+xml"})
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn("Заявка отправлена", body)
        self.assertEqual(len(_StubTelegram.calls), 1)
        self.assertIn("Нужен аудит", _StubTelegram.calls[0][1]["text"])

    def test_no_js_form_without_consent_is_rejected(self):
        port = self._start()
        fields = {"name": "Иван", "contact": "c", "message": "m"}
        status, _body, _ctype = _post_form(port, "/api/feedback", fields,
                                           {"X-Real-IP": "10.0.0.8", "Accept": "text/html"})
        self.assertEqual(status, 400)
        self.assertEqual(_StubTelegram.calls, [])

    def test_form_submission_without_html_accept_returns_json(self):
        port = self._start()
        fields = {"name": "Иван", "contact": "c", "message": "m", "consent": "on"}
        status, body, ctype = _post_form(port, "/api/feedback", fields, {"X-Real-IP": "10.0.0.10"})
        self.assertEqual(status, 200)
        self.assertIn("application/json", ctype)
        self.assertTrue(json.loads(body)["ok"])

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
