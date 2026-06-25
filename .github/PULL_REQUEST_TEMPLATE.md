## Description

<!-- Briefly describe the skill or change. One skill per PR. -->

## Checklist

- [ ] **One skill, one PR** — this change covers a single skill or a single
      update to an existing skill
- [ ] **Trigger description** is distinct and does not overlap existing skills
- [ ] **No real UCSD names/emails** — all examples use neutral placeholders
- [ ] **No secrets, credentials, or P3/P4 data** committed
- [ ] **`git diff --check` passes** — no whitespace issues
- [ ] **Privacy & access claims match enforcement** — scripts actually enforce
      what the docs promise (fail closed, not just warn)
- [ ] **Data handling is explicit** — PII/classified data is labeled in guardrails
- [ ] **Asset bundle provenance** (if adding assets): SOURCE.md, license,
      checksums.sha256 all present and verified
- [ ] **`allowed-tools`** is minimal and appropriate
- [ ] **`python3 scripts/validate.py` passes**
