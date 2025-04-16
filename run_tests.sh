set -e

if [ -f "/.dockerenv" ] || [ -f "/proc/1/cgroup" ] && grep -q "docker" /proc/1/cgroup; then
    echo "Running tests in Docker environment..."
    export DATABASE_URL="postgresql+asyncpg://postgres:password@postgres:5432/ml_course_test"
    
    if command -v nc &> /dev/null; then
        echo "Waiting for PostgreSQL..."
        while ! nc -z postgres 5432; do
            sleep 0.1
        done
        echo "PostgreSQL is ready!"
    fi
else
    echo "Setting up local test database..."
    
    if command -v sudo &> /dev/null && command -v psql &> /dev/null; then
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS ml_course_test;" || true
        sudo -u postgres psql -c "CREATE DATABASE ml_course_test;" || true
        export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ml_course_test"
    else
        echo "WARNING: Could not set up local database. Make sure PostgreSQL is installed and running."
        export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/ml_course_test"
    fi
fi

echo "Using DATABASE_URL: ${DATABASE_URL//:postgres@/:****@}"

PYTHONPATH=$PYTHONPATH:. pytest src/tests/ -v 