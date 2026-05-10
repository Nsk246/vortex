# VORTEX Model Set

VORTEX uses real model inference and fails closed when required model configuration is missing. The initial hosted-safe model set favors permissive licenses and clear model cards over leaderboard theater.

## Recommended Initial Production Candidates

| Juror | Env var | Model | License | Why this one |
|---|---|---|---|---|
| Visual face/deepfake | `VISUAL_FACE_MODEL_PATH` | `shunda012/vit-deepfake-detector` | Apache-2.0 | ViT image classifier trained for deepfake face detection with reported precision around 85%. |
| Visual general synthetic media | `VISUAL_GENERAL_MODEL_PATH` | `capcheck/ai-human-generated-image-detection` | Apache-2.0 | Broader AI-vs-human generated image detector with documented Apache-2.0 lineage. Useful as the second visual ensemble member. |
| Acoustic anti-spoofing | `AUDIO_MODEL_ID` | `Gustking/wav2vec2-large-xlsr-deepfake-audio-classification` | Apache-2.0 | Wav2Vec2/XLS-R classifier with Transformers-compatible processor and safetensors weights for local inference. |

## Runtime Policy

- `VISUAL_MODEL_LICENSE=production-approved` and `AUDIO_MODEL_LICENSE=production-approved` are required for production.
- `ALLOW_REMOTE_MODEL_DOWNLOADS=false` by default. For production, pre-download models into the image or mounted model volume.
- For local first-run validation, set `ALLOW_REMOTE_MODEL_DOWNLOADS=true` only if you are comfortable downloading from Hugging Face at runtime.
- Record every hosted checkpoint in the database-backed model registry before serving enterprise traffic.

## Local Download Examples

```bash
python - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download("shunda012/vit-deepfake-detector", local_dir="models/visual/shunda012-vit-deepfake-detector")
snapshot_download("capcheck/ai-human-generated-image-detection", local_dir="models/visual/capcheck-ai-human-generated-image-detection")
snapshot_download("Gustking/wav2vec2-large-xlsr-deepfake-audio-classification", local_dir="models/audio/gustking-wav2vec2-large-xlsr-deepfake-audio-classification")
PY
```

Then set:

```bash
VISUAL_FACE_MODEL_PATH=/models/visual/shunda012-vit-deepfake-detector
VISUAL_GENERAL_MODEL_PATH=/models/visual/capcheck-ai-human-generated-image-detection
AUDIO_MODEL_ID=/models/audio/gustking-wav2vec2-large-xlsr-deepfake-audio-classification
ALLOW_REMOTE_MODEL_DOWNLOADS=false
```

## Explicitly Not Production Defaults

- `nii-yamagishilab/wav2vec-large-anti-deepfake`: strong-looking research model, but the model card lists `cc-by-nc-sa-4.0`, so it is not suitable for hosted commercial/enterprise use without separate permission.
- Any checkpoint with unclear training data, missing license, or non-commercial terms should remain research-only until reviewed.

## Sources

- `shunda012/vit-deepfake-detector`: https://huggingface.co/shunda012/vit-deepfake-detector
- `capcheck/ai-human-generated-image-detection`: https://huggingface.co/capcheck/ai-human-generated-image-detection
- `Gustking/wav2vec2-large-xlsr-deepfake-audio-classification`: https://huggingface.co/Gustking/wav2vec2-large-xlsr-deepfake-audio-classification
- `nii-yamagishilab/wav2vec-large-anti-deepfake`: https://huggingface.co/nii-yamagishilab/wav2vec-large-anti-deepfake
