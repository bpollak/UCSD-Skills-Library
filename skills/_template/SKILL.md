---
name: ucsd-skill-name
description: One to three sentences stating exactly WHEN the agent should use this skill — the user intents, keywords, file types, or slash-commands that should trigger it. Be specific. Vague descriptions cause mis-triggers and collide with other skills. Example phrasing - "Use when ... Trigger on ... Also /your-command."
# allowed-tools: Read, Grep, WebFetch   # optional: declare the MINIMUM tools this skill needs
---

# UCSD Skill Name

<!--
  TEMPLATE — copy this folder to skills/<your-skill-name>/ and fill it in.
  - Folder name must equal the frontmatter `name` and your ideas.json name/id.
  - Keep SKILL.md focused; push long tables / full docs into references/ and link them.
  - Add a matching entry to ideas.json (start with status: "idea").
  - Delete unused sections and these comments before opening a PR.
-->

One-line statement of what this skill does and the outcome it produces.

## When to use

- Bullet the concrete situations that should trigger this skill.

## How to use this skill

1. Step the agent through the workflow.
2. Keep steps imperative and unambiguous.

## Guardrails

- State anything the agent must never do.

## Sources & currency

- Cite any policy, standard, or doc this skill encodes, with URLs and a "current as of"
  date. Put full reference material in `references/`.
