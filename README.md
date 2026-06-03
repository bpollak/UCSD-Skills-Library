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

## Installing a Skill

Copy or symlink a skill folder into the agent's skills directory, such as `~/.agents/skills/`.

## Trust Tiers

Every skill carries a `tier` in `ideas.json` so users can calibrate trust:

- **core** — team-built and fully vetted (the default surface)
- **verified** — community-contributed, reviewed, and CI-green
- **experimental** — clearly labeled, use-at-your-own-risk

See [GOVERNANCE.md](GOVERNANCE.md) for how tiers are assigned.

## Contributing

Contribution is open; publication is reviewed. Propose a skill in `ideas.json`, build it
from [`skills/_template/`](skills/_template/), and open a PR. See
[CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Validation

CI validates every PR. Run the same checks locally:

```sh
pip install pyyaml jsonschema
python3 scripts/validate.py        # structure, schema, catalog, trigger collisions
python3 scripts/security_scan.py   # secret gate + advisory security review
```

`ideas.json` is validated against [`schema/ideas.schema.json`](schema/ideas.schema.json).
