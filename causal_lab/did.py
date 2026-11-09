"""Two-period, two-group DiD only; simulated validation has known ground truth."""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def estimate(frame):
    required = {"unit", "treated", "post", "outcome"}
    if not required.issubset(frame) or frame[list(required)].isna().any().any():
        raise ValueError("Invalid panel")
    if not frame.treated.isin([0, 1]).all() or not frame.post.isin([0, 1]).all():
        raise ValueError("Binary design required")
    if frame.duplicated(["unit", "post"]).any() or not frame.groupby("unit").size().eq(2).all():
        raise ValueError("Balanced two-period panel required")
    if frame.groupby("unit").treated.nunique().max() != 1 or frame.treated.nunique() != 2:
        raise ValueError("Treatment must be time-invariant with controls")
    if frame.unit.nunique() < 30:
        raise ValueError("Too few clusters for this inference procedure")
    model = smf.ols("outcome ~ treated * post", frame).fit(
        cov_type="cluster", cov_kwds={"groups": frame.unit}
    )
    return {
        "estimate": float(model.params["treated:post"]),
        "ci95": model.conf_int().loc["treated:post"].tolist(),
        "assumptions": ["Parallel trends", "No anticipation", "Stable composition", "No spillover"],
        "warning": "Two periods cannot test pre-trends; causality is conditional on these assumptions",
    }


def simulation(seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for unit in range(400):
        treated = int(unit >= 200)
        fixed = rng.normal()
        for post in [0, 1]:
            rows.append(
                {
                    "unit": unit,
                    "treated": treated,
                    "post": post,
                    "outcome": fixed + post + 2 * treated * post + rng.normal(scale=0.3),
                }
            )
    return {"synthetic": True, "true_effect": 2, **estimate(pd.DataFrame(rows))}
