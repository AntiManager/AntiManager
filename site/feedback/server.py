#!/usr/bin/env python3
"""AntiManager feedback microservice.

Receives feedback-form submissions over HTTP and forwards them to a Telegram
chat via the Bot API. Standard library only: no third-party dependencies.

Endpoints:
  POST /api/feedback  {"name","contact","message","pack","consent","website"}
  GET  /healthz       liveness probe (not proxied publicly)

The bot token is read from the environment and never returned to a client.
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_NAME = 100
MAX_CONTACT = 200
MAX_MESSAGE = 3000
MAX_BODY = 16 * 1024
TELEGRAM_TEXT_LIMIT = 4096

# Context labels for the "Интересует" line. Keys match the ?pack= slugs the
# offer CTAs pass to /contact/.
PACK_LABELS = {
    "express": "Экспресс-диагностика",
    "process": "Проработка процессов",
    "library": "Библиотека + правила",
    "pilot": "Одна пилотная группа",
}


class Config:
    def __init__(self, env):
        self.token = (env.get("TELEGRAM_BOT_TOKEN") or "").strip()
        self.chat_id = (env.get("TELEGRAM_CHAT_ID") or "").strip()
        self.port = int(env.get("PORT") or "8080")
        self.api_base = (env.get("TELEGRAM_API_BASE") or "https://api.telegram.org").rstrip("/")
        self.rate_max = int(env.get("RATE_LIMIT_MAX") or "5")
        self.rate_window = int(env.get("RATE_LIMIT_WINDOW") or "600")


def validate(payload):
    """Return (data, error). `data` is a normalised dict when ok, else `error` explains."""
    if not isinstance(payload, dict):
        return None, "payload must be an object"
    if payload.get("consent") is not True:
        return None, "consent required"
    name = str(payload.get("name") or "").strip()
    contact = str(payload.get("contact") or "").strip()
    message = str(payload.get("message") or "").strip()
    pack = str(payload.get("pack") or "").strip()
    if not 1 <= len(name) <= MAX_NAME:
        return None, "invalid name"
    if not 1 <= len(contact) <= MAX_CONTACT:
        return None, "invalid contact"
    if not 1 <= len(message) <= MAX_MESSAGE:
        return None, "invalid message"
    if pack not in PACK_LABELS:
        pack = ""  # an unknown pack is not fatal; drop it rather than reject.
    return {"name": name, "contact": contact, "message": message, "pack": pack}, None


def format_message(data):
    """Plain-text Telegram message (no parse_mode, so user text cannot inject markup)."""
    pack = PACK_LABELS.get(data["pack"], "")
    lines = [
        "🔔 Заявка с сайта",
        "Имя: " + data["name"],
        "Контакт: " + data["contact"],
        "Интересует: " + (pack if pack else "—"),
        "",
        "Сообщение:",
        data["message"],
    ]
    return "\n".join(lines)[:TELEGRAM_TEXT_LIMIT]


class RateLimiter:
    """Sliding-window limiter, keyed by client IP, held in memory."""

    def __init__(self, max_events, window_seconds):
        self._max = max_events
        self._window = window_seconds
        self._hits = {}
        self._lock = threading.Lock()

    _SWEEP_AT = 1024

    def allow(self, key):
        now = time.monotonic()
        with self._lock:
            recent = [t for t in self._hits.get(key, []) if now - t < self._window]
            if len(recent) >= self._max:
                self._hits[key] = recent
                return False
            recent.append(now)
            self._hits[key] = recent
            # Opportunistic sweep so idle keys cannot accumulate without bound.
            if len(self._hits) > self._SWEEP_AT:
                for k in [k for k, v in self._hits.items() if now - v[-1] >= self._window]:
                    del self._hits[k]
            return True


class TelegramSender:
    def __init__(self, config, opener=None):
        self._config = config
        self._opener = opener or urllib.request.urlopen

    def send(self, text):
        url = "%s/bot%s/sendMessage" % (self._config.api_base, self._config.token)
        body = urllib.parse.urlencode({
            "chat_id": self._config.chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="POST")
        with self._opener(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not payload.get("ok"):
            raise RuntimeError("telegram rejected the message")


def make_handler(config, sender, limiter):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AntiManagerFeedback"
        sys_version = ""

        def _send_json(self, status, obj):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _path(self):
            return (self.path.split("?")[0].rstrip("/") or "/")

        def _client_ip(self):
            # Trust boundary: the service is reachable only through nginx on the
            # shared Docker network, and nginx overwrites both headers with the
            # real peer ($remote_addr). Never expose this port directly — a direct
            # client could then spoof the header and bypass the rate limiter.
            for header in ("X-Real-IP", "X-Forwarded-For"):
                value = self.headers.get(header)
                if value:
                    return value.split(",")[0].strip()
            return self.client_address[0]

        def do_GET(self):
            path = self._path()
            if path == "/healthz":
                self._send_json(200, {"ok": True})
            elif path == "/api/feedback":
                self._send_json(405, {"error": "method not allowed"})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self):
            if self._path() != "/api/feedback":
                self._send_json(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_BODY:
                self._send_json(400, {"error": "invalid"})
                return
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self._send_json(400, {"error": "invalid"})
                return

            # Honeypot: a filled hidden field means a bot — accept and drop silently.
            if isinstance(payload, dict) and str(payload.get("website") or "").strip():
                self._send_json(200, {"ok": True})
                return

            data, _error = validate(payload)
            if data is None:
                self._send_json(400, {"error": "invalid"})
                return

            if not limiter.allow(self._client_ip()):
                self._send_json(429, {"error": "too many requests"})
                return

            try:
                sender.send(format_message(data))
            except Exception as exc:  # noqa: BLE001 - never leak delivery details
                print("telegram send failed: %s" % exc, file=sys.stderr)
                self._send_json(502, {"error": "delivery failed"})
                return
            self._send_json(200, {"ok": True})

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    return Handler


def build_server(config, sender=None, limiter=None):
    sender = sender or TelegramSender(config)
    limiter = limiter or RateLimiter(config.rate_max, config.rate_window)
    return ThreadingHTTPServer(("0.0.0.0", config.port), make_handler(config, sender, limiter))


def main():
    config = Config(os.environ)
    if not config.token or not config.chat_id:
        print("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required", file=sys.stderr)
        return 2
    server = build_server(config)
    print("feedback service listening on :%d" % config.port, file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
