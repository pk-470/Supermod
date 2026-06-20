# Supermod

Supermod is a Discord bot that automates moderation and community tasks for the
**Omnivoracious Listeners** music-discussion server: a question of the day, album
submissions, weekly newsletters, and scheduled promotions, all backed by Google Sheets.

## Features

Each feature is a [discord.py](https://discordpy.readthedocs.io/) extension (cog),
auto-discovered from `supermod/features/`:

- **QOTD** — collects, approves, and posts a Question of the Day on a daily schedule.
- **Submissions** — manages album submissions to the masterlists (fetching,
  approving/rejecting, duplicate and prior-discussion checks, replacing old
  submissions, search).
- **Submissions Status** — posts the scheduled "submissions open" / "closed" announcements.
- **Promotions** — posts creator, friend, and partner ads on a schedule.
- **Newsletter** — builds the weekly newsletter and splits albums into genre channels.
- **General** — utility commands, including archiving a channel to an HTML transcript.

## Architecture

- **Entry point:** `main.py` builds the `Supermod` bot and, on `on_ready`, loads
  every feature package under `supermod/features/`.
- **Command prefix:** `,` (case-insensitive).
- **Storage:** Google Sheets via [gspread](https://docs.gspread.org/) and a service account.
- **Scheduling:** `discord.ext.tasks` loops on `America/Toronto` time.

## Requirements

- Python **3.13**
- A Discord bot token and a Google service account

## Local development

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Set `local_mode="ON"` in `main.py`'s `run_bot(...)` call to run locally. In local
mode, credentials are read from `.tokens/.env` (via `python-dotenv`) and
`.tokens/service_account.json`; in deployment (`local_mode="OFF"`) they come from
environment variables, with the service account supplied as `SERVICE_ACCOUNT_CRED`.
Configuration (Discord token, sheet URLs, channel and role IDs) is read in the
`supermod/features/*/*_constants.py` modules.

## Deployment (Heroku)

The bot runs as a worker dyno (`Procfile`: `worker: python main.py`) on the
**Heroku-24** stack, with the Python version pinned by `.python-version` (`3.13`).

To migrate an existing app from an older stack and deploy:

```bash
heroku stack:set heroku-24 -a YOUR_APP_NAME   # point at the Heroku-24 stack
git push heroku main                          # rebuild is required for the stack change
heroku ps -a YOUR_APP_NAME                    # ensure the worker is running
heroku logs --tail -a YOUR_APP_NAME
```
