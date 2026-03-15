#!/usr/bin/env python3
"""
Тренування моделей на Iris з різними параметрами.
Логування в MLflow, пуш метрик у Prometheus PushGateway, збереження кращої моделі в best_model/.
"""
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import mlflow
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

PARAM_GRID = [
    {"learning_rate": 0.001, "epochs": 50},
    {"learning_rate": 0.01, "epochs": 100},
    {"learning_rate": 0.05, "epochs": 150},
    {"learning_rate": 0.1, "epochs": 200},
]

EXPERIMENT_NAME = "Iris Classification"
BEST_MODEL_DIR = Path(__file__).resolve().parent.parent / "best_model"


def push_metrics_to_gateway(run_id: str, accuracy: float, loss: float, gateway_url: str) -> None:
    """Відправити accuracy та loss у PushGateway з міткою run_id."""
    registry = CollectorRegistry()
    g_accuracy = Gauge("mlflow_accuracy", "Accuracy from MLflow run", ["run_id"], registry=registry)
    g_loss = Gauge("mlflow_loss", "Loss from MLflow run", ["run_id"], registry=registry)
    g_accuracy.labels(run_id=run_id).set(accuracy)
    g_loss.labels(run_id=run_id).set(loss)
    push_to_gateway(gateway_url, job="mlflow_experiments", grouping_key={"run_id": run_id}, registry=registry)


def main() -> None:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    pushgateway_url = os.environ.get(
        "PUSHGATEWAY_URL",
        "http://localhost:9091",
    )

    mlflow.set_tracking_uri(tracking_uri)

    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
        print(f"✅ Створено експеримент '{EXPERIMENT_NAME}' (ID={experiment_id})")
    else:
        experiment_id = experiment.experiment_id
        print(f"ℹ Використовується експеримент '{EXPERIMENT_NAME}' (ID={experiment_id})")

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

    runs_summary = []

    for params in PARAM_GRID:
        learning_rate = params["learning_rate"]
        epochs = params["epochs"]

        with mlflow.start_run(experiment_id=experiment_id) as run:
            run_id = run.info.run_id
            mlflow.log_param("learning_rate", learning_rate)
            mlflow.log_param("epochs", epochs)

            model = LogisticRegression(max_iter=epochs, solver="lbfgs")
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)
            acc = accuracy_score(y_test, y_pred)
            loss = log_loss(y_test, y_proba)

            mlflow.log_metric("accuracy", acc)
            mlflow.log_metric("loss", loss)

            push_metrics_to_gateway(run_id, acc, loss, pushgateway_url)

            try:
                mlflow.sklearn.log_model(model, name="model")
            except Exception as e:
                print(f"  ⚠ Не вдалося зберегти артефакт у MinIO: {e}")
                print("  Переконайтесь, що порт 9000 проброшений: kubectl port-forward -n application svc/minio 9000:9000")

            runs_summary.append({"run_id": run_id, "accuracy": acc, "loss": loss})
            print(f"  Run {run_id[:8]}... accuracy={acc:.4f}, loss={loss:.4f}")

    best = max(runs_summary, key=lambda x: x["accuracy"])
    best_run_id = best["run_id"]
    print(f"\n✅ Найкращий run: {best_run_id} (accuracy={best['accuracy']:.4f})")

    try:
        client = mlflow.MlflowClient(tracking_uri=tracking_uri)
        artifact_path = client.download_artifacts(best_run_id, "model")
        BEST_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        dest = BEST_MODEL_DIR / "model"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(artifact_path, dest)
        print(f"✅ Модель скопійовано в {BEST_MODEL_DIR}/")
    except Exception as e:
        print(f"⚠ Не вдалося завантажити кращу модель у best_model/: {e}")
        print("  Для артефактів потрібен port-forward MinIO: kubectl port-forward -n application svc/minio 9000:9000")

    print("\n✅ Готово. Перевірте MLflow UI та Grafana → Explore → Prometheus (mlflow_accuracy, mlflow_loss).")


if __name__ == "__main__":
    main()
