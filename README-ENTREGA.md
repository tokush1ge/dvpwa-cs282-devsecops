# Entrega - Esteira DevSecOps com LLM sobre o DVPWA (CS-282)

Este repositorio contem o DVPWA e uma esteira reproduzivel de seguranca:
**scan inicial -> triagem com LLM -> remediacao com LLM -> patches manuais ->
segunda esteira de validacao**.

- **Relatorio final (leia primeiro):** [`RELATORIO-FINAL.md`](RELATORIO-FINAL.md)
- **Comparacao antes/depois:** [`artifacts/scan-after/comparison.md`](artifacts/scan-after/comparison.md)

## Estrutura

```
artifacts/
  scan-before/   relatorios Bandit/Semgrep/pip-audit/Gitleaks (antes dos patches)
  scan-after/    relatorios apos os patches + comparison.md
  prompts/       triage-prompt.md (gerado) e remediation-prompt.md
  llm/           llm-triage.md e llm-remediation.md (saidas do LLM)
  tests/         tests-before.txt (3 falhas) e tests-after.txt (3 passes)
scripts/
  run_scans.sh            roda as 4 ferramentas para um diretorio
  build_triage_prompt.py  gera o prompt de triagem a partir do scan-before
  compare_scans.py        gera comparison.md (before x after)
  run_pipeline.sh         orquestrador local (before | tests | after | all)
tests/security/           testes de regressao das 3 vulnerabilidades
.gitlab-ci.yml            esteira CI (4 stages)
```

## Vulnerabilidades tratadas (branch `fix/security-remediation`)

1. **SQL Injection** - `sqli/dao/student.py` (query parametrizada)
2. **Stored XSS** - `sqli/app.py` (`autoescape=True`)
3. **Session Fixation** - `sqli/views.py` (`new_session` no login)

Cada uma tem um commit `fix:` proprio e um teste de regressao dedicado.

## Como reproduzir

### Opcao A - CI (GitLab)
Faca push para um projeto GitLab; o `.gitlab-ci.yml` executa `scan_before`,
`build_triage_prompt`, `validate_after` (testes de regressao) e `scan_after`
(scans + comparison) automaticamente, publicando os relatorios como artifacts.

### Opcao B - Local

Requisitos: Python 3.11+ (funciona em 3.9), `git`, e as ferramentas
`bandit semgrep pip-audit` (via pip) + `gitleaks` (via brew/instalador oficial).

```bash
# 1) Ferramentas de scan
python3 -m venv .venv-tools && . .venv-tools/bin/activate
pip install bandit semgrep pip-audit
# gitleaks: brew install gitleaks  (ou instalador oficial)

# 2) Esteira completa (scan-before -> testes -> scan-after + comparison)
bash scripts/run_pipeline.sh all
```

### Rodar apenas os testes de regressao

Os testes exercitam o codigo real do DVPWA **sem** PostgreSQL/Redis/Docker
(modulos nativos sao substituidos por stubs em `tests/security/conftest.py`).

```bash
python3 -m venv .venv-app && . .venv-app/bin/activate
pip install -r requirements-dev.txt
pytest -v tests/security
```

- No codigo **vulneravel** (branch `main`): **3 testes falham** (exploits reproduzidos).
- No codigo **corrigido** (branch `fix/security-remediation`): **3 testes passam**.

### Executar a aplicacao (opcional)

Requer Docker. Nao e necessario para os scans nem para os testes de regressao.

```bash
docker-compose up   # app em http://localhost:8080
```

## Observacoes de reproducibilidade

- `pip-audit` audita `requirements.txt`; em macOS pode exigir `pg_config`
  (`brew install libpq`) para ler metadados do `psycopg2`. Em `python:3.11` do CI
  isso nao ocorre.
- Gitleaks roda com `--no-git` (escaneia o diretorio atual) e usa `.gitleaks.toml`
  para ignorar venvs locais e assets de terceiros.
