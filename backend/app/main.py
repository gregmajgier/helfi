from fastapi import FastAPI

from .auth.router import router as auth_router
from .meals.router import router as meals_router

app = FastAPI(title="Health App API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(meals_router, prefix="/meals", tags=["meals"])


@app.get("/health")
async def health():
    return {"status": "ok"}
