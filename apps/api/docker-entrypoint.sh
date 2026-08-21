#!/bin/sh
set -e

alembic upgrade head
exec uvicorn the21os.app:app --host 0.0.0.0 --port 8000
