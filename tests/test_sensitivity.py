import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from experiment import analyze, generate
from sensitivity import required_per_arm_guardrail, sensitivity


def test_sample_size_increases_near_guardrail_limit():
    small = required_per_arm_guardrail(.01, 0., .005)
    big = required_per_arm_guardrail(.01, .004, .005)
    assert 0 < small < big


def test_sensitivity_preserves_decision_and_scales_effect():
    result = analyze(generate(n_per_arm=100), bootstrap_repetitions=20)
    out = sensitivity(result, population=10000)
    assert out["decision_unchanged"] == result["decision"]
    assert out["incremental_conversions_at_observed_effect"] == pytest.approx(10000*result["primary_conversion"]["difference_absolute"])
    assert len(out["sample_size_scenarios"]) == 3


def test_guardrail_size_rejects_infeasible_margin():
    with pytest.raises(ValueError):
        required_per_arm_guardrail(.01, .005, .005)
    with pytest.raises(ValueError):
        sensitivity({"plan": {}}, population=0)
