from fastapi import FastAPI

app = FastAPI(title="VeXe Backend")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
