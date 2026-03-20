from fastapi import FastAPI

app = FastAPI(title="Backend Challenge API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
