#!/usr/bin/env python3
"""Advisory security scan for contributed skills.

Scope: skills/ only (the surface where contributions land).

  - HIGH (gates CI, exit 1): likely committed secrets.
  - REVIEW (advisory, exit 0): dangerous script patterns and external URLs that a
    human reviewer must look at before merge.

This is a backstop, NOT a guarantee. A skill's real risk often lives in its
natural-language instructions, which require human review (see SECURITY.md).

Run locally:  python3 scripts/security_scan.py
"""
import re
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"gh[pousr]_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"-----BEGIN[A-Z ]*PRIVATE KEY-----", "private key block"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (
        r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*[\"']?[^\s\"']{12,}",
        "hardcoded credential",
    ),
]

DANGER_PATTERNS = [
    (r"(?:curl|wget)\s[^|]*\|\s*(?:sh|bash)", "pipe-to-shell download execution"),
    (r"\beval\s*\(", "eval()"),
    (r"\bexec\s*\(", "exec()"),
    (r"\bos\.system\s*\(", "os.system()"),
    (r"\bsubprocess\.(?:call|run|Popen)\b", "subprocess execution"),
    (r"rm\s+-rf\s+(?:/|~|\$)", "destructive rm -rf"),
    (r"base64\s+-d", "base64 decode (possible obfuscation)"),
    (r"/dev/tcp/", "raw network socket"),
    (r"\bnc\s+-e\b", "netcat reverse shell"),
    (r"chmod\s+777", "world-writable chmod"),
]

URL_PATTERN = re.compile(r"https?://[^\s)\"'>\]]+")
# Domains we consider authoritative for citations (still listed, never gates).
TRUSTED = ("ucop.edu", "ucsd.edu", "policy.ucop.edu", "security.ucop.edu", "nist.gov")

high: list[str] = []
review: list[str] = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ci", action="store_true", help="Emit GitHub Actions annotations")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to scan")
    return parser.parse_args()


args = parse_args()
ROOT = args.root.resolve()
SKILLS = ROOT / "skills"
ci = args.ci


def emit(level: str, msg: str) -> None:
    (high if level == "HIGH" else review).append(msg)


for path in sorted(SKILLS.rglob("*")):
    if not path.is_file():
        continue
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
        review.append(f"{path.relative_to(ROOT)}: binary/opaque asset - reviewer must justify")
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        continue
    rel = path.relative_to(ROOT)

    for pat, label in SECRET_PATTERNS:
        if re.search(pat, text):
            emit("HIGH", f"{rel}: possible {label}")

    is_script = path.suffix in {".sh", ".bash", ".py", ".js", ".ts", ".rb", ".pl"}
    if is_script:
        for pat, label in DANGER_PATTERNS:
            if re.search(pat, text):
                emit("REVIEW", f"{rel}: dangerous pattern - {label}")

    for url in set(URL_PATTERN.findall(text)):
        if not any(t in url for t in TRUSTED):
            emit("REVIEW", f"{rel}: external URL (verify) - {url}")


for m in review:
    print(f"::warning:: {m}" if ci else f"REVIEW  {m}")
for m in high:
    print(f"::error:: {m}" if ci else f"HIGH    {m}")

if high:
    print(f"\nsecurity-scan: FAILED - {len(high)} high-severity finding(s)")
    sys.exit(1)
print(f"security-scan: OK ({len(review)} item(s) for human review)")
