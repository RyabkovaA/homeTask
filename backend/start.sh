#!/bin/bash
set -e

echo "==> Running database migrations..."
alembic upgrade head
echo "==> Migrations complete."

echo "==> Seeding knowledge base (if empty)..."
python -m app.seed_knowledge --if-empty
echo "==> Seed check complete."

echo "==> Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
