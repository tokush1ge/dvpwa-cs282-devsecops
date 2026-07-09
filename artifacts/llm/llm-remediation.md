# Remediacao assistida por LLM - DVPWA

> **Papel:** engenheiro de seguranca de software.
> **Entrada:** triagem (`llm-triage.md`) + trechos de codigo do DVPWA.
> Os patches abaixo foram **revisados e aplicados manualmente** pelo grupo
> (branch `fix/security-remediation`), conforme exige a trilha basica.

---

## Vulnerabilidade 1 - SQL Injection (`sqli/dao/student.py`)

**Causa raiz.** `Student.create` monta o comando SQL por interpolacao de string
Python:

```python
q = ("INSERT INTO students (name) "
     "VALUES ('%(name)s')" % {'name': name})
await cur.execute(q)
```

O valor de `name` (campo do formulario de alunos) e concatenado diretamente no
texto SQL. Um `name` como `Robert'); DROP TABLE students;--` altera a estrutura
do comando.

**Patch proposto (parametrizacao).**

```python
q = 'INSERT INTO students (name) VALUES (%(name)s)'
params = {'name': name}
async with conn.cursor() as cur:
    await cur.execute(q, params)
```

O driver (`aiopg`/`psycopg2`) passa a tratar `name` como parametro vinculado,
nunca como parte da instrucao. E o mesmo padrao ja usado nos demais DAOs
(`review.py`, `course.py`, `mark.py`).

**Testes funcionais que devem continuar passando.** Cadastro de aluno pelo form
(`POST /students/`) continua criando o aluno normalmente.

**Teste de regressao.** `tests/security/test_sqli_student_create.py`: injeta um
payload no `name` e verifica que ele **nao** aparece no texto SQL e que viaja como
parametro vinculado.

**Como confirmar no segundo scan.** Bandit `B608` e os alertas Semgrep de SQL em
`student.py` devem desaparecer no `scan-after`.

---

## Vulnerabilidade 2 - Stored XSS (`sqli/app.py`)

**Causa raiz.** O ambiente Jinja2 e configurado com autoescape desligado:

```python
setup_jinja(app, loader=PackageLoader('sqli', 'templates'),
            context_processors=[...],
            autoescape=False)
```

Templates como `course.jinja2` renderizam `{{ review.review_text }}` sem escape.
Uma review contendo `<script>alert(document.cookie)</script>` e armazenada no
banco e executada no navegador de quem visualiza o curso (Stored XSS).

**Patch proposto (habilitar autoescape).**

```python
setup_jinja(app, loader=PackageLoader('sqli', 'templates'),
            context_processors=[...],
            autoescape=True)
```

Com autoescape ligado, o Jinja2 escapa `<`, `>`, `&`, `"` por padrao. Os
templates que usam o filtro `| e` explicitamente continuam corretos (o filtro e
idempotente sobre valores ja escapados). Onde HTML confiavel precisar ser
renderizado, usa-se `| safe` de forma seletiva - nenhum caso desse tipo existe no
fluxo de reviews.

**Testes funcionais que devem continuar passando.** Todas as paginas continuam
renderizando; nomes de curso/aluno com caracteres normais aparecem intactos.

**Teste de regressao.** `tests/security/test_xss_autoescape.py`: renderiza um
payload pelo ambiente Jinja2 real do app e verifica que ele sai escapado
(`&lt;script&gt;`), nao como `<script>`.

**Como confirmar no segundo scan.** As ferramentas de SAST padrao nao sinalizam
esse defeito de configuracao; a confirmacao vem do **teste de regressao** e da
inspecao do template renderizado (justificativa tecnica prevista na secao 9 do
enunciado).

---

## Vulnerabilidade 3 - Session Fixation (`sqli/views.py::index`)

**Causa raiz.** No login bem-sucedido, o handler grava o usuario na **mesma**
sessao anonima, sem regenerar o identificador:

```python
if user and user.check_password(password):
    session['user_id'] = user.id
    auth_user = user
```

Se um atacante fixar previamente o cookie de sessao da vitima, esse mesmo
identificador se torna autenticado apos o login (Session Fixation).

**Patch proposto (regenerar a sessao no login).**

```python
from aiohttp_session import new_session
...
if user and user.check_password(password):
    session = await new_session(request)   # id de sessao novo
    session['user_id'] = user.id
    auth_user = user
```

`new_session` descarta a sessao anterior e cria uma nova com identificador
proprio, invalidando qualquer id fixado antes do login.

**Testes funcionais que devem continuar passando.** Login e logout continuam
funcionando; apos autenticar, a navegacao autenticada permanece valida.

**Teste de regressao.** `tests/security/test_session_fixation.py`: estabelece uma
sessao anonima, faz login e verifica que o identificador de sessao **muda** apos
o login.

**Como confirmar no segundo scan.** Assim como o XSS, e uma falha de logica nao
coberta pelo SAST padrao; a confirmacao vem do teste de regressao (id de sessao
regenerado).

---

## Resumo

| Vulnerabilidade | Arquivo | Patch | Validacao |
|---|---|---|---|
| SQL Injection | sqli/dao/student.py | Query parametrizada | Regressao + queda de B608/Semgrep |
| Stored XSS | sqli/app.py | `autoescape=True` | Regressao (payload escapado) |
| Session Fixation | sqli/views.py | `new_session` no login | Regressao (id muda) |
