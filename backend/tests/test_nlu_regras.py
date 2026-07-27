from app.nlu.regras import RuleBasedNLU


def test_reconhece_faturamento():
    r = RuleBasedNLU().parse("quanto faturei em março")
    assert r.intencao == "total_vendas_periodo"
    assert r.entidades["periodo_inicio"] == "2024-03-01"


def test_fora_de_escopo():
    assert RuleBasedNLU().parse("qual a capital da França").confianca < 0.70


def test_top_produtos_com_limite():
    r = RuleBasedNLU().parse("Quais os 5 produtos mais vendidos?")
    assert r.intencao == "top_produtos"
    assert r.entidades["limite"] == 5


def test_top_produtos_limite_padrao():
    r = RuleBasedNLU().parse("quais os produtos mais vendidos")
    assert r.intencao == "top_produtos"
    assert r.entidades["limite"] == 5


def test_ticket_medio():
    r = RuleBasedNLU().parse("qual o ticket médio em março")
    assert r.intencao == "ticket_medio"
    assert r.entidades["periodo_inicio"] == "2024-03-01"
