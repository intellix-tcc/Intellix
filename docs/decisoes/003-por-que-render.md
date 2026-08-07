# ADR 003 — Render para hospedar o backend

- **Status:** aceito
- **Data:** (preencher)
- **Decisores:** equipe Intellix

## Contexto

O backend FastAPI (com o modelo de IA carregado em memória) precisa ser hospedado a
custo zero no protótipo. As opções avaliadas foram Render, Railway e Fly.io.

## Decisão

Hospedar o backend no **Render** (free tier).

## Justificativa

- O **free tier do Render não expira**; o do Railway expira por consumo de crédito.
- Deploy automático a cada push no GitHub, sem configurar servidor manualmente.

## Consequências

- **Hibernação:** após ~15 min sem uso a instância dorme, e a primeira requisição
  leva ~30 s (reativação + carregamento do modelo). Não é bug.
  - Mitigação para a banca: `scripts/aquecer.sh` alguns minutos antes.
  - Em produção: plano pago básico elimina a hibernação.
- **Limite de RAM** (256–512 MB) exige dimensionar o modelo de IA para caber — o que
  favorece arquiteturas leves (LSTM / modelos destilados).
- Conexão ao Supabase **obrigatoriamente pela porta 6543** (pooler).
