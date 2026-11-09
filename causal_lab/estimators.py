"""Cross-fitted AIPW and honest train/test uplift comparisons."""

from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
from threadpoolctl import threadpool_limits
from src.experiment import proportion_difference, holm


def validate(frame):
    needed = [f"f{i}" for i in range(12)] + ["treatment", "visit", "conversion", "unit_id"]
    if not set(needed).issubset(frame) or frame[needed].isna().any().any():
        raise ValueError("Missing pre-treatment covariates or outcome")
    if frame.unit_id.duplicated().any() or not np.isfinite(frame[needed]).all().all():
        raise ValueError("Duplicate units or non-finite values")
    for c in ["treatment", "visit", "conversion"]:
        if not frame[c].isin([0, 1]).all():
            raise ValueError("Binary variables required")
    if min(frame.groupby("treatment").size()) < 30:
        raise ValueError("Insufficient arm size")


def summary(score):
    score = np.asarray(score)
    estimate = float(score.mean())
    se = float(score.std(ddof=1) / np.sqrt(len(score)))
    return {"estimate": estimate, "standard_error": se, "ci95": [estimate - 1.96 * se, estimate + 1.96 * se]}


def aipw(X, t, y, clip=0.01):
    t = np.asarray(t)
    y = np.asarray(y)
    n = len(t)
    e = np.empty(n)
    m0 = np.empty(n)
    m1 = np.empty(n)
    cv = StratifiedKFold(3, shuffle=True, random_state=42)
    for train, test in cv.split(X, t):
        prop = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
        prop.fit(X[train], t[train])
        e[test] = prop.predict_proba(X[test])[:, 1]
        for arm, dest in [(0, m0), (1, m1)]:
            model = HistGradientBoostingClassifier(
                max_iter=70, max_leaf_nodes=12, l2_regularization=5, random_state=42
            )
            idx = train[t[train] == arm]
            model.fit(X[idx], y[idx])
            dest[test] = model.predict_proba(X[test])[:, 1]
    bounded = np.clip(e, clip, 1 - clip)
    score = m1 - m0 + t * (y - m1) / bounded - (1 - t) * (y - m0) / (1 - bounded)
    return (
        {
            **summary(score),
            "propensity_min": float(e.min()),
            "propensity_max": float(e.max()),
            "clipped_fraction": float(np.mean(e != bounded)),
            "method": "3-fold cross-fitted AIPW; estimated propensity",
            "max_inverse_weight": float(np.max(t / bounded + (1 - t) / (1 - bounded))),
        },
        bounded,
        score,
    )


def fit_uplift(X, t, y):
    base = HistGradientBoostingClassifier(
        max_iter=80, max_leaf_nodes=12, l2_regularization=5, random_state=42
    )
    m0 = clone(base).fit(X[t == 0], y[t == 0])
    m1 = clone(base).fit(X[t == 1], y[t == 1])
    s = clone(base).fit(np.column_stack([X, t]), y)
    # X-learner imputed treatment responses; propensity combines the two effects.
    d0 = m1.predict_proba(X[t == 0])[:, 1] - y[t == 0]
    d1 = y[t == 1] - m0.predict_proba(X[t == 1])[:, 1]
    r0 = HistGradientBoostingRegressor(max_iter=60, max_leaf_nodes=8, random_state=42).fit(X[t == 0], d0)
    r1 = HistGradientBoostingRegressor(max_iter=60, max_leaf_nodes=8, random_state=42).fit(X[t == 1], d1)
    prediction = clone(base).fit(X, y)

    def predict(Z):
        p = float(t.mean())
        return {
            "T": m1.predict_proba(Z)[:, 1] - m0.predict_proba(Z)[:, 1],
            "S": s.predict_proba(np.column_stack([Z, np.ones(len(Z))]))[:, 1]
            - s.predict_proba(np.column_stack([Z, np.zeros(len(Z))]))[:, 1],
            "X": p * r0.predict(Z) + (1 - p) * r1.predict(Z),
            "predictive": prediction.predict_proba(Z)[:, 1],
        }

    return predict


def uplift_metrics(t, y, scores, e):
    t = np.asarray(t)
    y = np.asarray(y)
    pseudo = y * (t / e - (1 - t) / (1 - e))
    order = np.argsort(-scores, kind="stable")
    gain = np.cumsum(pseudo[order]) / len(t)
    fraction = np.arange(1, len(t) + 1) / len(t)
    # Center against random targeting. Discrete integration includes origin.
    auuc = float(np.trapezoid(np.r_[0, gain - fraction * pseudo.mean()], np.r_[0, fraction]))
    k = max(30, len(t) // 5)
    top = order[:k]
    rng = np.random.default_rng(42)
    boot = []
    for _ in range(100):
        idx = rng.integers(0, len(t), len(t))
        ordered = idx[np.argsort(-np.asarray(scores)[idx], kind="stable")]
        curve = np.cumsum(pseudo[ordered]) / len(t) - fraction * pseudo[idx].mean()
        boot.append(np.trapezoid(np.r_[0, curve], np.r_[0, fraction]))
    return {
        "auuc_bootstrap_ci95_fixed_model": np.quantile(boot, [0.025, 0.975]).tolist(),
        "bootstrap_scope": "100 user resamples, held-out fixed scores; excludes training uncertainty",
        "auuc_above_random": auuc,
        "top20_itt": summary(pseudo[top]),
        "definition": "HT gain minus random targeting; estimated treatment propensity",
    }


def analyze(frame):
    validate(frame)
    X = frame[[f"f{i}" for i in range(12)]].to_numpy()
    t = frame.treatment.to_numpy()
    y = frame.visit.to_numpy()
    a, b = frame[t == 0], frame[t == 1]
    ab = {c: proportion_difference(a[c], b[c]) for c in ["visit", "conversion"]}
    std = np.sqrt((X[t == 1].var(axis=0) + X[t == 0].var(axis=0)) / 2)
    balance = (X[t == 1].mean(axis=0) - X[t == 0].mean(axis=0)) / np.maximum(std, 1e-12)
    with threadpool_limits(limits=2):
        dr, e, score = aipw(X, t, y)
        train, test = train_test_split(np.arange(len(t)), test_size=0.3, random_state=42, stratify=t)
        models = fit_uplift(X[train], t[train], y[train])
        pred = models(X[test])
    comparison = {name: uplift_metrics(t[test], y[test], s, e[test]) for name, s in pred.items()}
    comparison["predictive"]["auc"] = float(roc_auc_score(y[test], pred["predictive"]))
    comparison["predictive"]["brier"] = float(brier_score_loss(y[test], pred["predictive"]))
    # Exploratory effect calibration with honest holdout and HT pseudo outcomes.
    segments = []
    for bucket in range(5):
        rank = pd.Series(pred["T"]).rank(method="first", pct=True).to_numpy()
        mask = (rank > bucket / 5) & (rank <= (bucket + 1) / 5)
        pseudo = y[test] * (t[test] / e[test] - (1 - t[test]) / (1 - e[test]))
        segments.append(
            {
                "quintile": bucket + 1,
                "n": int(mask.sum()),
                "predicted_cate": float(pred["T"][mask].mean()),
                **summary(pseudo[mask]),
            }
        )
    delta = 0.005
    p0 = float(a.visit.mean())
    ratio = len(b) / len(a)
    planned = float(
        NormalIndPower().solve_power(
            effect_size=proportion_effectsize(p0 + delta, p0), alpha=0.05, power=0.8, ratio=ratio
        )
    )
    return {
        "n": len(frame),
        "treated": len(b),
        "control": len(a),
        "outcome": "visit",
        "ab": ab,
        "holm": holm({k: v["p_value"] for k, v in ab.items()}),
        "aipw": dr,
        "ipw": summary(y * (t / e - (1 - t) / (1 - e))),
        "balance_smd": dict(zip([f"f{i}" for i in range(12)], balance.tolist(), strict=True)),
        "planning": {
            "baseline_visit": p0,
            "mde_absolute": delta,
            "control_required": planned,
            "treated_required": planned * ratio,
            "power": 0.8,
        },
        "srm": {
            "status": "not assessable",
            "reason": "Exact intended allocation not supplied; published .85 is rounded; do not use observed split to certify SRM",
        },
        "comparison": comparison,
        "effect_calibration": segments,
        "sensitivity": {
            "additive_unmeasured_bias": [
                {"bias": d, "adjusted_effect": dr["estimate"] - d} for d in [0, 0.001, 0.005, 0.01]
            ],
            "interpretation": "Hypothetical bias tipping exercise; not a bound inferred from data",
        },
        "business_guardrail": {
            "status": "unavailable",
            "reason": "Criteo has no unsubscribe, advertising cost or revenue; visit/conversion cannot certify profitability",
        },
        "decision": "Research estimates only; no rollout without exact assignment protocol, costs and safety outcomes",
        "assumptions": [
            "Published randomized assignment; intention-to-treat, NEVER condition on exposure",
            "SUTVA, no interference and outcome measurement integrity cannot be verified from anonymous rows",
            "Quintiles exploratory, no confirmatory CATE significance",
            "No DiD on cross-sectional Criteo",
        ],
    }
