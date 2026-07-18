#!/bin/sh
set -e

echo "== Verificando/creando base de datos =="
python -m src.db.init_db

echo "== Aplicando migraciones (alembic upgrade head) =="
alembic upgrade head

echo "== Iniciando servidor =="
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
