# Planejamento e inferência

## Antes do teste

Unidade: usuário. Atribuição A/B randomizada, 50/50. Métrica primária: converted. Baseline esperado 8%,
MDE absoluto 0,015, teste bilateral alpha 0,05, poder 0,80. Fórmula normal de duas proporções estima
5.570 usuários por braço. Dados sintéticos incluem 8.000 por braço, horizonte de 28 dias.

O plano é escrito em JSON antes da análise; não é registro externo nem prova de préregistro de uma
campanha real. Em trabalho real, versão/datas e desenho devem ser acordados antes de receber resultados.

## Validade

Uma linha por usuário, sem ausências ou duplicatas. Dados de todos os usuários elegíveis atribuídos aos
braços (intenção de tratar), sem filtrar por clique, exposição ou conversão. SRM chi-quadrado com alpha
0,001 detecta discrepância de contagem; passar SRM não prova randomização correta. Amostra/horizonte
incompletos ou SRM reprovado produzem conclusão inconclusiva.

Uma receita por usuário pode ter múltiplos pedidos; agregue antes de analisar. Clusterização por família,
empresa ou região exige outro erro padrão; esta versão assume usuários independentes e sem interferência.

## Estimativas

Diferença de conversão B-A, lift relativo se baseline não for zero. P-valor de z com proporção pooled;
IC de diferença pelo método Newcombe combinando Wilson. Receita: diferença de médias com Welch e
IC bootstrap percentil separado por braço, semente 42 e 1.000 repetições.

ANCOVA: `revenue ~ intercept + treatment + centered_pre_revenue`, com matriz sandwich HC3. O coeficiente
de treatment estima o efeito ajustado; o de pre_revenue é theta. O método segue a lógica de CUPED,
mas não é toda variante de CUPED publicada. Nenhuma covariável posterior ao tratamento é permitida.

Receita e descadastro recebem p-valores ajustados por Holm; a métrica primária foi definida previamente.
Os IC95 apresentados são **nominais e não simultâneos**. A ANCOVA e bootstrap complementam a receita;
não são buscas adicionais por uma métrica significativa para substituir a primária.

## Decisão

Benefício: IC primário excluir zero e estimativa atingir o MDE. Guardrail: limite superior do IC de
aumento de descadastro deve ser <=0,005. Não rejeitar hipótese de piora não basta para provar segurança.
Critério de adoção também exige validade/amostra/horizonte completos; resultado é candidato a decisão,
pois custo de implementação e validade externa não estão no dataset.

Não calcular ROI da receita total sintética sem custo/incrementalidade real. Diferenças de campanhas
observacionais não se tornam causais por usar este código. Regressão ou MMM exigem hipóteses adicionais.

## Peeking

Simula 1.000 testes sem efeito, dez análises com 100 novos usuários por braço por análise. Compara
rejeição apenas na análise final com parar em qualquer p<0,05. Informa taxa e IC Wilson da simulação.
O desenho mostra o problema, não implementa um teste sequencial válido.
