#!/usr/bin/env python3
"""Compara os relatorios de scan-before e scan-after e gera comparison.md.

Uso:
    python scripts/compare_scans.py artifacts/scan-before artifacts/scan-after > artifacts/scan-after/comparison.md
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


def count_bandit(data):
    return len((data or {}).get("results", [])) if data else 0


def count_semgrep(data):
    return len((data or {}).get("results", [])) if data else 0


def count_pip_audit(data):
    if not data:
        return 0
    deps = data.get("dependencies", data) if isinstance(data, dict) else data
    return sum(len(d.get("vulns", []) or []) for d in (deps or []))


def count_gitleaks(data):
    return len(data) if isinstance(data, list) else 0


TOOLS = [
    ("Bandit", "bandit.json", count_bandit),
    ("Semgrep", "semgrep.json", count_semgrep),
    ("pip-audit", "pip-audit.json", count_pip_audit),
    ("Gitleaks", "gitleaks.json", count_gitleaks),
]


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("uso: compare_scans.py <scan-before> <scan-after>\n")
        return 1
    before = Path(sys.argv[1])
    after = Path(sys.argv[2])

    print("# Comparacao scan-before x scan-after\n")
    print("Contagem de achados por ferramenta antes e depois dos patches.\n")
    print("| Ferramenta | Antes | Depois | Delta |")
    print("|---|---|---|---|")

    total_before = total_after = 0
    for name, fname, counter in TOOLS:
        b = counter(_load(before / fname))
        a = counter(_load(after / fname))
        total_before += b
        total_after += a
        delta = a - b
        arrow = "v" if delta < 0 else ("^" if delta > 0 else "=")
        print(f"| {name} | {b} | {a} | {arrow} {delta:+d} |")

    print(f"| **Total** | **{total_before}** | **{total_after}** | "
          f"**{total_after - total_before:+d}** |")
    print()
    print("> Interpretacao: uma reducao (delta negativo) indica que achados "
          "foram efetivamente corrigidos. Achados que permanecerem devem ser "
          "justificados no relatorio final (falso positivo, risco aceito ou "
          "fora do escopo das 3 vulnerabilidades tratadas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
