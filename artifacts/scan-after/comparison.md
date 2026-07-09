# Comparacao scan-before x scan-after

Contagem de achados por ferramenta antes e depois dos patches.

| Ferramenta | Antes | Depois | Delta |
|---|---|---|---|
| Bandit | 2 | 1 | v -1 |
| Semgrep | 7 | 5 | v -2 |
| pip-audit | 52 | 52 | = +0 |
| Gitleaks | 0 | 0 | = +0 |
| **Total** | **61** | **58** | **-3** |

> Interpretacao: uma reducao (delta negativo) indica que achados foram efetivamente corrigidos. Achados que permanecerem devem ser justificados no relatorio final (falso positivo, risco aceito ou fora do escopo das 3 vulnerabilidades tratadas).
