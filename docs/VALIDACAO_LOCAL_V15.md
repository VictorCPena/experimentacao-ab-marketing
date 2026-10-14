# Evidência Monte Carlo reproduzível — v1.5

## Ensaio executado

Comando: `python src/design_simulation.py --reps 2000 --per-arm 8000 --seed 42`

O experimento é **inteiramente sintético**, com braços independentes, probabilidades binomiais hipotéticas e quatro olhadas: 2.000, 4.000, 6.000 e 8.000 pessoas por braço.

| Propriedade simulada | Resultado amostral |
| --- | ---: |
| Falso positivo sob ausência de efeito, teste fixo final | **4,60%** |
| Falso positivo olhando quatro vezes sem correção (*peeking*) | **11,35%** |
| Poder nominal de `p<0.05` com ganho real de +1,5 p.p. | **92,65%** |
| Fração de réplicas também atingindo ganho **observado** >= MDE | **50,65%** |
| Guardrail de +0,2 p.p. realmente seguro: fração que comprova segurança | **41,0%** |
| Guardrail de +0,8 p.p. realmente inseguro: falsa liberação | **0,0% entre 2.000 réplicas** |

**Atenção:** zero falsa liberação observada em 2.000 repetições **não significa probabilidade verdadeira zero**. Resultados dependem do gerador e não devem ser transportados para uma campanha real. Poder para `p<0.05` não é poder da regra completa de adoção, sobretudo porque ela também requer ganho observado >= MDE, margem de guardrail, amostra, SRM e horizonte.

## Questões demonstradas

1. Um p-valor em cada uma de quatro olhadas não preserva a taxa de falso positivo de 5% no conjunto de consultas.
2. Acrescentar um critério de ganho prático pode reduzir substancialmente a taxa de adoção, mesmo quando existe um efeito verdadeiro do tamanho do MDE.
3. Um guardrail pode ser seguro de verdade, mas difícil de **demonstrar** com confiança para um evento raro e uma margem estreita.

Isso embasa o parecer **REVISAR** do experimento original, sem ajustar o plano depois de ver os resultados.
