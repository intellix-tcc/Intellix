# Modelos históricos

O modelo em produção fica em `backend/app/nlu/` (v1.1.0 e v1.2.0). Aqui ficam
as duas versões anteriores, que deixaram de estar no código mas são a fonte
de números do TCC. Os dois arquivos têm o número de versão 1.0.0 gravado
dentro; o nome do arquivo diz qual é qual.

| Arquivo | Treino | Métricas gravadas (teste real) | No TCC |
|---|---|---|---|
| `intellix_nlu_v1.0.0_2026-09-08.pt` | Colab, 08/09/2026 | intenção 93,3% · F1 entidades 0,838 | seção 5.5; avaliação de 13/10 (58%) |
| `intellix_nlu_v1.0.0_2026-10-21_retreino.pt` | 21/10/2026, conjunto sem vazamento | intenção 90,0% · F1 entidades 0,868 | avaliação de 04/11 (73%) |

Ler os metadados:

```python
import torch
m = torch.load("intellix_nlu_v1.0.0_2026-09-08.pt", map_location="cpu", weights_only=False)
print(m["data"], m["treino"], m["metricas"], len(m["vocab"]))
```

Detalhes em `docs/avaliacao-reproducao-0411.md`.
