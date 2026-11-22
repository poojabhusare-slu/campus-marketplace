from fastapi import FastAPI

app = FastAPI(title="Campus Marketplace API")


@app.get("/health")
def health_check():
    return {"status": "ok"}