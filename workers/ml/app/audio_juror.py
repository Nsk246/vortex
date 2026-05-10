from pathlib import Path
import tempfile
import time
import librosa
import numpy as np
import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
from .config import get_settings
from .media import extract_audio, load_audio_windows
from .schemas import JurorFinding, MediaJob
from .storage import download_to_temp


settings = get_settings()
_extractor = None
_model = None
_device = None


def load_model():
    global _extractor, _model, _device
    settings.require_production_models()
    if _model is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        local_only = not settings.allow_remote_model_downloads
        _extractor = AutoFeatureExtractor.from_pretrained(settings.audio_model_id, local_files_only=local_only)
        _model = AutoModelForAudioClassification.from_pretrained(settings.audio_model_id, local_files_only=local_only).to(_device)
        _model.eval()
    return _extractor, _model, _device


def _fake_probability(logits: torch.Tensor, id2label: dict) -> float:
    probs = torch.softmax(logits, dim=-1)[0]
    fake_indices = [idx for idx, label in id2label.items() if "fake" in label.lower() or "spoof" in label.lower()]
    if not fake_indices:
        fake_indices = [int(torch.argmax(probs).item())]
    return float(max(probs[int(idx)].item() for idx in fake_indices))


def analyze_audio(job: MediaJob) -> JurorFinding:
    start = time.perf_counter()
    extractor, model, device = load_model()
    media_path = download_to_temp(job.storage_key, suffix=Path(job.filename).suffix)
    audio_path = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name)
    if not job.content_type.startswith("audio/"):
        extract_audio(media_path, audio_path)
    else:
        audio_path = media_path
    windows, sr = load_audio_windows(audio_path)
    scores: list[float] = []
    rms_values: list[float] = []
    clipping_ratios: list[float] = []
    with torch.no_grad():
        for window in windows:
            rms_values.append(float(np.sqrt(np.mean(np.square(window)))))
            clipping_ratios.append(float(np.mean(np.abs(window) > 0.98)))
            inputs = extractor(window, sampling_rate=sr, return_tensors="pt", padding=True)
            inputs = {key: value.to(device) for key, value in inputs.items()}
            outputs = model(**inputs)
            scores.append(_fake_probability(outputs.logits, model.config.id2label))
    confidence = float(np.mean(scores))
    snr_proxy = float(np.mean(rms_values))
    clipping = float(np.mean(clipping_ratios))
    weight = max(0.15, min(1.0, 0.8 + snr_proxy - (clipping * 2)))
    return JurorFinding(
        juror_name="acoustic",
        confidence=confidence,
        weight=weight,
        quality={
            "window_count": len(windows),
            "sample_rate": sr,
            "rms_proxy": snr_proxy,
            "clipping_ratio": clipping,
            "latency_ms": round((time.perf_counter() - start) * 1000),
        },
        evidence=[
            {"window_index": idx, "fake_probability": score}
            for idx, score in sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:8]
        ],
        rationale="Acoustic juror aggregated anti-spoofing probabilities across normalized speech windows.",
        model_versions=[f"audio:{settings.audio_model_id}"],
    )
