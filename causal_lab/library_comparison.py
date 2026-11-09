"""Optional real-library comparisons, kept outside the lightweight dependency profile."""

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def compare(path):
    from dowhy import CausalModel
    from econml.dr import DRLearner
    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    f = pd.read_parquet(path).sample(n=20000, random_state=7)
    covariates = [f"f{i}" for i in range(12)]
    X = f[covariates].to_numpy()
    t = f.treatment.to_numpy()
    y = f.visit.to_numpy()
    with threadpool_limits(limits=2):
        causal = CausalModel(data=f, treatment="treatment", outcome="visit", common_causes=covariates)
        identified = causal.identify_effect(proceed_when_unidentifiable=False)
        effect = causal.estimate_effect(identified, method_name="backdoor.linear_regression")
        # DRLearner uses cross-fitting; CATE evaluated on held-out covariates only.
        n = 14000
        dr = DRLearner(
            model_propensity=make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)),
            model_regression=HistGradientBoostingRegressor(max_iter=60, max_leaf_nodes=10),
            model_final=RandomForestRegressor(
                n_estimators=50, min_samples_leaf=100, n_jobs=2, random_state=7
            ),
            cv=3,
            random_state=7,
        )
        dr.fit(y[:n], t[:n], X=X[:n])
        cate = dr.effect(X[n:])
    return {
        "sample_rows": len(f),
        "seed": 7,
        "outcome": "visit",
        "dowhy_adjusted_linear_ate": float(effect.value),
        "econml_drlearner_heldout_mean_cate": float(np.mean(cate)),
        "cate_quantiles": np.quantile(cate, [0.1, 0.5, 0.9]).tolist(),
        "limits": "Different model classes and 20k subsample; no interval coverage claim for EconML forest final stage. DoWhy graph encodes assumed sufficient adjustment; library does not prove absence of confounding.",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=Path("data/criteo_sample.parquet"))
    a = p.parse_args()
    r = compare(a.input)
    Path("evidence/library_comparison.json").write_text(json.dumps(r, indent=2))
    print(json.dumps(r, indent=2))
