# Estrutura da análise

O notebook `notebooks/analise_experimento.ipynb` encadeia pergunta, plano, checagens de validade,
estimativas, guardrail e decisão. `src/experiment.py` concentra funções estatísticas testáveis.
A tabela sintética em `data/` permite reproduzir a análise sem serviços externos.

As verificações de amostra, horizonte e SRM precedem a decisão. Conversão é a métrica primária;
receita é secundária e descadastro limita a adoção. A simulação de peeking é uma demonstração
separada, sem uso como evidência do efeito da campanha.

O CLI exporta dados intermediários em `work/evaluation/` para automação opcional. O notebook
chama as funções diretamente e não depende desses arquivos. `decision_memo.py` é um exportador
opcional de Markdown; a interpretação principal está no notebook.

Não há deploy, API ou relatório web. Os testes conferem os cálculos e casos de decisão.
