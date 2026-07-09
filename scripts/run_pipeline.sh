#!/usr/bin/env bash
# Orquestrador local da esteira (equivalente ao .gitlab-ci.yml, para rodar na maquina).
#
# Etapas:
#   before   -> roda os 4 scanners em artifacts/scan-before + gera triage-prompt
#   tests    -> roda os testes de regressao de seguranca (pytest)
#   after    -> roda os 4 scanners em artifacts/scan-after + gera comparison.md
#   all      -> before + tests + after
#
# Uso: scripts/run_pipeline.sh [before|tests|after|all]
set -u
STAGE="${1:-all}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

run_before() {
  echo "=== STAGE: scan-before ==="
  scripts/run_scans.sh artifacts/scan-before
  mkdir -p artifacts/prompts
  python scripts/build_triage_prompt.py artifacts/scan-before \
    > artifacts/prompts/triage-prompt.md
  echo ">> triage-prompt.md atualizado"
}

run_tests() {
  echo "=== STAGE: testes de regressao ==="
  pytest -v tests/security || true
}

run_after() {
  echo "=== STAGE: scan-after ==="
  scripts/run_scans.sh artifacts/scan-after
  python scripts/compare_scans.py artifacts/scan-before artifacts/scan-after \
    > artifacts/scan-after/comparison.md
  echo ">> comparison.md atualizado"
}

case "$STAGE" in
  before) run_before ;;
  tests)  run_tests ;;
  after)  run_after ;;
  all)    run_before; run_tests; run_after ;;
  *) echo "uso: run_pipeline.sh [before|tests|after|all]"; exit 1 ;;
esac
