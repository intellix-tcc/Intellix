# Confiança e filtro de domínio (TC2 F05)

- Limiar atual (fallbacks.py): **0,70**
- Válidas (12 intenções): 84 · Fora de domínio: 12

## Varredura do limiar

| Limiar | Aceitas (válidas) | Aceite indevido (fora de domínio) |
|---:|---:|---:|
| 0.50 | 78/84 | 0/12 |
| 0.60 | 78/84 | 0/12 |
| 0.70 | 78/84 | 0/12 |
| 0.80 | 76/84 | 0/12 |

## Margem entre intenções (top1 − top2)

| Conjunto | Margem mediana | Margem mínima |
|---|---:|---:|
| Válidas | 1.00 | 0.05 |
| Fora de domínio | 0.54 | 0.01 |

Margem pequena numa pergunta aceita = candidata a pedir confirmação.

## Custo do filtro de domínio (paráfrases válidas sem palavra-chave)

- 7/8 perguntas válidas foram barradas pelo filtro léxico (falso-negativo do filtro):
  - como foi março em comparação com fevereiro
  - o que saiu mais mês passado
  - quem é o destaque do time esse ano
  - o João está indo bem?
  - me mostra os números de 2024
  - qual o resumo do trimestre
  - quanto entrou no caixa em março
