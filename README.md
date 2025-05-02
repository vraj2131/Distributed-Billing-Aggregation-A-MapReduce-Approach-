# Distributed Billing Aggregation Pipeline

This project implements a scalable billing aggregation system using Apache Spark. We ingest raw API logs, compute per-user total durations and costs for different API tasks via MapReduce functions, and compare a naive single-process baseline with a distributed Spark implementation. Our goal is to provide an end-to-end pipeline that can run locally for development (via Docker Compose) and in production on Kubernetes—either on your laptop (Kind/Docker Desktop) or AWS EKS—with dynamic executor allocation and integrated logging.

---

## ⚙️ Prerequisites

* **Docker** & **Docker Compose** (for local development)
* **kubectl** & **Kubernetes** (Kind/Docker Desktop or EKS)
* **AWS CLI** & **ECR permissions** (if deploying to EKS)
* **Python 3.8+** with `pip` (for local testing & scripts)

---

## 📝 Setup

1. **Environment Variables**
   Ensure you have a `.env` file at the project root containing all required settings (ENVIRONMENT, Spark URLs, log paths, per-task rates, AWS credentials, LOG\_LEVEL).

2. **Install Python Dependencies** (for local tests):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 🚀 Local Development

Bring up a local Spark cluster and run the aggregation:

```bash
cd docker
docker-compose up --build
```

This spins up a Spark master, worker, and executes the Spark job in client mode. Results are written to `data/billing.txt`.

---

## 🐳 Kubernetes Cluster Mode

### 1. Create `.env` Secret

```bash
kubectl create secret generic app-env --from-file=.env=./.env
```

### 2. Deploy Manifests

```bash
kubectl apply -f configs/k8s/spark-serviceaccount.yaml
kubectl apply -f configs/k8s/fluent-bit-config.yaml
kubectl apply -f configs/k8s/fluent-bit-daemonset.yaml
kubectl apply -f configs/k8s/billing-cronjob.yaml   # schedule
# or for ad-hoc:
kubectl apply -f configs/k8s/billing-job.yaml
```

### 3. Monitor Logs

* **Local**: DaemonSet outputs to node logs.
* **AWS**: Fluent Bit ships logs to CloudWatch under `/kubernetes/fluent-bit-logs`.

Port-forward the Spark UI if needed:

```bash
kubectl port-forward $(kubectl get pod -l spark-app=billing-aggregation -o name) 4040:4040
```

---

## 🧪 Testing

Run logic tests without Spark:

```bash
pytest tests/test_naive.py
pytest tests/test_mapreduce.py
```

---

## 📦 Deploy to AWS EKS

1. **Tag & push** Docker image to ECR:

   ```bash
   docker build -t $ECR_URI:latest -f docker/spark/Dockerfile .
   docker push $ECR_URI:latest
   ```
2. **Create `app-env`** Secret in EKS (with AWS-mode `.env`).
3. **Apply** the same `configs/k8s/` manifests.

Your Spark job will run on EKS in cluster mode with dynamic allocation.

---

© 2025 Distributed Billing Aggregation

