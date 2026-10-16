# MLOps — Level 2 in this repo

This repo runs a Level-2 MLOps setup (CI + CD + CT) adapted to what it
is: the public lab/staging surface of HydroTwin — a baked static site
(28 station pages + per-station data sidecars) whose "models" are the
forecast artifacts baked into those pages. Heavy training lives in
`hydrotwin-models`; everything that can be checked, gated, monitored,
and released *here* is automated here.

## Concept map

| Level-2 concept | Implemented as | Where |
|---|---|---|
| CI — code tests | pytest suite runs on every PR and push to `main` | `.github/workflows/ci.yml`, `tests/` |
| CI — site integrity tests | every station page must carry each deploy-time patch marker with its exact single-install count; HT_DATA must parse with n=9131 from 2001-10-01 | `tests/test_site_integrity.py` |
| CI — data contracts | every sidecar JSON (dacp/, dacpw/, weekly/, soilsnow/) parses and matches its station axis/schema; drift bake/report consistency | `tests/test_data_contracts.py` |
| CI — link/asset checks | every relative href/src in the baked pages resolves to a repo file | `tests/test_links.py` |
| Model registry | versioned registry of all 10 models: stage (production/candidate), pooled daily + weekly RMSE, data window, artifact locations | `models/registry.json` |
| Validation gate | PRs touching `models/**` fail if a production-stage model's pooled RMSE regresses >1% vs the frozen baselines, unless the PR carries the `allow-regression` label | `models/gate.py`, `models/baselines.json`, `.github/workflows/model-gate.yml` |
| Monitoring | weekly job recomputes drift (PSI from `drift/drift_bake.json`), freshness (drift-report window vs data axis; DACP reach), and sidecar coverage; opens/updates one `mlops-monitor` issue on breach, silent otherwise | `monitor/monitor.py`, `.github/workflows/monitor.yml` |
| Continuous training (CT) | request + validation side here (honest stub); training itself runs in `hydrotwin-models` (`daily-retrain.yml` with pre-training `drift_check.py`); post-retrain metrics re-enter through the gate | `.github/workflows/retrain.yml`, `retrain/` |
| CD — site deploy | pushes to `main` redeploy GitHub Pages automatically (unchanged) | GitHub Pages |
| CD — releases | version tags (or manual dispatch) build the GitHub-flavor site ZIP (no `.github/`) and publish a GitHub Release with generated notes | `.github/workflows/release.yml` |
| Environments | production = `hydrotwin-site` main (CloudFront + Pages); dev = `hydrotwin-site` dev branch (S3); lab = this repo (Pages). Promotion is dev-first, human-approved | `ENVIRONMENTS.md` in hydrotwin-site; this repo's README |

## The gate, in one paragraph

`models/baselines.json` freezes the accepted build's pooled metrics
(25-year build, test era WY2025–26: daily champion PILSTMv1 0.2703,
weekly champion Transformer 0.4857). A PR that updates
`models/registry.json` with worse production numbers fails the gate
unless a maintainer deliberately labels it `allow-regression` — the
label re-runs the gate in warning mode, so the acceptance is visible
in the PR's check history.

## Monitoring thresholds

* PSI > 0.25 on any feature = drift breach (project convention:
  <0.10 stable, 0.10–0.25 watch, >0.25 drift).
* Drift report's recent window must end on the data-axis end
  (2026-09-30 for the current build).
* Daily DACP sidecars must reach within 14 days of the axis end.
* Every sidecar family must hold exactly one file per station.

## Honest limitations

* The training stage is a validated handoff, not a training run —
  this repo intentionally contains no training code or data pipeline.
* The lab repo is a snapshot synced from `hydrotwin-site` dev; a
  re-sync replaces site content. The MLOps overlay added here
  (`.github/`, `tests/`, `models/`, `monitor/`, `retrain/`,
  `MLOPS.md`) is additive and does not alter any station page; if a
  future re-sync is done by replacing the whole tree, re-apply the
  overlay afterwards.
* `chart3d/` sidecars exist on the dev build (post-dating this
  snapshot); when the lab repo gains them, add their contract to
  `tests/test_data_contracts.py` and the monitor's coverage list.
