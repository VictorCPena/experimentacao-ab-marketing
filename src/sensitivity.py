"""Sensibilidade do guardrail: impactos por população e amostra ilustrativa.

Esta análise NÃO altera o critério de decisão pré-especificado do experimento.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]


def required_per_arm_guardrail(base_rate: float, assumed_difference: float, margin: float,
                               alpha: float = .05, power: float = .8) -> int:
    """Aproximação normal para teste unilateral de não-inferioridade em duas proporções."""
    treatment_rate = base_rate + assumed_difference
    if not (0 < base_rate < 1 and 0 < treatment_rate < 1 and
            assumed_difference < margin and 0 < alpha < 1 and 0 < power < 1):
        raise ValueError("Cenário fora do domínio ou efeito igual/superior à margem")
    variance = base_rate*(1-base_rate) + treatment_rate*(1-treatment_rate)
    z = norm.ppf(1-alpha) + norm.ppf(power)
    return math.ceil(z*z*variance/(margin-assumed_difference)**2)


def sensitivity(analysis: dict, population: int = 10_000,
                assumptions: tuple[float, ...] = (0., .002, .004)) -> dict:
    if population <= 0:
        raise ValueError("População deve ser positiva")
    primary = analysis["primary_conversion"]
    guard = analysis["guardrail_unsubscribed"]
    margin = float(analysis["plan"]["guardrail_max_absolute_increase"])
    effect = float(primary["difference_absolute"])
    guard_effect = float(guard["difference_absolute"])
    scenarios = []
    for delta in assumptions:
        # Aproximação Wald não é adequada quando a proporção observada é zero.
        can_approximate = 0 < guard["rate_A"] < 1 and 0 < guard["rate_A"] + delta < 1
        scenarios.append({"assumed_increase_pp": 100*delta,
                          "illustrative_required_per_arm":
                          required_per_arm_guardrail(guard["rate_A"], delta, margin)
                          if can_approximate else None,
                          "distance_to_margin_pp": 100*(margin-delta),
                          "availability_note": None if can_approximate else
                          "Aproximação normal indisponível para taxa-base ou taxa projetada na fronteira."})
    return {"population": population,
            "incremental_conversions_at_observed_effect": population * effect,
            "additional_unsubscribes_at_observed_effect": population * guard_effect,
            "incremental_conversion_interval95": [population*float(v) for v in primary["ci95"]],
            "additional_unsubscribes_interval95": [population*float(v) for v in guard["ci95"]],
            "guardrail_limit_pp": 100*margin,
            "guardrail_upper_bound_pp": 100*float(guard["ci95"][1]),
            "guardrail_passes": float(guard["ci95"][1]) <= margin,
            "sample_size_scenarios": scenarios,
            "decision_unchanged": analysis["decision"],
            "assumptions": ["Projeções lineares por 10 mil usuários mantêm as taxas observadas; não são forecasts reais.",
                            "Tamanho de amostra é aproximação unilateral normal, com braços independentes, taxa-base fixa, alfa 5% e poder 80%.",
                            "Aproximação não substitui simulação calibrada nem preregistro; rareza do evento e testes múltiplos podem alterá-la.",
                            "Não usar análise pós-hoc para alterar a margem de proteção ou afirmar causalidade externa."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=ROOT/"work/evaluation/analise.json")
    parser.add_argument("--output", type=Path, default=ROOT/"work/evaluation/sensibilidade.json")
    args = parser.parse_args()
    result = sensitivity(json.loads(args.analysis.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
