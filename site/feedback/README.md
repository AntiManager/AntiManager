# Feedback microservice

Receives submissions from the `/contact/` form on antimanager.pro and forwards them to a
Telegram chat via the bot, so no personal data is stored on the site.

- Stack: Python 3, standard library only (image `python:3.12-alpine`, no dependencies).
- Endpoint: `POST /api/feedback` (JSON). Health probe: `GET /healthz`.
- The bot token lives only in a server-side env file and is never sent to a client.

## Contract

`POST /api/feedback`

```json
{ "name": "…", "contact": "…", "message": "…", "pack": "process", "consent": true, "website": "" }
```

- `name` 1–100, `contact` 1–200, `message` 1–3000 chars; `consent` must be `true`.
- `pack` is an optional context slug (`express|process|library|pilot`) mapped to a Russian label.
- `website` is a honeypot: if non-empty the request is accepted (`200`) and dropped silently.
- Responses: `200 {"ok":true}`, `400 {"error":"invalid"}`, `429 {"error":"too many requests"}`,
  `502 {"error":"delivery failed"}`. Rate limiting is per client IP, in memory.

## Configuration (env)

| Key | Default | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | **required** |
| `TELEGRAM_CHAT_ID` | — | **required**; the owner's private chat id |
| `PORT` | `8080` | |
| `TELEGRAM_API_BASE` | `https://api.telegram.org` | test seam |
| `RATE_LIMIT_MAX` | `5` | submissions per IP per window |
| `RATE_LIMIT_WINDOW` | `600` | seconds |

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
