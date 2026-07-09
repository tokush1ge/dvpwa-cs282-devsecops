"""Teste de regressao - SQL Injection em Student.create (sqli/dao/student.py).

Exploit original: a query de INSERT era montada por interpolacao de string
(`"... VALUES ('%(name)s')" % {'name': name}`), permitindo que o campo `name`
do formulario de alunos injetasse SQL arbitrario.

Invariante de seguranca verificada: o payload do usuario NUNCA pode aparecer
embutido no texto SQL enviado ao banco; ele deve viajar como parametro vinculado
(bound parameter). Antes do patch o teste FALHA (payload dentro do SQL); depois
do patch ele PASSA (payload vai em `params`, fora do SQL).
"""
import asyncio

from sqli.dao.student import Student

PAYLOAD = "Robert'); DROP TABLE students;--"


class _RecordingCursor:
    """Cursor falso que apenas registra a chamada a execute()."""

    def __init__(self):
        self.query = None
        self.params = "__NAO_CHAMADO__"

    async def execute(self, query, params=None):
        self.query = query
        self.params = params

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _RecordingConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


def test_student_create_uses_bound_parameters():
    cursor = _RecordingCursor()
    conn = _RecordingConn(cursor)

    asyncio.new_event_loop().run_until_complete(
        Student.create(conn, PAYLOAD)
    )

    assert cursor.query is not None, "execute() nao foi chamado"

    # 1) O payload nao pode estar embutido no texto SQL.
    assert "DROP TABLE" not in cursor.query.upper(), (
        "SQL Injection: payload do usuario foi concatenado no SQL:\n"
        f"{cursor.query}"
    )

    # 2) O valor deve ser passado como parametro vinculado, nao interpolado.
    assert cursor.params not in (None, "__NAO_CHAMADO__"), (
        "execute() foi chamado sem parametros vinculados (query nao parametrizada)"
    )
    values = (
        list(cursor.params.values())
        if isinstance(cursor.params, dict)
        else list(cursor.params)
    )
    assert PAYLOAD in values, (
        "O nome deveria ser passado como parametro vinculado contendo o payload cru"
    )
