# UCSD Skills

Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform specific tasks.

This repository catalogs UC San Diego skills for use and distribution with AI coding agents.

## Dashboard

Open `index.html` through a local web server so it can read `ideas.json`:

```sh
python3 -m http.server 8791 --bind 127.0.0.1
```

Then visit <http://127.0.0.1:8791/>.

## Skill Format

Each skill lives in its own folder and uses `SKILL.md` as the entrypoint:

```text
skills/example-skill/
└── SKILL.md
```

Skills can also include optional `references/`, `scripts/`, and `assets/` folders when the workflow needs them.

Use `skills/_template/` when starting a new skill.

## Catalog

`ideas.json` is the source of truth for skill metadata. Categories live in `categories.json` and are used by the dashboard. Every catalog entry also carries a trust `tier`:

- **core** - team-built and fully vetted
- **verified** - community-contributed, reviewed, and CI-green
- **experimental** - clearly labeled, use-at-your-own-risk

See [GOVERNANCE.md](GOVERNANCE.md) for how tiers are assigned.

## Installing a Skill

Install the built UCSD skills with one command:

```sh
curl -fsSL https://raw.githubusercontent.com/dbalders/UCSD-Skills-Library/main/scripts/install-skills.sh | GROUP="built" bash
```

The installer copies built skill folders into `~/.agents/skills/` by default. To install a specific skill, pass `SKILLS="tritonai-feedback"` instead of `GROUP`.

## Contributing

Contribution is open; publication is reviewed. Propose a skill in `ideas.json`, build it from [`skills/_template/`](skills/_template/), and open a PR. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Validation

CI validates every PR. Run the same checks locally:

```sh
pip install pyyaml jsonschema
python3 scripts/validate.py        # structure, schema, categories, catalog, trigger collisions
python3 scripts/security_scan.py   # secret gate + advisory security review
```

`ideas.json` is validated against [`schema/ideas.schema.json`](schema/ideas.schema.json).
