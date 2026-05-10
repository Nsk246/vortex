import json
from openai import OpenAI
from .config import get_settings


settings = get_settings()


def analyze_context(transcript: str | None, visual_summary: dict, audio_summary: dict, contested: bool = False) -> dict:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for Context Juror")
    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.openai_contested_model if contested else settings.openai_reasoning_model
    prompt = {
        "role": "user",
        "content": (
            "You are the Context Juror in a deepfake tribunal. Return strict JSON with "
            "confidence, weight, rationale, and evidence. Evaluate semantic consistency, "
            "speaker/context claims, transcript anomalies, and whether visual/audio jurors disagree.\n\n"
            f"Transcript:\n{transcript or '[no transcript available]'}\n\n"
            f"Visual summary:\n{visual_summary}\n\nAudio summary:\n{audio_summary}"
        ),
    }
    response = client.responses.create(model=model, input=[prompt])
    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError:
        return {"confidence": 0.5, "weight": 0.3, "rationale": response.output_text, "evidence": []}
