#!/bin/sh
set -e

alembic upgrade head
exec uvicorn the21secrets.app:app --host 0.0.0.0 --port 8000
