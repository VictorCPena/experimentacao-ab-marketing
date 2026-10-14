# Cenários, magnitude e decisão

A análise principal usa o plano pré-definido: métrica primária de conversão, limite de descadastro, horizonte fixo e testes de validade. O resultado `REVISAR` **não muda** por causa desta avaliação adicional.

## Como ler `make sensitivity`

O script lê `work/evaluation/analise.json` gerado por `make analyze` e produz `work/evaluation/sensibilidade.json` (não versionado):

- `incremental_conversions_at_observed_effect` transforma a diferença absoluta observada em quantidade *hipotética* para 10.000 usuários.
- `additional_unsubscribes_at_observed_effect` faz a mesma projeção para descadastros. Intervalos são escalados linearmente; não se tornam mais precisos ao projetar mais usuários.
- `sample_size_scenarios` dá **aproximações ilustrativas** de tamanho amostral por braço para demonstrar não-inferioridade no guardrail, considerando diferentes aumentos verdadeiros presumidos.
- À medida que o efeito verdadeiro presumido se aproxima da margem permitida, a amostra necessária cresce fortemente. **Não use a piora observada como parâmetro de um novo teste sem declarar a natureza pós-hoc.**

## O que faria em uma situação real

1. Confirmar que randomização, exposição, tracking e janela de observação estão corretos.
2. Validar custo de descadastro e assimetria das perdas; não interpretar só o p-valor da conversão.
3. Decidir antes do próximo experimento a margem, hipóteses, duração, amostragem e parada.
4. Planejar um novo experimento de confirmação com análise de poder, estimando o guardrail por métodos adequados a eventos raros, múltiplas métricas e dependência entre usuários quando houver.

Este laboratório é sintético, portanto não há ganho de receita comprovado em uma campanha real, causalidade fora do cenário nem ROI medido.
