from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.auth import get_current_user
from app.services.rag import index_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_doc = Document(user_id=current_user.id, title=doc_in.title)
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    try:
        chunk_count = await index_document(db, new_doc, doc_in.content)
    except Exception:
        db.delete(new_doc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to process document (embedding service unavailable).",
        )

    return DocumentResponse(
        id=new_doc.id,
        title=new_doc.title,
        created_at=new_doc.created_at,
        chunk_count=chunk_count,
    )


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    return [
        DocumentResponse(
            id=d.id, title=d.title, created_at=d.created_at, chunk_count=len(d.chunks)
        )
        for d in docs
    ]


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(doc)
    db.commit()