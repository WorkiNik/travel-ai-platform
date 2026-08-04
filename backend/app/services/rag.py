import logging

from google.genai import types, errors
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk, EMBEDDING_DIM
from app.services.ai import client

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """
    Режет текст на смысловые куски по абзацам, стараясь не превышать max_chars.
    Простая, но рабочая стратегия для MVP — соседние короткие абзацы объединяются.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


async def embed_text(text: str) -> list[float]:
    try:
        result = await client.aio.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        return result.embeddings[0].values
    except errors.APIError as e:
        logger.error(f"Embedding error [{e.code}]: {e.message}")
        raise


async def index_document(db: Session, document: Document, content: str) -> int:
    """Режет документ на чанки, эмбеддит каждый и сохраняет в БД. Возвращает число чанков."""
    chunks = chunk_text(content)
    for idx, chunk in enumerate(chunks):
        embedding = await embed_text(chunk)
        db.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=chunk,
                embedding=embedding,
            )
        )
    db.commit()
    return len(chunks)


async def search_similar_chunks(
    db: Session, user_id: int, query: str, top_k: int = 4
) -> list[str]:
    """Находит top_k наиболее релевантных чанков документов пользователя по смыслу запроса."""
    query_embedding = await embed_text(query)

    results = (
        db.query(DocumentChunk)
        .join(Document)
        .filter(Document.user_id == user_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
    return [r.content for r in results]


async def build_context_block(db: Session, user_id: int, query: str) -> str:
    """Собирает найденные чанки в текстовый блок для подмешивания в system prompt."""
    try:
        chunks = await search_similar_chunks(db, user_id, query)
    except Exception:
        logger.exception("RAG search failed, continuing without context")
        return ""

    if not chunks:
        return ""

    joined = "\n---\n".join(chunks)
    return (
        "The user has uploaded the following documents. Use this information "
        "if it's relevant to answering their question:\n\n" + joined
    )