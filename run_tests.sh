set -e

echo "Setting up test database with sudo..."

sudo -u postgres psql -c "DROP DATABASE IF EXISTS ml_course_test;"
sudo -u postgres psql -c "CREATE DATABASE ml_course_test;"

export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ml_course_test"
echo "Using DATABASE_URL: ${DATABASE_URL//:postgres@/:****@}"

PYTHONPATH=$PYTHONPATH:. pytest src/tests/ -v 