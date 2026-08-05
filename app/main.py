import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.core.config import API_HOST, API_PORT
from app.services import llm_service
from app.rag import vector_store
from app.routers import documents_router, scenarios_router, analysis_router

app = FastAPI(title="PolicyMind AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(documents_router.router)
app.include_router(scenarios_router.router)
app.include_router(analysis_router.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "llm_available": llm_service.is_available(), "policy_chunks": vector_store.total_chunks()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)
