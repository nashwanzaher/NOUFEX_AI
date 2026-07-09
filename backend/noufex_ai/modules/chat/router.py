from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from noufex_ai.deps import CurrentUserDep, SessionDep
from noufex_ai.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationList,
    ConversationMessages,
    ConversationRead,
    MessageRead,
)
from noufex_ai.modules.chat.service import ChatService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session: SessionDep,
    user: CurrentUserDep,
) -> ChatResponse:
    service = ChatService(session)
    result = await service.chat(
        tenant_id=user.tenant_id,
        user_id=user.id,
        request=payload,
    )
    return ChatResponse(
        conversation_id=result["conversation_id"],
        message=MessageRead.model_validate(result["message"]),
        tokens_used=result["tokens_used"],
        model=result["model"],
        rag_context_used=result["rag_context_used"],
        tool_calls_executed=result.get("tool_calls_executed"),
        tool_results=None,
    )


@router.post("/stream")
async def stream_chat(
    payload: ChatRequest,
    session: SessionDep,
    user: CurrentUserDep,
) -> StreamingResponse:
    service = ChatService(session)

    async def event_generator():
        async for chunk in service.stream_chat(
            tenant_id=user.tenant_id,
            user_id=user.id,
            request=payload,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=ConversationList)
async def list_conversations(
    session: SessionDep,
    user: CurrentUserDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> ConversationList:
    service = ChatService(session)
    items, total = await service.list_conversations(
        tenant_id=user.tenant_id, user_id=user.id, offset=offset, limit=limit
    )
    return ConversationList(
        items=[ConversationRead.model_validate(c) for c in items],
        total=total,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationMessages)
async def get_conversation(
    conversation_id: UUID,
    session: SessionDep,
    user: CurrentUserDep,
) -> ConversationMessages:
    from noufex_ai.modules.chat.models import Message
    from sqlmodel import select

    service = ChatService(session)
    conv = await service.get_conversation_messages(
        tenant_id=user.tenant_id, user_id=user.id, conversation_id=conversation_id
    )

    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = list(result.scalars().all())

    return ConversationMessages(
        conversation=ConversationRead.model_validate(conv),
        messages=[MessageRead.model_validate(m) for m in messages],
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    session: SessionDep,
    user: CurrentUserDep,
) -> None:
    service = ChatService(session)
    await service.delete_conversation(
        tenant_id=user.tenant_id, user_id=user.id, conversation_id=conversation_id
    )
