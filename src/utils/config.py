# src/utils/config.py
"""
Configuration loader for billing aggregation pipeline.
Loads environment variables from .env and provides a centralized Config class.
"""
import os
from dotenv import load_dotenv

# Load .env into environment
load_dotenv()

class Config:
    # Environment mode: 'local' or 'aws'
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local").lower()

    # Spark master URLs
    SPARK_MASTER_URL_LOCAL = os.getenv("SPARK_MASTER_URL_LOCAL")
    SPARK_MASTER_URL_AWS   = os.getenv("SPARK_MASTER_URL_AWS")

    # Spark application name
    SPARK_APP_NAME = os.getenv("SPARK_APP_NAME", "billing-aggregation")

    # Dynamic allocation settings (always enabled for K8s)
    SPARK_DYNAMIC_ALLOCATION_ENABLED            = os.getenv("SPARK_DYNAMIC_ALLOCATION_ENABLED", "true")
    SPARK_DYNAMIC_ALLOCATION_SHUFFLE_TRACKING   = os.getenv("SPARK_DYNAMIC_ALLOCATION_SHUFFLE_TRACKING_ENABLED", "true")
    SPARK_DYNAMIC_ALLOCATION_MIN_EXECUTORS      = os.getenv("SPARK_DYNAMIC_ALLOCATION_MIN_EXECUTORS", "1")
    SPARK_DYNAMIC_ALLOCATION_INITIAL_EXECUTORS  = os.getenv("SPARK_DYNAMIC_ALLOCATION_INITIAL_EXECUTORS", "2")
    SPARK_DYNAMIC_ALLOCATION_MAX_EXECUTORS      = os.getenv("SPARK_DYNAMIC_ALLOCATION_MAX_EXECUTORS", "10")
    SPARK_DYNAMIC_ALLOCATION_EXECUTOR_IDLE_TIMEOUT = os.getenv("SPARK_DYNAMIC_ALLOCATION_EXECUTOR_IDLE_TIMEOUT", "60s")

    # Resource configurations
    SPARK_DRIVER_MEMORY    = os.getenv("SPARK_DRIVER_MEMORY", "2g")
    SPARK_EXECUTOR_MEMORY  = os.getenv("SPARK_EXECUTOR_MEMORY", "4g")
    SPARK_EXECUTOR_CORES   = os.getenv("SPARK_EXECUTOR_CORES", "2")

    # Logging level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # Input path (local or AWS)
    LOG_SOURCE_PATH = (
        os.getenv("LOG_SOURCE_PATH_LOCAL") if ENVIRONMENT == "local"
        else os.getenv("LOG_SOURCE_PATH_AWS")
    )

    # AWS credentials (only used when ENVIRONMENT='aws')
    AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION            = os.getenv("AWS_REGION", "us-east-1")

    # Rates per API task (from RATE_<task> env vars)
    RATES = {
        name.split("_",1)[1]: float(val)
        for name, val in os.environ.items()
        if name.startswith("RATE_")
    }
