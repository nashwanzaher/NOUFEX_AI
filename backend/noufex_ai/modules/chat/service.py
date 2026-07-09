from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noufex_ai.exceptions import NotFoundError, UpstreamError
from noufex_ai.modules.agents.models import Agent
from noufex_ai.modules.agent_skills.registry import get_skill_registry
from noufex_ai.modules.browser.service import BrowserService
from noufex_ai.modules.chat.models import Conversation, Message
from noufex_ai.modules.chat.schemas import ChatRequest
from noufex_ai.modules.computer.service import ComputerService
from noufex_ai.modules.design.service import DesignService
from noufex_ai.modules.rag.schemas import RAGSearchRequest
from noufex_ai.modules.rag.service import RAGService
from noufex_ai.settings import settings

logger = logging.getLogger(__name__)

_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI

        if not settings.openai_api_key:
            raise UpstreamError("OpenAI API key not configured")
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
    return _openai_client


DEFAULT_SYSTEM_PROMPT = (
    "You are NOUFEX AI assistant. You are a powerful autonomous agent with access to "
    "computer control, web browsing, UI/UX design, and knowledge retrieval capabilities.\n\n"
    "You can:\n"
    "- Control the desktop: open/close windows, move mouse, click, type text, take screenshots\n"
    "- Browse the web: navigate to URLs, click elements, fill forms, extract content\n"
    "- Search the web and fetch page content\n"
    "- Design UI/UX: generate components, landing pages, dashboards, color palettes, animations\n"
    "- Review UI code for accessibility, responsiveness, and best practices\n"
    "- Retrieve information from uploaded documents via RAG\n"
    "- Run shell commands and manage files\n\n"
    "When the user asks you to perform a task, use the available tools to accomplish it. "
    "You have full access to the user's computer - use this power responsibly.\n\n"
    "IMPORTANT RULES:\n"
    "1. Always take a screenshot first when you need to see what's on the screen\n"
    "2. Before clicking, identify the correct element on screen\n"
    "3. After each action, verify the result before proceeding to the next step\n"
    "4. Use the simplest approach for each task\n"
    "5. If something fails, try an alternative approach\n"
    "6. Explain what you're doing at each step\n"
    "7. You MUST respond in the same language the user writes in\n"
    "8. If you don't know something, say so honestly"
)


# ── Service instances (lazy-init, shared across ChatService instances) ──
_computer_service: ComputerService | None = None
_browser_service: BrowserService | None = None
_design_service: DesignService | None = None
_skills_initialized = False


def _ensure_skills() -> None:
    global _computer_service, _browser_service, _design_service, _skills_initialized
    if _skills_initialized:
        return
    _computer_service = ComputerService()
    _browser_service = BrowserService()
    _design_service = DesignService()
    registry = get_skill_registry()
    registry.set_services(computer_service=_computer_service, browser_service=_browser_service, design_service=_design_service)
    _skills_initialized = True


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        _ensure_skills()

    async def _get_agent(self, *, tenant_id: UUID, agent_id: UUID | None) -> Agent | None:
        if agent_id is None:
            return None
        result = await self.session.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.tenant_id == tenant_id,
                Agent.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_conversation(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        conversation_id: UUID | None,
        agent_id: UUID | None,
    ) -> Conversation:
        if conversation_id:
            result = await self.session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.tenant_id == tenant_id,
                    Conversation.user_id == user_id,
                    Conversation.deleted_at.is_(None),
                )
            )
            conv = result.scalar_one_or_none()
            if conv is None:
                raise NotFoundError(f"Conversation {conversation_id} not found")
            return conv

        conv = Conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            agent_id=agent_id,
            status="active",
        )
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def _get_conversation_history(
        self, *, conversation_id: UUID, limit: int = 50
    ) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        formatted = []
        for m in messages:
            entry: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls_json:
                entry["tool_calls"] = json.loads(m.tool_calls_json)
            formatted.append(entry)
        return formatted

    async def _retrieve_rag_context(
        self, *, tenant_id: UUID, query: str, agent_id: UUID | None, top_k: int = 5
    ) -> str | None:
        rag_service = RAGService(self.session)
        search_request = RAGSearchRequest(query=query, agent_id=agent_id, top_k=top_k)
        search_response = await rag_service.search(tenant_id=tenant_id, request=search_request)

        if not search_response.results:
            return None

        context_parts = []
        for r in search_response.results:
            context_parts.append(f"[Source: Document chunk | Score: {r.score}]\n{r.content}")
        return "\n\n---\n\n".join(context_parts)

    # ── Tool Calling Integration ───────────────────────────────────────

    async def _chat_with_tools(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        agent: Agent | None,
        use_tools: bool,
    ) -> dict[str, Any]:
        """Main LLM loop with tool calling support.
        
        Calls LLM with tools, executes tool calls, and loops until
        the LLM produces a final content response.
        """
        registry = get_skill_registry()
        tools = registry.to_openai_tools() if use_tools else None

        final_content = ""
        total_tokens = 0
        tool_calls_executed: list[dict] = []
        max_iterations = 10

        for iteration in range(max_iterations):
            response = await self._call_llm_with_tools(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )

            message = response.choices[0].message
            usage = response.usage
            total_tokens += usage.total_tokens if usage else 0

            if message.content:
                final_content += message.content

            if not message.tool_calls:
                break

            # Process tool calls
            for tc in message.tool_calls:
                func_name = tc.function.name
                try:
                    func_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                result = await registry.execute(func_name, func_args)
                result_str = json.dumps(result, ensure_ascii=False)[:15000]
                tool_calls_executed.append({
                    "tool": func_name,
                    "arguments": func_args,
                    "success": result.get("success", False),
                })

                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                    ],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

                if not message.content:
                    final_content += f"[Using tool: {func_name}]\n"

        if not final_content.strip():
            final_content = "I've completed the requested actions."

        return {
            "content": final_content.strip(),
            "tokens_used": total_tokens,
            "tool_calls_executed": tool_calls_executed,
        }

    async def chat(
        self, *, tenant_id: UUID, user_id: UUID, request: ChatRequest
    ) -> dict:
        agent = await self._get_agent(tenant_id=tenant_id, agent_id=request.agent_id)

        conv = await self._get_or_create_conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=request.conversation_id,
            agent_id=agent.id if agent else None,
        )

        history = await self._get_conversation_history(conversation_id=conv.id)

        rag_context = None
        if request.use_rag:
            rag_context = await self._retrieve_rag_context(
                tenant_id=tenant_id,
                query=request.message,
                agent_id=agent.id if agent else None,
                top_k=request.rag_top_k,
            )

        system_prompt = agent.system_prompt if agent else DEFAULT_SYSTEM_PROMPT
        if rag_context:
            system_prompt += f"\n\nUse the following context to answer the question:\n\n{rag_context}"

        messages_for_llm: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages_for_llm.extend(history)
        messages_for_llm.append({"role": "user", "content": request.message})

        user_message = Message(
            conversation_id=conv.id,
            role="user",
            content=request.message,
            token_count=len(request.message.split()),
        )
        self.session.add(user_message)
        await self.session.flush()

        model_used = agent.model if agent else settings.openai_default_model

        try:
            result = await self._chat_with_tools(
                messages=messages_for_llm,
                model=model_used,
                temperature=agent.temperature if agent else 0.2,
                max_tokens=agent.max_tokens if agent else 4096,
                agent=agent,
                use_tools=request.use_tools,
            )
        except Exception as exc:
            logger.error("LLM chat failed: %s", exc)
            raise UpstreamError(f"LLM request failed: {exc}") from exc

        response_content = result["content"]
        token_count = result["tokens_used"]
        tool_calls = result["tool_calls_executed"]

        tool_calls_json = json.dumps(tool_calls) if tool_calls else None

        assistant_message = Message(
            conversation_id=conv.id,
            role="assistant",
            content=response_content,
            token_count=token_count,
            model=model_used,
            tool_calls_json=tool_calls_json,
        )
        self.session.add(assistant_message)

        conv.message_count += 2
        conv.token_usage_input += token_count
        conv.token_usage_output += token_count
        if conv.message_count == 2:
            conv.title = request.message[:100]
        self.session.add(conv)
        await self.session.flush()

        return {
            "conversation_id": conv.id,
            "message": assistant_message,
            "tokens_used": token_count,
            "model": model_used,
            "rag_context_used": rag_context is not None,
            "tool_calls_executed": tool_calls,
        }

    async def stream_chat(
        self, *, tenant_id: UUID, user_id: UUID, request: ChatRequest
    ) -> AsyncIterator[str]:
        agent = await self._get_agent(tenant_id=tenant_id, agent_id=request.agent_id)

        conv = await self._get_or_create_conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=request.conversation_id,
            agent_id=agent.id if agent else None,
        )

        history = await self._get_conversation_history(conversation_id=conv.id)

        rag_context = None
        if request.use_rag:
            rag_context = await self._retrieve_rag_context(
                tenant_id=tenant_id,
                query=request.message,
                agent_id=agent.id if agent else None,
                top_k=request.rag_top_k,
            )

        system_prompt = agent.system_prompt if agent else DEFAULT_SYSTEM_PROMPT
        if rag_context:
            system_prompt += f"\n\nUse the following context to answer the question:\n\n{rag_context}"

        messages_for_llm: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages_for_llm.extend(history)
        messages_for_llm.append({"role": "user", "content": request.message})

        user_message = Message(
            conversation_id=conv.id,
            role="user",
            content=request.message,
            token_count=len(request.message.split()),
        )
        self.session.add(user_message)
        await self.session.flush()

        model_used = agent.model if agent else settings.openai_default_model
        full_content = ""
        total_tokens = 0
        tool_calls_executed: list[dict] = []
        registry = get_skill_registry()
        tools = registry.to_openai_tools() if request.use_tools else None

        try:
            for iteration in range(10):
                stream = await self._stream_llm_with_tools(
                    messages=messages_for_llm,
                    model=model_used,
                    temperature=agent.temperature if agent else 0.2,
                    max_tokens=agent.max_tokens if agent else 4096,
                    tools=tools,
                )

                collected_message = ""
                tool_calls_acc: dict[str, dict] = {}
                usage_info = None

                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    if delta.content:
                        collected_message += delta.content
                        full_content += delta.content
                        total_tokens += 1
                        yield json.dumps({"type": "token", "content": delta.content}) + "\n"

                    if delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in tool_calls_acc:
                                tool_calls_acc[idx] = {
                                    "id": tc_delta.id or "",
                                    "function": {"name": "", "arguments": ""},
                                }
                            if tc_delta.id:
                                tool_calls_acc[idx]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    tool_calls_acc[idx]["function"]["name"] = tc_delta.function.name
                                if tc_delta.function.arguments:
                                    tool_calls_acc[idx]["function"]["arguments"] += tc_delta.function.arguments

                    if chunk.usage:
                        usage_info = chunk.usage

                if tool_calls_acc:
                    yield json.dumps({"type": "tool_start", "count": len(tool_calls_acc)}) + "\n"

                    assistant_msg: dict[str, Any] = {"role": "assistant", "content": collected_message}
                    assistant_tool_calls = []
                    for idx in sorted(tool_calls_acc.keys()):
                        tc = tool_calls_acc[idx]
                        assistant_tool_calls.append({
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]},
                        })
                    assistant_msg["tool_calls"] = assistant_tool_calls
                    messages_for_llm.append(assistant_msg)

                    for idx in sorted(tool_calls_acc.keys()):
                        tc = tool_calls_acc[idx]
                        try:
                            func_args = json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            func_args = {}

                        yield json.dumps({
                            "type": "tool_execute",
                            "tool": tc["function"]["name"],
                            "arguments": func_args,
                        }) + "\n"

                        result = await registry.execute(tc["function"]["name"], func_args)
                        result_str = json.dumps(result, ensure_ascii=False)[:15000]
                        tool_calls_executed.append({
                            "tool": tc["function"]["name"],
                            "arguments": func_args,
                            "success": result.get("success", False),
                        })

                        messages_for_llm.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result_str,
                        })

                        yield json.dumps({
                            "type": "tool_result",
                            "tool": tc["function"]["name"],
                            "success": result.get("success", False),
                        }) + "\n"

                else:
                    if usage_info and usage_info.total_tokens:
                        total_tokens = max(total_tokens, usage_info.total_tokens)
                    break

            yield json.dumps({"type": "done", "model": model_used}) + "\n"

        except Exception as exc:
            logger.error("LLM stream failed: %s", exc)
            yield json.dumps({"type": "error", "message": str(exc)}) + "\n"
            return

        if full_content.strip() or tool_calls_executed:
            tool_calls_json = json.dumps(tool_calls_executed) if tool_calls_executed else None
            assistant_message = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_content.strip() or "(tool calls executed)",
                token_count=total_tokens,
                model=model_used,
                tool_calls_json=tool_calls_json,
            )
            self.session.add(assistant_message)

            conv.message_count += 2
            conv.token_usage_input += total_tokens
            conv.token_usage_output += total_tokens
            if conv.message_count == 2:
                conv.title = request.message[:100]
            self.session.add(conv)
            await self.session.flush()

    async def _call_llm_with_tools(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: list[dict] | None,
    ):
        client = _get_openai_client()

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        return await client.chat.completions.create(**kwargs)

    async def _stream_llm_with_tools(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: list[dict] | None,
    ):
        client = _get_openai_client()

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        return await client.chat.completions.create(**kwargs)

    async def list_conversations(
        self, *, tenant_id: UUID, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Conversation], int]:
        base = select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
        count_q = select(func.count()).select_from(base.subquery())
        count_result = await self.session.execute(count_q)
        total = count_result.scalar_one()

        q = base.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_conversation_messages(
        self, *, tenant_id: UUID, user_id: UUID, conversation_id: UUID
    ) -> Conversation:
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            raise NotFoundError(f"Conversation {conversation_id} not found")
        return conv

    async def delete_conversation(
        self, *, tenant_id: UUID, user_id: UUID, conversation_id: UUID
    ) -> None:
        conv = await self.get_conversation_messages(
            tenant_id=tenant_id, user_id=user_id, conversation_id=conversation_id
        )
        conv.soft_delete()
        self.session.add(conv)
        await self.session.flush()
