# AIOps Quality Project

Проєкт демонструє end-to-end MLOps/AIOps-пайплайн:
- FastAPI inference-сервіс із логуванням і метриками;
- Drift detection у рантаймі (демо-реалізація, розширюється до Alibi Detect/GE);
- GitLab CI retrain → build image → update Helm values;
- ArgoCD auto-sync Helm-чарту;
- Prometheus + Grafana для метрик;
- Loki + Promtail для логів.

## Швидка інструкція запуску і виконання (для здачі)

Це рекомендований порядок дій, щоб закрити всі acceptance-критерії.

### 0) Передумови

Потрібно мати встановлені: `python3.11+`, `docker`, `kubectl`, `helm`, доступ до `GitLab` і Kubernetes кластера.

Перевірка:
```bash
python --version
docker --version
kubectl version --client
helm version
```

### 1) Локальний запуск FastAPI

```bash
cd aiops-quality-project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python model/train.py
MODEL_PATH=artifacts/model.pkl uvicorn app.main:app --host 0.0.0.0 --port 8000
```

В іншому терміналі:
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2],"request_id":"local-test-1"}'
```

### 2) Підготовка значень перед деплоєм

Оновіть у `helm/values.yaml`:
- `image.repository` -> ваш GitLab Registry;
- `image.tag` -> початковий тег (наприклад `latest`);
- `env.DRIFT_WEBHOOK_URL` -> webhook GitLab trigger (опційно).

Оновіть у `argocd/application.yaml`:
- `spec.source.repoURL` -> URL вашого репозиторію;
- `spec.source.targetRevision` -> гілка (`main`);
- `spec.destination.namespace` -> namespace (`aiops`).

### 3) Збірка і пуш Docker-образу

```bash
export IMAGE_REPO="registry.gitlab.com/<group>/<project>/aiops-quality-service"
export IMAGE_TAG="manual-$(date +%Y%m%d%H%M)"
docker build -t "$IMAGE_REPO:$IMAGE_TAG" .
docker push "$IMAGE_REPO:$IMAGE_TAG"
```

Після цього проставте цей тег у `helm/values.yaml`.

### 4) Деплой у кластер (Helm + ArgoCD)

Ручний Helm smoke-test:
```bash
helm upgrade --install aiops-quality-service ./helm -n aiops --create-namespace
kubectl -n aiops get pods
kubectl -n aiops get svc
```

ArgoCD (GitOps):
```bash
kubectl apply -f argocd/application.yaml
kubectl -n argocd get application aiops-quality-service
```

### 5) Перевірка API в кластері

```bash
kubectl -n aiops port-forward svc/aiops-quality-service-aiops-quality-service 8000:8000
```

В іншому терміналі:
```bash
curl http://127.0.0.1:8000/health
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[9.9,9.9,9.9,9.9],"request_id":"k8s-test-1"}'
```

### 6) Перевірка логування і drift

```bash
kubectl -n aiops logs deploy/aiops-quality-service-aiops-quality-service -f
```

Щоб швидше побачити спрацювання drift, тимчасово зменште поріг:
```yaml
env:
  DRIFT_THRESHOLD: "0.1"
```

Повторіть кілька запитів на `/predict` і перевірте логи на `Drift detected`.

### 7) Перевірка метрик у Prometheus/Grafana

- Переконайтеся, що Prometheus скрапить `/metrics` (через `ServiceMonitor` або `additionalScrapeConfigs.yaml`).
- Імпортуйте `grafana/dashboards.json`.
- Перевірте панелі:
  - Requests/min
  - P95 latency
  - Drift events total
  - Drift events/min

### 8) Перевірка retrain у GitLab CI

Запустіть pipeline вручну (`Run pipeline`) або trigger webhook:
1. `retrain-model`;
2. `build-image`;
3. `update-helm-chart`.

Очікуваний результат:
- новий `artifacts/model.pkl`;
- новий Docker image tag;
- оновлений `helm/values.yaml` у Git;
- ArgoCD синхронізує новий реліз.

### 9) Що показати на здачі

Мінімальний набір доказів:
- успішний `curl /predict` через `kubectl port-forward`;
- логи `kubectl logs` з prediction і drift-подією;
- Grafana панелі з трафіком і latency;
- успішний GitLab pipeline retrain/build/release;
- ArgoCD статус `Synced` і `Healthy`.

## 1) Архітектура

1. Клієнт викликає `POST /predict`.
2. Сервіс логує вхідні дані, рахує prediction через `predict(data)`.
3. Виконується перевірка drift (`detect_drift(...)`).
4. Drift-івент інкрементує Prometheus метрику `inference_drift_events_total`.
5. За потреби зовнішній webhook тригерить GitLab `retrain-model`.
6. CI генерує нову модель, збирає Docker image, оновлює `helm/values.yaml`.
7. ArgoCD auto-sync застосовує оновлений чарт у кластер.

## 2) Структура

```text
aiops-quality-project/
├── app/main.py
├── model/train.py
├── helm/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── argocd/application.yaml
├── prometheus/additionalScrapeConfigs.yaml
├── grafana/dashboards.json
├── loki/promtail-config.yaml
├── .gitlab-ci.yml
└── README.md
```

## 3) Локальний запуск

```bash
cd aiops-quality-project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python model/train.py
MODEL_PATH=artifacts/model.pkl uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 4) Тестовий запит

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2],"request_id":"req-1"}'
```

Очікувана відповідь:
- `prediction` (числове передбачення),
- `drift_detected` (true/false),
- `request_id`,
- `model_path`.

## 5) Перевірка логування

### Локально
- Дивіться stdout процесу Uvicorn: там буде лог вхідних даних і відповіді.

### У Kubernetes
```bash
kubectl -n aiops logs deploy/<release-name>-aiops-quality-service -f
```

## 6) Перевірка drift detector

1. Встановіть нижчий поріг, наприклад у Helm values:
```yaml
env:
  DRIFT_THRESHOLD: "0.1"
```
2. Відправте кілька запитів на `/predict`.
3. Перевірте логи на повідомлення `Drift detected`.
4. Перевірте метрику `inference_drift_events_total` у Prometheus/Grafana.

## 7) Деплой через Helm + ArgoCD

### Helm (ручна перевірка)
```bash
helm upgrade --install aiops-quality-service ./helm -n aiops --create-namespace
kubectl -n aiops get pods
```

### ArgoCD (GitOps)
```bash
kubectl apply -f argocd/application.yaml
kubectl -n argocd get application aiops-quality-service
```

В `application.yaml` увімкнено:
- `automated.prune: true`
- `automated.selfHeal: true`

## 8) Перевірка `kubectl port-forward`

```bash
kubectl -n aiops port-forward svc/aiops-quality-service-aiops-quality-service 8000:8000
curl http://127.0.0.1:8000/health
```

## 9) Моніторинг і логування

### Prometheus
- Додайте `prometheus/additionalScrapeConfigs.yaml` у конфіг Prometheus.
- Або використовуйте ServiceMonitor з Helm-чарту (якщо встановлено kube-prometheus-stack).

### Grafana
- Імпортуйте `grafana/dashboards.json`.
- Панелі:
  - Requests/min
  - P95 latency
  - Drift events total
  - Drift events/min

### Loki + Promtail
- `loki/promtail-config.yaml` містить scrape pod-логів у namespace `aiops`.
- Для сервісу проставлені pod annotations (`promtail.io/scrape`, `promtail.io/job`) у Helm deployment.

## 10) GitLab CI retrain pipeline

`retrain-model`:
- запускає `python model/train.py`;
- генерує `artifacts/model.pkl`.

`build-image`:
- збирає і пушить новий образ;
- тег формату `${CI_COMMIT_SHORT_SHA}-${CI_PIPELINE_ID}`.

`update-helm-chart`:
- оновлює `helm/values.yaml` (`image.repository`, `image.tag`);
- пушить зміни в гілку, яку відслідковує ArgoCD.

Pipeline можна запустити:
- вручну (`Run pipeline`),
- через trigger token/webhook,
- від зовнішнього drift сервісу (через webhook endpoint GitLab Trigger API).

## 11) Як оновити модель

1. Запустити `retrain-model` job.
2. Переконатися, що `build-image` завершився успішно.
3. Переконатися, що `update-helm-chart` оновив тег у `helm/values.yaml`.
4. Перевірити, що ArgoCD синхронізував застосунок.
5. Перевірити нову версію через `/predict` та `/metrics`.

## 12) Checklist перевірки критеріїв

- [x] FastAPI inference з окремим `predict(data)`.
- [x] Drift detector з логуванням події.
- [x] GitLab CI job для retrain/build/release.
- [x] Helm chart із image/port/env.
- [x] ArgoCD application з auto-sync + self-heal.
- [x] Prometheus scrape конфіг + `/metrics`.
- [x] Grafana dashboard для requests/latency/drift.
- [x] Loki/Promtail конфіг для збору stdout.
