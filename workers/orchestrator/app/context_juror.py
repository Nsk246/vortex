import json
from openai import APIError, OpenAIError
from openai import OpenAI
from .config import get_settings


settings = get_settings()


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"confidence": 0.5, "weight": 0.3, "rationale": text, "evidence": []}


def _call_openai(client: OpenAI, model: str, prompt: dict) -> str:
    if hasattr(client, "responses"):
        response = client.responses.create(model=model, input=[prompt])
        return response.output_text
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return only strict JSON."},
            prompt,
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or "{}"


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
    try:
        return _extract_json(_call_openai(client, model, prompt))
    except (APIError, OpenAIError, AttributeError, ValueError) as exc:
        return {
            "confidence": 0.5,
            "weight": 0.2,
            "quality": {"llm_model": model, "provider_error": type(exc).__name__},
            "rationale": "Context juror used neutral fallback because the LLM provider call failed.",
            "evidence": [{"type": "provider_error", "message": str(exc)[:500]}],
        }
