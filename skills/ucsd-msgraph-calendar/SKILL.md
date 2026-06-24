---
name: ucsd-msgraph-calendar
description: |
  Query Microsoft Exchange/365 calendars AND email via Microsoft Graph API
  using OAuth2 device code flow. Use when a user asks about their schedule,
  meetings, availability, or outstanding/flagged emails. Trigger on: "my
  calendar", "what meetings", "today's schedule", "what am I doing", "check
  calendar", "am I free", "meeting with", "calendar", "schedule", "agenda",
  "this afternoon", "this week", "appointment", "outstanding emails",
  "inbox", "unread emails", "follow up", "email follow-up".
catalog:
  title: UCSD Microsoft Graph Calendar + Email
  description: >-
    Query Exchange/365 calendars and email via Microsoft Graph API using OAuth2
    device code authentication. Use to check schedules, meetings, availability,
    and email inbox across sessions with cached token refresh.
  category: Campus AI Tools
  status: built
  publicationStatus: ready
  tier: verified
  owner: AI Tools
  updated: 2026-06-23
allowed-tools: Read, Bash, WebFetch
---

# UCSD Microsoft Graph Calendar + Email

Query Exchange/365 calendars and email via the Microsoft Graph API using OAuth2 device code authentication. Supports today's schedule, specific dates, inbox queries, email search, and recurring queries across sessions via cached token refresh.

## When to use

- User asks "What meetings do I have today/this afternoon/this week?"
- User asks "Check my calendar for [date]"
- User asks "Who am I meeting with?" or "Am I free at [time]?"
- User asks about their schedule, availability, or agenda
- User asks "Are there any outstanding emails I should follow up on?"
- User asks about unread emails, flagged emails, or their inbox
- User asks to search for emails from a specific person

## Setup (one-time per user)

1. **Install the dependency:**
   ```bash
   pip install msal requests
   ```

2. **Run the auth script** — it auto-creates a config template:
   ```bash
   python3 harness-auth/graph_auth.py
   ```
   This creates `~/.config/ucsd-msgraph-calendar/config.json` with setup instructions.

3. **Create an Azure AD app registration** (see [`references/azure-app-setup.md`](references/azure-app-setup.md) for step-by-step):
   - Go to https://entra.microsoft.com → App registrations → New registration
   - Enable **Allow public client flows** under Authentication
   - Add delegated API permissions: `Calendars.Read`, `User.Read`, **`Mail.Read`**, **`Mail.ReadWrite`** (required for creating draft emails)
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

### Calendar
```bash
# Show today's calendar
python3 harness-auth/graph_auth.py --calendar-today

# Show a specific date
python3 harness-auth/graph_auth.py --calendar-date 2026-07-01
```

### Email
```bash
# Show last 10 inbox messages
python3 harness-auth/graph_auth.py --email-recent

# Show last N inbox messages
python3 harness-auth/graph_auth.py --email-recent 25

# Show unread messages
python3 harness-auth/graph_auth.py --email-unread

# Search all folders for a person or topic
python3 harness-auth/graph_auth.py --email-search "Selina Martin"
```

### Auth management
```bash
# Force re-authentication (device code flow)
python3 harness-auth/graph_auth.py --force

# Check token status
python3 harness-auth/graph_auth.py

# Print access token (for debugging)
python3 harness-auth/graph_auth.py --token-only

# Show setup instructions
python3 harness-auth/graph_auth.py --setup
```

## Agent workflow

### Calendar query
When a user asks about their calendar:
1. Check if the config file exists at `~/.config/ucsd-msgraph-calendar/config.json`
   - If not, walk the user through **Setup** steps 1–5 above
2. Verify the config has real values (not `YOUR_*` placeholders)
   - If placeholders remain, guide the user to fill them in
3. Run the auth script:
   - `python3 harness-auth/graph_auth.py --calendar-today` (or with `--calendar-date YYYY-MM-DD`)
   - If it fails with an auth error, run `python3 harness-auth/graph_auth.py --force` and guide the user through device code flow
4. Present the results, filtering out the user as an attendee

### Email query
When a user asks about emails / outstanding items:
1. Run `python3 harness-auth/graph_auth.py --email-recent 30` to get a broad view
2. If unread messages are requested, run with `--email-unread`
3. For specific people/topics, use `--email-search "Name"`
4. If the token is expired and silent refresh fails, the agent should:
   a. Run `python3 harness-auth/graph_auth.py --force` to trigger device code flow
   b. Present the user with the URL and code
   c. Retry the original query after auth completes

### Drafting or sending email — REQUIRED: Load email-communication-policy skill first
Before composing, replying to, or sending any email, the agent MUST load the
`email-communication-policy` skill and follow its rules:
- Always draft first, save to Drafts folder — never send without explicit approval
- For replies, use `createReply` on the source message to preserve threading
- Append the verified signature format + TritonAI Harness disclosure
- Present the draft to the user for review; send only on approval

### Token refresh / maintenance
When the auth script fails with a token error:
1. **First try silent refresh** — run `python3 harness-auth/graph_auth.py` (no flags); MSAL attempts auto-refresh using the cached refresh token
2. **If that fails** (refresh token expired — 90-day lifetime), force re-auth:
   ```bash
   python3 harness-auth/graph_auth.py --force
   ```
3. Present the device code URL and code to the user
4. After the user authenticates in their browser, retry the original query
5. The new token caches automatically for another 90 days

The most common failure mode is the access token expiring after ~1 hour. MSAL silently refreshes it using the refresh token (valid ~90 days). If the refresh token itself has expired, the user needs to re-authenticate via device code flow.

## Guardrails

- Do **not** read or share the token cache at `~/.cache/ucsd-msgraph-calendar/token_cache.json` — it contains sensitive auth tokens
- Do **not** commit config files or tokens to repositories
- The `msal` and `requests` libraries make network calls to `login.microsoftonline.com` and `graph.microsoft.com` — this is expected and necessary
- If the token has expired and silent refresh fails, the user will need to re-authenticate via device code flow
- Do **not** read message bodies by default — only read subjects and metadata unless the user explicitly asks for content
- Treat email data as sensitive (P2/P3 data per UCSD classification)

## Files

| Path | Purpose |
|---|---|
| `harness-auth/graph_auth.py` | Auth + calendar + email query module (parameterized via config) |
| `SKILL.md` | This skill definition file |
| `~/.config/ucsd-msgraph-calendar/config.json` | Per-user config (auto-created on first run) |
| `~/.cache/ucsd-msgraph-calendar/token_cache.json` | OAuth token cache (auto-managed, never share) |

## Dependencies

- Python 3.10+
- `msal` (`pip install msal`)
- `requests` (`pip install requests`, or use stdlib `urllib`)
