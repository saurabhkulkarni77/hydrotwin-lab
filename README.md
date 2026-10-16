# HydroTwin Lab

Lab environment for student collaboration.

This repo is a copy of the `hydrotwin-site` **dev** build @ `6125ba9a` (25-year dataset, Oct 2001 - Sep 2026), published via GitHub Pages so students can experiment without touching the main project environments (production / dev).

What's in this build:
- 14 stations, classic + `-3d` WebXR pages under `stations/`
- Statistics Data view (classic pages): stat cards, charts, tables
- True-live forecast: gap-fills USGS/Open-Meteo data to today at forecast time
- DACP confidence intervals (70/80/90/95%) with per-station data in `dacp/`
- Soil & snow columns (NRCS) in the day panel
- Model drift panels (data + concept drift)
- Per-station ablation tables

- Live site: https://saurabhkulkarni77.github.io/hydrotwin-lab/
- Pushes to `main` redeploy the Pages site automatically.

## MLOps (Level 2)

This repo runs a full CI/CD/CT setup — see [MLOPS.md](MLOPS.md) for the concept map.

- **CI:** the pytest suites in `tests/` validate every station page (patch-marker integrity, HT_DATA axis), every sidecar data contract, and every internal link on each PR and push (`.github/workflows/ci.yml`).
- **Model gate:** `models/registry.json` + `models/gate.py` block production-metric regressions (>1% pooled RMSE vs `models/baselines.json`) unless the PR carries the `allow-regression` label.
- **Monitoring:** a weekly workflow recomputes drift/freshness checks from `drift/` + the sidecars and files an `mlops-monitor` issue on threshold breaches.
- **Releases:** version tags (or a manual dispatch of the release workflow) publish the site ZIP as a GitHub Release.
