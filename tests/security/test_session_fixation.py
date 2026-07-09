"""Teste de regressao - Session Fixation no login (sqli/views.py :: index).

Exploit original: ao autenticar, o handler fazia `session['user_id'] = user.id`
mantendo o MESMO identificador de sessao de antes do login. Um atacante que
fixasse o cookie de sessao da vitima (ex.: via cookie pre-definido) passava a
compartilhar a sessao autenticada.

Este teste dirige o fluxo real de login usando o servidor de teste do aiohttp,
com um storage de sessao em memoria (sem Redis) e um banco falso que devolve o
usuario `superadmin`. Verifica a invariante: o identificador de sessao APOS o
login deve ser diferente do identificador conhecido ANTES do login.

Antes do patch o teste FALHA (mesmo id de sessao); depois do patch ele PASSA
(sessao regenerada com novo id).
"""
import asyncio
import uuid
from hashlib import md5

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from aiohttp_session import AbstractStorage, Session, session_middleware

from sqli import views

USERNAME = "superadmin"
PASSWORD = "superadmin"

# Ordem das colunas em User.from_raw:
# (id, first_name, middle_name, last_name, username, pwd_hash, is_admin)
USER_ROW = (1, "Super", None, "Admin", USERNAME, md5(PASSWORD.encode()).hexdigest(), True)


# ---- Storage de sessao em memoria (espelha o comportamento do RedisStorage) ----
class MemoryStorage(AbstractStorage):
    def __init__(self):
        super().__init__(cookie_name="SID")
        self._store = {}

    async def load_session(self, request):
        cookie = self.load_cookie(request)
        if cookie is None:
            return Session(None, data=None, new=True, max_age=self.max_age)
        key = str(cookie)
        stored = self._store.get(key)
        if stored is None:
            return Session(None, data=None, new=True, max_age=self.max_age)
        return Session(key, data=stored, new=False, max_age=self.max_age)

    async def save_session(self, request, response, session):
        key = session.identity
        if key is None:
            key = uuid.uuid4().hex
            self.save_cookie(response, key, max_age=session.max_age)
        else:
            if session.empty:
                self.save_cookie(response, "", max_age=session.max_age)
            else:
                key = str(key)
                self.save_cookie(response, key, max_age=session.max_age)
        self._store[key] = self._get_session_data(session)


# ---- Banco falso: responde as duas queries de sqli.dao.user.User ----
class _FakeCursor:
    def __init__(self):
        self._row = None

    async def execute(self, query, params=None):
        q = " ".join(query.split()).lower()
        if "from users where username" in q:
            self._row = USER_ROW if params and params[0] == USERNAME else None
        elif "from users where id" in q:
            self._row = USER_ROW if params and params[0] == 1 else None
        else:
            self._row = None

    async def fetchone(self):
        return self._row

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeConn:
    def cursor(self):
        return _FakeCursor()


class _FakeAcquire:
    async def __aenter__(self):
        return _FakeConn()

    async def __aexit__(self, *exc):
        return False


class _FakeDB:
    def acquire(self):
        return _FakeAcquire()


async def _login_handler(request):
    # Executa a funcao index REAL (sem o decorator de template) e devolve uma
    # resposta simples; o middleware de sessao anexa o cookie a esta resposta.
    await views.index.__wrapped__(request)
    return web.Response(text="ok")


def _build_app():
    app = web.Application(middlewares=[session_middleware(MemoryStorage())])
    app["db"] = _FakeDB()
    app.router.add_get("/", _login_handler)
    app.router.add_post("/", _login_handler)
    return app


async def _scenario():
    app = _build_app()
    jar = aiohttp.CookieJar(unsafe=True)  # aceita cookies em host 127.0.0.1
    async with TestClient(TestServer(app), cookie_jar=jar) as client:
        # 1) Sessao anonima estabelecida (id que um atacante poderia fixar).
        r1 = await client.get("/")
        assert "SID" in r1.cookies, "sessao anonima nao recebeu cookie SID"
        id_before = r1.cookies["SID"].value

        # 2) Login com credenciais validas usando a MESMA sessao.
        r2 = await client.post(
            "/", data={"username": USERNAME, "password": PASSWORD}
        )
        assert "SID" in r2.cookies, "login nao emitiu cookie de sessao"
        id_after = r2.cookies["SID"].value
        return id_before, id_after


def test_session_id_is_regenerated_on_login():
    id_before, id_after = asyncio.new_event_loop().run_until_complete(_scenario())
    assert id_after != id_before, (
        "Session Fixation: o id de sessao apos o login e o mesmo de antes "
        f"({id_before}); a sessao deveria ser regenerada no login."
    )
