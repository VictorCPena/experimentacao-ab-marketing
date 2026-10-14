"""Estudo Monte Carlo do plano A/B: poder, erro tipo I, peeking e guardrail.

Sementes fixas permitem auditoria; modelos binomiais independentes SÃO hipóteses,
não dados empíricos nem garantia de poder da análise com métricas correlacionadas.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.stats import norm
from experiment import ROOT, plan


def z_pvalues(k_a,k_b,n):
    a=np.asarray(k_a,dtype=float)/n
    b=np.asarray(k_b,dtype=float)/n
    pool=(np.asarray(k_a,dtype=float)+np.asarray(k_b,dtype=float))/(2*n)
    denom=np.sqrt(np.maximum(pool*(1-pool)*(2/n),1e-20))
    z=(b-a)/denom
    return 2*norm.sf(np.abs(z))


def newcombe_upper(k_a,k_b,n,alpha=.05):
    k_a,k_b=np.asarray(k_a,dtype=float),np.asarray(k_b,dtype=float)
    p_a,p_b=k_a/n,k_b/n
    z=norm.ppf(1-alpha/2)
    def bounds(p):
        center=(p+z*z/(2*n))/(1+z*z/n)
        half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
        return center-half,center+half
    lo_a,_=bounds(p_a)
    _,hi_b=bounds(p_b)
    return p_b-p_a+np.sqrt((hi_b-p_b)**2+(p_a-lo_a)**2)


def _conversion_study(rng,replicates,per_arm,looks,p_a,p_b,alpha,mde):
    counts_a=np.zeros(replicates,dtype=int)
    counts_b=np.zeros(replicates,dtype=int)
    ever=np.zeros(replicates,dtype=bool)
    p_each=[]
    for index, look_n in enumerate(looks):
        diff=int(look_n-(looks[index-1] if index else 0))
        counts_a+=rng.binomial(diff,p_a,replicates)
        counts_b+=rng.binomial(diff,p_b,replicates)
        pv=z_pvalues(counts_a,counts_b,look_n)
        ever|=(pv<alpha)
        p_each.append(pv)
    final=np.asarray(p_each[-1])
    uplift=(counts_b-counts_a)/per_arm
    return {'fixed_horizon_significant_rate':float(np.mean(final<alpha)),
            'naive_peeking_any_look_rate':float(np.mean(ever)),
            'meets_preregistered_primary_rate':float(np.mean((final<alpha)&(uplift>=mde)&(uplift>0)))}


def simulate(replicates=2000,per_arm=8000,looks=(.25,.5,.75,1.0),seed=42,
             conversion_base=.08, conversion_effect=.015,
             guardrail_base=.012, guardrail_effect_safe=.002,
             guardrail_effect_unsafe=.008):
    if not (100<=replicates<=20000 and 100<=per_arm<=100000 and
            0<conversion_base<1 and 0<=conversion_base+conversion_effect<=1 and
            0<guardrail_base<1 and 0<=guardrail_base+guardrail_effect_safe<1 and
            0<=guardrail_base+guardrail_effect_unsafe<1 and
            tuple(sorted(set(looks)))==tuple(looks) and 0<looks[0] and looks[-1]==1):
        raise ValueError('Cenário fora dos limites ou looks inválidos')
    scheduled=tuple(sorted(set(max(1,round(per_arm*share)) for share in looks)))
    if scheduled[-1]!=per_arm or len(scheduled)!=len(looks):
        raise ValueError('Looks devem representar tamanhos amostrais distintos')
    spec=plan()
    rng=np.random.default_rng(seed)
    alpha=spec['alpha'];mde=spec['mde_absolute'];margin=spec['guardrail_max_absolute_increase']
    null=_conversion_study(rng,replicates,per_arm,scheduled,conversion_base,conversion_base,alpha,mde)
    alt=_conversion_study(rng,replicates,per_arm,scheduled,conversion_base,
                          conversion_base+conversion_effect,alpha,mde)
    def guardrail(effect):
        ka=rng.binomial(per_arm,guardrail_base,size=replicates)
        kb=rng.binomial(per_arm,guardrail_base+effect,size=replicates)
        accepted=newcombe_upper(ka,kb,per_arm)<=margin
        return {'true_increase_pp':100*effect,
                'fraction_meeting_guardrail_upper_bound':float(accepted.mean()),
                'margin_pp':100*margin}
    safe=guardrail(guardrail_effect_safe)
    unsafe=guardrail(guardrail_effect_unsafe)
    return {'parameters':{'replicates':replicates,'per_arm':per_arm,'looks_at_n':list(scheduled),
                           'seed':seed,'alpha':alpha,'mde_pp':100*mde},
            'null_conversion':null,'alternative_conversion':alt,
            'safe_guardrail':safe,
            'unsafe_guardrail':unsafe,
            'interpretation':{'type_I_fixed':null['fixed_horizon_significant_rate'],
                              'type_I_naive_peeking':null['naive_peeking_any_look_rate'],
                              'power_nominal_pvalue_only':alt['fixed_horizon_significant_rate'],
                              'power_with_mde_rule':alt['meets_preregistered_primary_rate'],
                              'unsafe_guardrail_false_clearance':unsafe['fraction_meeting_guardrail_upper_bound']},
            'caveats':['Monte Carlo binomial com braços independentes; não simula correlação conversão/descadastro.',
                       'Peeking sem correção é intencionalmente inadequado, apenas exemplo de inflação de erro.',
                       'Fração de segurança não equivale a poder formal de não inferioridade.',
                       'Poder nominal não é automaticamente poder de adotar quando há guardrail e SRM.',
                       'Estimativas têm erro Monte Carlo e são cenários, não observação de campanha.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reps',type=int,default=2000)
    p.add_argument('--per-arm',type=int,default=8000)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--output',type=Path,default=ROOT/'work/evaluation/design_simulation.json')
    args=p.parse_args()
    result=simulate(args.reps,args.per_arm,seed=args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
