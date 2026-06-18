#!/usr/bin/env python3
"""Microsoft Graph Calendar — reusable auth + query for TritonAI harness.

Config: ~/.config/ucsd-msgraph-calendar/config.json (auto-created on first run)
Cache: ~/.cache/ucsd-msgraph-calendar/token_cache.json (auto-managed)

Usage:
    graph_auth.py                         # device code flow (interactive)
    graph_auth.py --force                 # re-authenticate
    graph_auth.py --diagnostics           # print non-secret auth diagnostics
    graph_auth.py --calendar-today        # print today's meetings
    graph_auth.py --calendar-date YYYY-MM-DD  # meetings on a specific date
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import msal
import requests

SKILL_NAME = "ucsd-msgraph-calendar"
CONFIG_DIR = os.path.expanduser(f"~/.config/{SKILL_NAME}")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.expanduser(f"~/.cache/{SKILL_NAME}")
CACHE_FILE = os.path.join(CACHE_DIR, "token_cache.json")
GRAPH_API_ROOT = "https://graph.microsoft.com/v1.0"
ALLOWED_GRAPH_HOSTS = {"graph.microsoft.com"}

DEFAULT_CONFIG = {
    "integration": "msgraph_calendar",
    "description": "Microsoft Graph Calendar access via TritonAI harness",
    "auth": {
        "type": "oauth2_device_code",
        "client_id": "YOUR_CLIENT_ID",
        "tenant_id": "YOUR_TENANT_ID",
        "scopes": ["Calendars.Read", "User.Read"],
        "account_hint": "user@organization.edu",
        "sign_in_url": "https://microsoft.com/devicelogin",
        "cache_file": CACHE_FILE,
    },
    "common_endpoints": {
        "calendar": "/me/calendarview?startDateTime={start}&endDateTime={end}",
        "user_profile": "/me",
    },
}


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _ensure_private_dir(path):
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)


def _repair_private_file(path):
    if os.path.exists(path):
        os.chmod(path, 0o600)


def _load_config():
    _ensure_dir(CONFIG_DIR)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)

    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    print("=" * 60)
    print("First-time setup required!")
    print(f"Config template created at: {CONFIG_FILE}")
    print()
    print("Edit it with your Microsoft Entra ID app registration details.")
    print("See the skill's references/azure-app-setup.md for step-by-step.")
    print()
    print("After editing the config, run this script again.")
    print("=" * 60)
    sys.exit(1)


def _save_cache(cache):
    _ensure_private_dir(CACHE_DIR)
    fd = os.open(CACHE_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(cache.serialize())
    _repair_private_file(CACHE_FILE)


def _load_cache():
    _ensure_private_dir(CACHE_DIR)
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        _repair_private_file(CACHE_FILE)
        with open(CACHE_FILE) as f:
            cache.deserialize(f.read())
    return cache


def _graph_url(path):
    parsed = urlparse(GRAPH_API_ROOT)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_GRAPH_HOSTS:
        raise RuntimeError("Microsoft Graph requests must use an approved HTTPS Graph host")
    return f"{GRAPH_API_ROOT.rstrip('/')}/{path.lstrip('/')}"


def _auth_diagnostics(result, auth):
    return {
        "authenticated": True,
        "expires_in": result.get("expires_in"),
        "scope": result.get("scope"),
        "token_type": result.get("token_type"),
        "account": result.get("id_token_claims", {}).get("preferred_username", auth["account_hint"]),
        "graph_api_root": GRAPH_API_ROOT,
        "cache_file": CACHE_FILE,
    }


def acquire_token(config, force=False):
    auth = config["auth"]
    authority = f"https://login.microsoftonline.com/{auth['tenant_id']}"

    cache = _load_cache()
    app = msal.PublicClientApplication(
        client_id=auth["client_id"],
        authority=authority,
        token_cache=cache,
    )

    account = None
    accounts = app.get_accounts(username=auth["account_hint"])
    if accounts:
        account = accounts[0]
    else:
        accounts = app.get_accounts()
        if accounts:
            account = accounts[0]

    if account and not force:
        result = app.acquire_token_silent(scopes=auth["scopes"], account=account)
        if result and "access_token" in result:
            _save_cache(cache)
            return result

    flow = app.initiate_device_flow(scopes=auth["scopes"])
    if "user_code" not in flow:
        raise RuntimeError(f"Device flow failed: {flow.get('error_description', flow)}")

    print("=" * 60)
    print("To sign in, open a browser and visit:")
    print(f"  {flow['verification_uri']}")
    print()
    print(f"Enter this code:  {flow['user_code']}")
    print("=" * 60)

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(f"Auth failed: {result.get('error_description', result)}")

    _save_cache(cache)
    return result


def get_events(config, date_str=None):
    result = acquire_token(config)
    token = result["access_token"]

    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    start = dt.strftime("%Y-%m-%d")
    end = (dt + timedelta(days=1)).strftime("%Y-%m-%d")

    headers = {
        "Authorization": f"Bearer {token}",
        "Prefer": 'outlook.timezone="Pacific Standard Time"',
    }
    url = _graph_url("/me/calendarview")
    resp = requests.get(
        url,
        headers=headers,
        params={"startDateTime": start, "endDateTime": end},
        timeout=30,
    )
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"API error: {data['error'].get('message', data['error'])}")

    return data.get("value", [])


def format_events(events, date_label, config):
    if not events:
        print(f"No events on {date_label}.")
        return

    meetings = []
    alldays = []
    user_email = config["auth"]["account_hint"].lower()
    user_parts = user_email.split("@")[0]
    user_variants = {
        user_email,
        user_parts,
        f"{user_parts}@ucsd.edu",
        "pollak, brett",
        "brett pollak",
    }

    for ev in events:
        start_raw = ev["start"]["dateTime"]
        end_raw = ev["end"]["dateTime"]
        is_allday = "T00:00:00" in start_raw and "T00:00:00" in end_raw

        start = start_raw.split("T")[1].split(".")[0][:5] if not is_allday else "all-day"
        end = end_raw.split("T")[1].split(".")[0][:5] if not is_allday else "all-day"
        subject = ev.get("subject", "(No subject)")
        location = ev.get("location", {}).get("displayName", "")
        loc_str = f" @ {location}" if location else ""
        attendees = [a.get("emailAddress", {}).get("name", "") for a in ev.get("attendees", [])]
        attendees = [a for a in attendees if a.lower() not in user_variants]
        att_str = f" with {', '.join(attendees)}" if attendees else ""

        entry = f"{start}–{end}  {subject}{loc_str}{att_str}"
        if is_allday:
            alldays.append(entry)
        else:
            meetings.append(entry)

    meetings.sort()
    if meetings:
        print(f"── {date_label} ──")
        for m in meetings:
            print(f"  {m}")
    if alldays:
        print()
        for a in alldays:
            print(f"  ⬜ {a}")


def main():
    parser = argparse.ArgumentParser(description=f"Microsoft Graph Calendar — {SKILL_NAME}")
    parser.add_argument("--force", action="store_true", help="Force re-authentication")
    parser.add_argument("--diagnostics", action="store_true", help="Print non-secret auth diagnostics")
    parser.add_argument("--calendar-today", action="store_true", help="Show today's calendar")
    parser.add_argument("--calendar-date", type=str, metavar="YYYY-MM-DD", help="Show calendar for a date")
    parser.add_argument("--setup", action="store_true", help="Print setup instructions and exit")
    args = parser.parse_args()

    config = _load_config()
    auth = config["auth"]

    if "YOUR_CLIENT_ID" in str(auth):
        print(f"ERROR: Please edit {CONFIG_FILE} with your real values.")
        print("Run with --setup for instructions.")
        sys.exit(1)

    try:
        if args.calendar_today or args.calendar_date:
            date_str = args.calendar_date
            label = date_str if date_str else datetime.now().strftime("%A, %B %d, %Y")
            events = get_events(config, date_str=date_str)
            format_events(events, label, config)
        elif args.setup:
            print(f"Setup instructions:")
            print(f"  1. Edit {CONFIG_FILE}")
            print(f"  2. Fill in client_id, tenant_id, and account_hint")
            print(f"  3. Ensure your Azure app has Calendars.Read and User.Read (delegated)")
            print(f"  4. Run again with --calendar-today to test")
        else:
            result = acquire_token(config, force=args.force)
            print(json.dumps(_auth_diagnostics(result, auth), indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
