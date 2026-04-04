# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# Keep Python output unbuffered (good for HF Spaces logs)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# ── Runtime ───────────────────────────────────────────────────────────────────
# HuggingFace Spaces expects the app on port 7860
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
