# Feedback microservice

Receives submissions from the `/contact/` form on antimanager.pro and forwards them to a
Telegram chat via the bot, so no personal data is stored on the site.

- Stack: Python 3, standard library only (image `python:3.12-alpine`, no dependencies).
- Endpoint: `POST /api/feedback` (JSON or a native form post). Health probe: `GET /healthz`.
  Anti-bot challenge: `GET /api/feedback/challenge`.
- The bot token lives only in a server-side env file and is never sent to a client.

## Contract

`GET /api/feedback/challenge` → `{"challenge","bits","issued","signature"}`. The client
finds a nonce such that `sha256("<challenge>:<nonce>")` has `bits` leading zero bits and sends
it back with the submission. The signature is an HMAC over `challenge.bits.issued`, so a bot
cannot backdate the issue time to defeat the fill-time trap and a challenge can be used once.

`POST /api/feedback`

```json
{
  "name": "…", "contact": "…", "message": "…", "pack": "process", "consent": true,
  "url": "",
  "challenge": "…", "challenge_bits": 16, "challenge_issued": 1763…,
  "challenge_signature": "…", "challenge_nonce": "12345"
}
```

- `name` 1–100, `contact` 1–200 chars, `consent` must be `true`; `message` is optional
  (0–3000 chars — an empty or omitted message is valid).
- `pack` is an optional context slug (`express|process|library|pilot|audit|documents`).
- `url` is the honeypot: any value (`url`, `website` or `email_confirm`) means a bot — the
  request is accepted (`200`) and dropped silently.
- The challenge fields are optional. Without them (the no-JS path) the message is still
  delivered unless the content heuristics flag it.

### Decisions

| Situation | Result |
|---|---|
| honeypot filled | `200`, dropped silently (`drop reason=honeypot`) |
| per-IP or global limit exceeded | `429` |
| valid challenge younger than 2 s | `200`, dropped silently (`drop reason=too_fast`) |
| valid challenge, clean content | delivered |
| valid challenge, suspicious content | delivered **quarantined** (`⚠️ Возможно спам (reasons)`) |
| no/expired/replayed challenge, clean content | delivered |
| no/expired/replayed challenge, suspicious content | delivered quarantined |

Suspicious signals: content with no Cyrillic at all (`latin_only`), a short non-empty message
with no digits (`short_no_detail`), price-probe words in Latin (`price_probe`), a generated-looking
mailbox (`random_mailbox`), a link in the message (`link_in_message`), a Latin-only name
(`latin_name`). A strong signal (`latin_only`, `link_in_message`) quarantines alone; otherwise
two weak ones do. Quarantine is deliberately **not** a drop: a false positive costs the owner a
glance, not a lost lead.

Responses: `200 {"ok":true}`, `400 {"error":"invalid"}`, `429 {"error":"too many requests"}`,
`502 {"error":"delivery failed"}`. Rate limiting is per client IP plus a global hourly backstop,
both in memory.

## Configuration (env)

| Key | Default | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | **required** |
| `TELEGRAM_CHAT_ID` | — | **required**; the owner's private chat id |
| `TELEGRAM_QUARANTINE_CHAT_ID` | same chat | optional; where quarantined messages go |
| `CHALLENGE_SECRET` | derived from the token | optional HMAC key override |
| `POW_BITS` | `16` | proof-of-work difficulty; lower = faster for users and bots |
| `PORT` | `8080` | |
| `TELEGRAM_API_BASE` | `https://api.telegram.org` | test seam |
| `RATE_LIMIT_MAX` | `5` | submissions per IP per window |
| `RATE_LIMIT_WINDOW` | `600` | seconds |
| `GLOBAL_RATE_LIMIT_MAX` | `120` | submissions per hour across all IPs |
| `GLOBAL_RATE_LIMIT_WINDOW` | `3600` | seconds |

## Local run

```bash
cd site/feedback
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=123 python server.py
```

## Tests

```bash
python -m unittest discover -s site/feedback/tests   # from the repository root
```

## Deploy (VPS)

The service runs as a Docker container named `antimanager-feedback` on the shared network
`vps_shared` (same network as `caddy` and `antimanager-web`). nginx in the site container
proxies `POST /api/feedback` to it, so it is never exposed directly.

1. On the VPS, create `$REMOTE_DIR/feedback.env` (the `REMOTE_DIR` from your `.env`) from
   `.env.example`, fill in the token and chat id, then `chmod 600 feedback.env`.
2. From the repository root: `powershell -File site/feedback/deploy.ps1` (reads `.env` for the
   VPS connection, builds the image on the server and restarts the container).
3. Deploy the site (`site/deploy.ps1`) so nginx picks up the `/api/feedback` location.

The container has no published port; only nginx on `vps_shared` can reach it.
