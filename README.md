# Experimento A/B de marketing

Uma campanha pode elevar conversão e, ao mesmo tempo, aumentar descadastros. Este projeto
investiga quando adotar uma variante, respeitando tamanho amostral, validade e limite de risco.
A entrega principal é um notebook reproduzível com plano, análise estatística e decisão argumentada.

## Abrir a análise

Requer Python 3.12. Na raiz deste repositório:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-notebook.txt
.venv/bin/python -m jupyterlab notebooks/analise_experimento.ipynb
```

Windows: use `.venv\Scripts\python`. No Jupyter, execute as células em ordem. O notebook é
entregue sem saídas gravadas; as tabelas e conclusões são calculadas na execução. Também pode
ser aberto em um editor com suporte a notebooks e kernel Python desse ambiente.

## Pergunta e método

- Unidade: usuário; alocação A/B 50/50; análise por atribuição.
- Primária: conversão. MDE absoluto de 1,5 p.p.; alpha 5%; poder 80%; horizonte mínimo 28 dias.
- Guardrail: aumento absoluto de descadastro limitado a 0,5 p.p., avaliado pelo limite superior do IC.
- Validade: SRM, amostra e horizonte completos antes de decidir.
- Receita: Welch, bootstrap e ajuste por covariável pré-teste; Holm nas métricas secundárias.
- Simulação separada mostra o risco de inspeções repetidas sem desenho sequencial.

O código estatístico está em `src/experiment.py`, com testes em `tests/`. Consulte
`docs/METODOLOGIA.md` para fórmulas e limitações. Os dados incluídos são inteiramente sintéticos;
nenhuma conclusão representa impacto em campanha real.

## Execução sem notebook

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/experiment.py
.venv/bin/python -m pytest tests -q
```

O CLI imprime a decisão e grava JSON/CSV locais em `work/evaluation/`, ignorados pelo Git.
Opcionalmente, `src/decision_memo.py` transforma a análise em Markdown nessa pasta.
Nenhum HTML ou gráfico pronto acompanha o projeto.

Dados externos: `src/experiment.py --input /caminho/teste.csv --observation-days 28`.
Colunas: `user_id,arm,converted,revenue,unsubscribed` e, para ajuste, `pre_revenue`.
Informe o horizonte realmente observado. Defina métricas, alocação, exclusões e critérios antes
da leitura dos efeitos; o script não comprova randomização nem procedência de dados externos.

Não há API ou hospedagem necessária: a análise roda no computador. O workflow GitHub é manual e opcional.
