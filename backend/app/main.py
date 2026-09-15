from fastapi import FastAPI

app = FastAPI(title="Health App API")


@app.get("/health")
async def health():
    return {"status": "ok"}
