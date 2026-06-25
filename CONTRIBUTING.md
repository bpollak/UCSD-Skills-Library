# Contributing a Skill

Anyone can propose and contribute a skill. To keep the library clean and safe,
**contribution is open but publication is reviewed**: everything lands through a pull
request, nothing is published unreviewed. See [GOVERNANCE.md](GOVERNANCE.md) for trust
tiers and [SECURITY.md](SECURITY.md) for the threat model.

## The flow

1. **Propose first.** Add `skills/<name>/SKILL.md` from the template with
   `catalog.status: "planned"` or `catalog.status: "idea"`. This is the dedup gate
   before anyone invests in building it.
2. **Claim and build.** On a feature branch, create `skills/<name>/` from
   [`skills/_template/`](skills/_template/). Update that skill's frontmatter as you go.
3. **Validate locally** and open a PR.
4. **Review.** A maintainer reviews against the checklist. Skills shipping `scripts/` or
   making network calls also get a security review routed by `CODEOWNERS`.
5. **Merge.** On merge, update `catalog.publicationStatus` and `catalog.tier` as
   appropriate.

## Skill layout

```text
skills/<name>/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

Only `SKILL.md` is required. Keep long tables, policy excerpts, and examples in
`references/` so the entrypoint stays focused.

## Conventions

- **Naming:** lowercase, hyphenated, and namespaced. UCSD-wide skills use the `ucsd-`
  prefix; the folder name must equal the frontmatter `name`.
- **Frontmatter is the catalog source:** `name`, trigger `description`, and the nested
  `catalog` block drive the generated `ideas.json`.
- **`description` is the trigger.** Write it to state exactly when the agent should use
  the skill. Avoid wording that overlaps another skill's triggers.
- **One skill, one job.** If your idea extends an existing skill, extend it rather than
  add a near-duplicate.
- **Categories:** choose a category from `categories.json`.
- **Tiers:** use `experimental` for unreviewed or idea-only work, `verified` for
  reviewed community contributions, and `core` for maintainer-owned vetted skills.
- **`allowed-tools` is recommended:** if your harness supports it, declare the minimum
  tools the skill needs.
- **Cite sources** for any policy or standard a skill encodes, with a current-as-of date.

## Catalog rules

- Do not edit `ideas.json` by hand; it is generated from `SKILL.md` frontmatter.
- Ordinary skill PRs should leave `ideas.json` alone unless the PR is specifically
  refreshing the dashboard artifact.
- Every real skill folder must include `name`, trigger `description`, and a `catalog`
  block in `SKILL.md`.
- `catalog.status` must be one of `planned`, `idea`, `in-progress`, `review`, `done`,
  or `built`.
- `catalog.publicationStatus` must be one of `draft`, `ready`, `published`, or
  `archived`.
- `catalog.tier` must be one of `core`, `verified`, or `experimental`.
- `catalog.category` must match one of the names in `categories.json`.
- `id` and `name` in the generated catalog come from the skill folder/frontmatter name.

The `_template` folder is documentation and is ignored by validation as a skill.

## Validate locally

```sh
pip install pyyaml jsonschema      # one-time
python3 scripts/build_catalog.py --check  # optional dashboard artifact freshness check
python3 scripts/validate.py        # structure + catalog + trigger collisions
python3 scripts/security_scan.py   # secret gate + advisory security review
```

Both run automatically in CI on every PR. Fix all `ERROR`/`HIGH` findings before
requesting review.

## Review checklist

Before opening a PR, run through this checklist. Items flagged with **(CI)** are
checked automatically; the rest require manual verification.

- [ ] **One skill, one PR.** Does not bundle changes to multiple skills or add
      unrelated assets. If you need to update an existing skill alongside a new
      one, submit separate PRs.
- [ ] **Trigger description is distinct.** `description` wording does not overlap
      with any existing skill's triggers (e.g. avoid "remember" or "what do we
      know about" if `ucsd-memory` already uses those).
- [ ] **No real-looking UCSD names or emails.** Use neutral placeholders
      (`example.com`, `Jane Smith`, `recipient@example.com`) in all examples,
      documentation, and test data.
- [ ] **No secrets, credentials, keys, or real P3/P4 data committed.**
- [ ] **`git diff --check` passes** — no trailing whitespace, no CRLF, no
      whitespace errors in any file. Run this before committing.
- [ ] **`scripts/` reviewed line-by-line;** no obfuscation, pipe-to-shell, or
      undisclosed network calls. External URLs are justified and documented.
- [ ] **Privacy & access claims match enforcement.** If the skill claims
      script-enforced privacy, RBAC, or anonymization, the scripts must actually
      enforce it (fail closed, not just warn). Otherwise remove the claims.
- [ ] **Data handling notes are explicit.** If the skill touches email, calendar,
      PII, or UCSD-classified data (P2/P3+), the guardrails must state the
      classification and define what crosses boundaries.
- [ ] **Asset bundles require provenance.** Any `assets/` directory with
      third-party files must include:
      - `SOURCE.md` with source URLs, version, and retrieval date
      - License/redistribution rationale
      - `checksums.sha256` with SHA-256 for every file (no stale references,
        all checksums verified against committed files)
- [ ] **`allowed-tools` is minimal.** Only list the tools the skill actually
      needs. `Read, Bash` is preferred for policy-only skills; expand only as
      necessary.
- [ ] **Instruction text** contains nothing that would steer an agent to
      exfiltrate data, disable safety, escalate privileges, or contact
      unexpected endpoints.
- [ ] **Catalog frontmatter** is present, valid, and tier is appropriate.
- [ ] **Validation passes.** Run `python3 scripts/validate.py` locally and fix
      all errors. **(CI)**
