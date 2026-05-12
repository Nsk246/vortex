from pathlib import Path
import time
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
from .config import get_settings
from .media import sample_video_frames
from .schemas import JurorFinding, MediaJob
from .storage import download_to_temp


settings = get_settings()
_face_model = None
_general_model = None


def _load_torchscript_model(path: str):
    model_path = Path(path)
    if not model_path.exists():
        raise RuntimeError(f"Configured model does not exist: {model_path}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = torch.jit.load(str(model_path), map_location=device)
    model.eval()
    return {"kind": "torchscript", "model": model, "device": device, "id": path}


def _load_transformers_model(model_id: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    local_only = not settings.allow_remote_model_downloads
    processor = AutoImageProcessor.from_pretrained(model_id, local_files_only=local_only)
    model = AutoModelForImageClassification.from_pretrained(model_id, local_files_only=local_only).to(device)
    model.eval()
    return {"kind": "transformers", "processor": processor, "model": model, "device": device, "id": model_id}


def _load_visual_model(model_ref: str):
    if Path(model_ref).exists():
        return _load_torchscript_model(model_ref)
    return _load_transformers_model(model_ref)


def load_models():
    global _face_model, _general_model
    settings.require_production_models()
    if _face_model is None:
        _face_model = _load_visual_model(settings.visual_face_model_path)
    if _general_model is None:
        _general_model = _load_visual_model(settings.visual_general_model_path)
    return _face_model, _general_model


def _fake_probability_from_labels(logits: torch.Tensor, id2label: dict) -> float:
    probs = torch.softmax(logits, dim=-1)[0]
    fake_indices = [
        int(idx)
        for idx, label in id2label.items()
        if any(token in label.lower() for token in ("fake", "deepfake", "ai", "generated", "synthetic"))
        and "real" not in label.lower()
        and "human" not in label.lower()
    ]
    if not fake_indices:
        fake_indices = [int(torch.argmax(probs).item())]
    return float(max(probs[idx].item() for idx in fake_indices))


def _predict(model_bundle: dict, frames: list[np.ndarray]) -> list[float]:
    model = model_bundle["model"]
    device = model_bundle["device"]
    if model_bundle["kind"] == "transformers":
        processor = model_bundle["processor"]
        scores: list[float] = []
        with torch.no_grad():
            for frame in frames:
                image = Image.fromarray(frame)
                inputs = processor(images=image, return_tensors="pt")
                inputs = {key: value.to(device) for key, value in inputs.items()}
                outputs = model(**inputs)
                scores.append(_fake_probability_from_labels(outputs.logits, model.config.id2label))
        return scores

    transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    scores: list[float] = []
    with torch.no_grad():
        for frame in frames:
            image = Image.fromarray(frame)
            tensor = transform(image).unsqueeze(0).to(device)
            logits = model(tensor)
            if isinstance(logits, tuple):
                logits = logits[0]
            prob = torch.sigmoid(logits.flatten()[0]).item()
            scores.append(float(prob))
    return scores


def analyze_visual(job: MediaJob) -> JurorFinding:
    start = time.perf_counter()
    face_model, general_model = load_models()
    media_path = download_to_temp(job.storage_key, suffix=Path(job.filename).suffix)
    frames = sample_video_frames(media_path)
    face_scores = _predict(face_model, frames)
    general_scores = _predict(general_model, frames)
    combined = [(face * 0.6) + (general * 0.4) for face, general in zip(face_scores, general_scores)]
    top_count = max(1, min(8, len(combined) // 10 or 1))
    top_scores = sorted(combined, reverse=True)[:top_count]
    aggregate_mean = float(np.mean(combined))
    aggregate_p90 = float(np.quantile(combined, 0.9))
    aggregate_p95 = float(np.quantile(combined, 0.95))
    face_p95 = float(np.quantile(face_scores, 0.95))
    general_p95 = float(np.quantile(general_scores, 0.95))
    top_mean = float(np.mean(top_scores))
    confidence = float(max(aggregate_mean, aggregate_p90, aggregate_p95, top_mean * 0.95, face_p95 * 0.75, general_p95))
    variance = float(np.var(combined))
    visibility_weight = min(len(frames) / max(settings.max_video_frames, 1), 1.0)
    stability_penalty = min(variance * 0.5, 0.2)
    weight = max(0.1, min(1.0, visibility_weight - stability_penalty))
    top_indices = sorted(range(len(combined)), key=lambda idx: combined[idx], reverse=True)[:5]
    return JurorFinding(
        juror_name="visual",
        confidence=confidence,
        weight=weight,
        quality={
            "sampled_frames": len(frames),
            "score_variance": variance,
            "aggregate_mean": aggregate_mean,
            "aggregate_p90": aggregate_p90,
            "aggregate_p95": aggregate_p95,
            "top_frame_mean": top_mean,
            "face_detector_p95": face_p95,
            "general_detector_p95": general_p95,
            "latency_ms": round((time.perf_counter() - start) * 1000),
        },
        evidence=[
            {
                "frame_index": idx,
                "face_detector_score": face_scores[idx],
                "general_detector_score": general_scores[idx],
                "combined_score": combined[idx],
            }
            for idx in top_indices
        ],
        rationale="Visual juror preserved upper-percentile face-forgery and synthetic-image signals across sampled frames.",
        model_versions=[
            f"face:{settings.visual_face_model_path}",
            f"general:{settings.visual_general_model_path}",
        ],
    )
