# Security

## Why skills need a threat model

A skill is not just documentation — it is **instructions an AI agent will follow**, plus
any `scripts/` it ships and any URLs it fetches at runtime. A malicious or careless skill
can therefore:

- **Inject instructions** that steer an agent to exfiltrate data, disable safety checks,
  escalate privileges, or contact attacker-controlled endpoints (the danger can be plain
  English, not code).
- **Execute code** via bundled scripts run in the user's environment.
- **Pull remote content** at runtime that changes after review.
- **Leak secrets** committed into the skill.

Open, self-serve skill registries with no review gate routinely end up distributing
malware. This library avoids that by design.

## How we mitigate

- **PR-only, no direct pushes.** `main` is protected; every change is reviewed.
- **Human review**, with a required **security review** for any skill shipping `scripts/`
  or making network calls (routed via `CODEOWNERS`).
- **Automated CI gates** on every PR:
  - `scripts/validate.py` — structure, schema, catalog consistency, trigger collisions.
  - `scripts/security_scan.py` — fails on likely committed secrets; flags dangerous
    script patterns and external URLs for human review.
- **Trust tiers** (`core` / `verified` / `experimental`) surfaced in the catalog so users
  can calibrate risk. See [GOVERNANCE.md](GOVERNANCE.md).
- **Reviewed builds only.** The published storefront builds from reviewed `main`, never
  from arbitrary branches.

Automation is a backstop, not a guarantee — the human review of a skill's instruction
text is the primary control.

## Contributor rules

- Never commit secrets, credentials, keys, or real P3/P4 data.
- No obfuscation (base64 blobs, minified payloads), pipe-to-shell, or undisclosed network
  calls.
- Declare every external URL the skill reads, and prefer authoritative sources.
- Declare minimal `allowed-tools` where supported.

## Reporting a vulnerable or malicious skill

Email **tritonai@ucsd.edu** with subject `SECURITY: <skill name>`. Include the skill,
the concern, and reproduction details if any. Please do **not** open a public issue for
suspected malicious content.

## Response & revocation

- Confirmed malicious/vulnerable skills are removed from `main` (revert) and delisted from
  the catalog (`publicationStatus: draft` / entry removed).
- Target: triage within **2 business days**; removal of confirmed malicious content
  **same day**.
- A note is added to the catalog entry or release notes recording the action.
