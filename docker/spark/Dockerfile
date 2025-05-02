# docker/spark/Dockerfile

# Base image with Spark pre-installed
FROM apache/spark:3.4.1

# Switch to root to install Python and dependencies
USER root

# Copy and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip3 install --no-cache-dir -r /app/requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application source and scripts
COPY src/ /app/src
COPY scripts/submit_spark_job.sh /app/scripts/submit_spark_job.sh

# Ensure scripts are executable
RUN chmod +x /app/scripts/submit_spark_job.sh

# Add source directory to PYTHONPATH
ENV PYTHONPATH=/app/src

# Default command: show Spark version (override in Docker Compose or CLI)
CMD ["spark-submit", "--version"]
