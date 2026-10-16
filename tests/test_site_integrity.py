"""Station-page integrity: every deploy-time patch is installed exactly
once, and the baked data axis is the 25-year axis (n=9131 from 2001-10-01).

The expected marker counts below are the *single-install signature* of the
current build, locked in from a census of all 28 pages (2026-10-16): each
patcher's idempotency marker must appear with exactly this count on every
page of its class. Counts of 2 are one installation whose banner text is
emitted in both the injected <style> block and the injected <script> block
(e.g. `ht-statsview v1`); a missing install drops the count, a duplicated
install raises it — either fails CI. The drift panel is anchored on its
canonical div, `<div id="ht-drift-panel">`, which the drift patcher itself
uses as its only safe skip check.
"""
import json

import pytest

from conftest import AXIS_N, AXIS_START, MODELS, STATIONS, read_page

CLASSIC_MARKERS = {
    "ht-statsview v1": 2,            # Statistics Data view (classic only)
    "ht-soilsnow v1": 2,             # soil/snow day-panel rows (classic only)
    "ht-dacp v1": 1,                 # DACP daily intervals
    "ht-weekly v1": 1,               # weekly outlook section (classic form)
    "ht-uiux v1": 1,                 # UI enhancer
    "ht-corr v1": 2,                 # multi-factor correlation section + boot
    "ht-fullforms v1": 1,            # model full-form glossary block
    '<div id="ht-drift-panel">': 1,  # drift panel (canonical anchor)
    'id="hts-top"': 1,               # statsview layout root
    'id="hts-sec-weekly"': 1,        # weekly section in the stats layout
    'id="htdc-on"': 1,               # DACP band toggle control
}

THREED_MARKERS = {
    "ht-dacp v1": 1,                 # DACP daily intervals
    "ht-weekly v1": 2,               # weekly outlook panel (3D form)
    "ht-uiux v1": 2,                 # UI enhancer
    "ht-live-gap v1": 2,             # true-live gap fill (3D only)
    "ht-ablfix v1": 1,               # ablation readout fix (3D only)
    '<div id="ht-drift-panel">': 1,  # drift panel (canonical anchor)
    'id="htdc-on"': 1,               # DACP band toggle control
    'id="htwk-canvas"': 1,           # weekly outlook canvas
}

# Patches that must NOT leak across page classes.
CLASSIC_FORBIDDEN = ("ht-live-gap v1", "ht-ablfix v1")
THREED_FORBIDDEN = ("ht-statsview v1", "ht-soilsnow v1", 'id="hts-top"')


def _extract_ht_data(html):
    """window.HT_DATA is a strict-JSON object literal; extract and parse it."""
    i = html.find("window.HT_DATA=")
    assert i >= 0, "window.HT_DATA assignment not found"
    j = html.find("{", i)
    depth, in_str, esc = 0, False, False
    for k in range(j, len(html)):
        c = html[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(html[j:k + 1])
    raise AssertionError("HT_DATA object is unbalanced")


@pytest.mark.parametrize("station", STATIONS)
def test_classic_page_markers(repo_root, station):
    html = read_page(repo_root, station, "")
    for marker, expected in CLASSIC_MARKERS.items():
        assert html.count(marker) == expected, (
            f"{station} classic: marker {marker!r} found "
            f"{html.count(marker)}x, expected {expected}x")
    for marker in CLASSIC_FORBIDDEN:
        assert marker not in html, f"{station} classic: unexpected {marker!r}"


@pytest.mark.parametrize("station", STATIONS)
def test_3d_page_markers(repo_root, station):
    html = read_page(repo_root, station, "-3d")
    for marker, expected in THREED_MARKERS.items():
        assert html.count(marker) == expected, (
            f"{station} 3d: marker {marker!r} found "
            f"{html.count(marker)}x, expected {expected}x")
    for marker in THREED_FORBIDDEN:
        assert marker not in html, f"{station} 3d: unexpected {marker!r}"


@pytest.mark.parametrize("station", STATIONS)
@pytest.mark.parametrize("kind", ["", "-3d"])
def test_page_axis_fragments(repo_root, station, kind):
    html = read_page(repo_root, station, kind)
    assert html.count(f'"start":"{AXIS_START}"') == 1
    assert html.count(f'"n":{AXIS_N}') == 1


@pytest.mark.parametrize("station", STATIONS)
def test_classic_ht_data_parses(repo_root, station):
    data = _extract_ht_data(read_page(repo_root, station, ""))
    assert data["start"] == AXIS_START
    assert data["n"] == AXIS_N
    assert data["station"]["stationId"] == f"USGS-{station}"
    assert data["models"] == MODELS
    for series in ("tmax", "tmin", "tmean", "precip", "flow"):
        assert len(data[series]) == AXIS_N, f"{station}: {series} length"
    assert len(data["pred"]) == len(MODELS)


def test_all_station_pages_exist(repo_root):
    pages = sorted(p.name for p in (repo_root / "stations").glob("*.html"))
    expected = sorted(
        [f"USGS-{s}.html" for s in STATIONS]
        + [f"USGS-{s}-3d.html" for s in STATIONS])
    assert pages == expected
