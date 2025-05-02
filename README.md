# Distributed Billing Aggregation Pipeline

A MapReduce-style billing aggregator for API logs, powered by Apache Spark. Supports both local Docker-Compose testing and Kubernetes cluster mode (Kind/Docker-Desktop or AWS EKS).

---

## 📁 Directory Structure

```
distributed-billing/
├── .gitignore
├── README.md
├── .env.template
├── requirements.txt
│
├── configs/                       # Kubernetes manifests
│   └── k8s/
│       ├── spark-serviceaccount.yaml
│       ├── fluent-bit-config.yaml
│       ├── fluent-bit-daemonset.yaml
│       ├── billing-cronjob.yaml   # Scheduled CronJob
│       └── billing-job.yaml       # On-demand Job
│
├── docker/
│   └── spark/
│       ├── Dockerfile             # Spark + Python image
│       └── docker-compose.yml     # Local Compose setup
│
├── scripts/
│   ├── run_local.sh               # `docker-compose up --build`
│   └── submit_spark_job.sh        # Spark-submit wrapper
│
├── src/
│   ├── mapreduce_billing/
│   │   ├── __init__.py            # Python package
│   │   ├── naive_aggregation.py   # Single-process baseline
│   │   ├── map_reduce.py          # Core Map & Reduce fns
│   │   └── spark_job.py           # Spark entrypoint
│   └── utils/
│       ├── config.py              # Loads .env → Config class
│       └── io.py                  # Reads from local or S3
│
└── tests/
    ├── test_naive.py             # Unit tests for naive_aggregation
    └── test_mapreduce.py         # Logic tests via FakeRDD
```

---

## ⚙️ Prerequisites

* **Docker** & **Docker-Compose** (for local)
* **kubectl** & **Kubernetes** (Docker-Desktop, Kind, or EKS)
* **AWS CLI** & **ECR permissions** (if deploying to EKS)
* **Python 3.8+** with `pip` (for local testing & running scripts)

---

## 📝 Setup

### 1. Environment Variables

Copy and customize:

```bash
cp .env.template .env
# Edit .env:
# - ENVIRONMENT=local (or aws)
# - SPARK_MASTER_URL_LOCAL/s3 endpoints
# - AWS_ACCESS_KEY_ID, SECRET, REGION
# - RATE_<task> values
```

### 2. Install Python Dependencies (optional for local testing)

Activate your venv and install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Local Testing (Docker-Compose)

1. **Build & launch** everything locally:

   ```bash
   cd docker
   docker-compose up --build
   ```

2. **run\_local.sh** will:

   * Build the Spark image
   * Start a Spark master + worker container
   * Run your Spark job in client mode
   * Tear down when complete

3. **Check output** in `data/billing.txt` (or printed to console).

---

## 🐳 Kubernetes Cluster Mode (Local or AWS)

#### A) Prepare `.env` Secret

```bash
kubectl create secret generic app-env \
  --from-file=.env=./.env
```

#### B) Apply Manifests

```bash
kubectl apply -f configs/k8s/spark-serviceaccount.yaml
kubectl apply -f configs/k8s/fluent-bit-config.yaml
kubectl apply -f configs/k8s/fluent-bit-daemonset.yaml
kubectl apply -f configs/k8s/billing-cronjob.yaml    # scheduled runs
# or on-demand:
kubectl apply -f configs/k8s/billing-job.yaml
```

#### C) Monitor Logs

* **Local**: logs appear via DaemonSet stdout on each node.
* **AWS**: Fluent Bit ships logs to CloudWatch under `/kubernetes/fluent-bit-logs`.

You can also port-forward the Spark UI:

```bash
kubectl get pods --selector=app=spark-driver
kubectl port-forward <driver-pod> 4040:4040
```

---

## 📖 Testing

Run pure-Python tests without Spark:

```bash
pytest tests/test_naive.py
pytest tests/test_mapreduce.py
```

---

## 📦 Deploy to AWS EKS

1. **Tag & push** Docker image to ECR:

   ```bash
   ```

docker build -t \$ECR\_URI\:latest -f docker/spark/Dockerfile .
docker push \$ECR\_URI\:latest

```
2. **Create `app-env`** in EKS (AWS-mode `.env`).
3. **Apply** the same `configs/k8s/` manifests.

Your Spark job will now run on EKS in cluster mode with dynamic allocation.

---

## 🔧 Further Reading

- Spark on Kubernetes: https://spark.apache.org/docs/latest/running-on-kubernetes.html  
- Fluent Bit → CloudWatch: https://docs.fluentbit.io/manual/pipeline/outputs/cloudwatch

---

© 2025 Distributed Billing Aggregation

```
