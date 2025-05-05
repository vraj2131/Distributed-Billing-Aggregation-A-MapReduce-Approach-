#!/usr/bin/env bash
set -e

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Choose master URL and deploy mode based on ENVIRONMENT
if [ "$ENVIRONMENT" = "aws" ]; then
  MASTER_URL="$SPARK_MASTER_URL_AWS"
  DEPLOY_MODE="cluster"
  INPUT_PATH="$LOG_SOURCE_PATH_AWS"
  OUTPUT_DIR="$OUTPUT_DIR_AWS"
  DYN_ENABLED="true"

elif [ "$ENVIRONMENT" = "kub" ]; then
  MASTER_URL="$SPARK_MASTER_URL_LOCAL_K8S"
  DEPLOY_MODE="cluster"
  INPUT_PATH="$LOG_SOURCE_PATH_LOCAL"
  OUTPUT_DIR="$OUTPUT_DIR_LOCAL"
  DYN_ENABLED="true"

else
  # default to standalone local
  MASTER_URL="$SPARK_MASTER_URL_LOCAL"
  DEPLOY_MODE="client"
  INPUT_PATH="$LOG_SOURCE_PATH_LOCAL"
  OUTPUT_DIR="$OUTPUT_DIR_LOCAL"
  DYN_ENABLED="false"
  STATIC_EXECUTORS=${SPARK_NUM_EXECUTORS:-3}
  echo "Running in standalone local mode: requesting $STATIC_EXECUTORS executors"
  EXECUTOR_INSTANCES_CONF="--conf spark.executor.instances=${STATIC_EXECUTORS}"
fi

if [ "${SPARK_EVENT_LOG_ENABLED,,}" = "true" ]; then
  mkdir -p "${SPARK_EVENT_LOG_DIR}"
fi

 echo ">>> Submitting Spark job to $MASTER_URL, reading $INPUT_PATH, writing to $OUTPUT_DIR"

# Submit the Spark job
spark-submit \
  --master ${MASTER_URL} \
  --deploy-mode ${DEPLOY_MODE} \
  --name ${SPARK_APP_NAME} \
  --driver-memory ${SPARK_DRIVER_MEMORY} \
  --executor-memory ${SPARK_EXECUTOR_MEMORY} \
  --executor-cores ${SPARK_EXECUTOR_CORES} \
  --conf spark.dynamicAllocation.enabled="${DYN_ENABLED}" \
  --conf spark.dynamicAllocation.shuffleTracking.enabled="${DYN_ENABLED}" \
  ${EXECUTOR_INSTANCES_CONF:-} \
  --conf spark.eventLog.enabled="${SPARK_EVENT_LOG_ENABLED}" \
  --conf spark.eventLog.dir="${SPARK_EVENT_LOG_DIR}" \
  --conf spark.driver.host="${SPARK_DRIVER_HOST}" \
  --conf spark.driver.port="${SPARK_DRIVER_PORT}" \
  --conf spark.driver.bindAddress="${SPARK_DRIVER_BIND_ADDRESS}" \
  /app/src/mapreduce_billing/spark_job.py \
    --input-path ${INPUT_PATH} \
    --output-dir "${OUTPUT_DIR}"
