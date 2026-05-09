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
