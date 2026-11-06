"""Figura 3 do TCC: diagrama de sequência de uma pergunta (rota /chat).

Segue a ordem de app/main.py::chat e app/sql/executor.py. Gerar:
    python sequencia.py            # escreve sequencia.png (precisa de matplotlib)
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

plt.rcParams["font.family"] = ["Liberation Sans", "DejaVu Sans"]  # Liberation Sans = métricas do Arial
FS = 7.6

PART = ["Usuário", "Interface\n(React)", "API\n(FastAPI, /chat)", "NLU\n(modelo treinado\n+ adaptador)",
        "Executor e\nmodelos de consulta", "Banco\n(PostgreSQL)"]
X = [0.4, 1.45, 2.6, 3.75, 4.9, 6.0]
W, H = 6.6, 8.6
fig = plt.figure(figsize=(W, H), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

TOPO = H - 0.15
y_fim = 0.25
for i, (x, nome) in enumerate(zip(X, PART)):
    if i == 0:  # ator
        cy = TOPO - 0.18
        ax.add_patch(plt.Circle((x, cy), 0.07, fill=False, lw=1))
        ax.plot([x, x], [cy - 0.07, cy - 0.3], color="k", lw=1)
        ax.plot([x - 0.13, x + 0.13], [cy - 0.15, cy - 0.15], color="k", lw=1)
        ax.plot([x, x - 0.11], [cy - 0.3, cy - 0.46], color="k", lw=1)
        ax.plot([x, x + 0.11], [cy - 0.3, cy - 0.46], color="k", lw=1)
        ax.text(x, cy - 0.55, nome, ha="center", va="top", fontsize=FS)
    else:
        ax.add_patch(Rectangle((x - 0.52, TOPO - 0.62), 1.04, 0.6, fc="#D9D9D9", ec="k", lw=0.9))
        ax.text(x, TOPO - 0.32, nome, ha="center", va="center", fontsize=FS, fontweight="bold" if False else "normal")

y = TOPO - 1.0
PASSO = 0.33
n = [0]


def msg(a, b, texto, resposta=False, extra=0.0):
    global y
    n[0] += 1
    xa, xb = X[a], X[b]
    rotulo = f"{n[0]}. {texto}"
    if a == b:  # mensagem para si mesmo
        ax.add_patch(FancyArrowPatch((xa + 0.04, y + 0.06), (xa + 0.04, y - 0.16),
                                     connectionstyle="arc3,rad=-1.6", arrowstyle="-|>", mutation_scale=7,
                                     lw=0.8, color="k"))
        ax.text(xa + 0.32, y - 0.05, rotulo, fontsize=FS, va="center", ha="left",
                bbox=dict(fc="white", ec="none", pad=0.6))
        y -= PASSO + 0.08 + extra
        return
    ax.add_patch(FancyArrowPatch((xa, y), (xb, y), arrowstyle="-|>" if not resposta else "->",
                                 mutation_scale=8, lw=0.8, color="k",
                                 linestyle=(0, (4, 2)) if resposta else "-"))
    ax.text((xa + xb) / 2, y + 0.04, rotulo, fontsize=FS, ha="center", va="bottom",
            bbox=dict(fc="white", ec="none", pad=0.6))
    y -= PASSO + extra


def alt(x0, x1, condicao, mensagem):
    """Bloco alt com uma mensagem dentro: cabeçalho, mensagem, borda."""
    global y
    topo = y + 0.12
    y -= 0.34
    mensagem()
    base = y + 0.14
    ax.add_patch(Rectangle((x0, base), x1 - x0, topo - base, fill=False, ec="#333333", lw=0.8))
    ax.add_patch(Rectangle((x0, topo - 0.2), 0.32, 0.2, fc="white", ec="#333333", lw=0.8))
    ax.text(x0 + 0.16, topo - 0.1, "alt", fontsize=FS - 0.4, ha="center", va="center", fontweight="bold")
    ax.text(x0 + 0.38, topo - 0.1, condicao, fontsize=FS - 0.4, ha="left", va="center", style="italic")
    y -= 0.12


msg(0, 1, "digita a pergunta")
msg(1, 2, "POST /chat (pergunta, contexto) + token")
msg(2, 2, "valida o token e o limite de requisições")
msg(2, 3, "parse(texto)")
msg(3, 2, "Interpretacao (intenção, confiança, entidades)", resposta=True)
alt(X[1] - 0.3, X[3] + 0.55, "[confiança < 0,70 ou pergunta fora do domínio]",
    lambda: msg(2, 1, "422: não entendi + exemplos", resposta=True))

msg(2, 5, "busca dono dos dados, catálogo e data de referência")
msg(5, 2, "empresa, catálogo, data", resposta=True)
msg(2, 2, "aplica filtros, contexto da conversa e refino")
msg(2, 4, "executar_template(interpretação)")
alt(X[2] - 0.3, X[4] + 0.55, "[parâmetro obrigatório ausente]",
    lambda: msg(4, 2, "422: pergunta o que falta", resposta=True))

msg(4, 5, "SQL fixo + parâmetros")
msg(5, 4, "linhas", resposta=True)
msg(4, 2, "ResultSet (ou 404 sem resultado)", resposta=True)
msg(2, 5, "registra a consulta em log_consulta")
msg(2, 1, "200: ResultSet em JSON", resposta=True)
msg(1, 0, "exibe a resposta", resposta=True)

for x in X:  # linhas de vida, até a última mensagem
    ax.plot([x, x], [TOPO - 0.75, y + 0.1], color="#555555", lw=0.7, ls=(0, (3, 3)), zorder=0)
ax.set_ylim(y, H)
fig.set_size_inches(W, H - y)
fig.savefig("sequencia.png", dpi=200, facecolor="white")
print("y final", round(y, 2))
