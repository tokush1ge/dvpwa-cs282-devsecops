# Prompt de remediacao - DVPWA

> Segunda interacao com o LLM, apos a triagem. Cole junto com `llm-triage.md` e os
> trechos de codigo relevantes.

Voce e um engenheiro de seguranca de software. Abaixo esta a triagem dos achados
mais relevantes do DVPWA, junto com trechos de codigo. Proponha correcoes seguras.

## Tarefas
1. Para cada vulnerabilidade selecionada, explique a causa raiz.
2. Proponha um patch minimo e seguro.
3. Indique quais testes funcionais devem continuar passando.
4. Indique um teste de regressao que demonstre que o exploit nao funciona mais.
5. Evite correcoes que apenas escondem o alerta da ferramenta sem corrigir a causa.

## Formato de saida
- Vulnerabilidade
- Causa raiz
- Patch proposto
- Teste de regressao
- Como confirmar no segundo scan

## Vulnerabilidades selecionadas (da triagem)
1. SQL Injection em `sqli/dao/student.py` (`Student.create`).
2. Stored XSS via `autoescape=False` em `sqli/app.py`.
3. Session Fixation no login em `sqli/views.py` (`index`).
