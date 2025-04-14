set -e

echo "Starting ML Course API..."

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 