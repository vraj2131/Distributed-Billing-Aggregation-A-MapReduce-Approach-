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
  K8S_IMAGE="${SPARK_K8S_IMAGE:-$DEFAULT_K8S_IMAGE}"
  UPLOAD_DIR=${SPARK_K8S_UPLOAD_PATH:-/tmp/spark-upload}
  K8S_IMAGE_CONF=( \
    --conf spark.kubernetes.file.upload.path=${UPLOAD_DIR} \
    --conf spark.kubernetes.driver.container.image="${K8S_IMAGE}" \
    --conf spark.kubernetes.executor.container.image="${K8S_IMAGE}" \
  )
    K8S_DATA_VOLUME_CONF=( \
    --conf spark.kubernetes.driver.volumes.hostPath.app-data.options.path=/Users/vraj21/Desktop/DIS/data \
    --conf spark.kubernetes.driver.volumes.hostPath.app-data.mount.path=/app/data \
    --conf spark.kubernetes.executor.volumes.hostPath.app-data.options.path=/Users/vraj21/Desktop/DIS/data \
    --conf spark.kubernetes.executor.volumes.hostPath.app-data.mount.path=/app/data \
  )
  K8S_VOLUME_CONF=( \
    --conf spark.kubernetes.driver.volumes.emptyDir.spark-event-logs.mount.path=/app/logs/spark-events \
    --conf spark.kubernetes.driver.volumes.emptyDir.spark-event-logs.mount.medium= \
    --conf spark.kubernetes.driver.volumes.hostPath.results-volume.options.path=/Users/vraj21/Desktop/DIS/data/results \
    --conf spark.kubernetes.driver.volumes.hostPath.results-volume.mount.path=/app/data/results \
    --conf spark.kubernetes.executor.volumes.hostPath.results-volume.options.path=/Users/vraj21/Desktop/DIS/data/results \
    --conf spark.kubernetes.executor.volumes.hostPath.results-volume.mount.path=/app/data/results \
  )
  K8S_DRIVER_ENV_CONFS=( \
    --conf spark.kubernetes.driverEnv.SPARK_MASTER_URL_AWS="${MASTER_URL}" \
    --conf spark.kubernetes.driverEnv.SPARK_EVENT_LOG_ENABLED="${SPARK_EVENT_LOG_ENABLED}" \
    --conf spark.kubernetes.driverEnv.SPARK_EVENT_LOG_DIR="${SPARK_EVENT_LOG_DIR}" \
    --conf spark.kubernetes.driverEnv.RATE_login="${RATE_login}" \
    --conf spark.kubernetes.driverEnv.RATE_getUserProfile="${RATE_getUserProfile}" \
    --conf spark.kubernetes.driverEnv.RATE_createOrder="${RATE_createOrder}" \
    --conf spark.kubernetes.driverEnv.RATE_updateInventory="${RATE_updateInventory}" \
    --conf spark.kubernetes.driverEnv.RATE_deleteOrder="${RATE_deleteOrder}" \
  )

elif [ "$ENVIRONMENT" = "kub" ]; then
  MASTER_URL="$SPARK_MASTER_URL_LOCAL_K8S"
  DEPLOY_MODE="cluster"
  INPUT_PATH="$LOG_SOURCE_PATH_LOCAL"
  OUTPUT_DIR="$OUTPUT_DIR_LOCAL"
  DYN_ENABLED="true"
  K8S_IMAGE="${SPARK_K8S_IMAGE:-$DEFAULT_K8S_IMAGE}"
  UPLOAD_DIR=${SPARK_K8S_UPLOAD_PATH:-/tmp/spark-upload}
  K8S_IMAGE_CONF=( \
    --conf spark.kubernetes.file.upload.path=${UPLOAD_DIR} \
    --conf spark.kubernetes.driver.container.image="${K8S_IMAGE}" \
    --conf spark.kubernetes.executor.container.image="${K8S_IMAGE}" \
  )
  K8S_DATA_VOLUME_CONF=( \
    --conf spark.kubernetes.driver.volumes.hostPath.app-data.options.path=/Users/vraj21/Desktop/DIS/data \
    --conf spark.kubernetes.driver.volumes.hostPath.app-data.mount.path=/app/data \
    --conf spark.kubernetes.executor.volumes.hostPath.app-data.options.path=/Users/vraj21/Desktop/DIS/data \
    --conf spark.kubernetes.executor.volumes.hostPath.app-data.mount.path=/app/data \
  )
  K8S_VOLUME_CONF=( \
    --conf spark.kubernetes.driver.volumes.emptyDir.spark-event-logs.mount.path=/app/logs/spark-events \
    --conf spark.kubernetes.driver.volumes.emptyDir.spark-event-logs.mount.medium= \
    --conf spark.kubernetes.driver.volumes.hostPath.results-volume.options.path=/Users/vraj21/Desktop/DIS/data/results \
    --conf spark.kubernetes.driver.volumes.hostPath.results-volume.mount.path=/app/data/results \
    --conf spark.kubernetes.executor.volumes.hostPath.results-volume.options.path=/Users/vraj21/Desktop/DIS/data/results \
    --conf spark.kubernetes.executor.volumes.hostPath.results-volume.mount.path=/app/data/results \
  )
  K8S_DRIVER_ENV_CONFS=( \
    --conf spark.kubernetes.driverEnv.SPARK_MASTER_URL_LOCAL_K8S="${MASTER_URL}" \
    --conf spark.kubernetes.driverEnv.SPARK_EVENT_LOG_ENABLED="${SPARK_EVENT_LOG_ENABLED}" \
    --conf spark.kubernetes.driverEnv.SPARK_EVENT_LOG_DIR="${SPARK_EVENT_LOG_DIR}" \
    --conf spark.kubernetes.driverEnv.RATE_login="${RATE_login}" \
    --conf spark.kubernetes.driverEnv.RATE_getUserProfile="${RATE_getUserProfile}" \
    --conf spark.kubernetes.driverEnv.RATE_createOrder="${RATE_createOrder}" \
    --conf spark.kubernetes.driverEnv.RATE_updateInventory="${RATE_updateInventory}" \
    --conf spark.kubernetes.driverEnv.RATE_deleteOrder="${RATE_deleteOrder}" \
  )

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

DRIVER_CONF=""
if [ "$ENVIRONMENT" = "local" ]; then
  DRIVER_CONF="\
    --conf spark.driver.host=${SPARK_DRIVER_HOST} \
    --conf spark.driver.port=${SPARK_DRIVER_PORT} \
    --conf spark.driver.bindAddress=${SPARK_DRIVER_BIND_ADDRESS}"
fi

# Submit the Spark job 
spark-submit \
  --master ${MASTER_URL} \
  --deploy-mode ${DEPLOY_MODE} \
  --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark-serviceaccount \
  --conf spark.kubernetes.authenticate.executor.serviceAccountName=spark-serviceaccount \
  --name ${SPARK_APP_NAME} \
  --driver-memory ${SPARK_DRIVER_MEMORY} \
  --executor-memory ${SPARK_EXECUTOR_MEMORY} \
  --executor-cores ${SPARK_EXECUTOR_CORES} \
  --conf spark.dynamicAllocation.enabled="${DYN_ENABLED}" \
  --conf spark.dynamicAllocation.shuffleTracking.enabled="${DYN_ENABLED}" \
  ${EXECUTOR_INSTANCES_CONF:-} \
  "${K8S_IMAGE_CONF[@]:-}" \
  "${K8S_DATA_VOLUME_CONF[@]:-}" \
  "${K8S_VOLUME_CONF[@]:-}" \
  --conf spark.eventLog.enabled="${SPARK_EVENT_LOG_ENABLED}" \
  --conf spark.eventLog.dir="${SPARK_EVENT_LOG_DIR}" \
  ${K8S_DRIVER_ENV_CONFS[@]:-} \
  ${DRIVER_CONF} \
  local:///app/src/mapreduce_billing/spark_job.py \
    --input-path ${INPUT_PATH} \
    --output-dir "${OUTPUT_DIR}"
