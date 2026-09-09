# Telegram Assistant Bot

A personal-assistant Telegram bot built with [Telethon](https://docs.telethon.dev/).

**Features**
- `/start`, `/help` — owner sees a management menu; everyone else sees a welcome message
- Forwards DMs from other users to you, and lets you reply back through the bot
- `/assistant on|off|status` — turn message-forwarding on/off
- `/alive`, `/ping` — customizable status cards (cycle styles, toggle quotes, reset)
- `/whisper <text>` (used as a reply) — sends a secret note only the sender and the replied-to user can reveal

No owner name, usernames, or branding are hardcoded anywhere — everything comes from environment variables.

## 1. Get your credentials

| Variable | Where to get it |
|---|---|
| `API_ID`, `API_HASH` | https://my.telegram.org → API Development Tools |
| `BOT_TOKEN` | Message [@BotFather](https://t.me/BotFather) → `/newbot` |
| `OWNER_ID` | Message [@userinfobot](https://t.me/userinfobot) to get your numeric ID |

## 2. Run locally

```bash
cp .env.example .env
# edit .env with your real values
pip install -r requirements.txt
python main.py
```

## 3. Deploy on Render

**Option A — Blueprint (recommended)**
1. Push this folder to a GitHub repo.
2. In Render: **New → Blueprint**, point it at your repo (it will read `render.yaml`).
3. Render will ask you to fill in the env vars (`API_ID`, `API_HASH`, `BOT_TOKEN`, `OWNER_ID`, `OWNER_NAME`, `SUPPORT_URL`) — enter them and deploy.

**Option B — Manual**
1. Push this folder to a GitHub repo.
2. In Render: **New → Background Worker** (not "Web Service" — this bot doesn't listen on a port).
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Add the environment variables listed above under the **Environment** tab.
6. Deploy.

> Important: this bot must run as a **Background Worker**, not a Web Service — Telethon's polling loop doesn't bind to an HTTP port, so a Web Service would fail Render's health check.

## 4. Notes on persistence

- `DB/assistant_db.json` and `DB/alive_config.json` store users/stats/settings on disk.
- Render's free-tier disks are **ephemeral** — these files (and the `bot_session` login session) reset on redeploy or restart. For durable storage across deploys, attach a [Render Disk](https://render.com/docs/disks) or switch to an external database.

## Project structure

```
.
├── main.py               # entry point
├── config.py              # reads all settings from environment variables
├── plugins/
│   ├── assistant.py        # menus, message forwarding, owner replies
│   ├── alive.py             # /alive and /ping customization
│   └── whisper.py           # secret whisper messages
├── requirements.txt
├── Procfile
├── render.yaml
└── .env.example
```
