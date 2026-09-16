from contextlib import asynccontextmanager

from fastapi import FastAPI

from .auth.router import router as auth_router
from .config import settings
from .db.cosmos import get_cosmos_client, init_cosmos
from .meals.router import router as meals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.db_backend == "cosmos":
        await init_cosmos(get_cosmos_client(), settings.cosmos_database_name)
    yield


app = FastAPI(title="Health App API", lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(meals_router, prefix="/meals", tags=["meals"])


@app.get("/health")
async def health():
    return {"status": "ok"}
