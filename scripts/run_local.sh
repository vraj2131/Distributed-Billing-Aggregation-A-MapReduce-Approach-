#!/usr/bin/env bash
set -e

# Run the full local Spark stack (master, worker, submit), 
# abort when the submit job finishes, and exit with its code.
docker-compose -f docker/docker-compose.yml up \
  --build \
  --abort-on-container-exit \
  --exit-code-from spark-submit
