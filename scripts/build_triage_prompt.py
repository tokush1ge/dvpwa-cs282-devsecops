#!/usr/bin/env python3
"""Gera o prompt de triagem para o LLM a partir dos relatorios do scan inicial.

Uso:
    python scripts/build_triage_prompt.py artifacts/scan-before > artifacts/prompts/triage-prompt.md

O script le os JSONs de Bandit, Semgrep, pip-audit e Gitleaks, extrai um resumo
compacto de cada ferramenta e monta um prompt de triagem pronto para colar em
qualquer LLM (interface web, modelo local ou API).
"""
import json
import sys
from pathlib import Path


def _load(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null")
    except json.JSONDecodeError:
        return None


def summarize_bandit(data):
    if not data:
        return "  (sem relatorio)"
    results = data.get("results", [])
    if not results:
        return "  Nenhum achado."
    lines = []
    for r in results:
        lines.append(
            f"  - [{r.get('test_id')}] {r.get('issue_severity')}/"
            f"{r.get('issue_confidence')} {r.get('filename')}:"
            f"{r.get('line_number')} - {r.get('issue_text')}"
        )
    return "\n".join(lines)


def summarize_semgrep(data):
    if not data:
        return "  (sem relatorio)"
    results = data.get("results", [])
    if not results:
        return "  Nenhum achado."
    lines = []
    for r in results:
        extra = r.get("extra", {})
        sev = extra.get("severity", "?")
        msg = (extra.get("message", "") or "").strip().replace("\n", " ")
        lines.append(
            f"  - [{r.get('check_id')}] {sev} {r.get('path')}:"
            f"{r.get('start', {}).get('line')} - {msg[:160]}"
        )
    return "\n".join(lines)


def summarize_pip_audit(data):
    if not data:
        return "  (sem relatorio)"
    deps = data.get("dependencies", data) if isinstance(data, dict) else data
    lines = []
    for dep in deps or []:
        for v in dep.get("vulns", []) or []:
            fix = ", ".join(v.get("fix_versions", []) or []) or "sem fix conhecido"
            lines.append(
                f"  - {dep.get('name')}=={dep.get('version')} "
                f"{v.get('id')} (fix: {fix})"
            )
    return "\n".join(lines) if lines else "  Nenhuma dependencia vulneravel."


def summarize_gitleaks(data):
    if data is None:
        return "  (sem relatorio)"
    if not data:
        return "  Nenhum segredo detectado."
    lines = []
    for f in data:
        lines.append(
            f"  - [{f.get('RuleID')}] {f.get('File')}:{f.get('StartLine')} "
            f"- {f.get('Description')}"
        )
    return "\n".join(lines)


TEMPLATE = """# Prompt de triagem - DVPWA

> Gerado automaticamente por `scripts/build_triage_prompt.py` a partir de `{src}`.
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
{bandit}

## Relatorio Semgrep (SAST)
{semgrep}

## Relatorio pip-audit (dependencias)
{pip_audit}

## Relatorio Gitleaks (segredos)
{gitleaks}
"""


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("uso: build_triage_prompt.py <dir-scan-before>\n")
        return 1
    src = Path(sys.argv[1])
    out = TEMPLATE.format(
        src=src,
        bandit=summarize_bandit(_load(src / "bandit.json")),
        semgrep=summarize_semgrep(_load(src / "semgrep.json")),
        pip_audit=summarize_pip_audit(_load(src / "pip-audit.json")),
        gitleaks=summarize_gitleaks(_load(src / "gitleaks.json")),
    )
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
