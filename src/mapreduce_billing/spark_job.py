# # src/mapreduce_billing/spark_job.py
# """
# Spark job entry-point for billing aggregation on Kubernetes (local or AWS):
# - Dynamically selects Spark master URL based on ENVIRONMENT
# - Always uses dynamic allocation with shuffle tracking
# - Reads API logs from a local file or S3
# - Computes per-user total duration and cost using map_records & reduce_records
# """
# import os
# import argparse
# from dotenv import load_dotenv
# from pyspark.sql import SparkSession
# from .map_reduce import map_records, reduce_records


# def build_spark_session():
#     # Load environment variables
#     load_dotenv()
#     env = os.getenv("ENVIRONMENT", "local").lower()

#     # Select master URL per environment
#     if env == "aws":
#         master_url = os.getenv("SPARK_MASTER_URL_AWS")
#     else:
#         master_url = os.getenv("SPARK_MASTER_URL_LOCAL")

#     app_name = os.getenv("SPARK_APP_NAME", "billing-aggregation")
#     builder = SparkSession.builder.master(master_url).appName(app_name)

#     # Enable dynamic allocation and shuffle tracking
#     builder = builder.config("spark.dynamicAllocation.enabled", "true")
#     builder = builder.config("spark.dynamicAllocation.shuffleTracking.enabled", "true")

#     # Dynamic allocation tuning
#     builder = builder.config(
#         "spark.dynamicAllocation.minExecutors",
#         os.getenv("SPARK_DYNAMIC_ALLOCATION_MIN_EXECUTORS", "1")
#     )
#     builder = builder.config(
#         "spark.dynamicAllocation.initialExecutors",
#         os.getenv("SPARK_DYNAMIC_ALLOCATION_INITIAL_EXECUTORS", "2")
#     )
#     builder = builder.config(
#         "spark.dynamicAllocation.maxExecutors",
#         os.getenv("SPARK_DYNAMIC_ALLOCATION_MAX_EXECUTORS", "10")
#     )
#     builder = builder.config(
#         "spark.dynamicAllocation.executorIdleTimeout",
#         os.getenv("SPARK_DYNAMIC_ALLOCATION_EXECUTOR_IDLE_TIMEOUT", "60s")
#     )

#     # Common resource settings
#     builder = builder.config(
#         "spark.driver.memory",
#         os.getenv("SPARK_DRIVER_MEMORY", "2g")
#     )
#     builder = builder.config(
#         "spark.executor.memory",
#         os.getenv("SPARK_EXECUTOR_MEMORY", "4g")
#     )
#     builder = builder.config(
#         "spark.executor.cores",
#         os.getenv("SPARK_EXECUTOR_CORES", "2")
#     )

#     return builder.getOrCreate()


# def main():
#     parser = argparse.ArgumentParser(
#         description="Spark billing aggregation job on Kubernetes"
#     )
#     parser.add_argument(
#         "--input-path", required=True,
#         help="Path to API logs (local or S3 URI)"
#     )
#     args = parser.parse_args()

#     spark = build_spark_session()
#     sc = spark.sparkContext

#     # Read log lines and apply MapReduce
#     lines_rdd = sc.textFile(args.input_path)
#     user_pairs = map_records(lines_rdd)
#     user_totals = user_pairs.reduceByKey(reduce_records)

#     # Output results
#     for user, (duration, cost) in sorted(user_totals.collect(), key=lambda x: x[0]):
#         print(f"{user}: total_duration={duration}ms, total_cost={cost:.2f}")

#     spark.stop()


# if __name__ == "__main__":
#     main()

# src/mapreduce_billing/spark_job.py
"""
Spark job entry-point for billing aggregation on Kubernetes (local or AWS):
- Dynamically selects Spark master URL based on ENVIRONMENT
- Always uses dynamic allocation with shuffle tracking
- Reads API logs from a local file or S3
- Computes per-user total duration and cost using map_records & reduce_records
- Includes exception handling and structured logging
"""
import os
from datetime import datetime
import sys
import argparse
import logging
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from mapreduce_billing.map_reduce import map_records, reduce_records


def setup_logging():
    """
    Configure logging based on LOG_LEVEL env var.
    """
    load_dotenv()
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    return logging.getLogger(__name__)


def build_spark_session(logger):
    """
    Build and return a SparkSession configured for dynamic allocation.
    """
    env = os.getenv("ENVIRONMENT", "local").lower()
    if env == "aws":
        master_url = os.getenv("SPARK_MASTER_URL_AWS")
    elif env == "kub":
        master_url = os.getenv("SPARK_MASTER_URL_LOCAL_K8S")
    else:
        master_url = os.getenv("SPARK_MASTER_URL_LOCAL")
        
    app_name = os.getenv("SPARK_APP_NAME", "billing-aggregation")

    try:
        logger.info(f"Connecting to Spark master at {master_url}")
        builder = SparkSession.builder.master(master_url).appName(app_name)
        
        if env == "local":
            num_exec = os.getenv("SPARK_NUM_EXECUTORS", "3")
            builder = builder.config("spark.executor.instances", num_exec)
        # Enable dynamic allocation
        dyn_enabled = "true" if env in ("kub", "aws") else "false"
        builder = builder.config("spark.dynamicAllocation.enabled", dyn_enabled)
        if env in ("kub", "aws"):
            builder = builder.config("spark.dynamicAllocation.shuffleTracking.enabled", "true")
            # Dynamic allocation settings
            builder = builder.config(
                "spark.dynamicAllocation.minExecutors",
                os.getenv("SPARK_DYNAMIC_ALLOCATION_MIN_EXECUTORS", "1")
            )
            builder = builder.config(
                "spark.dynamicAllocation.initialExecutors",
                os.getenv("SPARK_DYNAMIC_ALLOCATION_INITIAL_EXECUTORS", "2")
            )
            builder = builder.config(
                "spark.dynamicAllocation.maxExecutors",
                os.getenv("SPARK_DYNAMIC_ALLOCATION_MAX_EXECUTORS", "10")
            )
            builder = builder.config(
                "spark.dynamicAllocation.executorIdleTimeout",
                os.getenv("SPARK_DYNAMIC_ALLOCATION_EXECUTOR_IDLE_TIMEOUT", "60s")
            )
        builder = builder.config("spark.driver.host", os.getenv("SPARK_DRIVER_HOST")) \
    .config("spark.driver.port", os.getenv("SPARK_DRIVER_PORT")) \
    .config("spark.driver.bindAddress", os.getenv("SPARK_DRIVER_BIND_ADDRESS"))
        # Resource settings
        builder = builder.config(
            "spark.driver.memory",
            os.getenv("SPARK_DRIVER_MEMORY", "2g")
        )
        builder = builder.config(
            "spark.executor.memory",
            os.getenv("SPARK_EXECUTOR_MEMORY", "4g")
        )
        builder = builder.config(
            "spark.executor.cores",
            os.getenv("SPARK_EXECUTOR_CORES", "2")
        )
        
        # if os.getenv("SPARK_EVENT_LOG_ENABLED", "true").lower() == "true":
        #     log_dir = os.getenv("SPARK_EVENT_LOG_DIR", "/app/tmp/spark-events")
        #     try:
        #         os.makedirs(log_dir, exist_ok=True)
        #     except Exception as e:
        #         logger.warning(f"Could not create Spark event log dir {log_dir}: {e}")
        #     builder = builder.config("spark.eventLog.enabled", "true") \
        #                     .config("spark.eventLog.dir", log_dir)
        builder = (
        builder
        .config("spark.eventLog.enabled", os.getenv("SPARK_EVENT_LOG_ENABLED"))
        .config("spark.eventLog.dir",     os.getenv("SPARK_EVENT_LOG_DIR"))
)
        
        spark = builder.getOrCreate()
        logger.info("Spark session created successfully")
        return spark
    except Exception:
        logger.exception("Failed to create Spark session")
        sys.exit(1)


def main():
    logger = setup_logging()
    parser = argparse.ArgumentParser(
        description="Spark billing aggregation job on Kubernetes"
    )
    parser.add_argument(
        "--input-path", required=True,
        help="Path to API logs (local or S3 URI)"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="If given, writes results to a timestamped file in this directory"
    )
    args = parser.parse_args()

    try:
        logger.info(f"Starting billing aggregation with input: {args.input_path}")
        spark = build_spark_session(logger)
        sc = spark.sparkContext

        logger.debug("Reading log lines from input path")
        lines_rdd = sc.textFile(args.input_path)

        logger.debug("Mapping records")
        user_pairs = map_records(lines_rdd)

        logger.debug("Reducing records")
        user_totals = user_pairs.reduceByKey(reduce_records)

        logger.info("Collecting results")
        results = user_totals.collect()
        for user, (duration, cost) in sorted(results, key=lambda x: x[0]):
            logger.info(f"{user}: total_duration={duration}ms, total_cost={cost:.2f}")

        if args.output_dir:
            os.makedirs(args.output_dir, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"billing_results_{ts}.txt"
            out_path = os.path.join(args.output_dir, filename)
            with open(out_path, "w") as f:
                for user, (duration, cost) in sorted(user_totals.collect(), key=lambda x: x[0]):
                    f.write(f"{user}: total_duration={duration}ms, total_cost={cost:.2f}\n")
        logger.info(f"Results written to {out_path}")
        
        spark.stop()
        logger.info("Billing aggregation job completed successfully")
    except Exception:
        logger.exception("Billing aggregation job failed unexpectedly")
        sys.exit(1)


if __name__ == "__main__":
    main()
