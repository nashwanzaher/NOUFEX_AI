from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from noufex_ai.deps import CurrentUserDep, SessionDep, require_scope
from noufex_ai.modules.rag.schemas import (
    DocumentList,
    DocumentRead,
    RAGSearchRequest,
    RAGSearchResponse,
)
from noufex_ai.modules.rag.service import RAGService

router = APIRouter()


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    session: SessionDep = None,
    user: CurrentUserDep = Depends(require_scope("rag:write")),
) -> DocumentRead:
    content = await file.read()
    service = RAGService(session)
    doc = await service.upload_document(
        tenant_id=user.tenant_id,
        file_content=content,
        filename=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
    )
    return DocumentRead.model_validate(doc)


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    session: SessionDep,
    user: CurrentUserDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> DocumentList:
    service = RAGService(session)
    items, total = await service.list_documents(
        tenant_id=user.tenant_id, offset=offset, limit=limit
    )
    return DocumentList(
        items=[DocumentRead.model_validate(d) for d in items],
        total=total,
    )


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUserDep,
) -> DocumentRead:
    service = RAGService(session)
    doc = await service.get_document(tenant_id=user.tenant_id, document_id=document_id)
    return DocumentRead.model_validate(doc)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("rag:write")),
) -> None:
    service = RAGService(session)
    await service.delete_document(tenant_id=user.tenant_id, document_id=document_id)


@router.post("/search", response_model=RAGSearchResponse)
async def search_knowledge(
    payload: RAGSearchRequest,
    session: SessionDep,
    user: CurrentUserDep,
) -> RAGSearchResponse:
    service = RAGService(session)
    return await service.search(tenant_id=user.tenant_id, request=payload)
