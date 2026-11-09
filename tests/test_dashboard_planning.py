"""Exercise the visible controls and the statistical planning contract."""

from pathlib import Path

import pytest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
from streamlit.testing.v1 import AppTest

from causal_lab.planning import required_per_arm

ROOT = Path(__file__).resolve().parents[1]


def test_sample_size_reaches_power_and_uses_ceiling():
    n = required_per_arm(0.05, 0.005)
    effect = proportion_effectsize(0.055, 0.05)
    calc = NormalIndPower()
    assert calc.power(effect, nobs1=n, alpha=0.05) >= 0.8
    assert calc.power(effect, nobs1=n - 1, alpha=0.05) < 0.8
    assert required_per_arm(0.05, 0.01) < n


@pytest.mark.parametrize("baseline,mde", [(0, 0.01), (0.99, 0.02), (0.1, -0.01), (float("nan"), 0.01)])
def test_invalid_planning_inputs(baseline, mde):
    with pytest.raises(ValueError):
        required_per_arm(baseline, mde)


def test_dashboard_precision_and_fixed_outcome(monkeypatch):
    monkeypatch.chdir(ROOT)
    app = AppTest.from_file(str(ROOT / "causal_lab/dashboard.py")).run()
    assert not app.exception
    slider = app.slider[1]
    assert slider.value == 0.005
    assert slider.proto.step == 0.001 and slider.proto.format == "%.3f"
    assert "0.500 percentage points" in " ".join(x.value for x in app.caption)
    app.selectbox[0].select("conversion").run()
    assert not app.exception
    assert "conversion" in app.caption[1].value
    assert app.subheader[0].value == "Cross-fitted estimates — visit"
    app.slider[1].set_value(0.007).run()
    assert not app.exception
    assert "0.700 percentage points" in " ".join(x.value for x in app.caption)
    assert str(required_per_arm(0.05, 0.007)) in " ".join(x.value for x in app.markdown)
