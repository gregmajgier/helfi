from fastapi import FastAPI

from .auth.router import router as auth_router

app = FastAPI(title="Health App API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health():
    return {"status": "ok"}
