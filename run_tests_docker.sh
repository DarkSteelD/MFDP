set -e

echo "Running tests using Docker Compose..."

docker-compose -f docker-compose.test.yml build
docker-compose -f docker-compose.test.yml run --rm test-runner

echo "Cleaning up test containers..."
docker-compose -f docker-compose.test.yml down 