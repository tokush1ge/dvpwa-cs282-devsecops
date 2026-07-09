"""Teste de regressao - Stored XSS via autoescape do Jinja2 (sqli/app.py).

Exploit original: o ambiente Jinja2 da aplicacao era configurado com
`autoescape=False`. Templates como course.jinja2 renderizam `{{ review.review_text }}`
sem escape, entao uma review contendo `<script>...</script>` era refletida crua
no HTML (Stored XSS).

Este teste constroi o app REAL via sqli.app.init(), obtem o ambiente Jinja2
efetivamente usado e renderiza um payload. Antes do patch o teste FALHA (script
cru no output); depois do patch ele PASSA (payload escapado como &lt;script&gt;).
"""
from pathlib import Path

import aiohttp_jinja2

from sqli.app import init as init_app

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = str(REPO_ROOT / "config" / "dev.yaml")

PAYLOAD = "<script>alert('xss')</script>"


def _render_review(text: str) -> str:
    # init() apenas registra handlers de startup para db/redis (nao conecta),
    # entao e seguro construir o app sem infraestrutura.
    app = init_app(["-c", CONFIG])
    env = aiohttp_jinja2.get_env(app)
    # Reproduz o uso real do template: variavel de review interpolada no HTML.
    template = env.from_string("<li>{{ review_text }}</li>")
    return template.render(review_text=text)


def test_review_text_is_html_escaped():
    output = _render_review(PAYLOAD)

    assert "<script>" not in output, (
        "Stored XSS: review_text foi renderizado sem escape (autoescape desligado):\n"
        f"{output}"
    )
    assert "&lt;script&gt;" in output, (
        "O payload deveria aparecer escapado no HTML (autoescape habilitado)"
    )
