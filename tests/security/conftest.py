"""Configuracao dos testes de regressao de seguranca.

Estes testes exercitam o codigo REAL do DVPWA (sqli.*) sem precisar de
PostgreSQL, Redis ou Docker. Para isso, substituimos por stubs em `sys.modules`
apenas os modulos que exigem infraestrutura nativa (aiopg, aioredis e o backend
Redis do aiohttp_session). Nenhum modulo do proprio DVPWA e alterado.
"""
import sys
import types
from pathlib import Path

# 1) Torna o pacote `sqli` importavel (raiz do repositorio no sys.path).
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# 2) Stub de aiopg / aiopg.connection (usados apenas como type hint no DVPWA).
class _Connection:  # pragma: no cover - placeholder de tipo
    pass


_aiopg = types.ModuleType("aiopg")
_aiopg.Connection = _Connection
_aiopg_connection = types.ModuleType("aiopg.connection")
_aiopg_connection.Connection = _Connection
_aiopg.connection = _aiopg_connection


async def _create_pool(*a, **k):  # pragma: no cover - nunca chamado nos testes
    raise RuntimeError("aiopg stub: create_pool nao deve ser usado em testes")


_aiopg.create_pool = _create_pool
sys.modules.setdefault("aiopg", _aiopg)
sys.modules.setdefault("aiopg.connection", _aiopg_connection)


# 3) Stub de aioredis (importado por sqli.services.redis).
_aioredis = types.ModuleType("aioredis")


async def _create_redis_pool(*a, **k):  # pragma: no cover
    raise RuntimeError("aioredis stub: nao deve ser usado em testes")


_aioredis.create_pool = _create_redis_pool
sys.modules.setdefault("aioredis", _aioredis)


# 4) Stub do backend Redis do aiohttp_session (importado por sqli.middlewares).
#    Importamos o pacote real primeiro e apenas substituimos o submodulo redis.
import aiohttp_session  # noqa: E402

_redis_storage = types.ModuleType("aiohttp_session.redis_storage")


class RedisStorage:  # pragma: no cover - placeholder, sessao real usa storage de teste
    def __init__(self, *a, **k):
        pass


_redis_storage.RedisStorage = RedisStorage
sys.modules.setdefault("aiohttp_session.redis_storage", _redis_storage)
setattr(aiohttp_session, "redis_storage", _redis_storage)
