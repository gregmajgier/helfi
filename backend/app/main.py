from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth.router import router as auth_router
from .config import settings, validate_production_settings
from .db.cosmos import close_cosmos_client, get_cosmos_client, init_cosmos
from .meals.router import router as meals_router
from .workouts.router import router as workouts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_settings(settings)
    if settings.db_backend == "cosmos":
        await init_cosmos(get_cosmos_client(), settings.cosmos_database_name)
    yield
    if settings.db_backend == "cosmos":
        await close_cosmos_client()


app = FastAPI(title="Health App API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "422", "message": "validation error"}},
    )


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(meals_router, prefix="/meals", tags=["meals"])
app.include_router(workouts_router, prefix="/workouts", tags=["workouts"])


@app.get("/health")
async def health():
    return {"status": "ok"}
