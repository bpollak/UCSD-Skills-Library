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

- [ ] Clear, single purpose; does not duplicate or conflict with an existing skill.
- [ ] `description` triggers are specific and do not collide with other skills.
- [ ] No secrets, credentials, keys, or real P3/P4 data committed.
- [ ] `scripts/` reviewed line-by-line; no obfuscation, pipe-to-shell, or undisclosed
      network calls. External URLs are justified.
- [ ] Instruction text contains nothing that would steer an agent to exfiltrate data,
      disable safety, escalate privileges, or contact unexpected endpoints.
- [ ] `allowed-tools`, if present, is minimal; sources are cited and dated.
- [ ] `catalog` frontmatter is present, valid, and tier is appropriate.
