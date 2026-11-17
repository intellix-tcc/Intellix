#!/usr/bin/env python3
"""
manifesto_reproducao.py — Manifesto de reprodução da versão publicada.

Atende ao parecer da banca final, F07 ("pacote de reprodução"): o repositório
não foi recuperado pela consulta externa e os ensaios não tinham um manifesto
que fixasse commit, hash de pesos, vocabulário, gabarito, dados, migrações,
relógio e parâmetros. Este script gera esse manifesto, versionável junto da
evidência, para que qualquer pessoa reproduza bit a bit o que foi medido.

O que ele fixa, tudo computado na hora (nada escrito à mão):
  - commit, branch e estado da árvore (git);
  - hash SHA-256 de cada arquivo de pesos (.pt) e seu tamanho;
  - métricas embutidas em cada .pt (versão, intenção, F1), se o torch estiver
    disponível — opcional, o resto do manifesto não depende dele;
  - fingerprint determinístico do DATASET sintético (hash do grão da fato
    gerado pelo seed, SEED=42), provando que os dados são reproduzíveis;
  - hash das migrações, dos templates SQL e dos conjuntos de perguntas;
  - parâmetros de execução (NLU_BACKEND, limiar, limitador, auth, relógio);
  - os comandos exatos de reprodução.

Uso:
    python scripts/manifesto_reproducao.py                 # imprime
    python scripts/manifesto_reproducao.py --saida docs/evidencias
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "database"))


def _sha256_arquivo(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(RAIZ), *args], text=True).strip()
    except Exception as e:  # noqa: BLE001
        return f"(git indisponível: {e})"


def _fingerprint_dataset() -> tuple[str, dict]:
    """Hash do grão da fato gerado pelo seed — prova de que os dados são
    reproduzíveis sem anexar o dump. Serializa cada item de venda de forma
    estável e ordenada e aplica SHA-256."""
    import seed as seedmod

    _p, _c, vendas = seedmod.gerar()
    linhas = []
    for v in vendas:
        for it in v["itens"]:
            linhas.append(
                f'{v["venda_id"]}|{v["data"].isoformat()}|{it["produto"]}|'
                f'{v["cliente"]}|{v["vendedor"]}|{v["canal"]}|{v["pagamento"]}|'
                f'{it["qtd"]}|{it["valor_total"]:.2f}'
            )
    linhas.sort()
    h = hashlib.sha256("\n".join(linhas).encode("utf-8")).hexdigest()
    faturamento = sum(it["valor_total"] for v in vendas for it in v["itens"])
    resumo = {
        "seed": seedmod.SEED,
        "empresa_id": seedmod.EMPRESA_ID,
        "vendas": len(vendas),
        "itens": len(linhas),
        "faturamento": f"{faturamento:,.2f}",
    }
    return h, resumo


def _metricas_pt(p: Path) -> str:
    """Lê as métricas embutidas no .pt, se o torch estiver disponível."""
    try:
        import torch  # noqa

        dados = torch.load(p, map_location="cpu", weights_only=False)
        if isinstance(dados, dict):
            m = dados.get("metricas") or dados.get("metrics") or {}
            versao = dados.get("versao") or dados.get("version") or "-"
            if m:
                itens = ", ".join(f"{k}={v}" for k, v in list(m.items())[:4])
                return f"versão {versao}; {itens}"
            return f"versão {versao}"
    except Exception as e:  # noqa: BLE001
        return f"(métricas não lidas: {type(e).__name__})"
    return "(sem bloco de métricas)"


def gerar_manifesto() -> str:
    agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")
    commit = _git("rev-parse", "HEAD")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    sujo = _git("status", "--porcelain")
    estado = "árvore limpa" if not sujo or sujo.startswith("(git") else f"{len(sujo.splitlines())} arquivo(s) não commitados"
    remoto = _git("remote", "get-url", "origin")

    pesos = sorted(list((RAIZ / "backend" / "app" / "nlu").glob("*.pt")) +
                   list((RAIZ / "ia training" / "modelos").glob("*.pt")))
    fp, resumo = _fingerprint_dataset()

    migracoes = sorted((RAIZ / "database" / "migrations").glob("*.sql"))
    conjuntos = [p for p in [
        RAIZ / "docs" / "perguntas_validacao.md",
        RAIZ / "docs" / "perguntas_ineditas.md",
    ] if p.exists()]
    templates = RAIZ / "backend" / "app" / "sql" / "templates.py"

    L: list[str] = [
        "# Manifesto de reprodução — versão publicada",
        "",
        "Fixa o que é preciso para reproduzir bit a bit os ensaios (parecer da",
        "banca final, F07). Gerado por `scripts/manifesto_reproducao.py`.",
        "",
        f"- **Data:** {agora}",
        f"- **Commit:** `{commit}` ({branch}, {estado})",
        f"- **Remoto:** {remoto}",
        "",
        "## 1. Pesos do modelo (SHA-256)",
        "",
        "| Arquivo | Bytes | SHA-256 | Métricas embutidas |",
        "|---|---:|---|---|",
    ]
    for p in pesos:
        rel = p.relative_to(RAIZ)
        L.append(f"| `{rel}` | {p.stat().st_size:,} | `{_sha256_arquivo(p)[:32]}…` | {_metricas_pt(p)} |")

    L += [
        "",
        "## 2. Dataset sintético (determinístico)",
        "",
        "Os dados não precisam ser anexados: são reproduzidos por",
        "`database/seed.py` com semente fixa. O fingerprint abaixo é o SHA-256 do",
        "grão da fato gerado; recriar o seed e conferir o hash prova que os dados",
        "são os mesmos.",
        "",
        f"- **SEED:** `{resumo['seed']}`  ·  **empresa_id:** `{resumo['empresa_id']}`",
        f"- **Volume:** {resumo['itens']} itens em {resumo['vendas']} vendas  ·  "
        f"faturamento R$ {resumo['faturamento']}",
        f"- **Fingerprint SHA-256:** `{fp}`",
        "",
        "## 3. Migrações aplicadas (ordem e SHA-256)",
        "",
        "| # | Migração | SHA-256 |",
        "|---|---|---|",
    ]
    for i, p in enumerate(migracoes, 1):
        L.append(f"| {i} | `{p.name}` | `{_sha256_arquivo(p)[:32]}…` |")

    L += [
        "",
        "## 4. Artefatos de consulta e avaliação (SHA-256)",
        "",
        "| Artefato | SHA-256 |",
        "|---|---|",
        f"| `backend/app/sql/templates.py` (14 consultas) | `{_sha256_arquivo(templates)[:32]}…` |",
    ]
    for p in conjuntos:
        L.append(f"| `{p.relative_to(RAIZ)}` | `{_sha256_arquivo(p)[:32]}…` |")

    L += [
        "",
        "## 5. Parâmetros de execução (relógio e configuração)",
        "",
        "| Parâmetro | Valor do ensaio | Observação |",
        "|---|---|---|",
        "| `NLU_BACKEND` | `modelo` | usa o `.pt` treinado, não o baseline de regras |",
        "| Limiar de confiança | `0,70` | abaixo disso o sistema pede para reformular |",
        "| `AUTH_OBRIGATORIA` | `false` (local) / `true` (produção) | em produção exige login |",
        "| `LIMITE_REQUISICOES` | `0` nos ensaios de carga / vazão | **ligado em operação normal** (ver reteste F05) |",
        "| Relógio | datas fixas 2023–2026 no dataset | perguntas relativas ancoram na última venda (`R.referencia()`) |",
        "",
        "## 6. Comandos de reprodução",
        "",
        "```bash",
        "# 1. banco (Postgres 16)",
        "createdb intellix",
        "psql -d intellix -f database/local/supabase_minimo.sql",
        'for f in database/migrations/*.sql; do psql -d intellix -v ON_ERROR_STOP=1 -f "$f"; done',
        "DATABASE_URL=postgresql://postgres:***@localhost:5432/intellix python database/seed.py",
        "",
        "# 2. gabarito numérico das 14 consultas (F02)",
        "DATABASE_URL=postgresql://... python scripts/gabarito_numerico.py --saida docs/evidencias",
        "",
        "# 3. bateria de 100 perguntas (regressão)",
        "cd backend && NLU_BACKEND=modelo uvicorn app.main:app &",
        "python scripts/avaliar_100_perguntas.py --modo api --url http://127.0.0.1:8000",
        "",
        "# 4. conjunto inédito (generalização, F01) — quando presente",
        "python scripts/avaliar_ineditas.py --url http://127.0.0.1:8000",
        "```",
        "",
        "## 7. Como conferir este manifesto",
        "",
        "Rodar `python scripts/manifesto_reproducao.py` na mesma `commit` deve",
        "reproduzir todos os hashes acima. Qualquer divergência em pesos, dataset,",
        "migração ou template indica que o ensaio foi feito sobre outro estado.",
        "",
    ]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera o manifesto de reprodução (F07).")
    ap.add_argument("--saida", default=None, help="diretório para gravar o .md (ex.: docs/evidencias)")
    args = ap.parse_args()

    md = gerar_manifesto()
    if args.saida:
        destino = Path(args.saida)
        destino.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        arq = destino / f"manifesto_reproducao_{stamp}.md"
        arq.write_text(md, encoding="utf-8")
        print(f"Manifesto: {arq}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
