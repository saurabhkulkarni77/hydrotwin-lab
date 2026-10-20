"""Baked-data contracts: every per-station sidecar JSON parses and matches
its station axis/schema, and the drift bake/report are internally
consistent.

Families covered (the sidecar families present in this repo snapshot):
  soilsnow/<site>.json  - daily soil/snow series on the full 9131-day axis
  weekly/<site>.json    - weekly-outlook baked forecasts (12 weekly leads)
  dacp/<site>.json      - daily DACP conformal quantiles, levels 70/80/90/95
  dacpw/<site>.json     - weekly DACP conformal quantiles, same levels
  corr/<site>.json      - multi-factor correlation matrix (ht-corr v1)
  oldfc/<site>.json     - pre-drift-fix baked fans, last 400 issue days (ht-oldfc v1)
  drift/drift_bake.json + drift/drift_report.json - baked drift analysis

When a new sidecar family is added to the repo, add its contract here.
"""
import json

import pytest

from conftest import AXIS_END, AXIS_N, AXIS_START, MODELS, STATIONS

DRIFT_FEATURES = {"tmax_c", "tmin_c", "tmean_c", "precip_mm", "log10_flow"}
DACP_LEVELS = [70, 80, 90, 95]


def _load(repo_root, *parts):
    with open(repo_root.joinpath(*parts), encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("family", ["dacp", "dacpw", "weekly", "soilsnow", "corr", "oldfc"])
def test_sidecar_coverage(repo_root, family):
    files = sorted(p.stem for p in (repo_root / family).glob("*.json"))
    assert files == sorted(STATIONS), f"{family}/ must hold one file per station"


@pytest.mark.parametrize("station", STATIONS)
def test_soilsnow_contract(repo_root, station):
    obj = _load(repo_root, "soilsnow", f"{station}.json")
    assert obj["site"] == station
    assert obj["start"] == AXIS_START
    assert obj["n"] == AXIS_N
    for key in ("sms", "stmp", "swe"):
        assert len(obj[key]) == AXIS_N, f"{station} soilsnow {key} length"


@pytest.mark.parametrize("station", STATIONS)
def test_weekly_contract(repo_root, station):
    obj = _load(repo_root, "weekly", f"{station}.json")
    assert obj["site"] == station
    assert obj["v"] == "ht-weekly v1"
    assert obj["start"] == AXIS_START
    assert obj["models"] == MODELS
    assert set(obj["rmse_test"]) == set(MODELS)
    assert set(obj["predw"]) == set(MODELS)
    n_issue = len(obj["dates"])
    assert n_issue > 0 and obj["dates"] == sorted(obj["dates"])
    for model in MODELS:
        rows = obj["predw"][model]
        assert len(rows) == n_issue
        assert all(len(row) == 12 for row in rows), (
            f"{station} weekly {model}: every issue row must carry 12 leads")


@pytest.mark.parametrize("station", STATIONS)
def test_corr_contract(repo_root, station):
    obj = _load(repo_root, "corr", f"{station}.json")
    assert obj["site"] == station
    assert obj["v"] == "ht-corr v1"
    assert obj["start"] == AXIS_START
    assert obj["end"] == AXIS_END
    keys = [v["key"] for v in obj["vars"]]
    assert "logflow" in keys and "flow" in keys
    k = len(keys)
    assert len(obj["matrix"]) == k and all(len(row) == k for row in obj["matrix"])
    for i in range(k):
        assert obj["matrix"][i][i] == 1.0, f"{station} corr diagonal {keys[i]}"
        for j in range(k):
            r = obj["matrix"][i][j]
            assert r is None or -1.0 <= r <= 1.0
            assert obj["n"][i][j] > 0
    assert len(obj["lead1_logflow"]) == k and len(obj["lead1_n"]) == k


@pytest.mark.parametrize("family", ["dacp", "dacpw"])
@pytest.mark.parametrize("station", STATIONS)
def test_dacp_contract(repo_root, family, station):
    obj = _load(repo_root, family, f"{station}.json")
    assert obj["site"] == station
    assert obj["levels"] == DACP_LEVELS
    assert set(obj["q"]) == set(MODELS)
    assert len(obj["dates"]) > 0
    assert obj["dates"] == sorted(obj["dates"])
    assert obj["dates"][-1] <= AXIS_END


def test_drift_bake_contract(repo_root):
    bake = _load(repo_root, "drift", "drift_bake.json")
    assert sorted(bake) == sorted(STATIONS)
    for station, entry in bake.items():
        feats = entry["data"]["features"]
        assert set(feats) == DRIFT_FEATURES, f"{station} drift features"
        assert all(v >= 0 for v in feats.values()), f"{station} PSI negative"
        # Headline PSI is the worst feature's PSI (stored rounded to 4 dp).
        assert abs(entry["data"]["psi"] - max(feats.values())) < 0.01
        assert entry["data"]["worst"] == max(feats, key=feats.get)
        assert set(entry["models"]) == set(MODELS)


def test_drift_report_contract(repo_root):
    report = _load(repo_root, "drift", "drift_report.json")
    # The 2026-10-19 drift-fix data swap re-based the report on the full
    # record; the pre-swap contract pinned the 2001-2023 baseline and went
    # red on the swap commit. Windows now span the whole axis.
    assert report["windows"]["baseline"] == [AXIS_START, AXIS_END]
    assert report["windows"]["recent"] == ["2025-10-01", AXIS_END]
    assert report["models"] == MODELS
    assert sorted(report["stations"]) == sorted(STATIONS)


@pytest.mark.parametrize("station", STATIONS)
def test_oldfc_contract(repo_root, station):
    """oldfc/<site>.json: the pre-drift-fix baked fans (last 400 issue days x
    7 leads x 10 models), extracted from the lab pages' own pre-swap bake so
    the old-weights comparison compares like with like."""
    obj = _load(repo_root, "oldfc", f"{station}.json")
    assert obj["site"] == station
    assert obj["v"] == "ht-oldfc v1"
    assert obj["src_commit"] == "0908430a8e"
    assert obj["start"] == AXIS_START
    assert obj["n"] == AXIS_N
    assert obj["from_issue"] == AXIS_N - 400
    assert obj["models"] == MODELS
    assert sorted(obj["pred"]) == sorted(MODELS)
    for name in MODELS:
        rows = obj["pred"][name]
        assert len(rows) == 400, f"{station}/{name}: {len(rows)} rows"
        assert all(len(r) == 7 for r in rows), f"{station}/{name}: row width"
