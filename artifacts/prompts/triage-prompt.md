# Prompt de triagem - DVPWA

> Gerado automaticamente por `scripts/build_triage_prompt.py` a partir de `artifacts/scan-before`.
> Cole este prompt em qualquer LLM disponivel ao grupo (interface web, modelo local ou API).

Voce e um analista de seguranca de software. Abaixo estao os relatorios de
Bandit, Semgrep, pip-audit e Gitleaks executados sobre o DVPWA (Damn Vulnerable
Python Web Application).

## Tarefas
1. Agrupe achados duplicados ou equivalentes.
2. Identifique provaveis falsos positivos e explique brevemente.
3. Priorize achados que parecem exploraveis no DVPWA.
4. Escolha pelo menos tres vulnerabilidades candidatas para correcao.
5. Para cada vulnerabilidade escolhida, indique evidencia, arquivo/linha, causa
   raiz provavel e estrategia de correcao.

## Formato de saida esperado
- Tabela com: ID, ferramenta, arquivo, severidade, decisao, justificativa.
- Secao final: vulnerabilidades selecionadas para remediacao.

---

## Relatorio Bandit (SAST Python)
  - [B608] MEDIUM/LOW sqli/dao/student.py:42 - Possible SQL injection vector through string-based query construction.
  - [B324] HIGH/HIGH sqli/dao/user.py:41 - Use of weak MD5 hash for security. Consider usedforsecurity=False

## Relatorio Semgrep (SAST)
  - [python.lang.security.audit.formatted-sql-query.formatted-sql-query] WARNING sqli/dao/student.py:45 - Detected possible formatted SQL query. Use parameterized queries instead.
  - [python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query] ERROR sqli/dao/student.py:45 - Avoiding SQL string concatenation: untrusted input concatenated with raw SQL query can result in SQL Injection. In order to execute raw query safely, prepared s
  - [python.lang.security.audit.md5-used-as-password.md5-used-as-password] WARNING sqli/dao/user.py:41 - It looks like MD5 is used as a password hash. MD5 is not considered a secure password hash because it can be cracked by an attacker in a short amount of time. U
  - [javascript.lang.security.audit.detect-non-literal-regexp.detect-non-literal-regexp] WARNING sqli/static/js/materialize.js:565 - RegExp() called with a `t` function argument, this might allow an attacker to cause a Regular Expression Denial-of-Service (ReDoS) within your application as Re
  - [javascript.lang.security.audit.unsafe-formatstring.unsafe-formatstring] INFO sqli/static/js/materialize.js:645 - Detected string concatenation with a non-literal variable in a util.format / console.log function. If an attacker injects a format specifier in the string, it w
  - [javascript.lang.security.audit.unsafe-formatstring.unsafe-formatstring] INFO sqli/static/js/materialize.js:661 - Detected string concatenation with a non-literal variable in a util.format / console.log function. If an attacker injects a format specifier in the string, it w
  - [javascript.lang.security.audit.unsafe-formatstring.unsafe-formatstring] INFO sqli/static/js/materialize.js:699 - Detected string concatenation with a non-literal variable in a util.format / console.log function. If an attacker injects a format specifier in the string, it w

## Relatorio pip-audit (dependencias)
  - aiohttp==3.5.3 PYSEC-2021-76 (fix: 3.7.4)
  - aiohttp==3.5.3 PYSEC-2024-24 (fix: 3.9.2)
  - aiohttp==3.5.3 PYSEC-2023-120 (fix: 3.8.5)
  - aiohttp==3.5.3 PYSEC-2023-250 (fix: 3.9.0)
  - aiohttp==3.5.3 PYSEC-2023-251 (fix: 3.9.0)
  - aiohttp==3.5.3 PYSEC-2023-246 (fix: 3.8.6)
  - aiohttp==3.5.3 PYSEC-2023-247 (fix: 3.8.0)
  - aiohttp==3.5.3 PYSEC-2024-26 (fix: 3.9.2)
  - aiohttp==3.5.3 PYSEC-2026-1100 (fix: 3.13.3)
  - aiohttp==3.5.3 PYSEC-2026-1101 (fix: 3.13.3)
  - aiohttp==3.5.3 PYSEC-2026-1098 (fix: 3.9.4)
  - aiohttp==3.5.3 PYSEC-2026-1103 (fix: 3.10.11)
  - aiohttp==3.5.3 PYSEC-2026-1102 (fix: 3.9.4)
  - aiohttp==3.5.3 PYSEC-2026-1104 (fix: 3.12.14)
  - aiohttp==3.5.3 PYSEC-2026-1106 (fix: 3.13.3)
  - aiohttp==3.5.3 PYSEC-2026-1107 (fix: 3.13.3)
  - aiohttp==3.5.3 PYSEC-2026-1099 (fix: 3.13.3)
  - aiohttp==3.5.3 PYSEC-2026-1105 (fix: 3.13.3)
  - aiohttp==3.5.3 PYSEC-2026-237 (fix: 3.14.1)
  - aiohttp==3.5.3 PYSEC-2026-1109 (fix: 3.13.3)
  - aiohttp==3.5.3 PYSEC-2026-1097 (fix: 3.13.3)
  - aiohttp==3.5.3 GHSA-p998-jp59-783m (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-hcc4-c3v8-rx92 (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-m5qp-6w8w-w647 (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-pjjw-qhg8-p2p9 (fix: 3.8.6)
  - aiohttp==3.5.3 GHSA-3wq7-rqq7-wx6j (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-mwh4-6h8g-pg8w (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-966j-vmvw-g2g9 (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-63hf-3vf5-4wqf (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-c427-h43c-vf67 (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-w2fm-2cpv-w7v5 (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-2vrm-gr82-f7m5 (fix: 3.13.4)
  - aiohttp==3.5.3 GHSA-jg22-mg44-37j8 (fix: 3.14.0)
  - aiohttp==3.5.3 GHSA-hg6j-4rv6-33pg (fix: 3.14.0)
  - aiohttp==3.5.3 GHSA-4fvr-rgm6-gqmc (fix: 3.14.1)
  - aiohttp==3.5.3 GHSA-2fqr-mr3j-6wp8 (fix: 3.14.1)
  - aiohttp==3.5.3 GHSA-63hw-fmq6-xxg2 (fix: 3.14.1)
  - aiohttp==3.5.3 GHSA-m6qw-4cw2-hm4m (fix: 3.14.0)
  - aiohttp==3.5.3 GHSA-hpj7-wq8m-9hgp (fix: 3.14.1)
  - aiohttp==3.5.3 GHSA-g3cq-j2xw-wf74 (fix: 3.14.1)
  - aiohttp==3.5.3 GHSA-9x8q-7h8h-wcw9 (fix: 3.14.1)
  - aiohttp==3.5.3 GHSA-xcgm-r5h9-7989 (fix: 3.14.1)
  - idna==2.8 PYSEC-2024-60 (fix: 3.7)
  - idna==2.8 PYSEC-2026-215 (fix: 3.15)
  - jinja2==2.10 PYSEC-2021-66 (fix: 2.11.3)
  - jinja2==2.10 PYSEC-2019-217 (fix: 2.10.1)
  - jinja2==2.10 PYSEC-2026-1473 (fix: 3.1.3)
  - jinja2==2.10 PYSEC-2026-1471 (fix: 3.1.6)
  - jinja2==2.10 PYSEC-2026-1474 (fix: 3.1.4)
  - jinja2==2.10 PYSEC-2026-1475 (fix: 3.1.5)
  - pyyaml==3.13 PYSEC-2018-49 (fix: 5.1)
  - pyyaml==3.13 PYSEC-2021-142 (fix: 5.4)

## Relatorio Gitleaks (segredos)
  Nenhum segredo detectado.
