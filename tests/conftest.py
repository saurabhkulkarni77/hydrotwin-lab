"""Shared fixtures/constants for the HydroTwin Lab CI test suite.

The suite validates the *baked* site exactly as it is served by GitHub
Pages: station-page patch integrity, baked data contracts, and internal
link targets. Everything is stdlib-only apart from pytest itself.
"""
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The 14 USGS stations in this build (filename stems under stations/,
# sidecar stems under dacp/, dacpw/, weekly/, soilsnow/).
STATIONS = [
    "01463500", "01646500", "02320500", "03294500", "05331000",
    "06214500", "06934500", "07374000", "08057000", "08158000",
    "08313000", "09380000", "11447650", "14105700",
]

# Canonical model order used by the pages' HT_DATA.
MODELS = [
    "Transformer", "GP Matérn", "GP RBF", "TFT", "LSTM", "ARIMA",
    "SARIMA", "PatchTST", "PILSTMv1", "GCN",
]

# Data axis of the 25-year build.
AXIS_START = "2001-10-01"
AXIS_N = 9131
AXIS_END = "2026-09-30"


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


def read_page(repo_root, station, kind):
    """kind is '' for the classic page or '-3d' for the 3D page."""
    path = repo_root / "stations" / f"USGS-{station}{kind}.html"
    return path.read_text(encoding="utf-8", errors="replace")
