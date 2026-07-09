#!/usr/bin/env bash
# Roda as 4 ferramentas obrigatorias e salva os relatorios JSON no diretorio alvo.
#
# Uso:
#   scripts/run_scans.sh artifacts/scan-before
#   scripts/run_scans.sh artifacts/scan-after
#
# Requer: bandit, semgrep, pip-audit e gitleaks no PATH.
# Os "|| true" garantem que a esteira continue mesmo quando uma ferramenta
# retorna codigo != 0 por ter encontrado achados (comportamento esperado).
set -u

OUT="${1:?uso: run_scans.sh <dir-de-saida>}"
mkdir -p "$OUT"

echo ">> Bandit"
bandit -r sqli -f json -o "$OUT/bandit.json" || true

echo ">> Semgrep"
semgrep scan --config auto --json --output "$OUT/semgrep.json" sqli || true

echo ">> pip-audit"
# --no-deps: audita exatamente os pacotes fixados em requirements.txt sem tentar
# resolver/compilar dependencias nativas (ex.: psycopg2 precisa de pg_config).
pip-audit -r requirements.txt --no-deps -f json -o "$OUT/pip-audit.json" || true

echo ">> Gitleaks"
GITLEAKS_CONFIG_ARG=""
[ -f .gitleaks.toml ] && GITLEAKS_CONFIG_ARG="--config .gitleaks.toml"
gitleaks detect \
  --source . \
  $GITLEAKS_CONFIG_ARG \
  --report-format json \
  --report-path "$OUT/gitleaks.json" \
  --no-git || true

echo ">> Relatorios salvos em $OUT"
