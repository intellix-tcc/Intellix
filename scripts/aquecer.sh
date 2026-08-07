#!/bin/bash
# Acorda a instância do Render antes da banca (mata a hibernação de ~30s).
# Rode uns 10 min antes da apresentação.
time curl -s https://intellix-api.onrender.com/health
