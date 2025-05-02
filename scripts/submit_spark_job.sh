#!/usr/bin/env bash
set -e

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Choose master URL and deploy mode based on ENVIRONMENT
if [ "$ENVIRONMENT" = "aws" ]; then
  MASTER_URL=$SPARK_MASTER_URL_AWS
  DEPLOY_MODE=cluster
else
  MASTER_URL=$SPARK_MASTER_URL_LOCAL
  DEPLOY_MODE=client
fi

# Submit the Spark job
spark-submit \
  --master ${MASTER_URL} \
  --deploy-mode ${DEPLOY_MODE} \
  --name ${SPARK_APP_NAME} \
  --driver-memory ${SPARK_DRIVER_MEMORY} \
  --executor-memory ${SPARK_EXECUTOR_MEMORY} \
  --executor-cores ${SPARK_EXECUTOR_CORES} \
  --conf spark.dynamicAllocation.enabled=true \
  --conf spark.dynamicAllocation.shuffleTracking.enabled=true \
  /app/src/mapreduce_billing/spark_job.py \
    --input-path ${LOG_SOURCE_PATH}
