# Supermod

Supermod is a Discord bot that automates moderation and community tasks for the **Omnivoracious Listeners**
music-discussion server: a question of the day, album submissions, weekly newsletters, and scheduled promotions,
all backed by Google Sheets.

## Overview

- **Entry point:** `uv run supermod`
- **Command prefix:** `,` (case-insensitive).
- **Deployment:** the `super-mod` [Heroku](https://www.heroku.com/) app (worker dyno).

## Features

- **General** — utility commands, including archiving a channel to an HTML transcript.
- **Newsletter** — builds the weekly newsletter and splits albums into genre channels.
- **Promotions** — posts creator, friend, and partner ads on a schedule.
- **QOTD** — collects, approves, and posts a Question of the Day on a daily schedule.
- **Submissions** — manages album submissions to the masterlists (fetching, approving/rejecting, duplicate and
  prior-discussion checks, replacing old submissions, search).
- **Submissions Status** — posts the scheduled "submissions open" / "closed" announcements.

## Development

### Requirements

- Python **3.13**
- [uv](https://docs.astral.sh/uv/) for dependency management
- A Discord bot token and a Google service account

### Setup

```bash
uv sync                # create the venv and install deps
touch .local           # mark this as a local-dev run (gitignored)
uv run supermod        # or: uv run python -m supermod
```

### Credentials

Credentials load differently per mode:

- **Development** (`.local` present): read from `.secrets/.env` and the `.secrets/service_account.json` file (gitignored).
- **Deployment** (no marker): read from environment variables, with the Google service-account JSON passed as a single
  `SERVICE_ACCOUNT_CRED` variable.

## Deployment (Heroku)

The bot runs as a worker dyno ([`Procfile`](Procfile): `worker: python -m supermod`) on the **Heroku-24** stack, with the Python
version pinned by `.python-version` (`3.13`).

To deploy:

```bash
git push heroku main                       # build and release
heroku ps -a super-mod                     # ensure the worker is running
heroku logs --tail -a super-mod
```
