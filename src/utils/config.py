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
    ENVIRONMENT = os.getenv("ENVIRONMENT", "kub").lower()

    # Spark master URLs
    SPARK_MASTER_URL_LOCAL = os.getenv("SPARK_MASTER_URL_LOCAL")
    SPARK_MASTER_URL_LOCAL_K8S   = os.getenv("SPARK_MASTER_URL_LOCAL_K8S")
    SPARK_MASTER_URL_AWS   = os.getenv("SPARK_MASTER_URL_AWS")
    
    SPARK_MASTER_URL = (
        SPARK_MASTER_URL_AWS
        if ENVIRONMENT == "aws" else
        SPARK_MASTER_URL_LOCAL_K8S
        if ENVIRONMENT == "kub" else
        SPARK_MASTER_URL_LOCAL
    )


    # Spark application name
    SPARK_APP_NAME = os.getenv("SPARK_APP_NAME", "billing-aggregation")

    # Dynamic allocation settings (always enabled for K8s)
    SPARK_DYNAMIC_ALLOCATION_ENABLED = (
        "true" if ENVIRONMENT in ("kub", "aws") else
        "false"
    )
    SPARK_DYNAMIC_ALLOCATION_SHUFFLE_TRACKING = "true" if ENVIRONMENT in ("kub", "aws") else "false"

    # Only meaningful when dynamic allocation is enabled
    SPARK_DYNAMIC_ALLOCATION_MIN_EXECUTORS      = (
        os.getenv("SPARK_DYNAMIC_ALLOCATION_MIN_EXECUTORS", "2")
        if ENVIRONMENT in ("kub", "aws") else None
    )
    SPARK_DYNAMIC_ALLOCATION_INITIAL_EXECUTORS  = (
        os.getenv("SPARK_DYNAMIC_ALLOCATION_INITIAL_EXECUTORS", "2")
        if ENVIRONMENT in ("kub", "aws") else None
    )
    SPARK_DYNAMIC_ALLOCATION_MAX_EXECUTORS      = (
        os.getenv("SPARK_DYNAMIC_ALLOCATION_MAX_EXECUTORS", "10")
        if ENVIRONMENT in ("kub", "aws") else None
    )
    SPARK_DYNAMIC_ALLOCATION_EXECUTOR_IDLE_TIMEOUT = (
        os.getenv("SPARK_DYNAMIC_ALLOCATION_EXECUTOR_IDLE_TIMEOUT", "60s")
        if ENVIRONMENT in ("kub", "aws") else None
    )
    
    # Static executor count (used in standalone local mode)
    SPARK_NUM_EXECUTORS = os.getenv("SPARK_NUM_EXECUTORS", "3")

    # Resource configurations
    SPARK_DRIVER_MEMORY    = os.getenv("SPARK_DRIVER_MEMORY", "2g")
    SPARK_EXECUTOR_MEMORY  = os.getenv("SPARK_EXECUTOR_MEMORY", "4g")
    SPARK_EXECUTOR_CORES   = os.getenv("SPARK_EXECUTOR_CORES", "2")
    
    SPARK_DRIVER_HOST        = os.getenv(
        "SPARK_DRIVER_HOST",
        "localhost" if ENVIRONMENT == "local" else "spark-submit"
    )
    SPARK_DRIVER_PORT      = os.getenv("SPARK_DRIVER_PORT", "7078")
    SPARK_DRIVER_BIND_ADDRESS = os.getenv("SPARK_DRIVER_BIND_ADDRESS", "0.0.0.0")

    SPARK_EVENT_LOG_ENABLED = os.getenv("SPARK_EVENT_LOG_ENABLED", "true").lower()
    SPARK_EVENT_LOG_DIR     = os.getenv("SPARK_EVENT_LOG_DIR")
    
    # Logging level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    SPARK_K8S_IMAGE = os.getenv(
        "SPARK_K8S_IMAGE",
        "distributed-billing-spark:latest"
    )

    # Input path (local or AWS)
    LOG_SOURCE_PATH = (
        os.getenv("LOG_SOURCE_PATH_AWS")
        if ENVIRONMENT == "aws"
        else os.getenv("LOG_SOURCE_PATH_LOCAL")
    )
    
    OUTPUT_DIR = (
        os.getenv("OUTPUT_DIR_AWS")
        if ENVIRONMENT == "aws"
        else os.getenv("OUTPUT_DIR_LOCAL")
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
