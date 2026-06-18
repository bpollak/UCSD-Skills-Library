# Codex PR Webhook Review Service

This repo includes a local GitHub webhook receiver that reviews PRs with Codex,
runs the same repository checks as CI, and posts one sticky GitHub comment per PR.

The actual reviewer should run on this Mac because it uses the local Codex app CLI
with `gpt-5.5` and high reasoning. The public webhook endpoint can be a Cloudflare
Tunnel in front of the local service.

## Architecture

```text
GitHub pull_request webhook
  -> Cloudflare Tunnel hostname, or any HTTPS tunnel
  -> http://127.0.0.1:8787/github/webhook
  -> local Codex review worker
  -> sticky PR comment on GitHub
```

The webhook handler verifies GitHub's `X-Hub-Signature-256`, immediately returns
`202 Accepted`, and performs the slow review in a background worker so GitHub does
not time out.

## What It Reviews

For `pull_request` actions `opened`, `reopened`, `synchronize`, `ready_for_review`,
and `edited`, the service:

- Fetches the PR into an isolated git worktree under `.codex-pr-reviewer/`.
- Runs the trusted local `scripts/validate.py --root <pr-worktree>`.
- Runs the trusted local `scripts/security_scan.py --root <pr-worktree>`.
- Runs `git diff --check` and diff summary commands.
- Asks Codex to review merge readiness against `README.md`, `CONTRIBUTING.md`,
  `GOVERNANCE.md`, `SECURITY.md`, `schema/ideas.schema.json`, and `CODEOWNERS`.
- Creates or updates a comment marked with `<!-- ucsd-skills-codex-pr-review -->`.
- Records reviewed head SHAs in `.codex-pr-reviewer/state.json`.

## Local Setup

Create a GitHub token that can read pull requests/contents and write PR comments.
For a fine-grained token, grant this repository:

- Contents: Read
- Pull requests: Read
- Issues: Read and Write
- Metadata: Read

Install validation dependencies once:

```sh
python3 -m pip install pyyaml jsonschema
```

Set secrets:

```sh
export PR_REVIEW_GITHUB_TOKEN="github_pat_..."
export PR_REVIEW_WEBHOOK_SECRET="$(openssl rand -hex 32)"
```

`GITHUB_TOKEN` or `GH_TOKEN` also work when `PR_REVIEW_GITHUB_TOKEN` is not set.

Run the webhook receiver:

```sh
python3 scripts/pr_review_service.py
```

Health check:

```sh
curl http://127.0.0.1:8787/healthz
```

Manual review without a webhook:

```sh
python3 scripts/pr_review_service.py --review-pr 12
```

Dry-run manual review:

```sh
python3 scripts/pr_review_service.py --review-pr 12 --dry-run --force
```

## Cloudflare Tunnel

Cloudflare Tunnel is the recommended way to expose the local receiver without opening
an inbound port on the Mac.

Install and log in:

```sh
brew install cloudflared
cloudflared tunnel login
```

Create and route a named tunnel:

```sh
cloudflared tunnel create ucsd-skills-pr-reviewer
cloudflared tunnel route dns ucsd-skills-pr-reviewer pr-reviewer.example.com
```

Copy the tunnel UUID printed by `cloudflared tunnel create`, then create
`~/.cloudflared/ucsd-skills-pr-reviewer.yml`:

```yaml
tunnel: REPLACE_WITH_TUNNEL_ID
credentials-file: /Users/davidbalderston/.cloudflared/REPLACE_WITH_TUNNEL_ID.json

ingress:
  - hostname: pr-reviewer.example.com
    service: http://127.0.0.1:8787
  - service: http_status:404
```

Run it:

```sh
cloudflared tunnel --config ~/.cloudflared/ucsd-skills-pr-reviewer.yml run ucsd-skills-pr-reviewer
```

For a quick disposable URL during testing:

```sh
cloudflared tunnel --url http://127.0.0.1:8787
```

## GitHub Webhook

In GitHub repository settings:

- Payload URL: `https://pr-reviewer.example.com/github/webhook`
- Content type: `application/json`
- Secret: the value of `PR_REVIEW_WEBHOOK_SECRET`
- Events: choose **Pull requests**
- Active: enabled

Use the GitHub webhook redelivery button to replay a delivery after changing the
service.

## Codex Settings

Defaults:

```sh
CODEX_PATH=/Applications/Codex.app/Contents/Resources/codex
CODEX_MODEL=gpt-5.5
CODEX_REASONING_EFFORT=high
CODEX_TIMEOUT_SECONDS=3600
```

If you want the service to connect to a specific Codex app-server endpoint, set:

```sh
export CODEX_REMOTE="ws://127.0.0.1:PORT"
```

The service passes that through as `codex --remote "$CODEX_REMOTE" exec ...`.

## launchd Example

Create `~/Library/LaunchAgents/com.ucsd-skills.pr-reviewer.plist` with your real
token and webhook secret:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ucsd-skills.pr-reviewer</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/davidbalderston/Github/UCSD-Skills-Library/scripts/pr_review_service.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/davidbalderston/Github/UCSD-Skills-Library</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PR_REVIEW_GITHUB_TOKEN</key>
    <string>github_pat_REPLACE_ME</string>
    <key>PR_REVIEW_WEBHOOK_SECRET</key>
    <string>REPLACE_ME</string>
    <key>CODEX_MODEL</key>
    <string>gpt-5.5</string>
    <key>CODEX_REASONING_EFFORT</key>
    <string>high</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/Users/davidbalderston/Github/UCSD-Skills-Library/.codex-pr-reviewer/service.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/davidbalderston/Github/UCSD-Skills-Library/.codex-pr-reviewer/service.err.log</string>
</dict>
</plist>
```

Then load it:

```sh
launchctl load ~/Library/LaunchAgents/com.ucsd-skills.pr-reviewer.plist
```

Unload it:

```sh
launchctl unload ~/Library/LaunchAgents/com.ucsd-skills.pr-reviewer.plist
```

## Notes

- Draft PRs are reviewed by default. Add `--skip-drafts` to ignore drafts.
- Use `--allow-unsigned` only for local webhook testing.
- The service uses a sticky comment rather than creating a new comment every run.
- Local state and worktrees live under `.codex-pr-reviewer/`, which is ignored by git.
- Token/secret-like environment variables are scrubbed before running checks or Codex.
- A pure Cloudflare Worker can receive webhooks, but it cannot run this local Codex
  review. Use Cloudflare Tunnel when you want Codex-app-backed reviews.
