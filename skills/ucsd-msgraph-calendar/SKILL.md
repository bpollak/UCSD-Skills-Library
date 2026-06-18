---
name: ucsd-msgraph-calendar
description: |
  Query Microsoft Exchange/365 calendars via Microsoft Graph API using OAuth2
  device code flow. Use when a user asks about their schedule, meetings, or
  availability. Trigger on: "my calendar", "what meetings", "today's schedule",
  "what am I doing", "check calendar", "am I free", "meeting with", "calendar",
  "schedule", "agenda", "this afternoon", "this week", "appointment".
catalog:
  title: UCSD Microsoft Graph Calendar
  description: >-
    Query Exchange/365 calendars via Microsoft Graph API using OAuth2 device code
    authentication. Use to check schedules, meetings, and availability across
    sessions with cached token refresh.
  category: Campus AI Tools
  status: built
  publicationStatus: draft
  tier: experimental
  owner: AI Tools
  updated: 2026-06-18
allowed-tools: Read, Bash, WebFetch
---

# UCSD Microsoft Graph Calendar

Query Exchange/365 calendars via the Microsoft Graph API using OAuth2 device code authentication. Supports today's schedule, specific dates, and recurring queries across sessions via cached token refresh.

## When to use

- User asks "What meetings do I have today/this afternoon/this week?"
- User asks "Check my calendar for [date]"
- User asks "Who am I meeting with?" or "Am I free at [time]?"
- User asks about their schedule, availability, or agenda

## Setup (one-time per user)

1. **Install the dependency:**
   ```bash
   pip install msal
   ```

2. **Run the auth script** — it auto-creates a config template:
   ```bash
   python3 scripts/graph_auth.py
   ```
   This creates `~/.config/ucsd-msgraph-calendar/config.json` with setup instructions.

3. **Create an Azure AD app registration** (see [`references/azure-app-setup.md`](references/azure-app-setup.md) for step-by-step):
   - Go to https://entra.microsoft.com → App registrations → New registration
   - Enable **Allow public client flows** under Authentication
   - Add delegated API permissions: `Calendars.Read`, `User.Read`
   - Note the Application (client) ID and Directory (tenant) ID

4. **Fill in the config** at `~/.config/ucsd-msgraph-calendar/config.json`:
   ```json
   {
     "auth": {
       "client_id": "your-application-id",
       "tenant_id": "your-directory-id",
       "account_hint": "your.email@ucsd.edu"
     }
   }
   ```

5. **Authenticate:** Run the script again — it will give you a code to enter at https://microsoft.com/devicelogin. The token caches locally for 90-day silent refresh.

## Usage

```bash
# Show today's calendar
python3 scripts/graph_auth.py --calendar-today

# Show a specific date
python3 scripts/graph_auth.py --calendar-date 2026-07-01

# Re-authenticate (force new device code flow)
python3 scripts/graph_auth.py --force

# Show setup instructions again
python3 scripts/graph_auth.py --setup

# Show non-secret auth diagnostics
python3 scripts/graph_auth.py --diagnostics
```

## Agent workflow

When a user asks about their calendar:

1. Check if the config file exists at `~/.config/ucsd-msgraph-calendar/config.json`
   - If not, walk the user through **Setup** steps 1–5 above
2. Verify the config has real values (not `YOUR_*` placeholders)
   - If placeholders remain, guide the user to fill them in
3. Run `python3 scripts/graph_auth.py --calendar-today` (or with `--calendar-date YYYY-MM-DD`)
4. Present the results, filtering out the user as an attendee

## Guardrails

- Do **not** read or share the token cache at `~/.cache/ucsd-msgraph-calendar/token_cache.json` — it contains sensitive auth tokens
- Do **not** commit config files or tokens to repositories
- The `msal` and `requests` libraries make network calls to `login.microsoftonline.com` and `graph.microsoft.com` — this is expected and necessary
- Token-bearing Microsoft Graph calls are restricted to the approved `graph.microsoft.com` endpoint
- If the token has expired and silent refresh fails, the user will need to re-authenticate via device code flow

## Files

| Path | Purpose |
|---|---|
| `scripts/graph_auth.py` | Auth + calendar query module (parameterized via config) |
| `references/azure-app-setup.md` | Step-by-step Azure AD app registration guide |
| `~/.config/ucsd-msgraph-calendar/config.json` | Per-user config (auto-created on first run) |
| `~/.cache/ucsd-msgraph-calendar/token_cache.json` | OAuth token cache (auto-managed, never share) |

## Dependencies

- Python 3.10+
- `msal` (`pip install msal`)
- `requests` (`pip install requests`, or use stdlib `urllib`)
