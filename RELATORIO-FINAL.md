# Relatorio Final - Esteira DevSecOps com LLM sobre o DVPWA

**Disciplina:** CS-282 - Sistemas de Software Seguro | **Trilha:** Basica
**Alvo:** DVPWA - Damn Vulnerable Python Web Application (`anxolerd/dvpwa`)
**Ferramentas:** Bandit, Semgrep, pip-audit, Gitleaks

---

## 1. Resumo executivo

Construimos uma esteira reproduzivel que executa o ciclo completo:

> scan inicial -> triagem com LLM -> remediacao com LLM -> patches manuais -> segunda esteira de validacao

Foram escolhidas, exploradas, corrigidas e validadas **3 vulnerabilidades**:

| # | Vulnerabilidade | Arquivo | Deteccao | Validacao |
|---|---|---|---|---|
| 1 | SQL Injection | `sqli/dao/student.py` | Bandit B608 + Semgrep | Teste de regressao + queda no scan |
| 2 | Stored XSS | `sqli/app.py` (autoescape) | Revisao manual/LLM | Teste de regressao |
| 3 | Session Fixation | `sqli/views.py` (login) | Revisao manual/LLM | Teste de regressao |

Cada teste de regressao **falha no codigo vulneravel** (prova do exploit) e
**passa apos o patch** (prova da correcao).

---

## 2. Primeira esteira (scan-before)

Relatorios em `artifacts/scan-before/`. Contagem de achados:

| Ferramenta | Achados | Principais |
|---|---|---|
| Bandit | 2 | B608 (SQLi, student.py), B324 (MD5, user.py) |
| Semgrep | 7 | SQL em student.py (x2), md5 em user.py, 4 em `static/js/materialize.js` (terceiros) |
| pip-audit | 52 | CVEs em aiohttp, jinja2, pyyaml, aioredis (versoes antigas) |
| Gitleaks | 0 | nenhum segredo pelas regras padrao |

A triagem completa esta em `artifacts/llm/llm-triage.md`. Destaque: as ferramentas
de SAST padrao detectaram o SQLi e o hash fraco, mas **nao** o Stored XSS nem o
Session Fixation - ambos sao falhas de logica/configuracao encontradas na revisao
por LLM. Isso justifica o valor da etapa de triagem alem do output bruto das
ferramentas.

---

## 3. Vulnerabilidades: exploracao, patch e validacao

### 3.1 SQL Injection - `sqli/dao/student.py`

- **Exploracao.** `Student.create` montava a query por interpolacao:
  `"INSERT INTO students (name) VALUES ('%(name)s')" % {'name': name}`. Um nome
  como `Robert'); DROP TABLE students;--` (campo do form de alunos) altera o
  comando SQL.
- **Patch (commit `fix(sqli)`).** Query parametrizada
  `INSERT INTO students (name) VALUES (%(name)s)` com `params={'name': name}`.
- **Regressao.** `tests/security/test_sqli_student_create.py` verifica que o
  payload nao aparece no texto SQL e viaja como parametro vinculado.
- **Confirmacao no scan.** Bandit B608 e os alertas Semgrep de SQL em student.py
  **desaparecem** no scan-after.

### 3.2 Stored XSS - `sqli/app.py`

- **Exploracao.** Jinja2 configurado com `autoescape=False`. Uma review contendo
  `<script>alert(document.cookie)</script>` (via `POST /courses/{id}/review`) e
  armazenada e renderizada crua em `course.jinja2` (`{{ review.review_text }}`),
  executando no navegador de quem abre o curso (Stored XSS persistente).
- **Patch (commit `fix(xss)`).** `autoescape=True` no setup do Jinja2.
- **Regressao.** `tests/security/test_xss_autoescape.py` renderiza um payload pelo
  ambiente Jinja2 **real** do app e exige saida escapada (`&lt;script&gt;`).
- **Confirmacao no scan.** Nao detectado por SAST padrao (falha de configuracao);
  confirmado por teste de regressao e inspecao do HTML renderizado - justificativa
  tecnica prevista na secao 9 do enunciado.

### 3.3 Session Fixation - `sqli/views.py::index`

- **Exploracao.** No login, `session['user_id'] = user.id` era gravado na mesma
  sessao anonima, sem regenerar o id. Um id de sessao fixado antes do login
  permanece valido apos autenticar.
- **Patch (commit `fix(session)`).** `session = await new_session(request)` antes
  de gravar o usuario, gerando novo id de sessao.
- **Regressao.** `tests/security/test_session_fixation.py` estabelece sessao
  anonima, faz login e exige que o id de sessao **mude**.
- **Confirmacao no scan.** Falha de logica nao coberta por SAST padrao; confirmada
  por teste de regressao.

---

## 4. Segunda esteira (scan-after) e comparacao

Relatorios em `artifacts/scan-after/`. Comparacao automatica
(`artifacts/scan-after/comparison.md`):

| Ferramenta | Antes | Depois | Delta |
|---|---|---|---|
| Bandit | 2 | 1 | -1 |
| Semgrep | 7 | 5 | -2 |
| pip-audit | 52 | 52 | 0 |
| Gitleaks | 0 | 0 | 0 |
| **Total** | **61** | **58** | **-3** |

**Interpretacao dos achados que permaneceram:**

- **Bandit B324 / Semgrep `md5-used-as-password` (user.py):** hash MD5 de senha.
  **Fora do escopo** das 3 vulnerabilidades tratadas; candidato de ranking (ver
  secao 6).
- **Semgrep em `sqli/static/js/materialize.js` (4 achados):** **falsos positivos**
  em biblioteca de front-end de terceiros; nao fazem parte da superficie do app.
- **pip-audit (52 CVEs, inalterado):** dependencias antigas fixadas em
  `requirements.txt`. Nao mexemos nas versoes para nao quebrar a app na trilha
  basica; candidato de ranking.
- **XSS e Session Fixation:** nao apareciam na contagem das ferramentas nem antes
  nem depois (SAST padrao nao os detecta); a evidencia de correcao vem dos testes
  de regressao.

---

## 5. Evidencia dos testes de regressao

| Momento | Comando | Resultado | Artefato |
|---|---|---|---|
| Antes dos patches | `pytest tests/security` | **3 failed** (exploits reproduzidos) | `artifacts/tests/tests-before.txt` |
| Depois dos patches | `pytest tests/security` | **3 passed** (exploits corrigidos) | `artifacts/tests/tests-after.txt` |

---

## 6. Candidatos ao ranking (nao incluidos nas 3 obrigatorias)

- **Hash de senha MD5 (user.py):** migrar para algoritmo com sal e custo (ex.:
  `bcrypt`/`argon2`). Detectado por Bandit B324 e Semgrep.
- **Dependencias vulneraveis (52 CVEs):** atualizar `requirements.txt` (aiohttp,
  jinja2, pyyaml, aioredis) e revalidar com pip-audit.
- **CSRF middleware desativado (app.py) / cookie de sessao `httponly=False`
  (middlewares.py):** endurecimento adicional.

---

## 7. Mapa dos entregaveis (secao 10 do enunciado)

| # | Entregavel | Onde |
|---|---|---|
| 1 | Repositorio com DVPWA, pipeline e instrucoes | este repo + `.gitlab-ci.yml` + `README-ENTREGA.md` |
| 2 | Relatorios da primeira esteira | `artifacts/scan-before/` |
| 3 | Prompt e saida da triagem LLM | `artifacts/prompts/triage-prompt.md`, `artifacts/llm/llm-triage.md` |
| 4 | Prompt e saida da remediacao LLM | `artifacts/prompts/remediation-prompt.md`, `artifacts/llm/llm-remediation.md` |
| 5 | Commits com patches manuais | branch `fix/security-remediation` (3 commits `fix:`) |
| 6 | Testes de regressao (>=2 vulnerabilidades) | `tests/security/` (3 testes) |
| 7 | Relatorios da segunda esteira | `artifacts/scan-after/` |
| 8 | Relatorio final comparando antes/depois | este arquivo + `artifacts/scan-after/comparison.md` |
