"""Inferência para um A/B randomizado por usuário, horizonte fixo e plano prévio."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm, t

ROOT = Path(__file__).resolve().parents[1]


def sample_size(baseline=.08, mde=.015, alpha=.05, power=.8):
    if not 0 < baseline < baseline+mde < 1 or not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError("Parâmetros de planejamento inválidos")
    p1, p2 = baseline, baseline+mde
    average = (p1+p2)/2
    numerator = norm.ppf(1-alpha/2)*math.sqrt(2*average*(1-average))
    numerator += norm.ppf(power)*math.sqrt(p1*(1-p1)+p2*(1-p2))
    return int(math.ceil(numerator**2/mde**2))


def plan():
    return {"unit": "user_id", "allocation_B": .5, "alpha": .05, "power": .8,
            "baseline_conversion": .08, "mde_absolute": .015,
            "required_per_arm": sample_size(), "primary": "converted",
            "secondary": ["revenue_per_user", "unsubscribed"],
            "minimum_observation_days": 28, "srm_alpha": .001,
            "analysis": "Intenção de tratar; uma linha por usuário randomizado; teste bilateral.",
            "stopping": "Horizonte fixo. Não interromper ao observar p<0.05.",
            "multiple_testing": "Uma métrica primária; Holm nas duas métricas secundárias.",
            "guardrail_max_absolute_increase": .005,
            "decision": "SRM deve passar; completar horizonte/amostra; IC primário excluir zero; estimativa atingir MDE; guardrail atender limite."}


def validate(frame):
    required = {"user_id", "arm", "converted", "revenue", "pre_revenue", "unsubscribed"}
    if not required.issubset(frame.columns) or frame[list(required)].isna().any().any():
        raise ValueError("Schema inválido ou valores ausentes")
    if frame.user_id.duplicated().any():
        raise ValueError("Unidade experimental repetida; agregar por usuário antes da análise")
    if set(frame.arm.unique()) != {"A", "B"}:
        raise ValueError("Necessário exatamente dois braços A/B")
    if min(frame.groupby('arm').size()) < 30:
        raise ValueError("Poucas unidades por braço para este protocolo")
    for column in ("converted", "unsubscribed"):
        if not frame[column].isin([0, 1]).all():
            raise ValueError(f"{column} deve ser 0/1")
    for column in ("revenue", "pre_revenue"):
        if not np.isfinite(frame[column]).all() or (frame[column] < 0).any():
            raise ValueError("Receita deve ser finita e não negativa")


def wilson(successes, n, alpha=.05):
    z = norm.ppf(1-alpha/2)
    p = successes/n
    center = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return center-half, center+half


def proportion_difference(a, b, alpha=.05):
    a, b = np.asarray(a), np.asarray(b)
    p_a, p_b = float(a.mean()), float(b.mean())
    difference = p_b-p_a
    pooled = float((a.sum()+b.sum())/(len(a)+len(b)))
    se = math.sqrt(pooled*(1-pooled)*(1/len(a)+1/len(b)))
    z = difference/se if se else 0.
    lo_a, hi_a = wilson(a.sum(), len(a), alpha)
    lo_b, hi_b = wilson(b.sum(), len(b), alpha)
    # Newcombe: combina intervalos Wilson dos dois braços.
    low = difference-math.sqrt((p_b-lo_b)**2+(hi_a-p_a)**2)
    high = difference+math.sqrt((hi_b-p_b)**2+(p_a-lo_a)**2)
    return {"rate_A": p_a, "rate_B": p_b, "difference_absolute": difference,
            "relative_lift": difference/p_a if p_a else None,
            "ci95": [low, high], "p_value": float(2*norm.sf(abs(z))), "method": "z pooled; IC Newcombe/Wilson"}


def sample_ratio_mismatch(a_count, b_count, allocation_B=.5):
    total = a_count+b_count
    if total <= 0 or not 0 < allocation_B < 1:
        raise ValueError("Contagem/alocação inválida")
    expected = np.array([total*(1-allocation_B), total*allocation_B])
    observed = np.array([a_count, b_count])
    statistic = float(((observed-expected)**2/expected).sum())
    return {"chi2": statistic, "p_value": float(chi2.sf(statistic, 1)), "expected": expected.tolist()}


def mean_difference(a, b, alpha=.05):
    a, b = np.asarray(a), np.asarray(b)
    va, vb = a.var(ddof=1)/len(a), b.var(ddof=1)/len(b)
    se = math.sqrt(va+vb)
    df = (va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1)) if se else len(a)+len(b)-2
    difference = float(b.mean()-a.mean())
    half = float(t.ppf(1-alpha/2, df)*se)
    return {"mean_A": float(a.mean()), "mean_B": float(b.mean()), "difference": difference,
            "standard_error": se, "ci95": [difference-half, difference+half],
            "p_value": float(2*t.sf(abs(difference/se), df)) if se else 1., "method": "Welch"}


def bootstrap_mean_difference(a, b, repetitions=1000, seed=42):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a), np.asarray(b)
    diffs = np.empty(repetitions)
    for i in range(repetitions):
        diffs[i] = rng.choice(b, len(b), replace=True).mean()-rng.choice(a, len(a), replace=True).mean()
    return {"ci95": np.quantile(diffs, [.025, .975]).tolist(), "repetitions": repetitions,
            "seed": seed, "method": "Bootstrap percentil separado por braço; unidades independentes"}


def covariate_adjustment(frame):
    treatment = (frame.arm == "B").astype(float).to_numpy()
    covariate = frame.pre_revenue.to_numpy()-frame.pre_revenue.mean()
    y = frame.revenue.to_numpy()
    X = np.column_stack([np.ones(len(frame)), treatment, covariate])
    if np.linalg.matrix_rank(X) < X.shape[1]:
        return {"available": False, "reason": "Covariável sem variação ou matriz singular"}
    inv = np.linalg.inv(X.T @ X)
    beta = inv @ X.T @ y
    residual = y-X @ beta
    leverage = np.einsum('ij,jk,ik->i', X, inv, X)
    weighted = X*(residual/np.maximum(1-leverage, 1e-9))[:, None]
    covariance = inv @ (weighted.T @ weighted) @ inv
    se = math.sqrt(max(covariance[1, 1], 0))
    half = float(t.ppf(.975, len(frame)-X.shape[1])*se)
    return {"available": True, "difference": float(beta[1]), "theta": float(beta[2]),
            "standard_error": se, "ci95": [float(beta[1]-half), float(beta[1]+half)],
            "method": "ANCOVA com receita préteste centrada e erro padrão robusto HC3; princípio CUPED",
            "assumption": "pre_revenue foi medida antes da randomização; nenhuma covariável pós-tratamento."}


def holm(p_values):
    items = sorted(p_values.items(), key=lambda item: item[1])
    adjusted, running = {}, 0.
    for index, (name, p) in enumerate(items):
        running = max(running, min(1., p*(len(items)-index)))
        adjusted[name] = running
    return adjusted


def analyze(frame, observation_days=28, bootstrap_repetitions=1000):
    validate(frame)
    specification = plan()
    a, b = frame[frame.arm == "A"], frame[frame.arm == "B"]
    srm = sample_ratio_mismatch(len(a), len(b), specification["allocation_B"])
    primary = proportion_difference(a.converted, b.converted)
    revenue = mean_difference(a.revenue, b.revenue)
    guardrail = proportion_difference(a.unsubscribed, b.unsubscribed)
    adjusted = holm({"revenue": revenue["p_value"], "unsubscribed": guardrail["p_value"]})
    covariate = covariate_adjustment(frame)
    if covariate["available"]:
        covariate["estimated_variance_reduction_pct"] = float(100*(1-covariate["standard_error"]**2/revenue["standard_error"]**2)) if revenue['standard_error'] else None
    validity = {"srm_pass": srm["p_value"] >= specification["srm_alpha"],
                "sample_complete": min(len(a), len(b)) >= specification["required_per_arm"],
                "horizon_complete": observation_days >= specification["minimum_observation_days"]}
    if not all(validity.values()):
        decision = "INCONCLUSIVO: corrigir validade/completar plano antes de decidir"
    elif primary["ci95"][0] > 0 and primary["difference_absolute"] >= specification["mde_absolute"]:
        if guardrail["ci95"][1] <= specification["guardrail_max_absolute_increase"]:
            decision = "CANDIDATO A ADOÇÃO: benefício primário e guardrail atendem ao plano; avaliar custo de implementação"
        else:
            decision = "REVISAR: benefício primário, mas segurança do guardrail ainda não demonstrada"
    else:
        decision = "NÃO ADOTAR COM BASE NESTE TESTE: critério de benefício prático/estatístico não atendido"
    return {"plan": specification, "n_A": len(a), "n_B": len(b),
            "observation_days": observation_days, "validity": validity, "srm": srm,
            "primary_conversion": primary, "secondary_revenue": revenue,
            "revenue_bootstrap": bootstrap_mean_difference(a.revenue, b.revenue, bootstrap_repetitions),
            "guardrail_unsubscribed": guardrail, "secondary_holm_adjusted_p": adjusted,
            "pretest_covariate_adjustment": covariate, "decision": decision,
            "causal_scope": "Efeito da atribuição B neste experimento randomizado sintético; não prova efeito em clientes reais.",
            "limits": ["Sem inferência causal em bases observacionais só por aplicar este script.",
                       "Não corrigir SRM removendo usuários depois de ver resultados.",
                       "IC convencional não autoriza testes repetidos diários."]}


def generate(n_per_arm=8000, seed=42):
    rng = np.random.default_rng(seed)
    n = n_per_arm*2
    pre = rng.gamma(3, 25, n)
    arm = np.array(['A']*n_per_arm+['B']*n_per_arm)
    rng.shuffle(arm)
    treatment = (arm == 'B').astype(int)
    conversion_probability = np.clip(.08 + .018*treatment + .0001*(pre-pre.mean()), .02, .30)
    converted = rng.binomial(1, conversion_probability)
    # Receita total por usuário inclui consumo préexistente + conversão adicional.
    revenue = np.maximum(0, .65*pre + rng.normal(0, 9, n) + converted*rng.gamma(4, 15, n))
    unsubscribed = rng.binomial(1, .012+.0005*treatment)
    return pd.DataFrame({"user_id": [f"U{i:06}" for i in range(n)], "arm": arm,
                         "converted": converted, "revenue": revenue.round(2), "pre_revenue": pre.round(2),
                         "unsubscribed": unsubscribed})


def peeking_simulation(repetitions=1000, looks=10, per_look=100, seed=43):
    """Monte Carlo sob H0: mostra inflação de falso positivo ao testar repetidamente."""
    rng = np.random.default_rng(seed)
    any_rejection = final_rejection = 0
    for _ in range(repetitions):
        a = b = 0
        rejected = False
        for look in range(1, looks+1):
            a += rng.binomial(per_look, .08)
            b += rng.binomial(per_look, .08)
            n = look*per_look
            p = (a+b)/(2*n)
            se = math.sqrt(p*(1-p)*2/n)
            pvalue = 2*norm.sf(abs((b-a)/n/se)) if se else 1
            rejected = rejected or pvalue < .05
        any_rejection += rejected
        final_rejection += pvalue < .05
    def result(successes):
        return {"rate": successes/repetitions, "monte_carlo_ci95": list(wilson(successes, repetitions))}
    return {"repetitions": repetitions, "looks": looks, "users_per_arm_per_look": per_look,
            "fixed_final_analysis": result(final_rejection), "stop_if_p_below_005": result(any_rejection),
            "note": "Simulação sob efeito nulo; não é método de teste sequencial válido."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--observation-days', type=int)
    args = parser.parse_args()
    if args.input and args.observation_days is None:
        parser.error('Com dados externos, informe --observation-days conforme o horizonte realmente observado.')
    observation_days = args.observation_days if args.observation_days is not None else 28
    if observation_days < 0:
        parser.error('--observation-days deve ser não negativo')
    output = ROOT / "work/evaluation"
    output.mkdir(parents=True, exist_ok=True)
    # Plano salvo antes de gerar e analisar os resultados sintéticos.
    (output / "plano_previo.json").write_text(json.dumps(plan(), indent=2, ensure_ascii=False))
    frame = pd.read_csv(args.input) if args.input else generate()
    if not args.input:
        frame.to_csv(ROOT / "data/experimento_sintetico.csv", index=False)
    results = analyze(frame, observation_days)
    results['synthetic_data'] = True if not args.input else 'external_unverified'
    (output / "analise.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    frame.groupby('arm').agg(users=('user_id','size'), conversion=('converted','mean'),
        revenue_per_user=('revenue','mean'), unsubscribed=('unsubscribed','mean')).to_csv(output / 'resumo_bracos.csv')
    (output / "simulacao_peeking.json").write_text(json.dumps(peeking_simulation(), indent=2, ensure_ascii=False))
    print(json.dumps({"n_per_arm": min(results['n_A'], results['n_B']),
                      "primary": results['primary_conversion'], "decision": results['decision']}, indent=2))


if __name__ == "__main__":
    main()
