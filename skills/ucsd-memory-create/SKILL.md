---
name: ucsd-memory-create
description: Create and maintain a local TritonAI memory vault. Use when a user asks for $memory-create, memory setup, an Obsidian-style memory graph, daily conversation sync, weekly memory cleanup, or cross-platform background memory jobs for TritonAI Code/OpenCode.
catalog:
  title: UCSD Memory Create
  description: >-
    Create and maintain a local TritonAI memory vault with Obsidian-style
    Markdown notes, daily conversation sync jobs, and weekly cleanup jobs for
    TritonAI Code/OpenCode users.
  category: Knowledge & Documentation
  status: review
  publicationStatus: draft
  tier: experimental
  owner: AI Tools
  updated: 2026-06-18
---

# UCSD Memory Create

<!-- Methodology provenance: local-first agent memory pattern from TritonAI/Codex usage, plus David Allen GTD capture/review discipline for daily collection and weekly cleanup. -->

Set up a local Markdown memory vault plus scheduled OpenCode jobs that keep it useful.

## Workflow

1. Confirm the memory root. Default to `~/TritonAI/Memory` on macOS/Linux and `%USERPROFILE%\TritonAI\Memory` on Windows.
2. Create the vault folders and starter files:
   - `AGENTS.md`
   - `README.md`
   - `inbox.md`
   - `conversations/`
   - `calendar/`
   - `email/`
   - `meetings/`
   - `people/`
   - `projects/`
   - `sources/`
   - `summaries/`
   - `.memory/config.json`
   - `.memory/logs/`
   - `.memory/prompts/`
3. Copy `assets/prompts/daily-sync.md` and `assets/prompts/weekly-cleanup.md` into `.memory/prompts/`.
4. Write `AGENTS.md` so future agents treat the vault as local-first memory, preserve source provenance, avoid secrets, and use Obsidian-style wikilinks.
5. Write `.memory/config.json` with at least:
   - `version`
   - `root`
   - `createdAt`
   - `enabledSources`
   - `dailySchedule`
   - `weeklySchedule`
   - `opencodeCommand`
   - `lastRun`
6. Install the schedules only after the user confirms background jobs. Use the adapter in `references/scheduler-adapters.md`.
7. Run the initial sync manually once, then show where logs and generated notes landed.

## Schedule Shape

No wrapper command is required. Schedule OpenCode directly with an absolute `opencode` path. OpenCode 1.15.13 uses `run --dir <directory> <message>`; pass the prompt file contents as the message.

```sh
"OPENCODE_COMMAND" run --dir "<memory-root>" "$(cat "<memory-root>/.memory/prompts/daily-sync.md")"
"OPENCODE_COMMAND" run --dir "<memory-root>" "$(cat "<memory-root>/.memory/prompts/weekly-cleanup.md")"
```

Use OS-native scheduling:

- macOS: LaunchAgent
- Windows: Task Scheduler
- Linux fallback: systemd user timer or cron

Read `references/scheduler-adapters.md` before creating, updating, or removing schedules.

## Memory Rules

- Keep the vault human-readable Markdown first. Use YAML frontmatter and `[[wikilinks]]` so Obsidian can build the graph.
- Store raw or near-raw imported material under `sources/`; store distilled durable notes under `people/`, `projects/`, `meetings/`, `conversations/`, and `summaries/`.
- Preserve provenance with source path, source kind, imported-at timestamp, and confidence.
- Prefer appending dated entries to rewriting history unless the weekly cleanup is deduplicating or consolidating.
- Keep a short run report in `.memory/logs/`.

## Guardrails

- Do not ingest email, calendar, Jira, Drive, or other external systems unless the user explicitly opts in and the needed connector/auth already exists.
- Do not send email, update Jira, publish files, or make external changes from memory jobs.
- Do not store API keys, tokens, passwords, private keys, session cookies, or unrelated secrets.
- Treat sensitive data conservatively. If a source appears to contain regulated or high-risk data, summarize at a high level or skip it and record the skip reason.
- Do not overwrite an existing memory vault without inspecting it and preserving user-authored notes.
- Schedule uninstall must remove only scheduler entries created for the memory jobs; leave the memory vault unless the user explicitly asks to delete it.

## Sources & Currency

- This skill encodes a local operational workflow, not UCSD policy.
- Scheduler details are in `references/scheduler-adapters.md`, current as of 2026-06-18.
