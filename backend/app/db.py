import os
import threading

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv()

# ---------------------------------------------------------------------------
# Pool de conexões
#
# Antes, cada pergunta abria uma conexão nova com o Supabase. Medido nas 100
# perguntas em produção (docs/avaliacao-100-perguntas.md, seção 3.3), só
# abrir a conexão custava ~1,1 s por requisição no Render: cada conexão nova
# repete TCP + TLS + autenticação até o banco de prod (us-west-2, Oregon). O
# pool abre a conexão uma vez e a reaproveita.
#
# prepare_threshold=None é OBRIGATÓRIO aqui: o Transaction pooler do Supabase
# (porta 6543) não mantém prepared statements entre transações. Com conexão
# reaproveitada, o psycopg passaria a preparar consultas repetidas (a partir
# da 5ª execução) e o banco responderia "prepared statement ... does not
# exist". Com uma conexão por requisição isso nunca aparecia; com o pool,
# aparece já na 5ª pergunta igual.
# ---------------------------------------------------------------------------

_pool: ConnectionPool | None = None
_trava = threading.Lock()


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL nao definida. Copie backend/.env.example para "
            "backend/.env e preencha com a connection string do Supabase."
        )
    return url


def get_pool() -> ConnectionPool:
    """Cria o pool na primeira chamada (preguiçoso), para que importar o app
    sem DATABASE_URL -- como no CI -- continue funcionando."""
    global _pool
    if _pool is None:
        with _trava:
            if _pool is None:
                _pool = ConnectionPool(
                    conninfo=_database_url(),
                    min_size=1,
                    max_size=int(os.environ.get("DB_POOL_MAX", "4")),
                    kwargs={"prepare_threshold": None},
                    # testa a conexão antes de entregar: o Supavisor e o
                    # "sono" do Render podem derrubar conexões ociosas
                    check=ConnectionPool.check_connection,
                    # sem isto, com o banco fora do ar a requisição esperaria
                    # 30 s (padrão) antes do fallback "banco_indisponivel"
                    timeout=float(os.environ.get("DB_POOL_TIMEOUT", "10")),
                    max_idle=300,
                    open=True,
                )
    return _pool


def get_connection():
    """Uso igual ao de antes: `with get_connection() as conn: ...`.

    Ao sair do `with`, a conexão volta para o pool (com commit se não houve
    erro, rollback se houve), em vez de ser fechada. Se o pool não conseguir
    entregar uma conexão a tempo, levanta PoolTimeout, que é subclasse de
    psycopg.OperationalError -- o mesmo tipo tratado como banco fora do ar.
    """
    return get_pool().connection()


def declarar_empresa(conn, empresa_id: str) -> None:
    """Diz ao banco de qual empresa é esta transação (C14, migration 006).

    As políticas de RLS só deixam o usuário da aplicação (intellix_app) ver e
    gravar linhas com esse empresa_id. O terceiro argumento `true` faz a
    declaração valer só até o fim da transação atual: é o que funciona no
    Transaction pooler do Supabase (porta 6543), onde a conexão física pode
    mudar entre uma transação e outra. Por isso tudo o que a requisição faz
    no banco precisa acontecer dentro do mesmo `with get_connection()`.

    Conectado como `postgres` (dono das tabelas), o RLS não se aplica e esta
    chamada é inofensiva: o código funciona antes e depois da troca de usuário.
    """
    conn.execute("select set_config('app.empresa_id', %s, true)", (str(empresa_id),))


def fechar_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_empresa_id() -> str:
    # MVP de tenant unico: sem autenticacao ainda, a empresa vem de config.
    # Quando houver login (fora do escopo do TCC por ora), isso passa a vir
    # do usuario autenticado em vez de uma env var fixa.
    empresa_id = os.environ.get("EMPRESA_ID")
    if not empresa_id:
        raise RuntimeError("EMPRESA_ID nao definida em backend/.env")
    return empresa_id
