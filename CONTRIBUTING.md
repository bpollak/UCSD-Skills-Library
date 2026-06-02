# Contributing a Skill

Anyone can propose and contribute a skill. To keep the library clean and safe,
**contribution is open but publication is reviewed** — everything lands through a pull
request, nothing is published unreviewed. See [GOVERNANCE.md](GOVERNANCE.md) for trust
tiers and [SECURITY.md](SECURITY.md) for the threat model.

## The flow

1. **Propose first.** Add an entry to `ideas.json` with `status: "idea"` describing the
   skill. This is the dedup gate — a maintainer confirms it doesn't overlap an existing
   skill or another proposal before you invest in building it.
2. **Claim & build.** On a feature branch, create `skills/<name>/` (see layout below).
   Update your `ideas.json` entry as you go (`status`, `checklist`).
3. **Validate locally** (see below) and open a PR.
4. **Review.** A maintainer reviews against the checklist; skills shipping `scripts/` or
   making network calls also get a security review (`CODEOWNERS` routes this).
5. **Merge.** On merge, set `publicationStatus`/`checklist.published` appropriately.

## Skill layout

```
skills/<name>/
├── SKILL.md            # required entrypoint
├── references/         # optional: detail loaded on demand (tables, full docs, examples)
├── scripts/            # optional: executable helpers (triggers security review)
└── assets/             # optional: static files
```

Start from [`skills/_template/`](skills/_template/) — copy it and fill it in.

## Conventions

- **Naming:** lowercase, hyphenated, and namespaced. UCSD-wide skills use the `ucsd-`
  prefix; the folder name must equal the frontmatter `name` and the catalog `name`/`id`.
- **Frontmatter is minimal:** only `name` and `description` are required. Rich metadata
  (category, status, tier) lives in `ideas.json`, not the frontmatter.
- **`description` is the trigger.** Write it to state exactly *when* the agent should use
  the skill. Avoid wording that overlaps another skill's triggers — the validator flags
  collisions.
- **One skill, one job.** If your idea extends an existing skill, extend it rather than
  add a near-duplicate.
- **`allowed-tools` (recommended):** if your harness supports it, declare the *minimum*
  tools the skill needs. Least privilege by default.
- **Cite sources** for any policy/standard a skill encodes, with a "current as of" date.

## Validate locally

```sh
pip install pyyaml jsonschema      # one-time
python3 scripts/validate.py        # structure + catalog + trigger collisions
python3 scripts/security_scan.py   # secret gate + advisory security review
```

Both run automatically in CI on every PR. Fix all `ERROR`/`HIGH` findings before
requesting review.

## Review checklist (what a reviewer checks)

- [ ] Clear, single purpose; does not duplicate or conflict with an existing skill.
- [ ] `description` triggers are specific and don't collide with other skills.
- [ ] No secrets, credentials, keys, or real P3/P4 data committed.
- [ ] `scripts/` reviewed line-by-line; no obfuscation, pipe-to-shell, or undisclosed
      network calls. External URLs are justified.
- [ ] Instruction text contains nothing that would steer an agent to exfiltrate data,
      disable safety, escalate privileges, or contact unexpected endpoints.
- [ ] `allowed-tools` (if present) is minimal; sources are cited and dated.
- [ ] `ideas.json` entry is present, valid, and tier is appropriate.
