# reset-databases.sh
#!/bin/bash

echo "Resetting databases..."

# Stop services if running
docker compose stop weaviate postgres

# Remove volumes (WARNING: This deletes ALL data)
docker compose down -v

# Start services again
docker compose up -d weaviate postgres

echo "✅ Databases reset complete!"
echo "Waiting for databases to be ready..."

sleep 10

echo "Ready to go!"