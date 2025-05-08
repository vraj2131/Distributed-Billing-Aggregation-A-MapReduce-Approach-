# Distributed Billing Aggregation Pipeline

This project implements a scalable billing aggregation system using Apache Spark. We ingest raw API logs, compute per-user total durations and costs for different API tasks via MapReduce functions, and compare a naive single-process baseline with a distributed Spark implementation. Our goal is to provide an end-to-end pipeline that can run locally (via Docker Compose), on Kubernetes (Kind or EKS), or in production on AWS—with dynamic executor allocation and integrated logging.

---

## ⚙️ Prerequisites

- Docker & Docker Compose  
- kubectl & Kubernetes (Kind or AWS EKS)  
- AWS CLI (for EKS mode)  
- Python 3.8+ with `pip`

---

## 📝 Setup

1. **Environment Variables**  
   Ensure you have a `.env` file at the root with all the required settings:
   - `ENVIRONMENT=naive | local | kub | aws`
   - Task rates like `RATE_login=0.005`
   - AWS credentials (for EKS mode)
   - `LOG_LEVEL=INFO` (optional)

2. **Install Python Dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 🐍 Naive Approach

Sequential Python script for baseline billing aggregation.

```bash
time python src/mapreduce_billing/naive_aggregation.py      --input-path ./data/api_logs.txt      --output-path ./data/billing_naive.txt
```

---

## 💻 Local Spark Standalone Mode

Run Spark in standalone mode using Docker Compose.

### Configuration

- Set `ENVIRONMENT=local` in `.env`
- In `config.py`, set `ENVIRONMENT = "local"` (line 15)
- In `spark_job.py`, set `ENVIRONMENT = "local"` (line 24)
- In `scripts/submit_spark_job.sh`, make sure line 125 is:
  `/app/src/mapreduce_billing/spark_job.py \`

### Commands

```bash
chmod +x scripts/submit_spark_job.sh
docker-compose up -d spark-master spark-worker history-server
docker-compose run --rm spark-submit
docker-compose down
```

---

## ☸️ Spark on Kubernetes (Kind)

Run Spark in cluster mode inside a local Kind-based Kubernetes cluster.

### Configuration

- Set `ENVIRONMENT=kub` in `.env`
- In `config.py`, set `ENVIRONMENT = "kub"` (line 15)
- In `spark_job.py`, set `ENVIRONMENT = "kub"` (line 24)
- In `scripts/submit_spark_job.sh`, make sure line 125 is:
  `local:///app/src/mapreduce_billing/spark_job.py \`

---

### Build & Create Cluster

```bash
docker build -t distributed-billing-spark:latest .
kind create cluster --name spark-cluster --config config/k8s/kind-spark-cluster.yaml
kind load docker-image distributed-billing-spark:latest --name spark-cluster
kubectl config use-context kind-spark-cluster
kubectl get nodes
```

---

### Role Binding & ConfigMap

```bash
kubectl delete clusterrolebinding spark-sa-admin 2>/dev/null || true
kubectl create clusterrolebinding spark-sa-admin --clusterrole=admin --serviceaccount=default:spark-serviceaccount
kubectl delete configmap app-env
kubectl create configmap app-env --from-env-file=.env
```

---

### Apply Manifests

```bash
kubectl apply -f config/k8s/spark-serviceaccount.yaml
kubectl apply -f config/k8s/spark-master-ui-svc.yaml
kubectl apply -f config/k8s/history-server.yaml
kubectl apply -f config/k8s/fluent-bit-config.yaml
kubectl apply -f config/k8s/fluent-bit-daemonset.yaml
kubectl apply -f config/k8s/spark-history-ui-svc.yaml
```

---

### Start History Server (New Terminal)

```bash
kubectl config use-context kind-spark-cluster
kubectl port-forward svc/spark-history-ui 18080:18080
```

Visit `http://localhost:18080` to view the Spark UI.

---

### Run Spark Job

```bash
kubectl apply -f config/k8s/billing-job.yaml
```

---

### Monitor Job & View Logs

```bash
kubectl get pods --watch
kubectl logs $(kubectl get pods -l job-name=billing-on-demand -o jsonpath='{.items[0].metadata.name}') -c spark-submit
kubectl logs billing-aggregation-$(kubectl get pods -l spark-app-name=billing-aggregation,spark-role=driver -o jsonpath='{.items[0].metadata.name}' | cut -d'-' -f3)-driver -c spark-kubernetes-driver
```

---

### Cleanup

```bash
kubectl delete job billing-on-demand
kubectl delete -f config/k8s/history-server.yaml
kubectl delete -f config/k8s/spark-master-ui-svc.yaml
kubectl delete -f config/k8s/spark-serviceaccount.yaml
kubectl delete -f config/k8s/spark-history-ui-svc.yaml
kubectl delete configmap app-env
kind delete cluster --name spark-cluster
```

---

## ☁️ Spark on AWS EKS (Overview)

For AWS EKS deployment, we created an EKS cluster with a managed node group using the AWS CLI. We built and pushed our Docker image to Amazon ECR, configured kubeconfig for EKS, created a ConfigMap for environment variables, and applied the same billing job manifest. The Spark job ran in cluster mode with dynamic executor allocation, fetched logs from S3, and streamed job progress to CloudWatch. The Spark History UI was accessed via port forwarding.

---

## 🧪 Testing

```bash
pytest tests/test_naive.py
pytest tests/test_mapreduce.py
```

---

## 📁 Output

Output files (e.g. `billing_results_*.txt`) are saved to:

```bash
./data/results/
```

---

© 2025 Distributed Billing Aggregation – Scalable billing logic for logs, built to run anywhere.