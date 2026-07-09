# Triagem assistida por LLM - DVPWA

> **Entrada:** relatorios de `artifacts/scan-before/` (Bandit, Semgrep, pip-audit, Gitleaks)
> e o prompt `artifacts/prompts/triage-prompt.md`.
> **Papel:** analista de seguranca de software.

## 1. Panorama dos achados brutos

| Ferramenta | Achados | Observacao |
|---|---|---|
| Bandit | 2 | 1x SQLi (B608), 1x MD5 fraco (B324) |
| Semgrep | 7 | 3 relevantes (SQLi + MD5), 4 em biblioteca de terceiros |
| pip-audit | 52 | dependencias desatualizadas (aiohttp, jinja2, pyyaml, aioredis) |
| Gitleaks | 0 | nenhum segredo detectado pelas regras padrao |

## 2. Agrupamento e deduplicacao

- **SQL Injection (student.py):** Bandit `B608` (linha 42) e Semgrep
  `formatted-sql-query` + `sqlalchemy-execute-raw-query` (linha 45) apontam para
  **o mesmo defeito**: `Student.create` monta a query por interpolacao de string.
  Sao 3 alertas para 1 causa raiz.
- **Hash fraco (user.py):** Bandit `B324` e Semgrep `md5-used-as-password`
  (linha 41) apontam para **o mesmo defeito**: uso de MD5 para senha.
- **Dependencias (pip-audit):** 52 CVEs concentrados em 4 pacotes; e um unico
  problema de fundo (versoes antigas fixadas em `requirements.txt`).

## 3. Provaveis falsos positivos

| Achado | Ferramenta | Decisao | Justificativa |
|---|---|---|---|
| `unsafe-formatstring` x3 em `sqli/static/js/materialize.js` | Semgrep | Falso positivo | Codigo de terceiros (Materialize CSS), nao e a superficie de ataque do app; fora do escopo. |
| `detect-non-literal-regexp` em `materialize.js` | Semgrep | Falso positivo | Idem; biblioteca minificada de front-end. |
| Parte dos 52 CVEs do pip-audit | pip-audit | Ruido de fundo | Reais, porem muitos exigem vetores nao expostos pelo DVPWA; nao sao o foco das 3 vulnerabilidades escolhidas. |

## 4. Achados NAO detectados pelas ferramentas (revisao manual/LLM)

A leitura do codigo revelou duas vulnerabilidades **exploraveis** que o SAST de
regras padrao **nao** sinaliza (sao falhas de logica/configuracao):

- **Stored XSS:** `sqli/app.py` configura o Jinja2 com `autoescape=False`. Reviews
  de curso (`{{ review.review_text }}` em `course.jinja2`) sao renderizadas sem
  escape -> injecao de `<script>` persistente.
- **Session Fixation:** `sqli/views.py::index` autentica setando
  `session['user_id']` **sem regenerar** o identificador de sessao. O id anterior
  ao login continua valido apos autenticar.

> Isto ilustra o valor da etapa de triagem por LLM: alem de deduplicar o ruido
> das ferramentas, ela identifica classes de vulnerabilidade que o SAST padrao
> nao cobre. O enunciado (secao 9) admite explicitamente achados validados por
> justificativa tecnica quando a ferramenta nao os detecta.

## 5. Priorizacao (exploratabilidade no DVPWA)

| Prioridade | Vulnerabilidade | Exploravel? | Evidencia |
|---|---|---|---|
| Alta | SQL Injection (student.py) | Sim, via form de alunos | Bandit B608 + Semgrep |
| Alta | Stored XSS (autoescape) | Sim, via review de curso | Revisao de codigo + teste de regressao |
| Alta | Session Fixation (login) | Sim, via cookie fixado | Revisao de codigo + teste de regressao |
| Media | MD5 em senhas (user.py) | Impacto pos-comprometimento | Bandit B324 + Semgrep |
| Media | Dependencias vulneraveis | Depende do vetor | pip-audit (52 CVEs) |

## 6. Tabela consolidada de triagem

| ID | Ferramenta | Arquivo | Severidade | Decisao | Justificativa |
|---|---|---|---|---|---|
| T-01 | Bandit/Semgrep | sqli/dao/student.py:42 | Alta | **Corrigir** | SQLi por interpolacao de string; explor. via `name`. |
| T-02 | Manual/LLM | sqli/app.py:29 | Alta | **Corrigir** | Stored XSS: `autoescape=False`. |
| T-03 | Manual/LLM | sqli/views.py (index) | Alta | **Corrigir** | Session Fixation: id nao regenerado no login. |
| T-04 | Bandit/Semgrep | sqli/dao/user.py:41 | Alta | Aceito (fora do escopo das 3) | MD5 em senha; candidato de ranking. |
| T-05 | pip-audit | requirements.txt | Variada | Aceito (fora do escopo) | 52 CVEs de deps antigas; candidato de ranking. |
| T-06 | Semgrep | sqli/static/js/materialize.js | Baixa/Info | Falso positivo | Biblioteca de terceiros. |

## 7. Vulnerabilidades selecionadas para remediacao

Escolhidas **3 vulnerabilidades** para o ciclo completo (exploracao -> patch ->
validacao), atendendo ao minimo da trilha basica:

1. **SQL Injection** em `sqli/dao/student.py` (`Student.create`).
2. **Stored XSS** via `autoescape=False` em `sqli/app.py`.
3. **Session Fixation** no login em `sqli/views.py` (`index`).

Cada uma tem teste de regressao dedicado em `tests/security/`, que **falha** no
codigo vulneravel (evidencia do exploit) e **passa** apos o patch.
