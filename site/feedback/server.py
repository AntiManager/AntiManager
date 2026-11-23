#!/usr/bin/env python3
"""AntiManager feedback microservice.

Receives feedback-form submissions over HTTP and forwards them to a Telegram
chat via the Bot API. Standard library only: no third-party dependencies.

Endpoints:
  POST /api/feedback  {"name","contact","message","pack","consent","website"}
  GET  /healthz       liveness probe (not proxied publicly)

The bot token is read from the environment and never returned to a client.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
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

# Anti-bot tuning. The proof of work is a speed bump for stateless form fillers,
# not a wall: the real filter is the signed challenge (a bot must fetch one and
# solve it) plus the heuristics below.
POW_BITS = 16                # leading zero bits the client must find
CHALLENGE_TTL = 2 * 60 * 60  # a challenge older than this is stale
MIN_FILL_TIME = 2.0          # a signed challenge younger than this means a bot
CLOCK_SKEW = 60              # tolerated client/server clock skew

# Minimal HTML page returned to a no-JS browser that submits the form natively
# (application/x-www-form-urlencoded). API clients still get JSON.
HTML_NOTICE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — AntiManager</title></head>
<body style="font-family:system-ui,sans-serif;background:#0a0a0a;color:#fff;max-width:34rem;margin:4rem auto;padding:0 1.25rem;line-height:1.6">
<h1 style="font-size:1.5rem">{title}</h1>
<p><a href="/contact/" style="color:#ef4444">Вернуться на сайт</a></p>
</body></html>"""

# Context labels for the "Интересует" line. Keys match the ?pack= slugs the
# offer CTAs pass to /contact/.
PACK_LABELS = {
    "express": "Экспресс-диагностика",
    "process": "Проработка процессов",
    "library": "Библиотека + правила",
    "pilot": "Одна пилотная группа",
    "audit": "Полный чек-лист ПС (120 критериев)",
    "documents": "Типовые документы производственной системы",
}


class Config:
    def __init__(self, env):
        self.token = (env.get("TELEGRAM_BOT_TOKEN") or "").strip()
        self.chat_id = (env.get("TELEGRAM_CHAT_ID") or "").strip()
        self.port = int(env.get("PORT") or "8080")
        self.api_base = (env.get("TELEGRAM_API_BASE") or "https://api.telegram.org").rstrip("/")
        self.rate_max = int(env.get("RATE_LIMIT_MAX") or "5")
        self.rate_window = int(env.get("RATE_LIMIT_WINDOW") or "600")
        self.global_max = int(env.get("GLOBAL_RATE_LIMIT_MAX") or "120")
        self.global_window = int(env.get("GLOBAL_RATE_LIMIT_WINDOW") or "3600")
        self.quarantine_chat_id = (env.get("TELEGRAM_QUARANTINE_CHAT_ID") or "").strip()
        self.pow_bits = int(env.get("POW_BITS") or str(POW_BITS))
        # The challenge signing key is a domain-separated derivation of the bot
        # token, so the service stays zero-config and challenges survive a
        # restart. An explicit CHALLENGE_SECRET overrides it.
        explicit = (env.get("CHALLENGE_SECRET") or "").strip()
        self.challenge_secret = (
            explicit.encode("utf-8") if explicit
            else hmac.new(self.token.encode("utf-8"), b"feedback-challenge-v1",
                          hashlib.sha256).digest()
        )


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
    # The message is optional: name + contact are the required minimum.
    if len(message) > MAX_MESSAGE:
        return None, "invalid message"
    if pack not in PACK_LABELS:
        pack = ""  # an unknown pack is not fatal; drop it rather than reject.
    return {"name": name, "contact": contact, "message": message, "pack": pack}, None


def format_message(data, prefix=""):
    """Plain-text Telegram message (no parse_mode, so user text cannot inject markup).

    `prefix` (e.g. a quarantine warning) is prepended and eats into the length
    budget so the whole message still fits Telegram's limit.
    """
    if prefix:
        prefix = prefix + "\n\n"
    budget = max(TELEGRAM_TEXT_LIMIT - len(prefix), 0)
    pack = PACK_LABELS.get(data["pack"], "")
    lines = [
        "🔔 Заявка с сайта",
        "Имя: " + data["name"],
        "Контакт: " + data["contact"],
        "Интересует: " + (pack if pack else "—"),
    ]
    if data["message"]:
        lines += ["", "Сообщение:", data["message"]]
    else:
        lines.append("Сообщение: —")
    return prefix + "\n".join(lines)[:budget]


# --- Challenge / proof of work ----------------------------------------------
#
# GET /api/feedback/challenge returns a short-lived, HMAC-signed challenge. The
# client grinds SHA-256 over "<challenge>:<nonce>" until the digest has `bits`
# leading zero bits and submits the nonce. A stateless form filler (the observed
# threat) never calls the endpoint, so it lands in quarantine. The signed issue
# time also gives the server an unforgeable "time spent on the form" signal.

class Challenge:
    """Issues and verifies signed proof-of-work challenges."""

    def __init__(self, secret, bits, ttl=CHALLENGE_TTL, min_fill=MIN_FILL_TIME, clock_skew=CLOCK_SKEW):
        self._secret = secret
        self._bits = bits
        self._ttl = ttl
        self._min_fill = min_fill
        self._skew = clock_skew
        self._used = {}
        self._lock = threading.Lock()

    def _sign(self, challenge, bits, issued):
        msg = ("%s.%d.%d" % (challenge, bits, issued)).encode("utf-8")
        return hmac.new(self._secret, msg, hashlib.sha256).hexdigest()

    def issue(self, now=None):
        issued = int(now if now is not None else time.time())
        challenge = secrets.token_hex(16)
        return {
            "challenge": challenge,
            "bits": self._bits,
            "issued": issued,
            "signature": self._sign(challenge, self._bits, issued),
        }

    def verify(self, payload, now=None):
        """Return (ok, issued, reason). `reason` is None on success."""
        now = now if now is not None else time.time()
        try:
            challenge = str(payload.get("challenge") or "")
            nonce = str(payload.get("challenge_nonce") or "")
            issued = int(payload.get("challenge_issued"))
            bits = int(payload.get("challenge_bits"))
            signature = str(payload.get("challenge_signature") or "")
        except (TypeError, ValueError):
            return False, None, "no_challenge"
        if not challenge or not nonce or bits <= 0 or bits > 32:
            return False, None, "no_challenge"
        expected = self._sign(challenge, bits, issued)
        # Compare bytes: compare_digest raises TypeError on non-ASCII str, which
        # a hostile client could use to turn a bad challenge into a 500.
        if not hmac.compare_digest(expected.encode("utf-8"), signature.encode("utf-8", "replace")):
            return False, None, "bad_challenge"
        if issued > now + self._skew or now - issued > self._ttl:
            return False, issued, "stale_challenge"
        if now - issued < self._min_fill:
            return True, issued, "too_fast"
        if not leading_zero_bits("%s:%s" % (challenge, nonce), bits):
            return False, issued, "bad_pow"
        with self._lock:
            self._sweep(now)
            if challenge in self._used:
                return False, issued, "replay"
            self._used[challenge] = issued + self._ttl
        return True, issued, None

    def _sweep(self, now):
        if len(self._used) > 2048:
            for key in [k for k, expiry in self._used.items() if expiry < now]:
                del self._used[key]


def leading_zero_bits(text, bits):
    """True when sha256(text) has at least `bits` leading zero bits."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    value = int.from_bytes(digest, "big")
    return value.bit_length() <= (len(digest) * 8 - bits)


# --- Content heuristics ------------------------------------------------------

CYRILLIC = re.compile(r"[А-Яа-яЁё]")
LATIN_NAME = re.compile(r"^[A-Za-z][A-Za-z .'\-]*$")
RANDOM_MAILBOX = re.compile(r"^[a-z]{6,}\d{2,}@", re.IGNORECASE)
PRICE_WORDS = re.compile(
    r"\b(price|pricing|precio|prezzo|preis|pretium|cost|цена|стоимость)\b", re.IGNORECASE)
URL_IN_TEXT = re.compile(
    r"(https?://|www\.|\b[a-z0-9-]+\.(?:com|net|org|ru|io|xyz|top|shop|site|online)\b)",
    re.IGNORECASE)

# A single strong signal quarantines; otherwise two weak ones do. Quarantine is
# still delivered (with a warning prefix), so a false positive costs the owner a
# glance rather than a lost lead.
STRONG_SIGNALS = {"latin_only", "link_in_message"}


def suspicion(data, has_challenge):
    """Return the list of spam signals for an otherwise valid submission."""
    reasons = []
    text = data["name"] + " " + data["message"]
    if not CYRILLIC.search(text):
        reasons.append("latin_only")
        # Only judge detail when a message exists: an empty optional message is
        # a legitimate short lead, not a "short_no_detail" spam signal.
        if data["message"] and len(data["message"].split()) <= 12 and not re.search(r"\d", data["message"]):
            reasons.append("short_no_detail")
        if data["message"] and PRICE_WORDS.search(data["message"]):
            reasons.append("price_probe")
    if LATIN_NAME.match(data["name"]):
        reasons.append("latin_name")
    if RANDOM_MAILBOX.match(data["contact"]):
        reasons.append("random_mailbox")
    if URL_IN_TEXT.search(data["message"]):
        reasons.append("link_in_message")
    if not has_challenge:
        reasons.append("no_challenge")
    return reasons


def is_quarantine(reasons):
    if any(reason in STRONG_SIGNALS for reason in reasons):
        return True
    weak = [reason for reason in reasons if reason != "no_challenge"]
    return len(weak) >= 2


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

    def send(self, text, chat_id=None):
        url = "%s/bot%s/sendMessage" % (self._config.api_base, self._config.token)
        body = urllib.parse.urlencode({
            "chat_id": chat_id or self._config.chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="POST")
        with self._opener(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not payload.get("ok"):
            raise RuntimeError("telegram rejected the message")


def make_handler(config, sender, limiter, challenge, global_limiter):
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

        def _send_html(self, status, title):
            body = HTML_NOTICE.format(title=title).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _is_form(self):
            ctype = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            return ctype == "application/x-www-form-urlencoded"

        def _parse_body(self, raw):
            """Parse the request body into a payload dict, or None when unreadable.

            JSON is the API contract; a no-JS browser form POST arrives as
            application/x-www-form-urlencoded, where a checked checkbox is sent
            as "consent=on" and is absent when unchecked.
            """
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                return None
            if self._is_form():
                fields = urllib.parse.parse_qs(text, keep_blank_values=True)
                payload = {key: value[0] for key, value in fields.items()}
                payload["consent"] = "consent" in fields
                return payload
            try:
                return json.loads(text)
            except ValueError:
                return None

        def _reply(self, status, obj, html_title):
            """JSON for API clients; a small HTML page for a no-JS browser submit."""
            accept = self.headers.get("Accept") or ""
            if self._is_form() and "text/html" in accept:
                self._send_html(status, html_title)
            else:
                self._send_json(status, obj)

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

        def _log_event(self, kind, reason):
            # No message text or contact — only the verdict, for tuning.
            print("feedback %s reason=%s ip=%s" % (kind, reason, self._client_ip()),
                  file=sys.stderr)

        def do_GET(self):
            path = self._path()
            if path == "/healthz":
                self._send_json(200, {"ok": True})
            elif path == "/api/feedback/challenge":
                self._send_json(200, challenge.issue())
            elif path == "/api/feedback":
                self._send_json(405, {"error": "method not allowed"})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self):
            if self._path() != "/api/feedback":
                self._reply(404, {"error": "not found"}, "Страница не найдена")
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_BODY:
                self._reply(400, {"error": "invalid"}, "Проверьте форму и попробуйте снова")
                return
            raw = self.rfile.read(length)
            payload = self._parse_body(raw)
            if payload is None:
                self._reply(400, {"error": "invalid"}, "Проверьте форму и попробуйте снова")
                return

            # Honeypot: a filled hidden field means a bot — accept and drop silently.
            # `url` is the current field name; `website` is kept for older clients.
            if isinstance(payload, dict) and any(
                str(payload.get(field) or "").strip()
                for field in ("url", "website", "email_confirm")
            ):
                self._log_event("drop", "honeypot")
                self._reply(200, {"ok": True}, "Заявка отправлена")
                return

            data, _error = validate(payload)
            if data is None:
                self._reply(400, {"error": "invalid"}, "Проверьте форму и попробуйте снова")
                return

            ip = self._client_ip()
            if not limiter.allow(ip):
                self._log_event("drop", "rate_ip")
                self._reply(429, {"error": "too many requests"}, "Слишком много заявок — напишите в Telegram")
                return
            if not global_limiter.allow("*"):
                self._log_event("drop", "rate_global")
                self._reply(429, {"error": "too many requests"}, "Слишком много заявок — напишите в Telegram")
                return

            challenge_ok, _issued, reason = challenge.verify(payload)
            if reason == "too_fast":
                # A signed challenge younger than MIN_FILL_TIME is a machine
                # filling the form instantly. Drop silently: no feedback loop.
                self._log_event("drop", "too_fast")
                self._reply(200, {"ok": True}, "Заявка отправлена")
                return

            reasons = suspicion(data, challenge_ok)
            quarantine = is_quarantine(reasons)
            if reason in ("bad_pow", "replay", "bad_challenge", "stale_challenge"):
                reasons.append(reason)

            try:
                if quarantine:
                    prefix = "⚠️ Возможно спам (%s)" % ", ".join(reasons)
                    sender.send(format_message(data, prefix),
                                chat_id=config.quarantine_chat_id or None)
                    self._log_event("quarantine", ",".join(reasons))
                else:
                    sender.send(format_message(data))
                    self._log_event("deliver", "ok")
            except Exception as exc:  # noqa: BLE001 - never leak delivery details
                print("telegram send failed: %s" % exc, file=sys.stderr)
                self._reply(502, {"error": "delivery failed"}, "Не удалось отправить — напишите в Telegram")
                return
            self._reply(200, {"ok": True}, "Заявка отправлена")

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    return Handler


def build_server(config, sender=None, limiter=None, challenge=None, global_limiter=None):
    sender = sender or TelegramSender(config)
    limiter = limiter or RateLimiter(config.rate_max, config.rate_window)
    challenge = challenge or Challenge(config.challenge_secret, config.pow_bits)
    global_limiter = global_limiter or RateLimiter(config.global_max, config.global_window)
    return ThreadingHTTPServer(
        ("0.0.0.0", config.port),
        make_handler(config, sender, limiter, challenge, global_limiter),
    )


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
