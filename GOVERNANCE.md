# Governance

How the UCSD Skills Library stays clean, safe, and open as it grows. The guiding
principle: **contribution is open; publication is earned; risk is always labeled.**

## Trust tiers

Every skill carries a `tier` in `ideas.json`, surfaced in the storefront so users can
calibrate trust.

| Tier | Meaning | Who maintains | Bar to publish |
|---|---|---|---|
| **core** | Team-built and fully vetted; the default surface. | Maintainers | Full review + CI green |
| **verified** | Community-contributed, reviewed, and CI-green. | Contributor + maintainer | Review + CI green |
| **experimental** | Use-at-your-own-risk; clearly labeled and separated. | Contributor | CI green + basic review |

Tier is assigned by a maintainer at merge. A skill can be promoted (e.g. experimental →
verified) after it matures.

## Roles

- **Maintainers** — own the catalog, schema, and tooling; approve PRs; assign tiers; run
  periodic audits. (Listed in `.github/CODEOWNERS`.)
- **Security reviewers** — required reviewers for any skill shipping `scripts/` or making
  network calls.
- **Contributors** — anyone proposing or building a skill via PR.

## Decisions

- Changes land via PR with **at least one maintainer approval**.
- Skills that ship executable code or network calls additionally require a **security
  reviewer approval**.
- Disputes over duplication/scope are resolved by maintainers, favoring *extend an
  existing skill* over *add a near-duplicate*.

## Lifecycle

1. **Idea** — proposed in `ideas.json` (`status: idea`); deduped before any building.
2. **In progress** — being built on a branch.
3. **Done / published** — merged, reviewed, tier assigned.
4. **Deprecated** — superseded or stale skills are retired during periodic audits
   (`publicationStatus: draft` or entry removed) so the catalog doesn't rot.

`ideas.json` is the single source of truth for the roadmap and catalog; the dashboard
(`index.html`) renders it.

## Keeping the catalog clean

- Unique, namespaced names enforced by CI.
- Trigger-collision detection so skills don't fight over the same user intent.
- Propose-before-build dedup gate.
- Periodic audit for duplicates, conflicts, and staleness.
