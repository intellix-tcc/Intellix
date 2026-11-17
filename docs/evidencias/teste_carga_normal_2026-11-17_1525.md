# Reteste de carga do /chat em configuração normal — 17/11/2026 15:25 (UTC+0000)

- **Alvo:** `http://127.0.0.1:8000` (local)  ·  **limitador:** LIGADO (/chat = 30/min por IP)
- **Escopo:** caracterização sob config normal; **não** mede vazão máxima nem
  disponibilidade (propriedades da hospedagem — ver decisão 003 sobre a hibernação do Render).

## 1. Partida fria × quente (caminho da aplicação)

- **Fria** (1ª pergunta, abre o pool de conexões): **55 ms**
- **Quente** (mediana de 24 seguintes): **17 ms**

> A partida fria de *instância* do Render (hibernação ~30 s) não é reproduzível
> localmente; aqui está o caminho frio da aplicação (abertura do pool).

## 2. Latência por estado (mistura de consultas)

| Estado | N | Mediana | p95 | Máx |
|---|---:|---:|---:|---:|
| 200 consulta | 18 | 19 ms | 40 ms | 55 ms |
| 404 sem_resultado | 3 | 11 ms | 13 ms | 13 ms |
| 422 baixa_confianca | 2 | 5 ms | 5 ms | 5 ms |
| 422 parametro_faltando | 2 | 12 ms | 14 ms | 14 ms |

## 3. Limitador ativo (a proteção que o teste anterior desligou)

Burst de 35 perguntas /chat do mesmo IP em poucos segundos:

- **30** responderam **200** (dentro do limite de 30/min);
- **5** responderam **429 `limite_requisicoes`** (bloqueadas pela proteção).

Em operação normal, um cliente é limitado a 30 perguntas/min por IP; o teste de
capacidade (`teste_carga.py`) desliga isso de propósito e, por isso, não
representa a operação normal — é a leitura que o parecer pedia para separar.

## Reproduzir

```bash
cd backend && NLU_BACKEND=modelo AUTH_OBRIGATORIA=false \
  EMPRESA_ID=00000000-0000-0000-0000-000000000001 DATABASE_URL=postgresql://... \
  uvicorn app.main:app --port 8000 &
python scripts/teste_carga_normal.py --url http://127.0.0.1:8000 --saida docs/evidencias
```

