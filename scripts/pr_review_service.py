#!/usr/bin/env python3
"""GitHub webhook receiver that reviews PRs with local Codex."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import logging
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MARKER = "<!-- ucsd-skills-codex-pr-review -->"
DEFAULT_CODEX = "/Applications/Codex.app/Contents/Resources/codex"
STATE_SCHEMA_VERSION = 1
REVIEW_ACTIONS = {"opened", "reopened", "synchronize", "ready_for_review", "edited"}
SENSITIVE_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "API_KEY", "ACCESS_KEY", "PRIVATE_KEY")
LOG = logging.getLogger("pr-review-service")


@dataclass
class CommandResult:
    label: str
    command: list[str]
    returncode: int
    output: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def markdown(self, limit: int = 6000) -> str:
        command = " ".join(self.command)
        output = truncate(self.output.strip() or "(no output)", limit)
        status = "PASS" if self.ok else "FAIL"
        return f"### {self.label}: {status}\n\n`{command}`\n\n```text\n{output}\n```"


@dataclass(frozen=True)
class ReviewJob:
    owner: str
    repo: str
    number: int
    head_sha: str
    action: str
    delivery_id: str


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str | None, api_url: str = "https://api.github.com") -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        body = None
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ucsd-skills-codex-pr-reviewer",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(f"{self.api_url}{path}", data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GitHubError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"GitHub API {method} {path} failed: {exc}") from exc

        if not raw:
            return None
        return json.loads(raw)

    def get_pull(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        return self.request("GET", f"/repos/{owner}/{repo}/pulls/{number}")

    def list_issue_comments(self, owner: str, repo: str, number: int) -> list[dict[str, Any]]:
        comments: list[dict[str, Any]] = []
        page = 1
        while True:
            query = urllib.parse.urlencode({"per_page": 100, "page": page})
            chunk = self.request("GET", f"/repos/{owner}/{repo}/issues/{number}/comments?{query}")
            if not chunk:
                return comments
            comments.extend(chunk)
            if len(chunk) < 100:
                return comments
            page += 1

    def upsert_review_comment(self, owner: str, repo: str, number: int, body: str) -> int:
        for comment in self.list_issue_comments(owner, repo, number):
            if MARKER in str(comment.get("body", "")):
                comment_id = int(comment["id"])
                self.request("PATCH", f"/repos/{owner}/{repo}/issues/comments/{comment_id}", {"body": body})
                return comment_id
        created = self.request("POST", f"/repos/{owner}/{repo}/issues/{number}/comments", {"body": body})
        return int(created["id"])


@dataclass
class ReviewContext:
    args: argparse.Namespace
    client: GitHubClient
    state_dir: Path
    state_path: Path
    state: dict[str, Any]
    state_lock: threading.Lock
    token: str | None
    jobs: "queue.Queue[ReviewJob]"
    repo_filter: tuple[str, str] | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="Only accept events for owner/name. Defaults to git remote origin.")
    parser.add_argument("--remote", default="origin", help="Local git remote name used for refs.")
    parser.add_argument("--host", default=os.environ.get("PR_REVIEW_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PR_REVIEW_PORT", "8787")))
    parser.add_argument("--path", default=os.environ.get("PR_REVIEW_WEBHOOK_PATH", "/github/webhook"))
    parser.add_argument("--review-pr", type=int, action="append", help="Manually review this PR number and exit.")
    parser.add_argument("--force", action="store_true", help="Review even if the head SHA was already reviewed.")
    parser.add_argument("--dry-run", action="store_true", help="Print comments instead of posting to GitHub.")
    parser.add_argument("--skip-drafts", action="store_true", help="Skip draft pull requests.")
    parser.add_argument("--allow-unsigned", action="store_true", help="Allow unsigned webhook requests. Use only locally.")
    parser.add_argument(
        "--state-dir",
        default=os.environ.get("PR_REVIEW_STATE_DIR", str(ROOT / ".codex-pr-reviewer")),
        help="Directory for local state, logs, and temporary worktrees.",
    )
    parser.add_argument(
        "--codex-path",
        default=os.environ.get("CODEX_PATH") or (DEFAULT_CODEX if Path(DEFAULT_CODEX).exists() else "codex"),
        help="Path to the Codex CLI.",
    )
    parser.add_argument("--codex-model", default=os.environ.get("CODEX_MODEL", "gpt-5.5"))
    parser.add_argument("--codex-effort", default=os.environ.get("CODEX_REASONING_EFFORT", "high"))
    parser.add_argument("--codex-timeout", type=int, default=int(os.environ.get("CODEX_TIMEOUT_SECONDS", "3600")))
    parser.add_argument("--codex-remote", default=os.environ.get("CODEX_REMOTE"), help="Optional app-server URL.")
    parser.add_argument("--github-api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    parser.add_argument("--max-webhook-bytes", type=int, default=int(os.environ.get("PR_REVIEW_MAX_WEBHOOK_BYTES", "10485760")))
    parser.add_argument("--log-level", default=os.environ.get("PR_REVIEW_LOG_LEVEL", "INFO"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    state_dir = Path(args.state_dir).resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "worktrees").mkdir(parents=True, exist_ok=True)

    token = os.environ.get("PR_REVIEW_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    webhook_secret = os.environ.get("PR_REVIEW_WEBHOOK_SECRET") or os.environ.get("WEBHOOK_SECRET")
    if not token and not args.dry_run:
        LOG.error("Set PR_REVIEW_GITHUB_TOKEN, GITHUB_TOKEN, or GH_TOKEN before posting GitHub comments.")
        return 2
    if not webhook_secret and not args.allow_unsigned and not args.review_pr:
        LOG.error("Set PR_REVIEW_WEBHOOK_SECRET or pass --allow-unsigned for local-only testing.")
        return 2

    repo_filter = parse_repo(args.repo) if args.repo else detect_repo(args.remote)
    client = GitHubClient(token=token, api_url=args.github_api_url)
    state_path = state_dir / "state.json"
    state = load_state(state_path)
    context = ReviewContext(
        args=args,
        client=client,
        state_dir=state_dir,
        state_path=state_path,
        state=state,
        state_lock=threading.Lock(),
        token=token,
        jobs=queue.Queue(),
        repo_filter=repo_filter,
    )

    if args.review_pr:
        owner, repo = repo_filter
        for number in args.review_pr:
            pull = client.get_pull(owner, repo, number)
            job = ReviewJob(owner, repo, number, str(pull["head"]["sha"]), "manual", "manual")
            process_job(context, job)
        return 0

    worker = threading.Thread(target=worker_loop, args=(context,), daemon=True)
    worker.start()

    handler = make_handler(context, webhook_secret)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    LOG.info("Webhook receiver listening on http://%s:%s%s", args.host, args.port, args.path)
    LOG.info("Accepting GitHub pull_request actions: %s", ", ".join(sorted(REVIEW_ACTIONS)))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOG.info("Stopping")
        server.shutdown()
        return 130


def make_handler(context: ReviewContext, webhook_secret: str | None) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/healthz":
                self.respond(HTTPStatus.OK, {"ok": True, "queued": context.jobs.qsize()})
                return
            self.respond(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if urllib.parse.urlsplit(self.path).path != context.args.path:
                self.respond(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return

            try:
                raw = self.read_body()
                if not context.args.allow_unsigned:
                    verify_signature(raw, self.headers.get("X-Hub-Signature-256"), webhook_secret)
                event = self.headers.get("X-GitHub-Event", "")
                delivery = self.headers.get("X-GitHub-Delivery", "")
                payload = json.loads(raw.decode("utf-8"))
                accepted = handle_webhook_payload(context, event, delivery, payload)
            except PermissionError as exc:
                LOG.warning("Rejected webhook: %s", exc)
                self.respond(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
                return
            except ValueError as exc:
                LOG.warning("Bad webhook payload: %s", exc)
                self.respond(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            except Exception as exc:
                LOG.exception("Webhook handling failed")
                self.respond(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                return

            self.respond(HTTPStatus.ACCEPTED if accepted else HTTPStatus.OK, {"accepted": accepted})

        def read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", "0"))
            if length > context.args.max_webhook_bytes:
                raise ValueError("webhook payload is too large")
            return self.rfile.read(length)

        def respond(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, format: str, *args: Any) -> None:
            LOG.info("%s - %s", self.address_string(), format % args)

    return Handler


def handle_webhook_payload(context: ReviewContext, event: str, delivery: str, payload: dict[str, Any]) -> bool:
    if event == "ping":
        LOG.info("Received GitHub webhook ping")
        return False
    if event != "pull_request":
        LOG.info("Ignoring GitHub event %s", event)
        return False

    action = str(payload.get("action") or "")
    if action not in REVIEW_ACTIONS:
        LOG.info("Ignoring pull_request action %s", action)
        return False

    repo_info = payload.get("repository") or {}
    full_name = str(repo_info.get("full_name") or "")
    owner, repo = parse_repo(full_name)
    if context.repo_filter and (owner, repo) != context.repo_filter:
        LOG.warning("Ignoring webhook for unexpected repo %s/%s", owner, repo)
        return False

    pull = payload.get("pull_request") or {}
    number = int(pull["number"])
    head_sha = str(pull.get("head", {}).get("sha") or "")
    job = ReviewJob(owner=owner, repo=repo, number=number, head_sha=head_sha, action=action, delivery_id=delivery)
    context.jobs.put(job)
    LOG.info("Queued PR #%s from %s event %s at %s", number, event, action, head_sha[:12])
    return True


def worker_loop(context: ReviewContext) -> None:
    while True:
        job = context.jobs.get()
        try:
            process_job(context, job)
        except Exception:
            LOG.exception("Review job failed for %s/%s#%s", job.owner, job.repo, job.number)
        finally:
            context.jobs.task_done()


def process_job(context: ReviewContext, job: ReviewJob) -> None:
    pull = context.client.get_pull(job.owner, job.repo, job.number)
    number = int(pull["number"])
    title = str(pull.get("title") or "")
    head_sha = str(pull["head"]["sha"])
    key = f"{job.owner}/{job.repo}#{number}"

    if context.args.skip_drafts and pull.get("draft"):
        LOG.info("Skipping draft PR #%s: %s", number, title)
        return
    with context.state_lock:
        already_reviewed = context.state.get("pulls", {}).get(key, {}).get("head_sha") == head_sha
    if already_reviewed and not context.args.force:
        LOG.info("Skipping PR #%s at %s; already reviewed", number, head_sha[:12])
        return

    LOG.info("Reviewing PR #%s at %s from %s: %s", number, head_sha[:12], job.action, title)
    result, review_succeeded = review_pull(context.args, pull, context.state_dir, job.owner, job.repo, context.token)
    comment_id: int | None
    if context.args.dry_run:
        print(f"\n--- PR #{number} dry-run comment ---\n{result}\n")
        comment_id = None
    else:
        comment_id = context.client.upsert_review_comment(job.owner, job.repo, number, result)
        LOG.info("Posted review comment %s for PR #%s", comment_id, number)

    with context.state_lock:
        state_entry = {
            "comment_id": comment_id,
            "reviewed_at": now_iso(),
            "title": title,
            "last_delivery_id": job.delivery_id,
            "last_action": job.action,
        }
        if review_succeeded:
            state_entry["head_sha"] = head_sha
        else:
            state_entry["failed_head_sha"] = head_sha
        context.state.setdefault("pulls", {})[key] = state_entry
        save_state(context.state_path, context.state)


def review_pull(
    args: argparse.Namespace,
    pull: dict[str, Any],
    state_dir: Path,
    owner: str,
    repo: str,
    token: str | None,
) -> tuple[str, bool]:
    number = int(pull["number"])
    head_sha = str(pull["head"]["sha"])
    base_ref = str(pull["base"]["ref"])
    base_sha = str(pull["base"]["sha"])
    worktree = state_dir / "worktrees" / f"pr-{number}-{head_sha[:12]}"

    cleanup_worktree(worktree)
    try:
        prepare_worktree(args.remote, owner, repo, number, base_ref, worktree, token)
        checks = run_local_checks(worktree, base_ref)
        prompt = build_codex_prompt(pull, owner, repo, base_ref, base_sha, head_sha, checks)
        codex_body = run_codex(args, worktree, prompt)
        return normalize_comment(codex_body, pull, checks), True
    except Exception as exc:
        LOG.exception("PR #%s review failed", number)
        return failure_comment(pull, base_ref, head_sha, exc), False
    finally:
        cleanup_worktree(worktree)


def prepare_worktree(
    remote: str,
    owner: str,
    repo: str,
    number: int,
    base_ref: str,
    worktree: Path,
    token: str | None,
) -> None:
    fetch_env = git_env(token)
    remote_url = f"https://github.com/{owner}/{repo}.git" if token else remote
    run_or_raise(["git", "fetch", "--no-tags", remote_url, f"+refs/heads/{base_ref}:refs/remotes/{remote}/{base_ref}"], ROOT, fetch_env)
    run_or_raise(["git", "fetch", "--no-tags", remote_url, f"+refs/pull/{number}/head:refs/remotes/{remote}/pr/{number}"], ROOT, fetch_env)
    run_or_raise(["git", "worktree", "add", "--detach", str(worktree), f"refs/remotes/{remote}/pr/{number}"], ROOT, os.environ.copy())


def cleanup_worktree(worktree: Path) -> None:
    if not worktree.exists():
        return
    subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if worktree.exists():
        shutil.rmtree(worktree)


def run_local_checks(worktree: Path, base_ref: str) -> list[CommandResult]:
    commands = [
        ("Changed files", ["git", "diff", "--name-status", f"origin/{base_ref}...HEAD"]),
        ("Diff stat", ["git", "diff", "--stat", f"origin/{base_ref}...HEAD"]),
        ("Whitespace/conflict check", ["git", "diff", "--check", f"origin/{base_ref}...HEAD"]),
        ("Catalog validation", [sys.executable, str(ROOT / "scripts" / "validate.py"), "--root", str(worktree)]),
        ("Security scan", [sys.executable, str(ROOT / "scripts" / "security_scan.py"), "--root", str(worktree)]),
    ]
    return [run_command(label, command, worktree, timeout=180) for label, command in commands]


def run_codex(args: argparse.Namespace, worktree: Path, prompt: str) -> str:
    output_path = worktree / ".codex-pr-review.md"
    command = [args.codex_path]
    if args.codex_remote:
        command.extend(["--remote", args.codex_remote])
    command.extend(["-a", "never"])
    command.extend(
        [
            "exec",
            "-m",
            args.codex_model,
            "-c",
            f'model_reasoning_effort="{args.codex_effort}"',
            "-s",
            "read-only",
            "--ephemeral",
            "--color",
            "never",
            "-C",
            str(worktree),
            "-o",
            str(output_path),
            "-",
        ]
    )
    LOG.info("Starting Codex review with %s / %s", args.codex_model, args.codex_effort)
    result = subprocess.run(
        command,
        cwd=worktree,
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=args.codex_timeout,
        env=scrubbed_env(),
    )
    output = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else result.stdout
    if result.returncode != 0:
        raise RuntimeError(f"Codex exited {result.returncode}:\n{truncate(result.stdout, 8000)}")
    if not output.strip():
        raise RuntimeError("Codex finished without producing a review body")
    return output.strip()


def build_codex_prompt(
    pull: dict[str, Any],
    owner: str,
    repo: str,
    base_ref: str,
    base_sha: str,
    head_sha: str,
    checks: list[CommandResult],
) -> str:
    number = pull["number"]
    title = pull.get("title") or ""
    author = pull.get("user", {}).get("login") or "unknown"
    body = pull.get("body") or "(no PR body)"
    draft = "yes" if pull.get("draft") else "no"
    checks_markdown = "\n\n".join(check.markdown() for check in checks)

    return f"""You are reviewing a pull request for the UCSD Skills Library.

Write the exact GitHub PR comment body that should be posted. Return only Markdown.

Pull request:
- Repo: {owner}/{repo}
- PR: #{number}
- Title: {title}
- Author: {author}
- Draft: {draft}
- Base: {base_ref} ({base_sha})
- Head: {head_sha}
- Body: {body}

Review standard:
- Treat README.md, CONTRIBUTING.md, GOVERNANCE.md, SECURITY.md, schema/ideas.schema.json, and .github/CODEOWNERS as authoritative.
- Decide whether this PR is good to merge, needs fixes, or is blocked.
- Check skill naming, SKILL.md frontmatter, ideas.json/catalog alignment, category validity, trigger specificity/collisions, trust tier/publication status, and source citations when applicable.
- Review security risk in skill instructions, scripts, assets, external URLs, network behavior, secrets, P3/P4 data, obfuscation, and tool permissions.
- Use the automated command output below as evidence, but inspect the working tree and diff yourself where needed.
- Do not modify files. Do not approve unsafe changes just because automated checks pass.
- Be concise and specific. Include file paths and line numbers for required fixes when you can.
- Never print a discovered secret. Refer to the file/path and the type of issue instead.

Required output format:
{MARKER}
## Codex PR Review

**Verdict:** one of `Good to merge`, `Needs fixes`, or `Blocked`
**Reviewed commit:** `{head_sha}`

### Gate Results
- Catalog validation: pass/fail and the important reason.
- Security scan: pass/fail/review and the important reason.
- Contributing checklist: brief pass/fail summary.

### Required Fixes
- If there are no required fixes, write `None`.

### Notes
- Mention non-blocking follow-ups, risk, or reviewer attention areas.

Automated command output:

{checks_markdown}
"""


def normalize_comment(body: str, pull: dict[str, Any], checks: list[CommandResult]) -> str:
    cleaned = body.strip()
    if MARKER not in cleaned:
        cleaned = f"{MARKER}\n{cleaned}"
    if "Reviewed commit" not in cleaned:
        cleaned += f"\n\n_Reviewed commit: `{pull['head']['sha']}`_"
    footer = f"\n\n---\n_Automated Codex review updated {now_iso()}._"
    return truncate_comment(cleaned + footer, checks)


def failure_comment(pull: dict[str, Any], base_ref: str, head_sha: str, exc: Exception) -> str:
    detail = truncate(str(exc), 6000)
    return f"""{MARKER}
## Codex PR Review

**Verdict:** `Blocked`
**Reviewed commit:** `{head_sha}`

### Gate Results
- Catalog validation: not completed.
- Security scan: not completed.
- Contributing checklist: not completed.

### Required Fixes
- The local review service failed before it could complete the merge-readiness review. A maintainer should check the service logs and rerun the reviewer for this PR.

### Notes
- Base branch: `{base_ref}`
- Error:

```text
{detail}
```

---
_Automated Codex review updated {now_iso()}._
"""


def truncate_comment(body: str, checks: list[CommandResult]) -> str:
    if len(body) <= 60000:
        return body
    summary = "\n".join(f"- {check.label}: {'PASS' if check.ok else 'FAIL'}" for check in checks)
    return truncate(body, 56000) + f"\n\n### Local Check Summary\n{summary}\n\n_Comment truncated by the local review service._"


def run_command(label: str, command: list[str], cwd: Path, timeout: int) -> CommandResult:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        env=scrubbed_env(),
    )
    return CommandResult(label=label, command=command, returncode=result.returncode, output=result.stdout)


def run_or_raise(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    display = redact_command(command)
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(display)} failed with exit {result.returncode}:\n{result.stdout}")


def verify_signature(raw: bytes, signature_header: str | None, secret: str | None) -> None:
    if not secret:
        raise PermissionError("webhook secret is not configured")
    if not signature_header or not signature_header.startswith("sha256="):
        raise PermissionError("missing X-Hub-Signature-256")
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise PermissionError("invalid webhook signature")


def git_env(token: str | None) -> dict[str, str]:
    env = os.environ.copy()
    if token:
        basic_auth = base64.b64encode(f"x-access-token:{token}".encode("utf-8")).decode("ascii")
        env.update(
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic_auth}",
            }
        )
    return env


def scrubbed_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        upper = key.upper()
        if any(marker in upper for marker in SENSITIVE_ENV_MARKERS):
            env.pop(key, None)
    env["NO_COLOR"] = "1"
    return env


def redact_command(command: list[str]) -> list[str]:
    return [re.sub(r"(https://)([^/@]+@)", r"\1***@", part) for part in command]


def detect_repo(remote: str) -> tuple[str, str]:
    result = subprocess.run(["git", "remote", "get-url", remote], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"Could not read git remote {remote}: {result.stderr.strip()}")
    url = result.stdout.strip()
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", url)
    if not match:
        raise RuntimeError(f"Could not infer owner/repo from remote URL: {url}")
    return match.group("owner"), match.group("repo")


def parse_repo(value: str) -> tuple[str, str]:
    if "/" not in value:
        raise ValueError("repo must be formatted as owner/name")
    owner, repo = value.split("/", 1)
    return owner, repo.removesuffix(".git")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": STATE_SCHEMA_VERSION, "pulls": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = path.with_suffix(f".invalid-{int(datetime.now().timestamp())}.json")
        path.rename(backup)
        LOG.warning("Moved invalid state file to %s", backup)
        return {"schema_version": STATE_SCHEMA_VERSION, "pulls": {}}
    state.setdefault("schema_version", STATE_SCHEMA_VERSION)
    state.setdefault("pulls", {})
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = Path(handle.name)
    tmp.replace(path)


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 80].rstrip() + "\n... [truncated by pr_review_service.py]"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
