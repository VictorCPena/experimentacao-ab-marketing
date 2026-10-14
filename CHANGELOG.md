## 1.6.0 — Estudos técnicos adicionais

- `src/advanced_design.py`: cenários correlacionados e randomização por cluster, inferência Welch por cluster e simulação de gasto conservador de alfa.
- Smoke de Monte Carlo no CI.

## v1.5.0 — experimentos de robustez e avaliação reproduzíveis

- Simulação Monte Carlo do plano A/B, poder, falso positivo com peeking e risco do guardrail.
- Testes de reprodutibilidade e cenários-limite, smoke no CI.

# Histórico de evolução — experimentacao-ab-marketing

## 1.4.0 — estudo aprofundado

- README específico com pergunta de negócio, evidências e limitações.
- Nova capacidade analítica distinta das outras duas aplicações, com testes dedicados.
- Documentação operacional e workflow ajustado para executar a nova verificação.
- Mantido o escopo local com dados sintéticos e sem serviço pago.

## 1.2.x — base consolidada

- Repositório independente, geração de dados, testes, documentação e execução local.
- Correção do CI do MLOps no commit `40362b3` preservada neste pacote.
