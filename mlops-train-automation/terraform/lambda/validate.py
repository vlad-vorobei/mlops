"""
Lambda-функція валідації вхідних даних для MLOps пайплайну.
У реальному житті: перевірка JSON-схеми, колонок CSV, Great Expectations тощо.
"""


def handler(event, context):
    print("Validating data...")
    # Умовна логіка: у повному пайплайні — schema validation або перевірка CSV
    return {
        "status": "valid",
        "event": event,
    }
