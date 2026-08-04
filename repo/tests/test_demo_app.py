"""Smoke tests for the demo web UI (scripts/demo_app.py), using Flask's
test client rather than a live server. Skipped if flask isn't installed
(it's an optional "demo" extra, not a core dependency)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

flask_installed = importlib.util.find_spec("flask") is not None

REPO_ROOT = Path(__file__).resolve().parents[1]
SWEEP_CSV = REPO_ROOT / "data" / "network_sim_sweep.csv"


@pytest.fixture
def client():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import demo_app

    demo_app.app.testing = True
    return demo_app.app.test_client()


@pytest.mark.skipif(not flask_installed, reason="flask not installed (optional demo extra)")
def test_predict_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Predict transport" in resp.data


@pytest.mark.skipif(not flask_installed, reason="flask not installed (optional demo extra)")
@pytest.mark.skipif(not SWEEP_CSV.exists(), reason="run scripts/run_network_sweep.py first")
def test_predict_post_returns_regime(client):
    resp = client.post(
        "/",
        data={"particle_radius": "0.6", "mesh_pore_radius": "1.5", "adhesion": "3.0", "aspect_ratio": "1.0"},
    )
    assert resp.status_code == 200
    assert b"Predicted regime" in resp.data


@pytest.mark.skipif(not flask_installed, reason="flask not installed (optional demo extra)")
def test_recommend_page_loads(client):
    resp = client.get("/recommend")
    assert resp.status_code == 200
    assert b"Recommend next experiment" in resp.data


@pytest.mark.skipif(not flask_installed, reason="flask not installed (optional demo extra)")
def test_recommend_post_ranks_far_candidate_first(client):
    observed_csv = (
        "adhesion_depth,aspect_ratio,confinement,exponent\n"
        "0.0,1.0,0.2,0.98\n1.5,1.0,0.3,0.93\n0.0,3.0,0.2,1.01\n3.0,1.0,0.4,0.85\n"
    )
    candidates_csv = (
        "name,adhesion_depth,aspect_ratio,confinement\n"
        "candidate_A,4.0,1.0,0.5\ncandidate_D,0.0,1.0,0.2\n"
    )
    resp = client.post("/recommend", data={"observed_csv": observed_csv, "candidates_csv": candidates_csv})
    assert resp.status_code == 200
    body = resp.data.decode()
    # the far, unexplored candidate (A) should be ranked before the near one (D)
    assert body.index("candidate_A") < body.index("candidate_D")
