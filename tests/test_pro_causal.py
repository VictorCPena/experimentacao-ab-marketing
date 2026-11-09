import numpy as np
import pandas as pd
import pytest
from causal_lab.estimators import aipw, validate, uplift_metrics
from causal_lab.did import simulation, estimate
from src.experiment import holm


def test_aipw_recovers_randomized_ground_truth():
    rng = np.random.default_rng(17)
    X = rng.normal(size=(12000, 3))
    t = rng.binomial(1, 0.6, len(X))
    p = 0.15 + 0.08 * t + 0.03 * (X[:, 0] > 0)
    y = rng.binomial(1, p)
    result, e, _ = aipw(X, t, y)
    assert abs(result["estimate"] - 0.08) < 0.025
    assert result["ci95"][0] < 0.08 < result["ci95"][1]
    assert result["clipped_fraction"] == 0 and np.all((e > 0) & (e < 1))


def test_did_known_effect_and_bad_panel():
    r = simulation()
    assert r["synthetic"] and abs(r["estimate"] - 2) < 0.15
    with pytest.raises(ValueError):
        estimate(pd.DataFrame({"unit": [1, 1], "treated": [0, 0], "post": [0, 0], "outcome": [1, 2]}))


def test_holm_controls_family_order():
    corrected = holm({"a": 0.01, "b": 0.03, "c": 0.9})
    assert corrected["a"] == 0.03 and corrected["b"] == 0.06 and corrected["c"] == 0.9


def test_uplift_order_is_not_predictive_auc():
    rng = np.random.default_rng(3)
    x = rng.uniform(size=30000)
    t = rng.binomial(1, 0.5, len(x))
    y = rng.binomial(1, 0.05 + 0.3 * t * (x > 0.5))
    good = uplift_metrics(t, y, x, np.full(len(x), 0.5))
    bad = uplift_metrics(t, y, -x, np.full(len(x), 0.5))
    assert good["auuc_above_random"] > bad["auuc_above_random"]


def test_duplicate_units_invalid():
    f = pd.DataFrame({f"f{i}": [1.0, 2.0] for i in range(12)})
    f["treatment"] = [0, 1]
    f["visit"] = 0
    f["conversion"] = 0
    f["unit_id"] = [1, 1]
    with pytest.raises(ValueError, match="Duplicate"):
        validate(f)
