#!/bin/bash
set -e

echo "🟡 Rodando migrations Alembic..."
alembic upgrade head
echo "✅ Migrations concluídas."

echo "🚀 Iniciando aplicação FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
