import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from experiment import (analyze, covariate_adjustment, generate, holm, plan,
                        proportion_difference, sample_ratio_mismatch, sample_size, validate, mean_difference)


def test_sample_size_properties():
    assert sample_size(mde=.01) > sample_size(mde=.02)
    assert sample_size(power=.9) > sample_size(power=.8)
    with pytest.raises(ValueError):
        sample_size(baseline=.99, mde=.02)


def test_zero_difference_includes_zero():
    a = np.array([0]*90+[1]*10)
    result = proportion_difference(a, a)
    assert result['p_value'] == 1
    assert result['ci95'][0] < 0 < result['ci95'][1]


def test_effect_reverses_with_arms():
    a = np.array([0]*90+[1]*10)
    b = np.array([0]*75+[1]*25)
    first, reverse = proportion_difference(a,b), proportion_difference(b,a)
    assert first['ci95'][0] > 0
    assert first['difference_absolute'] == -reverse['difference_absolute']
    np.testing.assert_allclose(first['ci95'], [-reverse['ci95'][1], -reverse['ci95'][0]])


def test_srm_detects_bad_allocation():
    assert sample_ratio_mismatch(1000,1000)['p_value'] == 1
    assert sample_ratio_mismatch(1000,1800)['p_value'] < .001


def test_duplicate_user_rejected():
    frame = generate(n_per_arm=100)
    frame.loc[1,'user_id'] = frame.loc[0,'user_id']
    with pytest.raises(ValueError,match='repetida'):
        validate(frame)


def test_holm_monotone_and_bounded():
    assert holm({'a': .01,'b': .04,'c': .8}) == {'a': .03,'b': .08,'c': .8}


def test_covariate_adjustment_recovers_known_effect():
    frame = generate(n_per_arm=500)
    frame['revenue'] = 10 + 2*frame.pre_revenue + 3*(frame.arm=='B').astype(int)
    estimate = covariate_adjustment(frame)
    assert abs(estimate['difference']-3) < 1e-9
    assert abs(estimate['theta']-2) < 1e-9


def test_incomplete_experiment_cannot_be_adopted():
    result = analyze(generate(n_per_arm=100), observation_days=3, bootstrap_repetitions=30)
    assert not result['validity']['horizon_complete']
    assert not result['validity']['sample_complete']
    assert result['decision'].startswith('INCONCLUSIVO')


def test_srm_blocks_conclusion_even_with_positive_effect():
    frame = generate(n_per_arm=8000)
    frame = frame.drop(frame[frame.arm=='A'].index[:3000])
    result = analyze(frame,bootstrap_repetitions=30)
    assert not result['validity']['srm_pass']
    assert result['decision'].startswith('INCONCLUSIVO')


def test_welch_matches_scipy_for_unequal_variance_and_sample_size():
    from scipy.stats import ttest_ind
    rng=np.random.default_rng(5)
    a=rng.normal(20,3,400)
    b=rng.normal(23,10,650)
    result=mean_difference(a,b)
    reference=ttest_ind(b,a,equal_var=False)
    assert abs(result['p_value']-reference.pvalue) < 1e-12
    np.testing.assert_allclose(result['ci95'],list(reference.confidence_interval()),rtol=1e-12)
