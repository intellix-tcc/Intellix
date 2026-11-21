import re, sys, subprocess
S = sys.argv[1]
md = open("/workspace/Intellix/docs/defesa/guia_maria_demo_e_arguicao.md", encoding="utf-8").read()
md = re.sub(r" ?\(\[tela\]\(telas/\d_[^)]+\)\)", "", md)
md = re.sub(r" ?\(\[exemplo com a A\]\(telas/\d_[^)]+\)\)", "", md)
md = re.sub(r"\[([^\]]+)\]\(#[^)]+\)", r"\1", md)
a = md.index("Material de apoio para a defesa."); b = md.index("Cada planilha tem duas abas.")
md = md[:a] + ("Arquivos da demonstração (pasta `docs/defesa/` do repositório): "
    "`Empresa_A_Loja_Estacao_Moda.xlsx` (loja de roupas, 14 linhas) e "
    "`Empresa_B_Papelaria_Traco_Fino.xlsx` (papelaria, 13 linhas, uma sem data de propósito).\n\n") + md[b:]
md = re.sub(r"Critério: uma ideia por frase.*?\n\n", "", md, flags=re.S)
md = re.sub(r"\n\*Testes executados em 19/11/2026.*?\*\s*$", "\n", md, flags=re.S)
md = md.replace("A fala completa, sincronizada com o operador, está na seção 3.2.", "Fala completa na seção 3.2.")
md = re.sub(r"\*\*Por que mudou:\*\*.*?\n\n", "", md, flags=re.S)
md = re.sub(r"^- \[ \] ", "- ☐ ", md, flags=re.M)
open(f"{S}/final.md", "w", encoding="utf-8").write(md)
subprocess.run(["pandoc", f"{S}/final.md", "-f", "gfm", "-t", "html5", "-s", "--metadata", "pagetitle=Guia da defesa - Maria Luiza",
                "-c", f"{S}/estilo2.css", "-o", f"{S}/final.html"], check=True)
h = open(f"{S}/final.html", encoding="utf-8").read()
h = h.replace('<ul class="task-list">', '<ul class="caixas1">').replace('<label><input type="checkbox" />', '☐ ').replace('</label></li>', '</li>')
open(f"{S}/final.html", "w", encoding="utf-8").write(h)
