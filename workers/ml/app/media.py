from pathlib import Path
import subprocess
import cv2
import librosa
import numpy as np
from .config import get_settings


settings = get_settings()


def sample_video_frames(video_path: Path) -> list[np.ndarray]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("Unable to open video for frame sampling")
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    step = max(frame_count // settings.max_video_frames, 1)
    frames: list[np.ndarray] = []
    index = 0
    while len(frames) < settings.max_video_frames:
        ok, frame = capture.read()
        if not ok:
            break
        if index % step == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        index += 1
    capture.release()
    if not frames:
        raise ValueError("No frames sampled from media")
    return frames


def extract_audio(media_path: Path, output_path: Path) -> Path:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(media_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return output_path


def load_audio_windows(audio_path: Path) -> tuple[list[np.ndarray], int]:
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    window = settings.audio_window_seconds * sr
    if len(audio) < window:
        return [audio], sr
    windows = [audio[start : start + window] for start in range(0, len(audio) - window + 1, window)]
    return windows, sr

