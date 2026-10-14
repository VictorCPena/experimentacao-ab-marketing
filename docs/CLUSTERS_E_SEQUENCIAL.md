# Correlacionar métricas, randomização por cluster e testes sequenciais

## Por que importa
Dados reais de marketing podem conter interdependência entre conversão e descadastro, membros do mesmo grupo/cidade e múltiplas análises durante uma campanha. Isso invalida a hipótese simples de observações independentes do ensaio A/B original.

## Modelo de dependência
`advanced_design.generate_clustered` randomiza **clusters inteiros** em A ou B, usa mistura gaussiana de efeitos compartilhados no cluster e covariação latente entre dois resultados binários: conversão e descadastro. O `latent_icc` é correlação na variável latente, **não** o ICC Bernoulli estimado. Valores verdadeiros de efeito são configurados antes da simulação.

`cluster_diff` analisa médias por cluster com erro de Welch em unidades **cluster**, impondo tamanho igual por cluster e ao menos três clusters por braço. O cenário compara essa inferência com um z-teste ingênuo que trata todos os usuários como independentes, expondo o risco de significância artificial.

## Consultas sequenciais com controle explícito
`spending_boundaries` define gasto cumulativo de alfa inspirado em O'Brien-Fleming, mas a decisão usa **incrementos Bonferroni** por look (`alpha_i = A(t_i)-A(t_{i-1})`) para preservar `sum(alpha_i)<=0,05` sem assumir independência dos looks. É conservador e **não** pretende implementar a fronteira conjunta exata OBF. Compara:

- teste no último dia com alpha 5%; 
- interrupção ingênua ao obter p inferior a 0,05 em qualquer look;
- rejeição sob gasto de alfa por limiar incremental predefinido.

## Reproduzir

```bash
make advanced-smoke
make advanced-design
```

Os resultados vão para `work/evaluation/advanced_design.json` e são simulados (não dados de clientes). Configuração de referência com `reps=300, clusters=25, size=25, seed=42/51` obteve aproximadamente 17% de falsos positivos ignorando clusters versus 3,3% considerando clusters; no sequencial, 11,7% em peeking ingênuo versus 3% com o procedimento conservador de gasto de alfa. Esses pontos são amostras Monte Carlo; variar número de réplicas e seeds antes de comparar protocolos.

## Limitações e aprimoramentos possíveis
Interferência entre clusters, efeitos heterogêneos e ICC binomial real não são garantidos por essa simulação; cluster Welch exige clusters equivalentes. Gasto de alfa conservador custa poder estatístico versus métodos sequenciais especializados. Correlação observada pode não ser estimável quando uma métrica rara for constante (registrado via contagem de simulações estimáveis). A política final de liberação com guardrail continua exigindo margem de não inferioridade documentada.
