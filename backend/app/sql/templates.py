"""Lista fixa de consultas prontas (secao 7.7 do TCC: "geracao restrita a
templates parametrizados"). A pergunta do usuario nunca vira SQL: o NLU so
escolhe qual chave deste dicionario usar e preenche os %(...)s, que o
psycopg parametriza -- nunca f-string/concatenacao.

Nomes de tabela/coluna conferidos contra o schema real do Supabase (B7/B8).
As 12 chaves batem com as 12 intencoes definidas em `ia training/moldes.py`.

Convencao para parametros `*_nome` (busca por nome, ex.: vendedor_nome): quem
monta `entidades` (NLU) e responsavel por já vir com os `%` do ILIKE, ex.:
`"%fernanda%"` -- o template so usa `ilike %(vendedor_nome)s` direto.
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
    "quantidade_vendas": {
        "sql": """
            select to_char(d.data, 'YYYY-MM') as periodo,
                   count(distinct f.venda_id) as quantidade_vendas
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
            group by 1
            order by 1
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim"],
        "titulo": "Quantidade de vendas no período",
        "visual": "numero",
    },
    "top_clientes": {
        "sql": """
            select c.nome as cliente,
                   sum(f.valor_total) as faturamento
            from fato_item_venda f
            join dim_cliente c on c.id = f.cliente_id
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
            group by c.nome
            order by faturamento desc
            limit %(limite)s
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim", "limite"],
        "titulo": "Clientes que mais compraram",
        "visual": "barra",
    },
    "desempenho_vendedor": {
        "sql": """
            select v.nome as vendedor,
                   sum(f.valor_total) as faturamento,
                   count(distinct f.venda_id) as quantidade_vendas
            from fato_item_venda f
            join dim_vendedor v on v.id = f.vendedor_id
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
              and v.nome_norm ilike %(vendedor_nome)s
            group by v.nome
            order by faturamento desc
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim", "vendedor_nome"],
        "titulo": "Desempenho do vendedor",
        "visual": "tabela",
    },
    "produtos_sem_saida": {
        "sql": """
            select p.nome as produto,
                   p.categoria as categoria
            from dim_produto p
            where p.empresa_id = %(empresa_id)s
              and not exists (
                  select 1
                  from fato_item_venda f
                  join dim_data d on d.id = f.data_id
                  where f.produto_id = p.id
                    and d.data between %(periodo_inicio)s and %(periodo_fim)s
              )
            order by p.nome
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim"],
        "titulo": "Produtos sem saída no período",
        "visual": "tabela",
    },
    "comparacao_periodos": {
        "sql": """
            select 'periodo_a' as periodo,
                   coalesce(sum(f.valor_total), 0) as faturamento
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_a_inicio)s and %(periodo_a_fim)s
            union all
            select 'periodo_b' as periodo,
                   coalesce(sum(f.valor_total), 0) as faturamento
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_b_inicio)s and %(periodo_b_fim)s
        """,
        "obrigatorios": ["periodo_a_inicio", "periodo_a_fim", "periodo_b_inicio", "periodo_b_fim"],
        "titulo": "Comparação entre períodos",
        "visual": "barra",
    },
    "variacao_periodo": {
        "sql": """
            with atual as (
                select coalesce(sum(f.valor_total), 0) as total
                from fato_item_venda f
                join dim_data d on d.id = f.data_id
                where f.empresa_id = %(empresa_id)s
                  and d.data between %(periodo_atual_inicio)s and %(periodo_atual_fim)s
            ),
            anterior as (
                select coalesce(sum(f.valor_total), 0) as total
                from fato_item_venda f
                join dim_data d on d.id = f.data_id
                where f.empresa_id = %(empresa_id)s
                  and d.data between %(periodo_anterior_inicio)s and %(periodo_anterior_fim)s
            )
            select atual.total as periodo_atual,
                   anterior.total as periodo_anterior,
                   round((atual.total - anterior.total) / nullif(anterior.total, 0) * 100, 2) as variacao_percentual
            from atual, anterior
        """,
        "obrigatorios": [
            "periodo_atual_inicio",
            "periodo_atual_fim",
            "periodo_anterior_inicio",
            "periodo_anterior_fim",
        ],
        "titulo": "Variação entre períodos",
        "visual": "numero",
    },
    "vendas_por_canal": {
        "sql": """
            select f.canal as canal,
                   sum(f.valor_total) as faturamento,
                   count(distinct f.venda_id) as quantidade_vendas
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
            group by f.canal
            order by faturamento desc
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim"],
        "titulo": "Vendas por canal",
        "visual": "barra",
    },
    "vendas_por_categoria": {
        "sql": """
            select p.categoria as categoria,
                   sum(f.valor_total) as faturamento
            from fato_item_venda f
            join dim_produto p on p.id = f.produto_id
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
            group by p.categoria
            order by faturamento desc
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim"],
        "titulo": "Vendas por categoria",
        "visual": "barra",
    },
    "vendas_por_pagamento": {
        "sql": """
            select f.forma_pagamento as forma_pagamento,
                   sum(f.valor_total) as faturamento,
                   count(distinct f.venda_id) as quantidade_vendas
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data between %(periodo_inicio)s and %(periodo_fim)s
            group by f.forma_pagamento
            order by faturamento desc
        """,
        "obrigatorios": ["periodo_inicio", "periodo_fim"],
        "titulo": "Vendas por forma de pagamento",
        "visual": "barra",
    },
}
