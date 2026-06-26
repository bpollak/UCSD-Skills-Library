---
name: ucsd-dsmlp-deploy
description: Use when a UC San Diego citizen-developer app needs to move toward hosting on the TritonAI DSMLP Kubernetes platform — packaging the app to the platform's standards, building the container via GitHub Actions, and generating the Helm chart for handoff. Trigger on "deploy my app", "host this on DSMLP", "get this onto the TritonAI platform", "Helm chart", "containerize this for UCSD", or when an app built from the claude-webapp-template is ready for review/deployment. Also /ucsd-dsmlp-deploy.
catalog:
  title: UCSD DSMLP Deployment Packaging
  description: >-
    Package agent-built citizen-developer apps for TritonAI DSMLP hosting with
    template conventions, GitHub Actions container builds, and a handoff Helm chart.
  category: Engineering Support
  status: review
  publicationStatus: draft
  tier: experimental
  owner: AI Tools
  updated: 2026-06-26
allowed-tools: Read, Write, Edit, Bash
---

# UCSD DSMLP Deployment Packaging

Package an agent-built web app so the TritonAI platform team can review and deploy it
onto DSMLP (the campus Kubernetes platform). You (the agent) own everything up to the
handoff: repo structure, container build, and Helm chart. The platform team owns the
actual deployment.

**V1 is deliberately opinionated.** One blessed stack, one pipeline. The team will
loosen this as the platform matures — don't improvise around it.

## The pipeline (who does what)

```
YOU (the app's agent, with the developer)
  1. App follows the template conventions
  2. GitHub repo + Actions workflow → container image on ghcr.io
     ✅ green checkmark on the build = the handoff milestone
  3. Helm chart in the repo (copy the ride-along chart, Step 3)
        │  handoff: repo link + DEPLOYMENT.md (Step 4)
        ▼
TRITONAI PLATFORM TEAM (not you)
  4. Code review (team forks your repo; they may patch security issues)
  5. Namespace, TLS certs, volumes, secrets installation
  6. Deploy-time value tweaks (replicas, resources) — app by app
  7. Auth proxy (campus SAML → OAuth), Splunk visibility
```

## Step 1 — Follow the template

Start from (or conform to) the platform template:
**<https://github.com/agt/claude-webapp-template>** — fork it, clone it, or pull its
files into an existing repo; matching its conventions is what matters:

- **Stack:** Python / FastAPI, served by uvicorn (`app.main:app`) on **port 8000** —
  the only port available in the dev sandbox and the platform's expected HTTP port.
- **Container:** `python:3.13-slim` base; non-root user `appuser` (UID 1000); app
  code in `/app`; deps from `requirements.txt`.
- **Health endpoint:** `/api/health` must respond — the container healthcheck and the
  platform depend on it.
- **Configuration via environment variables only** (e.g. `SECRET_KEY`,
  `DATABASE_URL` pattern in the template). No config files with per-environment
  values baked into the image.
- **Data:** if the app persists data, keep it under a single data directory — it maps
  to the chart's optional PVC.
- Read the template's `AGENTS.md`/`CLAUDE.md` for sandbox constraints (unprivileged
  user, no sudo/apt — if you need system packages, they go in the Dockerfile, not the
  sandbox).

## Step 2 — Container build with the green checkmark

The template's `.github/workflows/docker.yml` builds the image and pushes to
**ghcr.io** (image named after the repo, tagged by `docker/metadata-action`, auth via
the built-in `GITHUB_TOKEN`) on every push.

- The repo may be private or public — the developer's choice — but the platform team
  needs access at handoff.
- **A green checkmark on the build workflow is the milestone.** Until the container
  builds in Actions, there is nothing to hand off. If the build fails, fix the
  Dockerfile/workflow and push again — that iteration loop is fully yours.

## Step 3 — Add the Helm chart (ride-along)

**Don't generate a chart from scratch.** A pre-built, linted chart meeting the
platform spec rides along with this skill at
[assets/helm-chart/](assets/helm-chart/). Copy it into the app repo (as `chart/` or
`helm/<app-name>/`), rename it in `Chart.yaml`, and fill in `values.yaml` per its
[README](assets/helm-chart/README.md) — image, env vars, secret names, persistence.
Charts ship in each app's repo for now; a central chart registry may come later.

Verify before handoff: `helm lint .` and `helm template <app> .` must both succeed.

**Environment variables reach the container three ways** (the chart supports all three;
this is what "secrets via downward API" in the original prompt resolves to in practice):

- `env` — plain, non-secret values. Every non-secret var the app reads goes here.
- `envFrom` — bulk-inject all keys of a pre-existing Secret/ConfigMap.
- `extraEnv` — individual vars via `valueFrom`: `secretKeyRef`, `configMapKeyRef`, or
  Downward API `fieldRef`.

**Secrets are always installed outside Helm** (Sealed Secrets / External Secrets
Operator / `kubectl`) and referenced by name — never written into the chart or values.

**Stateful (SQLite / single-writer) apps:** keep `replicaCount: 1` and use
`strategy: Recreate` (both are the chart defaults) — two pods against one SQLite file
corrupt it. **If the app stores data in SQLite, set `litestream.enabled: true`** —
SQLite WAL mode is unsafe on the platform's networked (NFS) storage and will corrupt
without it. The chart ships the full Litestream pattern (live DB on a node-local
`emptyDir`, PVC as the replica target, a restore init container, and a continuous
native-sidecar replicator); just set `litestream.dbPath` to match the app's
`DATABASE_URL` path. Requires Kubernetes ≥ 1.29 — confirm with the platform team.

> **Canonical reference:** Adam's **`agt/gpu-reservation-app`** (`helm/gpu-reservation/`)
> is a real, deployed FastAPI+SQLite app whose chart is the production source of truth
> for these conventions — the three-mechanism env model, Recreate strategy, the
> Litestream sidecar, `persistence.usePvc`, and `AUTH_PROVIDER` presets
> (`local`/`jupyterhub`/`google`/`oidc`) for the campus auth proxy. The ride-along
> chart mirrors its Litestream implementation; for app-specific patterns not in the
> template (auth presets, roster sync, etc.) copy from that chart.

<details>
<summary>Provenance / fallback prompt</summary>

The chart implements this platform-team spec. Only fall back to generating from the
prompt if the ride-along chart genuinely can't be adapted — and then flag why:

> Please create a Helm chart for deployment of this app into Kubernetes. It should
> contain Deployment, Service, Ingress, as well as optional PVC for the data
> directory. The values file should permit specification of all environment
> variables; and should also allow definition of arbitrary "volume" and
> "volumeMounts" definitions, separate from the PVC. Assume all secrets are
> installed outside of Helm, and brought into the application via downward API.
> Please let me know if you see any gaps needing clarification.

</details>

Adapted or regenerated, the chart must satisfy this checklist:

- [ ] `Deployment`, `Service`, `Ingress` templates
- [ ] **Optional PVC** for the data directory (off by default, enabled via values)
- [ ] `values.yaml` can set **every environment variable** the app reads, across the
      three mechanisms (`env` / `envFrom` / `extraEnv`)
- [ ] `values.yaml` accepts **arbitrary `volumes` and `volumeMounts`** definitions,
      independent of the PVC
- [ ] **No secrets anywhere in the chart or values** — secrets are installed outside
      Helm and referenced by name (`envFrom`/`secretKeyRef`); `extraEnv` also supports
      Downward API `fieldRef`
- [ ] Image reference parameterized (the team points it at the ghcr.io image)
- [ ] Sane defaults — deploy-time specifics (replicas, resources, cert sources) get
      tuned by the platform team per app; the chart doesn't need to know them

## Step 4 — Handoff

Fill out the ride-along handoff doc
([references/handoff-template.md](references/handoff-template.md)) as
`DEPLOYMENT.md` in the app repo, then hand the platform team a repo link where:

- [ ] Build workflow shows a **green checkmark**; image is on ghcr.io
- [ ] Helm chart is in the repo, lints/renders, and passes the checklist above
- [ ] `DEPLOYMENT.md` is complete — every env var documented (name, purpose,
      example), secrets listed by name, persistence stated (or "stateless")
- [ ] Any **ride-along services** (e.g. OCR, validation engines) are declared up
      front — they become additional elements in the same chart, designed *with* the
      platform team, not improvised
- [ ] The team has repo access (private repo: add them; public: link suffices)

## Guardrails

- **Never commit secrets, tokens, or credentials** — not in the repo, the image, the
  chart, or `values.yaml`. Secrets are installed platform-side, outside Helm.
- **Never put P3/P4 data in the app or its fixtures** (student records, PII, PHI,
  credentials). Use the `ucsd-data-classification` skill if installed; when in
  doubt, stop and ask the platform team.
- **Don't build authentication.** No SAML, no hand-rolled OAuth, no password
  databases. Campus auth arrives via the platform's auth proxy (SAML→OAuth); the
  app should at most consume an OAuth identity — the canonical chart exposes
  `AUTH_PROVIDER` presets (`local`/`jupyterhub`/`google`/`oidc`) for exactly this. If
  the app needs login *now*, raise it with the team — auth is an open platform question.
- **Assume campus-only access** (UCSD network/VPN). Don't promise or design for
  public internet exposure.
- **Don't deploy.** No `kubectl`, no `helm install` against DSMLP. Generating the
  chart is the boundary; deployment is the platform team's.
- **Don't drift from the template stack** in V1. A different stack (Node, etc.) is a
  conversation with the team, not a unilateral choice.

## When to escalate to the platform team

- The app needs **ride-along services** or more than one container.
- The app needs **system packages** beyond the template base image and you're unsure
  they're acceptable.
- The app needs **login/user identity** before the auth proxy exists.
- Anything involving regulated data, external exposure, or a non-template stack.

## Sources & currency

Current as of **2026-06-10**; this is the V1 of a fast-moving platform — expect
revisions (auth design, chart registry, and review automation are explicitly open).

- Template repo: <https://github.com/agt/claude-webapp-template>
- Canonical deployed example: <https://github.com/agt/gpu-reservation-app>
  (`helm/gpu-reservation/`) — production source of truth for the chart conventions.
- Pipeline and decisions from the TritonAI hosting working sessions (2026-06-10):
  opinionated V1 template approved; charts live in app repos initially; team forks
  user repos and rebases; first pilots are PDF Remediator, then Faculty Finder.
