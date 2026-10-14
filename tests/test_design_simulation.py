import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from design_simulation import simulate, z_pvalues, newcombe_upper


def test_proportions_identical_have_pvalue_one():
    assert float(z_pvalues([10],[10],100)[0]) == 1
    assert float(newcombe_upper([0],[0],100)[0]) > 0


def test_simulation_reproducible_and_peeking_at_least_fixed():
    x=simulate(replicates=300,per_arm=300,seed=17)
    assert x==simulate(replicates=300,per_arm=300,seed=17)
    assert x['null_conversion']['naive_peeking_any_look_rate'] >= x['null_conversion']['fixed_horizon_significant_rate']
    assert x['unsafe_guardrail']['fraction_meeting_guardrail_upper_bound'] <= x['safe_guardrail']['fraction_meeting_guardrail_upper_bound'] + .1


def test_invalid_monte_carlo_rejected():
    with pytest.raises(ValueError):simulate(replicates=99)
    with pytest.raises(ValueError):simulate(looks=(.5,.25,1.))
    with pytest.raises(ValueError):simulate(looks=(.5,.5,1.))
    with pytest.raises(ValueError):simulate(conversion_base=1.0)
