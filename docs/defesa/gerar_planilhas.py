"""Uso: python docs/defesa/gerar_planilhas.py docs/defesa

Gera as duas planilhas fictícias da demonstração ao vivo da defesa.

Aba 1 "Vendas": no formato do template oficial (é a única que o Intellix lê).
Aba 2 "Conferência": fórmulas do próprio Excel que recalculam, a partir da aba
Vendas, os números que o Intellix deve responder (gabarito independente).
"""
import sys
from datetime import date

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

SAIDA = sys.argv[1]

CAB = ["id_venda", "data_venda", "produto", "categoria", "cliente", "vendedor",
       "canal", "forma_pagamento", "quantidade", "valor_unitario", "desconto", "valor_total"]

D = date
# (id, data, produto, categoria, cliente, vendedor, canal, pagamento, qtd, unit, desc)
EMPRESA_A = [
    # setembro/2026: 4 vendas, R$ 800
    ("A-101", D(2026, 9, 5), "Calça jeans", "Vestuário", "Carla Mendes", "Bruna", "loja", "pix", 1, 150, 0),
    ("A-101", D(2026, 9, 5), "Camiseta básica", "Vestuário", "Carla Mendes", "Bruna", "loja", "pix", 1, 50, 0),
    ("A-102", D(2026, 9, 12), "Jaqueta", "Vestuário", "Rafael Lima", "Diego", "site", "cartao_credito", 1, 250, 0),
    ("A-103", D(2026, 9, 18), "Tênis casual", "Calçados", "Paula Nunes", "Bruna", "loja", "cartao_debito", 1, 220, 0),
    ("A-103", D(2026, 9, 18), "Boné", "Acessórios", "Paula Nunes", "Bruna", "loja", "cartao_debito", 2, 40, 0),
    ("A-104", D(2026, 9, 26), "Camiseta básica", "Vestuário", "Jorge Alves", "Diego", "whatsapp", "pix", 1, 50, 0),
    # outubro/2026: 5 vendas, R$ 1.000
    ("A-201", D(2026, 10, 3), "Tênis casual", "Calçados", "Carla Mendes", "Bruna", "loja", "pix", 1, 220, 0),
    ("A-201", D(2026, 10, 3), "Boné", "Acessórios", "Carla Mendes", "Bruna", "loja", "pix", 2, 40, 0),
    ("A-202", D(2026, 10, 8), "Calça jeans", "Vestuário", "Rafael Lima", "Diego", "whatsapp", "pix", 1, 150, 0),
    ("A-202", D(2026, 10, 8), "Camiseta básica", "Vestuário", "Rafael Lima", "Diego", "whatsapp", "pix", 1, 50, 0),
    # A-203: o MESMO produto em duas linhas da mesma venda (teste de grão: vira 1 item com 4 un.)
    ("A-203", D(2026, 10, 15), "Camiseta básica", "Vestuário", "Paula Nunes", "Bruna", "loja", "dinheiro", 2, 50, 0),
    ("A-203", D(2026, 10, 15), "Camiseta básica", "Vestuário", "Paula Nunes", "Bruna", "loja", "dinheiro", 2, 50, 0),
    # A-204: com desconto
    ("A-204", D(2026, 10, 22), "Jaqueta", "Vestuário", "Jorge Alves", "Diego", "site", "cartao_credito", 1, 250, 50),
    ("A-205", D(2026, 10, 29), "Camiseta básica", "Vestuário", "Lívia Rocha", "Bruna", "loja", "cartao_debito", 2, 50, 0),
]

EMPRESA_B = [
    # setembro/2026: 3 vendas, R$ 450
    ("B-01", D(2026, 9, 10), "Mochila escolar", "Mochilas", "Sônia Prado", "Lucas", "loja", "pix", 1, 120, 0),
    ("B-01", D(2026, 9, 10), "Caderno universitário", "Cadernos", "Sônia Prado", "Lucas", "loja", "pix", 1, 30, 0),
    ("B-02", D(2026, 9, 20), "Caderno universitário", "Cadernos", "Tiago Reis", "Marina", "site", "cartao_credito", 5, 30, 0),
    ("B-03", D(2026, 9, 27), "Estojo", "Material escolar", "Helena Costa", "Lucas", "loja", "dinheiro", 3, 30, 0),
    ("B-03", D(2026, 9, 27), "Caneta gel", "Material escolar", "Helena Costa", "Lucas", "loja", "dinheiro", 3, 20, 0),
    # outubro/2026: 4 vendas, R$ 600
    ("B-11", D(2026, 10, 2), "Mochila escolar", "Mochilas", "Sônia Prado", "Lucas", "loja", "pix", 1, 120, 0),
    ("B-11", D(2026, 10, 2), "Caderno universitário", "Cadernos", "Sônia Prado", "Lucas", "loja", "pix", 2, 30, 0),
    ("B-12", D(2026, 10, 9), "Caderno universitário", "Cadernos", "Tiago Reis", "Marina", "site", "cartao_credito", 3, 30, 0),
    ("B-12", D(2026, 10, 9), "Caneta gel", "Material escolar", "Tiago Reis", "Marina", "site", "cartao_credito", 3, 20, 0),
    ("B-13", D(2026, 10, 16), "Mochila escolar", "Mochilas", "Helena Costa", "Lucas", "loja", "dinheiro", 1, 120, 0),
    ("B-13", D(2026, 10, 16), "Estojo", "Material escolar", "Helena Costa", "Lucas", "loja", "dinheiro", 1, 30, 0),
    ("B-14", D(2026, 10, 23), "Caderno universitário", "Cadernos", "Igor Batista", "Marina", "whatsapp", "pix", 4, 30, 0),
    # linha inválida de propósito: sem data -> o Intellix deve REJEITAR só ela e dizer o motivo
    ("B-15", None, "Caneta gel", "Material escolar", "Igor Batista", "Marina", "loja", "pix", 1, 20, 0),
]

FONTE = "Arial"
F = Font(name=FONTE, size=10)
FB = Font(name=FONTE, size=10, bold=True)
FCAB = Font(name=FONTE, size=10, bold=True, color="FFFFFF")
FILL_CAB = PatternFill("solid", fgColor="1F3A5F")
FILL_ERRO = PatternFill("solid", fgColor="FDE2E1")
FILL_GRAO = PatternFill("solid", fgColor="FFF4D6")
FILL_SEC = PatternFill("solid", fgColor="E8EEF6")
FINO = Side(style="thin", color="C9D3E0")
BORDA = Border(top=FINO, bottom=FINO, left=FINO, right=FINO)
MOEDA = '"R$" #,##0.00'


def aba_vendas(ws, linhas, destaques):
    ws.title = "Vendas"
    ws.append(CAB)
    for c in ws[1]:
        c.font, c.fill, c.alignment = FCAB, FILL_CAB, Alignment(horizontal="center")
    for i, (vid, d, prod, cat, cli, vend, canal, pag, q, u, desc) in enumerate(linhas, start=2):
        total = q * u - desc
        ws.append([vid, d, prod, cat, cli, vend, canal, pag, q, u, desc, total])
        ws.cell(i, 2).number_format = "dd/mm/yyyy"
        for col in (10, 11, 12):
            ws.cell(i, col).number_format = MOEDA
        for c in ws[i]:
            c.font, c.border = F, BORDA
        if vid in destaques:
            for c in ws[i]:
                c.fill = destaques[vid][0]
            ws.cell(i, 1).comment = Comment(destaques[vid][1], "Intellix")
    larg = [10, 12, 22, 17, 15, 11, 11, 16, 11, 14, 11, 13]
    for idx, w in enumerate(larg, start=1):
        ws.column_dimensions[ws.cell(1, idx).column_letter].width = w
    ws.freeze_panes = "A2"
    return len(linhas) + 1  # última linha de dados


def aba_conferencia(wb, ultima, nome, produtos, vendedores, canais):
    ws = wb.create_sheet("Conferência")
    rng = lambda col: f"Vendas!${col}$2:${col}${ultima}"  # noqa: E731
    A, B, C, F_, G, L = (rng(c) for c in "ABCFGL")
    ws["A1"] = f"Conferência manual — {nome} (dados fictícios)"
    ws["A1"].font = Font(name=FONTE, size=12, bold=True)
    ws["A2"] = ("Fórmulas do Excel calculadas direto da aba Vendas. O Intellix lê só a aba "
                "Vendas; esta aba serve para a banca conferir os números respondidos.")
    ws["A2"].font = Font(name=FONTE, size=9, italic=True)
    ws["A4"], ws["B4"], ws["C4"] = "Indicador", "Setembro/2026", "Outubro/2026"
    for c in ws[4][:3]:
        c.font, c.fill = FCAB, FILL_CAB
    ws["A5"], ws["B5"], ws["C5"] = "Início do mês", D(2026, 9, 1), D(2026, 10, 1)
    ws["A6"], ws["B6"], ws["C6"] = "Fim do mês", D(2026, 9, 30), D(2026, 10, 31)
    for r in (5, 6):
        for col in "BC":
            ws[f"{col}{r}"].number_format = "dd/mm/yyyy"
            ws[f"{col}{r}"].font = Font(name=FONTE, size=10, color="0000FF")

    def periodo(col):
        return f'{B},">="&{col}$5,{B},"<="&{col}$6'

    linhas = [
        ("Faturamento (R$)", lambda c: f"=SUMIFS({L},{periodo(c)})", MOEDA),
        # vendas distintas: cada linha vale 1/(nº de linhas com o mesmo id), só no período
        ("Nº de vendas (ids distintos)",
         lambda c: f"=SUMPRODUCT(({B}>={c}$5)*({B}<={c}$6)/COUNTIF({A},{A}))", "0"),
        ("Ticket médio (R$) = faturamento ÷ nº de vendas", lambda c: f"=IFERROR({c}7/{c}8,0)", MOEDA),
        ("Unidades vendidas", lambda c: f"=SUMIFS({rng('I')},{periodo(c)})", "0"),
        ("Linhas da planilha no período", lambda c: f"=COUNTIFS({periodo(c)})", "0"),
    ]
    r = 7
    for rot, f, fmt in linhas:
        ws.cell(r, 1, rot).font = FB
        for col in "BC":
            ws[f"{col}{r}"] = f(col)
            ws[f"{col}{r}"].number_format = fmt
            ws[f"{col}{r}"].font = F
        r += 1
    ws.cell(r, 1, "Variação do faturamento (out vs set)").font = FB
    ws[f"C{r}"] = "=IFERROR(C7/B7-1,0)"
    ws[f"C{r}"].number_format = "+0.0%;-0.0%;0.0%"
    ws[f"C{r}"].font = F
    r += 2

    def bloco(titulo, coluna, valores):
        nonlocal r
        ws.cell(r, 1, titulo).font = FB
        for col in "ABC":
            ws[f"{col}{r}"].fill = FILL_SEC
        r += 1
        for v in valores:
            ws.cell(r, 1, v).font = F
            for col in "BC":
                ws[f"{col}{r}"] = f'=SUMIFS({L},{periodo(col)},{coluna},$A{r})'
                ws[f"{col}{r}"].number_format = MOEDA
                ws[f"{col}{r}"].font = F
            r += 1
        r += 1

    bloco("Faturamento por produto", C, produtos)
    bloco("Faturamento por vendedor", F_, vendedores)
    bloco("Faturamento por canal", G, canais)

    ws.cell(r, 1, "Linhas sem data (devem ser rejeitadas na importação)").font = FB
    ws[f"B{r}"] = f'=COUNTBLANK({B})'
    ws[f"B{r}"].font = F
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16


def gerar(arquivo, nome, linhas, destaques):
    wb = Workbook()
    ultima = aba_vendas(wb.active, linhas, destaques)
    prods = list(dict.fromkeys(l[2] for l in linhas))
    vends = list(dict.fromkeys(l[5] for l in linhas))
    canais = list(dict.fromkeys(l[6] for l in linhas))
    aba_conferencia(wb, ultima, nome, prods, vends, canais)
    wb.save(arquivo)


gerar(f"{SAIDA}/Empresa_A_Loja_Estacao_Moda.xlsx", "Empresa A · Loja Estação Moda", EMPRESA_A, {
    "A-203": (FILL_GRAO, "Mesmo produto em duas linhas da mesma venda. O Intellix soma: vira 1 item "
                         "com 4 unidades e R$ 200,00. A venda conta UMA vez no ticket médio."),
    "A-204": (FILL_GRAO, "Venda com desconto: 1 × 250,00 − 50,00 = 200,00."),
})
gerar(f"{SAIDA}/Empresa_B_Papelaria_Traco_Fino.xlsx", "Empresa B · Papelaria Traço Fino", EMPRESA_B, {
    "B-15": (FILL_ERRO, "Linha SEM DATA, de propósito. Na importação ela deve ser rejeitada com o "
                        "motivo 'data inválida ou ausente', e as outras 12 linhas entram normalmente."),
})
print("ok")
