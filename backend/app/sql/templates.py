"""Lista fixa de consultas prontas (secao 7.7 do TCC: "geracao restrita a
templates parametrizados"). A pergunta do usuario nunca vira SQL: o NLU so
escolhe qual chave deste dicionario usar e preenche os %(...)s, que o
psycopg parametriza -- nunca f-string/concatenacao.

Nomes de tabela/coluna assumem o desenho de database/001_schema.sql
(fato_item_venda, dim_data, dim_produto). Ajustar aqui se o schema final
divergir.
"""

TEMPLATES: dict[str, dict] = {
    "total_vendas_periodo": {
        "sql": """
            select to_char(d.data, 'YYYY-MM') as periodo,
                   sum(f.valor_total) as faturamento
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
            group by 1
            order by 1
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim"],
        "titulo": "Faturamento no período",
        "visual": "numero",
    },
    "top_produtos": {
        "sql": """
            select p.nome as produto,
                   sum(f.quantidade) as quantidade,
                   sum(f.valor_total) as faturamento
            from fato_item_venda f
            join dim_produto p on p.id = f.produto_id
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
            group by p.nome
            order by faturamento desc
            limit %(limite)s
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim", "limite"],
        "titulo": "Produtos mais vendidos",
        "visual": "barra",
    },
    "ticket_medio": {
        "sql": """
            select avg(f.valor_total) as ticket_medio
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim"],
        "titulo": "Ticket médio",
        "visual": "numero",
    },
}
