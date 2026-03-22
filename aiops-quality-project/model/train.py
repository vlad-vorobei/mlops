import os
import pickle
from datetime import datetime, timezone

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression


def train_and_export(output_path: str) -> str:
    dataset = load_iris()
    model = LogisticRegression(max_iter=300)
    model.fit(dataset.data, dataset.target)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as model_file:
        pickle.dump(model, model_file)

    return output_path


if __name__ == "__main__":
    model_path = os.getenv("MODEL_OUTPUT_PATH", "artifacts/model.pkl")
    exported_path = train_and_export(model_path)
    print(
        f"[{datetime.now(timezone.utc).isoformat()}] Model retraining complete. "
        f"Exported to {exported_path}"
    )
