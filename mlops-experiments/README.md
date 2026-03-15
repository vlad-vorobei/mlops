# MLOps Experiments: MLflow + PushGateway + Grafana

Трекінг ML-експериментів через MLflow, метрики в Prometheus PushGateway та Grafana.

## Структура проєкту

```
mlops-experiments/
├── argocd/
│   └── applications/
│       ├── mlflow.yaml
│       ├── minio.yaml
│       ├── postgres.yaml
│       ├── pushgateway.yaml
│       └── kube-prometheus-stack.yaml
├── experiments/
│   ├── train_and_push.py
│   ├── requirements.txt
│   └── .env.example
├── best_model/
└── README.md
```

## Передумови

- Kubernetes-кластер з доступом через `kubectl`
- MLflow, PushGateway (і за бажанням MinIO, PostgreSQL) розгорнуті в кластері (наприклад, через ArgoCD Applications з `argocd/applications/`)
- Python 3, `pip`

## Перевірка MLflow і PushGateway у кластері

```bash
kubectl get pods -n application
kubectl get pods -n monitoring
kubectl get svc -n application
kubectl get svc -n monitoring
```

Очікується: поди `mlflow-*`, `minio-*`, `mlflow-postgres-*` в `application`; поди `pushgateway-*` в `monitoring`.

## Port-forward

Перед запуском скрипта:

```bash
kubectl port-forward -n application svc/mlflow 5000:5000
kubectl port-forward -n monitoring svc/pushgateway 9091:9091
kubectl port-forward -n application svc/minio 9000:9000
```

MLflow UI: **http://localhost:5000**, PushGateway: **http://localhost:9091**.

## Запуск train_and_push.py

```bash
cd experiments
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python train_and_push.py
```

Якщо pip ставить пакети в `~/.local` замість venv:

```bash
./venv/bin/pip install -r requirements.txt
./venv/bin/python train_and_push.py
```

У `.env`: `MLFLOW_TRACKING_URI=http://localhost:5000`, `PUSHGATEWAY_URL=http://localhost:9091`. Для артефактів у MinIO — port-forward на 9000 і відповідні змінні в `.env`.

## Метрики в Grafana

Port-forward на Grafana (ім'я сервісу залежить від встановлення):

```bash
kubectl get svc -A | grep -i grafana
kubectl port-forward -n <namespace> svc/<grafana-svc> 3000:80
```

Відкрити **http://localhost:3000** → **Explore** → джерело **Prometheus** → запити `mlflow_accuracy`, `mlflow_loss`.

Якщо Grafana немає в кластері — метрики видно в PushGateway: **http://localhost:9091** (вкладка Metrics).

## Скриншоти
Можна знайти в каталозі pictures/ls-9
