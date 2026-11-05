"""Filtros de detalhe (app/filtros.py): o trecho da pergunta vira o valor exato
do catálogo do dataset. Sem banco: o catálogo é montado à mão, com nomes da
base demo."""

from app.filtros import Catalogo, Item, chaves, descrever, extrair_filtros


def _itens(*nomes):
    return [Item(n, tuple(chaves(n))) for n in nomes]


CAT = Catalogo(
    produto=_itens(
        "Bota couro", "Cinto de couro", "Caixa de som portátil", "Caixa de bombons",
        "Camiseta básica", "Óculos de sol", "Kit skincare", "Kit gourmet", "Carregador rápido",
    ),
    categoria=_itens("Calçados", "Acessórios", "Beleza", "Eletrônicos", "Casa"),
    vendedor=_itens("Fernanda Dias", "Carlos Nunes", "Amanda Rocha"),
    cliente=_itens("Amanda Souza", "Beatriz Souza"),
    canal=["loja", "site", "whatsapp", "marketplace"],
    forma_pagamento=["pix", "cartao_credito", "cartao_debito", "dinheiro", "boleto"],
)


def f(texto, modelo=None):
    return extrair_filtros(texto, CAT, modelo)


def test_plural_e_preposicao_nao_atrapalham():
    assert f("Quantas botas de couro a gente vendeu no ano?") == {"produto": "Bota couro"}


def test_so_o_nucleo_do_nome_basta_quando_e_unico():
    assert f("quanto vendi de bota em 2026")["produto"] == "Bota couro"
    assert f("vendas de óculos em março")["produto"] == "Óculos de sol"


def test_nucleo_repetido_e_ambiguo_e_nao_filtra():
    # "caixa" é de dois produtos e "kit" de vários: melhor não recortar.
    assert "produto" not in f("quanto vendi de caixa em março")
    assert "produto" not in f("quantos kits vendemos")


def test_mais_palavras_desempata():
    assert f("quanto vendi de caixa de som")["produto"] == "Caixa de som portátil"


def test_palavra_secundaria_sozinha_nao_casa():
    # "couro" e "rápido" não são o núcleo de nenhum produto.
    assert "produto" not in f("qual produto de couro vende mais")
    assert "produto" not in f("qual produto sai mais rápido")


def test_categoria():
    assert f("e de calçados?") == {"categoria": "Calçados"}
    assert f("top produtos de eletronicos em 2025") == {"categoria": "Eletrônicos"}


def test_interjeicao_no_inicio_nao_e_categoria():
    assert "categoria" not in f("Beleza, e em 2025?")
    assert f("quanto vendi de beleza")["categoria"] == "Beleza"


def test_vendedor_pelo_primeiro_nome_e_cliente_so_pelo_nome_completo():
    assert f("quanto a Fernanda vendeu em março") == {"vendedor": "Fernanda Dias"}
    # "Amanda" é vendedora e também primeiro nome de cliente: vale a vendedora.
    assert f("e a amanda?") == {"vendedor": "Amanda Rocha"}
    assert f("quanto a cliente Beatriz Souza comprou")["cliente"] == "Beatriz Souza"


def test_canal_e_pagamento_com_sinonimos():
    assert f("vendas pelo zap em março") == {"canal": "whatsapp"}
    assert f("quanto entrou no pix") == {"forma_pagamento": "pix"}
    assert f("vendas no cartão de crédito") == {"forma_pagamento": "cartao_credito"}
    assert f("e no débito?") == {"forma_pagamento": "cartao_debito"}


def test_palavra_comum_so_vale_como_canal_com_pista():
    assert f("quanto vendi na loja em março") == {"canal": "loja"}
    assert "canal" not in f("quanto a loja faturou em março")
    assert "forma_pagamento" not in f("quanto dinheiro entrou em março")
    assert f("vendas em dinheiro") == {"forma_pagamento": "dinheiro"}


def test_trecho_do_modelo_tem_prioridade():
    # O modelo marcou "caixa de som": casa mesmo com "kit" também na frase.
    assert f("caixa de som ou kit", {"PRODUTO": "caixa de som"})["produto"] == "Caixa de som portátil"


def test_frase_sem_detalhe_nao_inventa_filtro():
    assert f("quanto faturei em março de 2024") == {}
    assert f("quais os 5 produtos mais vendidos?") == {}


def test_descricao_para_o_titulo():
    assert descrever({"produto": "Bota couro", "canal": "whatsapp"}) == "Bota couro · canal WhatsApp"
    assert descrever({"forma_pagamento": "pix"}) == "pagamento em Pix"
    assert descrever({"periodo_inicio": "2024-01-01"}) == ""
