import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.auth import get_current_user
from app.services.ai import get_ai_response, stream_ai_response, AIServiceError
from app.services.rag import build_context_block

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_conv = Conversation(user_id=current_user.id, title=conv_in.title)
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.get("/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = (
        db.query(Conversation)
        .options(joinedload(Conversation.messages))
        .filter(Conversation.id == conv_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.post("/{conv_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conv_id: int,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    user_message = Message(conversation_id=conv_id, role="user", content=msg_in.content)
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
        .all()
    )
    messages_for_ai = [{"role": m.role, "content": m.content} for m in history]

    # RAG: подмешиваем релевантные куски из документов пользователя
    context = await build_context_block(db, current_user.id, msg_in.content)

    try:
        ai_reply = await get_ai_response(messages_for_ai, context=context)
    except AIServiceError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    assistant_message = Message(conversation_id=conv_id, role="assistant", content=ai_reply)
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return assistant_message


@router.post("/{conv_id}/messages/stream")
async def add_message_stream(
    conv_id: int,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    user_message = Message(conversation_id=conv_id, role="user", content=msg_in.content)
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
        .all()
    )
    messages_for_ai = [{"role": m.role, "content": m.content} for m in history]

    # RAG: подмешиваем релевантные куски из документов пользователя
    context = await build_context_block(db, current_user.id, msg_in.content)

    async def event_generator():
        full_text = ""
        try:
            async for chunk in stream_ai_response(messages_for_ai, context=context):
                full_text += chunk
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
        except AIServiceError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        assistant_message = Message(conversation_id=conv_id, role="assistant", content=full_text)
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        yield f"data: {json.dumps({'done': True, 'id': assistant_message.id, 'created_at': assistant_message.created_at.isoformat()})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")