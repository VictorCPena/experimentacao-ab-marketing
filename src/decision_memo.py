"""Transforma a análise do A/B em um parecer legível, sem inventar números."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pct(value):
    return f"{100*value:.2f}%".replace(".", ",")


def memo(result: dict) -> str:
    primary = result["primary_conversion"]
    guard = result["guardrail_unsubscribed"]
    threshold = result["plan"]["guardrail_max_absolute_increase"]
    validity = result["validity"]
    valid = all(validity.values())
    lines = ["# Parecer de experimento A/B", "",
             "> Laboratório com dados sintéticos. Não representa teste em campanha real.", "",
             f"**Decisão:** {result['decision']}", "",
             "## Resultado principal", "",
             f"- Usuários: A = {result['n_A']:,}; B = {result['n_B']:,}.",
             f"- Conversão A = {pct(primary['rate_A'])}; B = {pct(primary['rate_B'])}.",
             f"- Diferença absoluta = {pct(primary['difference_absolute']).removesuffix('%')} p.p.", 
             f"- Lift relativo = {pct(primary['relative_lift']) if primary['relative_lift'] is not None else 'indefinido'}.",
             f"- IC de 95% da diferença: [{pct(primary['ci95'][0])}; {pct(primary['ci95'][1])}].",
             "", "## Segurança e validade", "",
             f"- Verificações de validade aprovadas: {'sim' if valid else 'não'} ({validity}).",
             f"- Descadastros A = {pct(guard['rate_A'])}; B = {pct(guard['rate_B'])}.",
             f"- Aumento máximo aceito no guardrail: {pct(threshold).removesuffix('%')} p.p.", 
             f"- Limite superior IC95 do aumento em descadastros: {pct(guard['ci95'][1]).removesuffix('%')} p.p.", 
             "", "## Próxima decisão", "",
             "Não promover automaticamente a variante B. Avaliar risco do guardrail e",
             "considerar novo experimento, com tamanho e horizonte planejados previamente.",
             "", "## Limites", "",
             "Inferências restritas a dados sintéticos e às hipóteses de randomização. IC",
             "convencional não cobre inspeções repetidas sem plano sequencial.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=ROOT / "resultados/analise.json")
    parser.add_argument("--output", type=Path, default=ROOT / "resultados/PARECER_DECISAO.md")
    args = parser.parse_args()
    data = json.loads(args.analysis.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(memo(data), encoding="utf-8")
    print(f"Parecer gerado: {args.output}")


if __name__ == "__main__":
    main()
