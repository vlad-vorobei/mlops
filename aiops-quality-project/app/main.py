import logging
import os
import pickle
import random
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

LOGGER = logging.getLogger("aiops-inference")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

MODEL_PATH = os.getenv("MODEL_PATH", "/models/model.pkl")
DRIFT_THRESHOLD = float(os.getenv("DRIFT_THRESHOLD", "0.7"))
DRIFT_WEBHOOK_URL = os.getenv("DRIFT_WEBHOOK_URL")

REQUEST_COUNT = Counter(
    "inference_requests_total",
    "Total number of inference requests",
    ["endpoint"],
)
DRIFT_COUNT = Counter(
    "inference_drift_events_total",
    "Total number of detected drift events",
)
LATENCY_SECONDS = Histogram(
    "inference_latency_seconds",
    "Inference request latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

app = FastAPI(title="AIOps Quality Inference Service", version="1.0.0")
MODEL = None


class PredictRequest(BaseModel):
    features: List[float] = Field(..., min_length=1)
    request_id: Optional[str] = None


class PredictResponse(BaseModel):
    prediction: float
    drift_detected: bool
    request_id: Optional[str] = None
    model_path: str


def load_model(path: str):
    """Load a pickle model or fallback to a lightweight mock."""
    if os.path.exists(path):
        with open(path, "rb") as model_file:
            return pickle.load(model_file)
    LOGGER.warning("Model file not found at %s. Falling back to mock model.", path)
    return None


def predict(data: List[float]) -> float:
    """Return model prediction for input features."""
    if MODEL is None:
        # deterministic mock prediction for demo mode
        return round(sum(data) / len(data), 4)

    if hasattr(MODEL, "predict"):
        prediction = MODEL.predict([data])[0]
        return float(prediction)

    raise RuntimeError("Loaded model does not support predict().")


def detect_drift(data: List[float], prediction: float) -> bool:
    """
    Simple drift heuristic:
    - uses random noise factor to imitate statistical detector output;
    - can be replaced by Alibi Detect / Great Expectations in production.
    """
    baseline_score = abs(prediction - (sum(data) / len(data)))
    synthetic_noise = random.uniform(0.0, 1.0) * 0.2
    score = min(1.0, baseline_score + synthetic_noise)
    drifted = score > DRIFT_THRESHOLD

    if drifted:
        DRIFT_COUNT.inc()
        LOGGER.warning("Drift detected (score=%.4f, threshold=%.2f)", score, DRIFT_THRESHOLD)
        if DRIFT_WEBHOOK_URL:
            # Webhook call intentionally omitted in demo template.
            LOGGER.info("Drift webhook configured: %s", DRIFT_WEBHOOK_URL)
        else:
            LOGGER.info("Drift detected without webhook target.")

    return drifted


@app.on_event("startup")
def startup_event():
    global MODEL
    MODEL = load_model(MODEL_PATH)
    LOGGER.info("Inference service started. model_path=%s", MODEL_PATH)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(payload: PredictRequest):
    REQUEST_COUNT.labels(endpoint="/predict").inc()
    started = time.perf_counter()

    try:
        LOGGER.info(
            "Incoming request request_id=%s features=%s",
            payload.request_id,
            payload.features,
        )
        prediction = predict(payload.features)
        drift_detected = detect_drift(payload.features, prediction)
    except Exception as exc:
        LOGGER.exception("Prediction failed: %s", exc)
        raise HTTPException(status_code=500, detail="Prediction failed") from exc
    finally:
        LATENCY_SECONDS.observe(time.perf_counter() - started)

    response = PredictResponse(
        prediction=prediction,
        drift_detected=drift_detected,
        request_id=payload.request_id,
        model_path=MODEL_PATH,
    )
    LOGGER.info("Prediction response request_id=%s output=%s", payload.request_id, response.dict())
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
