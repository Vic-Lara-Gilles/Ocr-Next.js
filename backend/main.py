import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.logger import get_logger
from app.routes import process, results, upload, rag, auth

logger = get_logger("ocr.api")

app = FastAPI(title="OCR Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(process.router)
app.include_router(results.router)
app.include_router(rag.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %d (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
