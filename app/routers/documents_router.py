from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.policy_models import PolicyDocument
from app.rag import ingest, vector_store

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(title: str = "", doc_type: str = "", file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    try:
        text = ingest.extract_text(file.filename, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    display_title = title or file.filename
    record = PolicyDocument(title=display_title, doc_type=doc_type, filename=file.filename)
    db.add(record)
    db.commit()
    db.refresh(record)

    chunk_count = vector_store.add_document(record.id, display_title, text)
    record.chunk_count = chunk_count
    db.commit()

    return {"id": record.id, "title": record.title, "chunks_indexed": chunk_count}


@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    return db.query(PolicyDocument).order_by(PolicyDocument.ingested_at.desc()).all()


@router.get("/search")
def search(q: str):
    return vector_store.search(q)
