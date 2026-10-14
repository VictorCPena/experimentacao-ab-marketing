# Laboratório de experimentação em marketing

Teste A/B sintético randomizado por usuário para avaliar conversão, receita por usuário e descadastros.
Código executável, plano prévio em arquivo e decisão de negócio com condições explícitas.

## Executar independentemente

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/experiment.py
.venv/bin/python -m pytest tests -q
```

Windows: substitua `.venv/bin/python` por `.venv\Scripts\python`.
No pacote completo: `python executar.py experiments`.

## Conteúdo

- Planejamento de tamanho de amostra, MDE absoluto, alfa e poder.
- Checagem de Sample Ratio Mismatch (SRM) e intenção de tratar.
- Conversão: diferença absoluta/relativa, teste bilateral e IC Newcombe/Wilson.
- Receita por usuário: Welch e bootstrap por braço.
- Covariável de receita préteste: ANCOVA com erro padrão robusto HC3, princípio CUPED.
- Holm nas duas métricas secundárias.
- Guardrail de descadastro e conclusão condicionada ao plano.
- Monte Carlo de peeking sob hipótese nula, com intervalo da incerteza da simulação.

Todos os usuários, receitas e efeitos são sintéticos. `resultados/analise.json` não é evidência de uma
campanha real. O relatório HTML e os CSV podem ser abertos sem executar código.

## Dados externos

CSV com `user_id,arm,converted,revenue,pre_revenue,unsubscribed`. Uma linha por usuário randomizado,
braços A/B, indicadores 0/1 e valores não negativos em reais. Receita préteste deve vir de antes da
atribuição ao braço. Todos os randomizados elegíveis entram; não selecionar apenas usuários expostos/conversores.

```bash
.venv/bin/python src/experiment.py --input /caminho/experimento.csv --observation-days 28
```

O plano desta versão permanece fixo: alocação 50/50, baseline 8%, MDE 1,5 ponto percentual,
alpha 5%, poder 80% e horizonte mínimo de 28 dias. Para outro experimento, modifique e registre o plano
**antes** de olhar resultados. O script não verifica a randomização real ou a origem das observações.

Leia `docs/METODOLOGIA.md` para hipóteses, múltiplos testes e interpretação.

Os HTML e gráficos incluídos são snapshots da execução entregue. Para atualizá-los, use `gerar_relatorios.py` na raiz do pacote completo após executar os fluxos. CSV/JSON são atualizados pelos scripts deste projeto.

## Versão portfólio · 1.1.0

Novo `src/decision_memo.py`: converte a inferência estatística em parecer executivo,
mostrando a métrica primária, o risco de descadastros e limitações. CI roda testes e
experimento determinístico. Novo HTML `resultados/RESUMO_ATUAL.html` é gerado sempre que
`make run` termina. O HTML `relatorio.html` é uma apresentação original/snapshot.

```bash
make setup
make test
make run
make report
cat resultados/PARECER_DECISAO.md
```

Os arquivos sintéticos não equivalem a uma campanha real. Para dados de clientes,
documente consentimento, coleta, unidade de randomização e janela observada.

**Próxima melhoria autoral:** executar análise de sensibilidade para margens do guardrail,
pré-especificando o plano sem escolher um limite depois de ver os dados.
