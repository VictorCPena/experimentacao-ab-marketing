# Experimento A/B de Marketing | Ganhar conversão não basta

**Estatística aplicada · Testes de hipótese · Intervalos de confiança · Guardrails · Python · Jupyter**

> **Decisão de negócio:** a variante B melhora a conversão. Mas devemos adotá-la se também pode aumentar os descadastros?

Este projeto é uma **análise de decisão**, não uma API nem um dashboard. Um notebook reproduz o desenho, a checagem de validade, a inferência e a recomendação final. O dataset é inteiramente sintético.

## Caso estudado

Experimento A/B simulado com **16.000 usuários** (8.000 por grupo) e **28 dias** de observação. Métrica primária: conversão. Métrica de proteção (*guardrail*): descadastro, com limite pré-definido de piora de **0,5 ponto percentual**.

### O que os dados mostraram

| Medida | Controle A | Variante B | Diferença |
| --- | ---: | ---: | ---: |
| Conversão | 7,84% | 10,08% | **+2,24 p.p.** |
| Descadastro | 1,03% | 1,49% | **+0,46 p.p.** |

- Conversão: **+28,55% de lift relativo**; IC95% da diferença aproximadamente **+1,35 a +3,12 p.p.**; `p ≈ 7,21 × 10⁻⁷`.
- Descadastro: embora a piora observada seja +0,46 p.p., o **limite superior do IC95% é +0,813 p.p.**, acima dos +0,5 p.p. tolerados pelo plano.
- Validade: SRM, tamanho amostral e horizonte foram aprovados no cenário simulado.

**Decisão do protocolo: `REVISAR`**. Há benefício estatístico na conversão, mas a margem de segurança para descadastros **não foi demonstrada**. A decisão não é “B ganhou, faça deploy”. Os intervalos apresentados são nominais, não simultâneos, e não devem ser transportados para campanhas reais.

## Por que a análise é mais do que um p-valor

1. **Planejamento antes dos resultados:** métrica primária, MDE de +1,5 p.p., α=5%, poder=80%, horizonte e guardrail.
2. **Validade da comparação:** verificações de duplicidade, alocação, SRM, amostra e período observado.
3. **Estimativa do efeito:** diferença de proporções, teste z *pooled*, IC Newcombe/Wilson.
4. **Métricas secundárias:** receita com Welch, bootstrap e ANCOVA com covariável pré-teste; ajuste de Holm.
5. **Disciplina de decisão:** limite superior do intervalo do guardrail e simulação de *peeking* para ilustrar risco de olhar os resultados repetidamente.

O plano JSON é salvo pelo script antes da geração e análise da simulação; **não é evidência de pré-registro externo**.

## Explorar o notebook

Requer **Python 3.12**. Na raiz do projeto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-notebook.txt
.venv/bin/python -m jupyterlab notebooks/analise_experimento.ipynb
```

Execute as células de cima para baixo. O notebook foi entregue **sem saídas gravadas** para obrigar a reprodução da análise. Ele gera suas tabelas e gráficos na própria sessão; não há HTML estático publicado.

### Rodar sem Jupyter

```bash
.venv/bin/python -m pip install -r requirements.txt
make test
make analyze
.venv/bin/python src/decision_memo.py
```

O CLI grava artefatos intermediários em `work/evaluation/`, ignorados pelo Git. `decision_memo.py` exporta um parecer Markdown opcional. Em dados externos, use `src/experiment.py --input caminho.csv --observation-days 28` e documente efetivamente a randomização e o período observado.

## Para quem lê o código

- [`notebooks/analise_experimento.ipynb`](notebooks/analise_experimento.ipynb): narrativa investigativa e decisão.
- `src/experiment.py`: funções de tamanho amostral, checagens e inferência.
- `src/decision_memo.py`: conversão opcional do resultado em parecer técnico.
- [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md): premissas, fórmulas e limitações.
- `tests/`: cenários de validade, estatística e guardrails.

**Limite:** os dados foram simulados; passar no SRM não prova randomização real, e a análise não estima ROI de campanha, efeito de rede, clusters ou causalidade em dados observacionais. [Workflow de CI](https://github.com/VictorCPena/experimentacao-ab-marketing/actions/workflows/ci.yml) sob disparo manual.
