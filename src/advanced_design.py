"""Plano experimental avançado: correlação, clusters e testes sequenciais.

OBF/Bonferroni incremental é um gasto de alpha CONSERVADOR (soma dos
incrementos<=alpha), não uma fronteira exata de group-sequential via joint normal.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, t
from experiment import ROOT


def spending_boundaries(fractions=(.25,.5,.75,1.), alpha=.05):
    """Budget crescente estilo O'Brien-Fleming, repartido por Bonferroni.

    Em qualquer dependência entre looks, P(alguma falsa rejeição)<=sum(alpha_increment)=alpha.
    """
    if not 0 < alpha < 1 or not fractions or len(set(fractions))!=len(fractions) or not (0<fractions[0] and fractions[-1]==1 and list(fractions)==sorted(fractions)):
        raise ValueError('Frações crescentes de informação devem terminar em 1')
    z=norm.isf(alpha/2)
    cumulative=[float(2*norm.sf(z/np.sqrt(frac))) for frac in fractions]
    spent=[cumulative[0]]+[cumulative[i]-cumulative[i-1] for i in range(1,len(cumulative))]
    return [{'fraction':float(f), 'cumulative_alpha_budget':float(c),
             'incremental_alpha_threshold':float(max(0,p))}
            for f,c,p in zip(fractions,cumulative,spent)]


def sequential_study(reps=2000, per_arm=3000, fractions=(.25,.5,.75,1.), effect=0, seed=51):
    if not 100<=reps<=20000 or not 200<=per_arm<=100000 or not -.05<=effect<=.05:
        raise ValueError('Simulação fora dos limites')
    schedule=spending_boundaries(fractions)
    looks=[int(round(per_arm*b['fraction'])) for b in schedule]
    if len(set(looks))!=len(looks):
        raise ValueError('Looks repetidos no n escolhido')
    rng=np.random.default_rng(seed)
    ca=np.zeros(reps,dtype=int);cb=np.zeros(reps,dtype=int)
    naive=np.zeros(reps,dtype=bool);safe=np.zeros(reps,dtype=bool)
    fixed=None
    a=0
    for look, boundary in zip(looks,schedule):
        increment=look-a
        ca+=rng.binomial(increment,.08,reps)
        cb+=rng.binomial(increment,.08+effect,reps)
        a=look
        prob=(ca+cb)/(2*look)
        se=np.sqrt(np.maximum(2*prob*(1-prob)/look,1e-20))
        p=2*norm.sf(np.abs((cb-ca)/look/se))
        naive|=p<.05
        safe|=p<boundary['incremental_alpha_threshold']
        fixed=p<.05
    return {'parameters':{'reps':reps,'n_per_arm':per_arm,'conversion_effect':effect,'seed':seed},
            'looks':schedule,
            'fixed_final_reject_rate':float(np.mean(fixed)),
            'naive_any_look_reject_rate':float(np.mean(naive)),
            'alpha_spending_bonferroni_any_reject_rate':float(np.mean(safe)),
            'note': 'Bonferroni usando alpha incremental: controla erro familiar por união, é mais conservador que OBF exato. Sob efeito, taxas são poder empírico; sob nulo, falso positivo.'}


def generate_clustered(clusters_per_arm=40, size=20, icc=.12, outcome_rho=.4,
                       effect_conv=.015, effect_unsub=.008, seed=42):
    """Randomização por cluster com efeitos compartilhados e dependência entre métricas.

    Mistura normal latente: ICC se refere à latente, NÃO ao ICC Bernoulli observado.
    """
    if not (10<=clusters_per_arm<=300 and 5<=size<=200 and 0<=icc<1
            and -1<outcome_rho<1 and -.08<=effect_conv<=.08 and -.012<=effect_unsub<=.05):
        raise ValueError('Parâmetros fora dos limites')
    rng=np.random.default_rng(seed)
    n_clusters=2*clusters_per_arm
    arms=np.array(['A']*clusters_per_arm+['B']*clusters_per_arm)
    rng.shuffle(arms)
    total=n_clusters*size
    shared=rng.normal(size=(n_clusters,2))
    local=rng.normal(size=(n_clusters,size,2))
    raw=np.sqrt(icc)*shared[:,None,:]+np.sqrt(1-icc)*local
    z_conv=raw[:,:,0]
    z_unsub=outcome_rho*raw[:,:,0]+np.sqrt(1-outcome_rho**2)*raw[:,:,1]
    conv_prop=.08+(arms=='B')*effect_conv
    unsub_prop=.012+(arms=='B')*effect_unsub
    if np.min(conv_prop)<0 or np.max(conv_prop)>=1 or np.min(unsub_prop)<0 or np.max(unsub_prop)>=1:
        raise ValueError('Probabilidade inválida para Bernoulli')
    convert=(norm.cdf(z_conv)<conv_prop[:,None]).astype(int)
    unsub=(norm.cdf(z_unsub)<unsub_prop[:,None]).astype(int)
    return pd.DataFrame({'cluster_id': np.repeat([f'C{i:04d}' for i in range(n_clusters)],size),
        'arm':np.repeat(arms,size), 'converted':convert.ravel(), 'unsubscribed':unsub.ravel()})


def cluster_diff(frame: pd.DataFrame, metric: str):
    """Diferença não ponderada de médias por cluster, Welch robusto a tamanhos (médias).

    Exige tamanhos iguais para estimando individual coincidir com o estimando cluster.
    """
    if not {'cluster_id','arm',metric}.issubset(frame) or frame.cluster_id.isna().any():
        raise ValueError('Schema de clusters inválido')
    groups=frame.groupby('cluster_id')
    if groups.arm.nunique().max()!=1 or groups.size().nunique()!=1:
        raise ValueError('Cada cluster pertence a um braço e possui o mesmo tamanho')
    if not frame[metric].isin([0,1]).all():
        raise ValueError('Resultado deve ser Bernoulli')
    by=groups.agg(arm=('arm','first'),mean=(metric,'mean'))
    a=by.loc[by.arm=='A','mean'].to_numpy()
    b=by.loc[by.arm=='B','mean'].to_numpy()
    if min(len(a),len(b))<3:
        raise ValueError('São necessários ao menos 3 clusters por braço')
    delta=float(b.mean()-a.mean())
    va=float(a.var(ddof=1)/len(a));vb=float(b.var(ddof=1)/len(b))
    se=np.sqrt(va+vb)
    dof=(va+vb)**2/(va*va/(len(a)-1)+vb*vb/(len(b)-1)) if se else len(a)+len(b)-2
    z=delta/se if se else (0 if delta==0 else np.inf)
    half=float(t.ppf(.975,dof)*se)
    return {'n_clusters_A':len(a),'n_clusters_B':len(b),'cluster_size':int(groups.size().iloc[0]),
            'difference':delta,'se_cluster':float(se), 'df_welch':float(dof),
            'ci95':[float(delta-half), float(delta+half)],
            'p_value':float(2*t.sf(abs(z),dof)),
            'method':'médias por cluster e Welch; equal cluster sizes; ITT cluster'}


def cluster_study(reps=300, clusters_per_arm=25, cluster_size=25, icc=.12,
                  outcome_rho=.4, seed=42):
    if not 100<=reps<=2000:
        raise ValueError('100..2000 réplicas')
    rng=np.random.default_rng(seed)
    null_cluster=null_naive=0
    unsafe_clear=0
    corr=[]
    for _ in range(reps):
        sample_seed=int(rng.integers(0,2**31-1))
        data=generate_clustered(clusters_per_arm,cluster_size,icc,outcome_rho,
                     effect_conv=0,effect_unsub=0,seed=sample_seed)
        stat=cluster_diff(data,'converted')
        null_cluster+=stat['p_value']<.05
        a=data.loc[data.arm=='A','converted']
        b=data.loc[data.arm=='B','converted']
        pool=(a.sum()+b.sum())/(len(a)+len(b))
        se=np.sqrt(2*pool*(1-pool)/len(a))
        naive=float(2*norm.sf(abs((b.mean()-a.mean())/se))) if se else 1.
        null_naive+=naive<.05
        empirical_corr=float(data[['converted','unsubscribed']].corr().iloc[0,1])
        if np.isfinite(empirical_corr):
            corr.append(empirical_corr)
        unsafe=generate_clustered(clusters_per_arm,cluster_size,icc,outcome_rho,
                    effect_conv=.015,effect_unsub=.008,seed=sample_seed)
        guard=cluster_diff(unsafe,'unsubscribed')
        unsafe_clear+=guard['ci95'][1]<=.005
    return {'reps':reps,'cluster_design':{'clusters_per_arm':clusters_per_arm,'cluster_size':cluster_size,
                 'latent_icc':icc,'outcome_latent_rho':outcome_rho},
            'null_false_positive':{'cluster_welch':null_cluster/reps,'naive_ignoring_clusters':null_naive/reps},
            'unsafe_guardrail_false_clearance':unsafe_clear/reps,
            'observed_conversion_unsubscribe_correlation_mean':float(np.mean(corr)) if corr else None,
            'correlation_estimable_replicates':len(corr),
            'caveats':['Correlação de métricas pode ser baixa com eventos raros apesar da correlação latente.',
                       'Modelo de clusters igualmente grandes; sem interferência entre clusters.',
                       'Correlação de conversão e descadastro não implica causalidade.',
                       'Resultados Monte Carlo variam com seed e não são estimativas de campanha real.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reps',type=int,default=300)
    p.add_argument('--clusters',type=int,default=25)
    p.add_argument('--size',type=int,default=25)
    p.add_argument('--output',type=Path,default=ROOT/'work/evaluation/advanced_design.json')
    a=p.parse_args()
    result={'sequential_null':sequential_study(reps=max(100,a.reps)),
            'cluster_correlated_metrics':cluster_study(a.reps,a.clusters,a.size)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
