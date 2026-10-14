import sys
from pathlib import Path

import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from advanced_design import spending_boundaries,sequential_study,generate_clustered,cluster_diff,cluster_study


def test_alpha_spending_incremental_guaranteed_budget():
    r=spending_boundaries()
    assert abs(sum(x['incremental_alpha_threshold'] for x in r)-.05)<1e-12
    assert r[0]['incremental_alpha_threshold'] < r[-1]['incremental_alpha_threshold']
    with pytest.raises(ValueError):spending_boundaries((.5,.5,1.))


def test_sequential_reproducibility_and_naive_vs_spending():
    a=sequential_study(reps=200,per_arm=500,seed=13)
    assert a==sequential_study(reps=200,per_arm=500,seed=13)
    assert 0<=a['alpha_spending_bonferroni_any_reject_rate']<=1
    assert a['alpha_spending_bonferroni_any_reject_rate']<=a['naive_any_look_reject_rate']


def test_correlated_clustered_data_and_cluster_analysis():
    frame=generate_clustered(clusters_per_arm=25,size=30,seed=7)
    assert frame.cluster_id.nunique()==50
    assert frame.groupby('cluster_id').arm.nunique().max()==1
    res=cluster_diff(frame,'converted')
    assert res['n_clusters_A']==25 and res['n_clusters_B']==25
    assert np.isfinite(res['p_value'])
    with pytest.raises(ValueError):cluster_diff(frame.drop(columns=['cluster_id']),'converted')


def test_cluster_study_is_deterministic_and_reports_risks():
    a=cluster_study(reps=100,clusters_per_arm=12,cluster_size=10,seed=7)
    b=cluster_study(reps=100,clusters_per_arm=12,cluster_size=10,seed=7)
    assert a==b
    assert 0<=a['null_false_positive']['cluster_welch']<=1
    assert 0<=a['unsafe_guardrail_false_clearance']<=1


def test_mixed_arms_inside_cluster_rejected():
    frame=generate_clustered(clusters_per_arm=10,size=10)
    frame.loc[1,'arm']='B' if frame.loc[0,'arm']=='A' else 'A'
    with pytest.raises(ValueError):cluster_diff(frame,'converted')
