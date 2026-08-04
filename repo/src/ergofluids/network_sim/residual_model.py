"""A small model predicting the *residual* between a simulated (or, in
future, real) subdiffusion exponent and the obstruction-scaling baseline's
implicit prediction (normal diffusion, exponent 1.0), from descriptors the
baseline itself does not use: adhesion strength and particle aspect ratio.
Also a coarse regime classifier (normal / mildly hindered / caged) on the
same features, since a discrete regime call is often the more robust,
directly useful output for a screening tool than a point exponent estimate
(see ../../../docs/ for why a classification framing was chosen as the
lower-risk first product bet).

This targets exactly the two documented failure modes of obstruction-scaling
found in real experimental literature during this project's research pass:
chemical-affinity-driven deviation (Wang 2026, Pharmaceutics,
doi:10.3390/pharmaceutics18050592) and particle-shape-driven deviation
(Rokhforouz et al. 2025, Soft Matter, doi:10.1039/d5sm00195a). It is trained
here on self-generated simulation data (network_sim/sweep.py), not on either
paper's own data, since neither publishes a raw dataset; validating against
real experimental data, if a suitable public dataset can be found, is the
natural next gate, not yet run.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import LeaveOneOut

FEATURE_COLUMNS = ["adhesion_depth", "aspect_ratio", "confinement"]

REGIME_BINS = [-np.inf, 0.7, 0.9, np.inf]
REGIME_LABELS = ["caged", "hindered", "normal"]


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["confinement"] = df["particle_radius"] / df["mean_pore_radius"]
    df["regime"] = pd.cut(df["simulated_exponent"], bins=REGIME_BINS, labels=REGIME_LABELS)
    return df


@dataclass
class ValidationResult:
    baseline_mae: float
    residual_model_mae: float
    n: int
    classifier_accuracy: float
    classifier_baseline_accuracy: float  # accuracy of always predicting the majority class


def leave_one_out_validate(df: pd.DataFrame) -> ValidationResult:
    """Leave-one-out, appropriate given the sweep's modest condition count
    (dozens, not thousands): every point gets held out exactly once, so the
    result is not sensitive to an arbitrary train/test split choice."""
    df = add_derived_columns(df)
    X = df[FEATURE_COLUMNS].to_numpy()
    y_residual = (df["simulated_exponent"] - df["baseline_exponent"]).to_numpy()
    y_regime = df["regime"].to_numpy()

    loo = LeaveOneOut()
    baseline_errors = []
    residual_model_errors = []
    correct = 0
    for train_idx, test_idx in loo.split(X):
        reg = RandomForestRegressor(n_estimators=200, max_depth=4, random_state=0)
        reg.fit(X[train_idx], y_residual[train_idx])
        pred_residual = reg.predict(X[test_idx])[0]
        baseline_pred_exponent = df["baseline_exponent"].to_numpy()[test_idx][0]
        corrected_pred = baseline_pred_exponent + pred_residual
        true_exponent = df["simulated_exponent"].to_numpy()[test_idx][0]

        baseline_errors.append(abs(true_exponent - baseline_pred_exponent))
        residual_model_errors.append(abs(true_exponent - corrected_pred))

        clf = RandomForestClassifier(n_estimators=200, max_depth=4, random_state=0)
        clf.fit(X[train_idx], y_regime[train_idx])
        pred_label = clf.predict(X[test_idx])[0]
        correct += int(pred_label == y_regime[test_idx][0])

    majority_class_frac = float(pd.Series(y_regime).value_counts(normalize=True).max())

    return ValidationResult(
        baseline_mae=float(np.mean(baseline_errors)),
        residual_model_mae=float(np.mean(residual_model_errors)),
        n=len(df),
        classifier_accuracy=correct / len(df),
        classifier_baseline_accuracy=majority_class_frac,
    )


def fit_full_models(df: pd.DataFrame):
    """Fit on the full sweep (no held-out split), for use by `predict.py`
    once `leave_one_out_validate` has shown the approach beats the baseline
    out of sample. Returns (residual_regressor, regime_classifier)."""
    df = add_derived_columns(df)
    X = df[FEATURE_COLUMNS].to_numpy()
    y_residual = (df["simulated_exponent"] - df["baseline_exponent"]).to_numpy()
    y_regime = df["regime"].to_numpy()

    reg = RandomForestRegressor(n_estimators=300, max_depth=4, random_state=0)
    reg.fit(X, y_residual)
    clf = RandomForestClassifier(n_estimators=300, max_depth=4, random_state=0)
    clf.fit(X, y_regime)
    return reg, clf
