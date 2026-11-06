"""Nome de vendedor -> padrão do ILIKE contra dim_vendedor.nome_norm.

nome_norm é gerado no banco por norm_key(): minúsculas e sem acento. O padrão
montado pela NLU precisa estar na mesma forma, senão "José" nunca casa com
"jose" e a pergunta volta "sem resultado".
"""

from app.nlu.adaptador_modelo import _chave_busca, _resolver_entidades


def _vendedor(texto: str, entidades_modelo: dict | None = None) -> str | None:
    ent = _resolver_entidades("desempenho_vendedor", texto.lower(), entidades_modelo or {}, texto)
    return ent.get("vendedor_nome")


def test_nome_com_acento_vira_chave_sem_acento():
    assert _vendedor("Quanto o José vendeu em 2024?") == "%jose%"
    assert _vendedor("Como foi o desempenho da Fátima em março de 2024?") == "%fatima%"


def test_nome_vindo_do_modelo_tambem_e_normalizado():
    assert _vendedor("desempenho em 2024", {"VENDEDOR": "Antônio"}) == "%antonio%"


def test_nome_sem_acento_continua_igual():
    assert _vendedor("Quanto a vendedora Fernanda vendeu em 2024?") == "%fernanda%"


def test_ranking_sem_nome_lista_todos():
    assert _vendedor("Quem vendeu mais em 2024?") == "%"


def test_chave_tira_curingas_do_ilike():
    assert _chave_busca(" Jo%sé_ ") == "jose"
