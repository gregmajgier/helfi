# Health App backend

FastAPI service backing the health app's meal tracker (and future modules).

## Local development

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # edit as needed; defaults run entirely in-memory
    uvicorn app.main:app --reload

## Tests

    pytest tests/ -v

Tests always run against the in-memory repositories and fake OAuth/nutrition
estimators — no Azure or Anthropic credentials are required.

## Container

    docker build -t health-app-backend .
    docker run -p 8000:8000 --env-file .env health-app-backend
    curl http://localhost:8000/health
