# Estudo de desenho experimental por Monte Carlo

## Por que simular

O exemplo principal gera um resultado (ainda que sintético). A simulação aqui, diferentemente, **repete muitos experimentos sob hipóteses verdadeiras conhecidas** para avaliar comportamento de uma regra de decisão. Ela **não altera a decisão** da fixture A/B nem produz estimativas de campanha real.

## Cenários

- H0 de conversão: nenhuma diferença entre A e B. Estimar taxa empírica de `p<0.05` no horizonte final.
- H1 de conversão: ganho real igual ao MDE de 0,015 em probabilidade absoluta. Medir significância e regra adicional de atingir MDE observado.
- Peeking ingênuo: quatro olhadas cumulativas no mesmo experimento. Medir probabilidade de detectar `p<0.05` em qualquer olhada sob H0 para evidenciar inflação. **Não é recomendado como estratégia válida de parada.**
- Guardrail: taxa-base de descadastro de 1,2%, cenário seguro com +0,2 p.p. e cenário inseguro com +0,8 p.p. Avaliar chance de o limite superior Newcombe/Wilson ficar <= +0,5 p.p.

## Como reproduzir

```bash
make analyze
make sensitivity
make simulate
```

Em `src/design_simulation.py`, padrão 2.000 réplicas, 8.000 usuários por braço, seed 42. Resultado em `work/evaluation/design_simulation.json` (ignorado). Mais repetições reduzem erro de Monte Carlo; limites de 20.000 réplicas e 100.000 por braço evitam uso excessivo na máquina.

## Limitações explícitas

A geração é binomial sem heterogeneidade, usuários independentes, sem cluster ou spillover. As duas métricas são simuladas separadamente e **não representam probabilidade conjunta de adoção**. A análise usa aproximação normal e IC Newcombe/Wilson na margem; eventos muito raros podem exigir simulações mais fiéis e métodos exatos. SRM e covariáveis não são simulados aqui. O intervalo não prova não inferioridade regulatória ou de produto.

## Critério de qualidade

Testes de semente, domínio, inflação por consultas repetidas, limites do guardrail e preservação da regra do estudo original. Decisão prática requer pré-registro, instrumentação e dados reais.
