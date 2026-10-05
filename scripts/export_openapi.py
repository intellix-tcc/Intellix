#!/usr/bin/env python3
"""Exporta o contrato OpenAPI da API (FB9 do retorno da orientação).

Gera docs/openapi.json com método, caminho, entradas e saídas de cada
endpoint -- a referência direta que o feedback pediu, sem depender de
descrição narrativa. Rodar com as dependências do backend instaladas:

    cd backend && pip install -r requirements.txt
    cd .. && python scripts/export_openapi.py

Importar o app não conecta ao banco (a conexão só acontece por request),
então este script roda sem DATABASE_URL.
"""

import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "backend"))

from app.main import app  # noqa: E402


def main() -> None:
    spec = app.openapi()
    destino = os.path.join(RAIZ, "docs", "openapi.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"OpenAPI exportado em: {destino}")
    print("Endpoints:")
    for caminho, metodos in sorted(spec.get("paths", {}).items()):
        for metodo in metodos:
            print(f"  {metodo.upper():6} {caminho}")


if __name__ == "__main__":
    main()
