set -e

python3 src/tests/setup_test_db.py

export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ml_course_test"
PYTHONPATH=$PYTHONPATH:. pytest src/tests/ -v 