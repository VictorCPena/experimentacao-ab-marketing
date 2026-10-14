# Parecer de experimento A/B

> Laboratório com dados sintéticos. Não representa teste em campanha real.

**Decisão:** REVISAR: benefício primário, mas segurança do guardrail ainda não demonstrada

## Resultado principal

- Usuários: A = 8,000; B = 8,000.
- Conversão A = 7,84%; B = 10,08%.
- Diferença absoluta = 2,24 p.p.
- Lift relativo = 28,55%.
- IC de 95% da diferença: [1,35%; 3,12%].

## Segurança e validade

- Verificações de validade aprovadas: sim ({'srm_pass': True, 'sample_complete': True, 'horizon_complete': True}).
- Descadastros A = 1,03%; B = 1,49%.
- Aumento máximo aceito no guardrail: 0,50 p.p.
- Limite superior IC95 do aumento em descadastros: 0,81 p.p.

## Próxima decisão

Não promover automaticamente a variante B. Avaliar risco do guardrail e
considerar novo experimento, com tamanho e horizonte planejados previamente.

## Limites

Inferências restritas a dados sintéticos e às hipóteses de randomização. IC
convencional não cobre inspeções repetidas sem plano sequencial.
