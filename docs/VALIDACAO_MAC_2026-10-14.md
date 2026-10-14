# Validação estatística — Mac local, 14/10/2026

Execução observada: `23 passed in 75.32s` no pytest. Todas as simulações abaixo são **inteiramente sintéticas**, não resultados de campanhas reais.

## Caso A/B (script original)

- 8.000 usuários em cada braço.
- Conversão A: 7,8375%; B: 10,075%; diferença +2,2375 p.p.; lift relativo +28,55%.
- IC95% nominal da diferença de conversão: [1,3534; 3,1232] p.p., `p≈7,207×10⁻⁷`.
- Decisão: `REVISAR`. O guardrail descadastro não foi demonstrado seguro no critério estabelecido.

## Simulação sequencial — 300 réplicas

Parâmetros de `make advanced-design`: 3.000 usuários por braço, efeito verdadeiro de conversão 0, seed 51, olhadas em 25%/50%/75%/100%.

| Protocolo | Rejeição sob H0 |
| --- | ---: |
| Apenas teste final fixo | 0,0500 |
| Qualquer p < 0,05 nas quatro olhadas (*peeking*) | 0,1167 |
| Bonferroni incremental com gasto de alfa | 0,0300 |

Controle do erro com Bonferroni via limite da união; não equivale a teste conjunto OBF exato. Com só 300 réplicas, há incerteza Monte Carlo relevante nas estimativas de cauda.

## Randomização em clusters, duas métricas correlacionadas — 300 réplicas

- 25 clusters por braço, 25 pessoas por cluster; ICC latente 0,12; correlação latente de outcomes 0,4.
- Sob nulo: taxa de rejeição `cluster_welch=0,0333` vs `naive_ignoring_clusters=0,17`.
- Aprovação incorreta de guardrail realmente inseguro: `0,01` nas hipóteses e regra da simulação.
- Correlação observada média conversão-descadastro `0,1091`; estimável em 300/300 réplicas.
- Correlação latente não é a correlação observada entre eventos raros e **não implica causalidade**.

## Reproduzir

```bash
make test
make analyze
make advanced-smoke  # 100 réplicas / 12 clusters por braço / tamanho 10
make advanced-design # 300 réplicas / 25 clusters por braço / tamanho 25
```

## Limitações e extensões

As taxas são estimativas Monte Carlo de um gerador específico com seed fixa, amostras igualmente distribuídas em clusters e ausência de interferência entre clusters. Não descrevem sempre como clusters reais variam em tamanho nem como rede social altera resultados. Um estudo posterior pode variar ICC, cluster-size imbalance e número de réplicas, com IC Monte Carlo para erro tipo I. O procedimento não constitui pré-registro externo ou autorização causal para um lançamento de produto.
