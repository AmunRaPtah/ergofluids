"""Minimal demo web UI over the two product CLIs (predict_transport.py,
recommend_next_experiment.py). Built so there's something to show a design
partner (Amsden, Wang, Nance, or Giuntoli, see
docs/design-partner-outreach-draft.md) immediately if any of them replies,
rather than only a command-line script. Same underlying functions as the
CLIs, not reimplemented logic.

Not validated against real data (see docs/gate-result-network-sim-*.md);
this UI states that plainly on every page, not just in this docstring.

Run: .venv/bin/python scripts/demo_app.py
Then open http://127.0.0.1:5000/
Requires: .venv/bin/pip install -e ".[demo]"
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
from flask import Flask, render_template_string, request

from ergofluids.network_sim.active_learning import ObservedPoint, fit_gp, recommend_next
from ergofluids.network_sim.baseline import baseline_predicted_exponent
from ergofluids.network_sim.residual_model import add_derived_columns, fit_full_models

REPO_ROOT = Path(__file__).resolve().parents[1]
SWEEP_CSV = REPO_ROOT / "data" / "network_sim_sweep.csv"

app = Flask(__name__)

DISCLAIMER = (
    "This tool is validated so far only on self-generated simulation data, plus real-data "
    "consistency checks on the underlying premise. It has not been validated against real "
    "transport measurements collected to test it directly. See docs/gate-result-network-sim-*.md "
    "in the repo for the full, honest record."
)

BASE_TEMPLATE = """
<!doctype html>
<title>ErgoFluids / network_sim demo</title>
<style>
  body { font-family: sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; }
  nav a { margin-right: 1rem; }
  .disclaimer { background: #fff3cd; border: 1px solid #ffe69c; padding: 0.75rem; border-radius: 4px; }
  table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
  th, td { border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }
  input, select { margin: 0.3rem 0; padding: 0.3rem; }
  label { display: block; margin-top: 0.6rem; }
</style>
<h1>ErgoFluids / network_sim</h1>
<p class="disclaimer">{{ disclaimer }}</p>
<nav>
  <a href="/">Predict transport</a>
  <a href="/recommend">Recommend next experiment</a>
</nav>
<hr>
{{ body|safe }}
"""


@app.route("/", methods=["GET", "POST"])
def predict():
    result_html = ""
    if request.method == "POST":
        if not SWEEP_CSV.exists():
            result_html = f"<p><b>Error:</b> {SWEEP_CSV} not found. Run scripts/run_network_sweep.py first.</p>"
        else:
            particle_radius = float(request.form["particle_radius"])
            mesh_pore_radius = float(request.form["mesh_pore_radius"])
            adhesion = float(request.form["adhesion"])
            aspect_ratio = float(request.form["aspect_ratio"])

            df = pd.read_csv(SWEEP_CSV)
            reg, clf = fit_full_models(df)
            baseline_exp = baseline_predicted_exponent(steric_only=(adhesion == 0))
            confinement = particle_radius / mesh_pore_radius
            x = [[adhesion, aspect_ratio, confinement]]
            residual = float(reg.predict(x)[0])
            regime = clf.predict(x)[0]
            proba = dict(zip(clf.classes_, clf.predict_proba(x)[0].tolist()))

            rows = "".join(f"<tr><td>{k}</td><td>{v:.3f}</td></tr>" for k, v in proba.items())
            result_html = f"""
            <h2>Result</h2>
            <table>
              <tr><td>Baseline exponent (obstruction-scaling)</td><td>{baseline_exp:.3f}</td></tr>
              <tr><td>Predicted exponent</td><td>{baseline_exp + residual:.3f}</td></tr>
              <tr><td>Predicted regime</td><td><b>{regime}</b></td></tr>
            </table>
            <h3>Regime probabilities</h3>
            <table>{rows}</table>
            """

    form_html = """
    <h2>Predict transport</h2>
    <form method="post">
      <label>Particle radius <input name="particle_radius" type="number" step="any" value="0.5" required></label>
      <label>Mesh pore radius <input name="mesh_pore_radius" type="number" step="any" value="1.5" required></label>
      <label>Adhesion depth (0 = purely steric) <input name="adhesion" type="number" step="any" value="0" required></label>
      <label>Aspect ratio (1 = sphere) <input name="aspect_ratio" type="number" step="any" value="1" required></label>
      <button type="submit">Predict</button>
    </form>
    """
    return render_template_string(BASE_TEMPLATE, disclaimer=DISCLAIMER, body=form_html + result_html)


@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    result_html = ""
    if request.method == "POST":
        try:
            observed_df = pd.read_csv(io.StringIO(request.form["observed_csv"]))
            candidates_df = pd.read_csv(io.StringIO(request.form["candidates_csv"]))
            required = {"adhesion_depth", "aspect_ratio", "confinement", "exponent"}
            missing = required - set(observed_df.columns)
            if missing:
                raise ValueError(f"observed data missing columns: {sorted(missing)}")

            observed = [
                ObservedPoint(
                    adhesion_depth=row.adhesion_depth,
                    aspect_ratio=row.aspect_ratio,
                    confinement=row.confinement,
                    exponent=row.exponent,
                    source="real",
                )
                for row in observed_df.itertuples()
            ]
            gp = fit_gp(observed)
            ranked = recommend_next(gp, candidates_df, strategy="uncertainty")

            result_html = "<h2>Ranked candidates (test the top row next)</h2>" + ranked.to_html(index=False)
        except Exception as exc:  # demo UI: show the error inline rather than a stack trace page
            result_html = f"<p><b>Error:</b> {exc}</p>"

    form_html = """
    <h2>Recommend next experiment</h2>
    <p>Paste your own observed data (columns: adhesion_depth, aspect_ratio, confinement, exponent)
    and a candidate pool (columns: adhesion_depth, aspect_ratio, confinement, + any label columns).</p>
    <form method="post">
      <label>Observed data (CSV)
        <textarea name="observed_csv" rows="6" cols="60">adhesion_depth,aspect_ratio,confinement,exponent
0.0,1.0,0.2,0.98
1.5,1.0,0.3,0.93
0.0,3.0,0.2,1.01
3.0,1.0,0.4,0.85</textarea>
      </label>
      <label>Candidate pool (CSV)
        <textarea name="candidates_csv" rows="6" cols="60">name,adhesion_depth,aspect_ratio,confinement
candidate_A,4.0,1.0,0.5
candidate_B,0.5,3.0,0.25
candidate_C,2.0,2.0,0.35
candidate_D,0.0,1.0,0.2</textarea>
      </label>
      <button type="submit">Recommend</button>
    </form>
    """
    return render_template_string(BASE_TEMPLATE, disclaimer=DISCLAIMER, body=form_html + result_html)


if __name__ == "__main__":
    app.run(debug=True)
