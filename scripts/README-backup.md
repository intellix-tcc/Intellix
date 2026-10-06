# Backup e restore do banco (C12)

Backup lógico dos **dados** do Intellix, feito em Python (psycopg) pelo
Transaction pooler (6543). O **schema** vive nas migrations
(`database/migrations/001-003`), então o backup carrega só os dados.

> Backup não testado não é backup. O procedimento abaixo **testa a
> restauração** de verdade e compara os números.

## Fazer o backup

```bash
cd ~/intellix/backend
source .venv/Scripts/activate          # Linux/macOS: .venv/bin/activate
# aponte para o banco a salvar (prod é o que importa para a banca):
export DATABASE_URL="postgresql://postgres.<ref>:<senha>@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
python ../scripts/backup_db.py --out-dir ../scripts/backups
```

Guarde o `.sql` gerado e **anote o manifesto** (contagens + soma de faturamento).

## Testar a restauração (o drill do C12)

Restaure num banco **descartável** e confira que os números batem. O alvo
mais prático é o `intellix-dev` (dados de teste, recriáveis com o seed):

1. No SQL Editor do **dev**, zere e recrie o schema:
   ```sql
   drop schema public cascade;
   create schema public;
   grant all on schema public to postgres, anon, authenticated, service_role;
   ```
2. Rode as migrations no dev: cole `001_schema.sql`, `002_dim_data.sql`,
   `003_views.sql` (nessa ordem) no SQL Editor.
3. Restaure os dados do backup:
   ```bash
   export DATABASE_URL="postgresql://postgres.<ref-DEV>:<senha>@...6543/postgres"
   python ../scripts/restore_db.py ../scripts/backups/intellix_backup_XXXX.sql
   ```
4. Compare as contagens impressas com o manifesto do backup. **Iguais =
   restauração validada.**
5. (Opcional) `refresh materialized view mv_faturamento_mensal;` e as demais,
   ou rode de novo o `seed.py` se quiser o dev de volta ao estado padrão.

## Camada extra: backup automático da plataforma

O Supabase também mantém backups automáticos: Dashboard do projeto →
**Database → Backups** (e o botão *Download backups*). Serve de rede de
segurança adicional, mas o drill acima é o que prova que sabemos restaurar.

## Registro dos drills

| Data | Banco salvo | sum(valor_total) | Restauração testada em | OK? |
|------|-------------|------------------|------------------------|-----|
|      |             |                  |                        |     |
