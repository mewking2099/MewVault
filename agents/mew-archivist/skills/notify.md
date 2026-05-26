---
name: notify
triggers: [notify me, send me a message, telegram, slack notification, notify when done, send notification, ping me, alert me]
description: Send notifications via Telegram or Slack. Use at session wrap, when a milestone is hit, or when a blocker is found. Handles message formatting and API delivery.
inject: on-trigger
claude_code_skills: []
source: mewvault/custom
---

# Notify Skill

Send notifications to Telegram or Slack from MewVault sessions.

## Setup

Store credentials once:
```bash
# Telegram (recommended — easiest setup)
mew secret set TELEGRAM_BOT_TOKEN   # from @BotFather
mew secret set TELEGRAM_CHAT_ID     # your personal chat ID

# Slack (incoming webhook)
mew secret set SLACK_WEBHOOK_URL    # from Slack App → Incoming Webhooks
```

**Getting your Telegram chat ID**: Message your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` — the `id` field in `chat` is your chat ID.

## Sending a notification

### Telegram
```python
import requests, subprocess

token = subprocess.check_output(["mew","secret","get","TELEGRAM_BOT_TOKEN"]).decode().strip()
chat_id = subprocess.check_output(["mew","secret","get","TELEGRAM_CHAT_ID"]).decode().strip()

def notify_telegram(message: str):
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
    )

notify_telegram("*MewVault* — session wrap complete ✓\n\n- Wrote 3 skills\n- Updated routing index\n- Suggested commit: `feat: phase-2 skills`")
```

### Slack
```python
import requests, subprocess

webhook = subprocess.check_output(["mew","secret","get","SLACK_WEBHOOK_URL"]).decode().strip()

def notify_slack(message: str):
    requests.post(webhook, json={"text": message})

notify_slack("*MewVault* — session wrap complete\n• Wrote 3 skills\n• Updated routing index")
```

## Message format guidelines

Keep notifications short — they're alerts, not reports:

```
*[Project]* — [status emoji]
• [What completed]
• [What's next / blocked]
[commit suggestion if applicable]
```

Status emojis:
- ✓ / ✅ — completed, wrapped
- ⚠️ — blocked, at risk
- 🔁 — in progress
- 📌 — reminder

## When to auto-notify

The `session-wrap` skill calls this automatically if credentials are configured. Also trigger manually when:
- A long-running task finishes (feasibility scan, research sweep)
- A MewKing plan is ready for review
- A blocker is found that needs human attention
- A milestone in Project_Status.md changes phase

## Checking if credentials are set

```python
import subprocess

def creds_available(key: str) -> bool:
    try:
        result = subprocess.run(["mew","secret","get", key], capture_output=True)
        return result.returncode == 0 and result.stdout.strip()
    except Exception:
        return False

use_telegram = creds_available("TELEGRAM_BOT_TOKEN") and creds_available("TELEGRAM_CHAT_ID")
use_slack = creds_available("SLACK_WEBHOOK_URL")
```

If neither is configured, skip silently — never fail a session wrap just because notifications aren't set up.

## MewVault context

- Notification credentials → `mewvault/secrets/` via `mew secret set`
- `session-wrap` skill should call this as a final step if available
- Keep messages under 200 characters for Telegram push notification previews
- Never include file paths, secrets, or internal IDs in notification text
