# Deployment Handoff — <App Name>

Ride-along template for the `ucsd-dsmlp-deploy` skill. Fill this out and include it
in the app repo (e.g. `DEPLOYMENT.md`) when handing off to the TritonAI platform
team. Everything here should be inferable from the repo — this file just saves the
reviewers the archaeology.

## App

- **Name / one-line purpose:**
- **Repo:** <URL> (private? team access granted: yes/no)
- **Image:** `ghcr.io/<owner>/<repo>` — build workflow status: ✅ / ❌
- **Stack:** (template-standard FastAPI unless noted)

## Configuration

| Env var | Purpose | Example (non-secret) | Secret? |
|---|---|---|---|
| `DATABASE_URL` | | `sqlite:////data/app.db` | no |
| `API_KEY_X` | | — | **yes — install as Secret** |

- **Secrets needed** (names + which keys, values delivered out-of-band):
- **Persistence:** stateless / data directory at `<path>`, expected size `<N>Gi`

## Ride-along services

None / list each (what it is, image or install method, how the app reaches it).

## Helm chart

- Location in repo: `chart/`
- `helm lint` + `helm template` pass: yes/no
- Anything non-default the team should know about (extra volumes, unusual mounts):

## Access & data

- **Audience:** campus-only (default) / other (explain)
- **Login needed?** no / yes → flagged to platform team (auth proxy is platform-side)
- **Data classification:** P1/P2 only confirmed? yes/no (P3/P4 must not be present)

## Contact

- **Developer / owner:**
- **Best way to reach for review questions:**
