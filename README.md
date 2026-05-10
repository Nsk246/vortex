# VORTEX

VORTEX is a production-oriented, multi-agent deepfake tribunal for enterprise media forensics.

It is a separate app/repo from ThinkTrace. The system accepts video and audio evidence, runs real ML jurors for visual and acoustic manipulation, uses cost-aware LLM/search calls for contextual verification, streams tribunal events live, and persists an auditable final verdict.

## Monorepo

```text
apps/web              Next.js courtroom UI
apps/api              FastAPI API, auth, orgs, cases, WebSockets
workers/ml            GPU/CPU ML inference workers
workers/orchestrator  Celery tribunal orchestration and judge logic
packages/shared       Shared TypeScript event/API contracts
infra                 Docker, deployment, and future Kubernetes assets
```

## What is real in v1

- Real media ingestion through FastAPI uploads.
- Real PostgreSQL persistence for users, orgs, cases, media, juror runs, audit events, and verdicts.
- Real Redis queue/pub-sub backbone.
- Real Celery task boundaries for orchestration and ML inference.
- Real ML integration points for visual and acoustic detectors. The workers load configured production model weights at runtime and fail closed when required models are missing.
- Real LLM/search integration boundary for transcript/context reasoning.
- Real live tribunal stream via WebSockets.
- Real enterprise controls: org isolation, JWT auth, quotas, signed object-storage hooks, and audit trails.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Fill required secrets and model paths.
3. Start local services:

```bash
docker compose up --build
```

4. Open `http://localhost:3000`.

## Required Production Configuration

VORTEX is intentionally configured to reject production runs without real detectors and secrets.

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `S3_ENDPOINT_URL`
- `S3_BUCKET`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `SEARCH_API_KEY`
- `VISUAL_FACE_MODEL_PATH`
- `VISUAL_GENERAL_MODEL_PATH`
- `AUDIO_MODEL_ID`

## Model License Gate

Before hosted production use, every checkpoint must have its license recorded in `model_registry`. Non-commercial checkpoints may be used for local research and evaluation only.

