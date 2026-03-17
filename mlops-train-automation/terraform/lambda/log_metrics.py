"""
Lambda-функція логування метрик для MLOps пайплайну.
У реальному житті: запит до MLflow API, mlflow.log_metric(...) тощо.
"""


def handler(event, context):
    print("Logging metrics to MLflow...")
    # Умовна логіка: тут можна було б зробити requests.post(...) до MLflow
    return {
        "status": "logged",
        "event": event,
    }
