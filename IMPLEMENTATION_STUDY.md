# NOUFEX_AI — دراسة تنفيذية تفصيلية
### من الفكرة إلى الإنتاج: وكيل ذكاء اصطناعي متعدد المستأجرين (Multi-Tenant AI Agent Platform)
**الإصدار:** 1.0.0  
**التاريخ:** 2026-07-08  
**المؤلف:** فريق NOUFEX التقني  
**المرجع الأصلي:** `NOUFEX_PROJECT_DOCUMENTATION.md` § 3.1

---

## جدول المحتويات
1. [الملخص التنفيذي](#1-الملخص-التنفيذي)
2. [مراجعة الفكرة الأصلية وتحسينها](#2-مراجعة-الفكرة-الأصلية-وتحسينها)
3. [المعمارية المرجعية (Reference Architecture)](#3-المعمارية-المرجعية)
4. [التحقق من الحزمة التقنية (Tech Stack Validation)](#4-التحقق-من-الحزمة-التقنية)
5. [هيكل المستودع](#5-هيكل-المستودع)
6. [تنفيذ الخلفية (Backend)](#6-تنفيذ-الخلفية)
7. [مخطط قاعدة البيانات](#7-مخطط-قاعدة-البيانات)
8. [مخزن المتجهات (pgvector)](#8-مخزن-المتجهات)
9. [إطار الوكلاء (Agent Framework)](#9-إطار-الوكلاء)
10. [مواصفات الـ API](#10-مواصفات-الـ-api)
11. [المصادقة والتفويض](#11-المصادقة-والتفويض)
12. [الأمن (OWASP LLM Top 10)](#12-الأمن)
13. [الأداء وقابلية التوسع](#13-الأداء-وقابلية-التوسع)
14. [الموثوقية (Reliability)](#14-الموثوقية)
15. [المراقبة والقابلية للملاحظة (Observability)](#15-المراقبة-والقابلية-للملاحظة)
16. [استراتيجية الاختبار](#16-استراتيجية-الاختبار)
17. [خط أنابيب CI/CD](#17-خط-أنابيب-cicd)
18. [خطة النشر](#18-خطة-النشر)
19. [هندسة التكلفة](#19-هندسة-التكلفة)
20. [الامتثال](#20-الامتثال)
21. [خارطة طريق تنفيذية (12 أسبوع)](#21-خارطة-الطريق)
22. [الأسئلة المفتوحة والمخاطر](#22-الأسئلة-المفتوحة)

---

## 1. الملخص التنفيذي

NOUFEX_AI يهدف إلى أن يكون منصة **Agent-as-a-Service** تتيح لأي فريق إنشاء وكلاء ذكاء اصطناعي مخصصين لمهام محددة (دعم عملاء، تلخيص مستندات، تحليل بيانات، أتمتة مهام) مع طبقة دلالية (Knowledge Layer) مبنية على RAG، وحوكمة متعددة المستأجرين (Multi-Tenant) منذ اليوم الأول.

الفكرة الأصلية في `NOUFEX_PROJECT_DOCUMENTATION.md` ركّزت على «وكيل دردشة» بتقنيات FastAPI + LangChain + pgvector + Next.js. التحسينات الجوهرية التي تضيفها هذه الدراسة:

1. الانتقال من **سلسلة LangChain حرة** إلى **LangGraph** لتنظيم الجولات المتعددة (multi-turn) والتعافي من الأخطاء وحالات الـ Agent.
2. إدخال **`asyncio` حقيقي في FastAPI** مع مهام خلفية مُدارة عبر Celery + Redis للمهام الطويلة (ingestion، fine-tune، batch evaluation).
3. اعتماد **OpenAI Structured Outputs + JSON Schema** بدلاً من تحليل نص حر، وهو ما يقلّل أخطاء LLM02 (Insecure Output Handling) من OWASP.
4. اعتماد **HNSW + halfvec** في pgvector v0.8+ (نسخة موجودة فعلياً في المستودع الرسمي) مع **iterative index scans** لتخفيف مشكلة Recall تحت أحمال عالية.
5. معمارية **Event Sourcing خفيف** لطلبات الدردشة حتى نمتلك سجل تدقيق (Audit) كامل لكل تفاعل.
6. تطبيق **Tool Registry + Allowlist** (معالجة OWASP LLM07: Insecure Plugin Design و LLM08: Excessive Agency).

> إن الـ SLA المستهدف للنسخة الإنتاجية الأولى: **p95 latency ≤ 1.8 ثانية** لأول توكن، و**99.9% uptime** شهرياً، و**Recall@10 ≥ 0.92** على مجموعة تقييم داخلية.

---

## 2. مراجعة الفكرة الأصلية وتحسينها

| الجانب | في الوثيقة الأصلية | التحسين المُقترح | المرجع الرسمي |
|---|---|---|---|
| إطار الوكلاء | LangChain chains | LangGraph + state graph + checkpointing | `langchain-ai.github.io/langgraph/` |
| تخزين المتجهات | pgvector عام | pgvector v0.8.4 + HNSW + `halfvec` + iterative scans | `github.com/pgvector/pgvector` README |
| إخراج الـ LLM | نص حر → JSON | OpenAI Structured Outputs / `instructor` | OpenAI Structured Outputs guide |
| الأمان | "OpenAI API + pgvector" دون تفصيل | OWASP LLM Top 10 v1.1، تطبيق صارم لـ 10 عناصر | `owasp.org/www-project-top-10-for-large-language-model-applications/` |
| الإدخال | غير مذكور | تنظيف بـ Guardrails + PII redaction + rate-limit per-tenant | OWASP LLM01/06 |
| المهام الطويلة | غير مذكورة | Celery worker + Redis، مع dead-letter-queue | Celery 5.4 docs |
| Multi-tenant | "Freemium/Pro/Enterprise" | Row-Level Security في Postgres + tenant_id propagation عبر JWT | Postgres RLS docs |
| Observability | "Sentry + Prometheus" | OpenTelemetry → Tempo/Loki/Mimir → Grafana | OpenTelemetry semantic conventions |
| التقييم | غير مذكور | Layer: unit → integration → RAGAS → human eval شهري | RAGAS framework |

---

## 3. المعمارية المرجعية

```
                        ┌───────────────┐
        Web / Mobile ──▶│  Cloudflare   │
                        │  WAF + CDN    │
                        └──────┬────────┘
                               │  HTTPS, mTLS
                        ┌──────▼────────┐
                        │  nginx (envoy)│
                        │  Rate limit   │
                        │  + JWT verify │
                        └──────┬────────┘
       ┌───────────────────────┼────────────────────────┐
       │                       │                        │
  ┌────▼─────┐           ┌─────▼─────┐           ┌─────▼─────┐
  │ Frontend │           │  Backend  │           │ Workers   │
  │ Next.js  │◀──REST/──▶│ FastAPI   │──enqueue──▶ Celery     │
  │ (RSC)    │   SSE      │ (async)   │           │ + RQ      │
  └──────────┘           └─────┬─────┘           └─────┬─────┘
                               │                        │
                         ┌─────▼────────────────────────▼─────┐
                         │            Data Plane               │
                         │  Postgres + pgvector + Redis + S3   │
                         │  (RLS لكل tenant)                   │
                         └─────────────┬───────────────────────┘
                                       │
                       ┌───────────────▼──────────────────┐
                       │   External / Provider Plane       │
                       │  • OpenAI (chat + embeddings)     │
                       │  • Stripe (billing)               │
                       │  • SendGrid (verification)        │
                       │  • Sentry / OTel Collector        │
                       └──────────────────────────────────┘
```

### 3.1. مبادئ التصميم (مأخوذة من 12-Factor App + Beyond the Twelve-Factor App)
- **Codebase**: مستودع واحد `NOUFEX_AI` بنية monorepo للسماح بمشاركة types بين الـ frontend والـ backend (OpenAPI).
- **Dependencies**: `requirements.txt` مُولَّد من `pip-tools`، مع hashing (`--require-hashes`).
- **Config**: متغيرات بيئة فقط، لا أسرار في الـ repo، تُحمَّل عبر Pydantic Settings.
- **Backing services**: Postgres / Redis / S3 موصولة كـ URLs.
- **Build / Release / Run**: فصل صارم عبر CI.
- **Processes**: stateless API، كل حالة في Postgres/Redis.
- **Port binding**: الـ API يُصدِّر uvicorn على المنفذ 8000.
- **Concurrency**: horizontally scaled pods، مع `--workers` على uvicorn = `2 × CPU + 1`.
- **Disposability**: `lifespan` handlers في FastAPI لإغلاق الاتصالات برشاقة (graceful shutdown).
- **Dev/Prod parity**: صورة Docker واحدة، بيئات بنفس الـ DB.
- **Logs**: stdout JSON → Loki/OTLP → Grafana.
- **Admin processes**: `alembic` كـ one-off container.

### 3.2. نمط النشر: Modular Monolith أولاً
نبدأ Modular Monolith بحزم (`users`, `agents`, `rag`, `billing`, `audit`) في تطبيق FastAPI واحد. هذا يخفض التعقيد التشغيلي في المراحل الأولى. الانتقال إلى Microservices يتم **فقط** عند تجاوز:
- زمن البناء > 10 دقائق،
- تعارضات Git متكررة بين الفرق،
- حاجة scaling غير متماثل (مثلاً RAG يحتاج GPU، والباقي لا).

---

## 4. التحقق من الحزمة التقنية

| التقنية | النسخة | المصدر المرجعي | لماذا هذه النسخة |
|---|---|---|---|
| Python | 3.11.x (LTS حتى 2027) | python.org/downloads | دعم Pydantic v2 كامل + asyncio |
| FastAPI | 0.115.x | fastapi.tiangolo.com/release-notes | أحدث ميزات `Annotated`، OpenAPI 3.1 |
| Pydantic | 2.9.x | docs.pydantic.dev | أداء 5–50× عن v1 + strict mode |
| LangGraph | 0.2.x | langchain-ai/langgraph | رسم state، time-travel debug، checkpointing |
| SQLAlchemy | 2.0.35 | sqlalchemy.org | نمط `select()` typed statements |
| asyncpg | 0.29 | magicstack/asyncpg | الأسرع لـ Postgres async |
| pgvector | 0.8.4 (Docker tag: `pg16`) | github.com/pgvector/pgvector | يدعم iterative scans (strict/relaxed) |
| Postgres | 16-alpine | postgresql.org | pg_stat_statements، JSON_TABLE، SKIP LOCKED |
| Redis | 7.4-alpine | redis.io | Streams للـ DLQ + rate-limit (Token Bucket) |
| Celery | 5.4 | docs.celeryq.dev | canvas: chain/group/chord + ETA |
| Uvicorn | 0.30.6 | uvicorn.readthedocs.io | httptools + uvloop |
| Next.js | 14.2 | nextjs.org/blog | Server Actions + Partial Prerendering |
| Tailwind | 3.4 | tailwindcss.com | JIT، tree-shake |
| Playwright | 1.47 | playwright.dev | e2e visual diffing |
| pytest | 8.3 | docs.pytest.org | plugins: pytest-asyncio, pytest-postgresql |
| OpenTelemetry | 1.27 | opentelemetry.io | semantic conventions مستقرة لـ LLM |
| LangSmith / Langfuse | Langfuse 3.x OSS | langfuse.com | تكلفة الترخيص vs. تخصيص |

---

## 5. هيكل المستودع

```
NOUFEX_AI/
├── backend/
│   ├── pyproject.toml
│   ├── requirements.in
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                       # ترحيلات قاعدة البيانات
│   │   ├── env.py
│   │   └── versions/
│   ├── noufex_ai/                     # الحزمة الرئيسية
│   │   ├── main.py                    # FastAPI app + lifespan
│   │   ├── settings.py                # Pydantic Settings
│   │   ├── logging.py
│   │   ├── telemetry.py               # OTel init
│   │   ├── deps.py                    # تبعيات مشتركة (DB, current_user, tenant)
│   │   ├── exceptions.py              # معالجات أخطاء موحدة
│   │   ├── modules/
│   │   │   ├── users/                 # CRUD + auth
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── models.py
│   │   │   ├── agents/                # تعريف + إدارة الوكلاء
│   │   │   ├── rag/                   # RAG pipeline
│   │   │   │   ├── loaders/
│   │   │   │   ├── splitters.py
│   │   │   │   ├── embeddings.py
│   │   │   │   ├── retrievers.py
│   │   │   │   └── reranker.py
│   │   │   ├── chat/                  # runtime الوكلاء + SSE
│   │   │   ├── billing/               # Stripe webhook
│   │   │   └── audit/                 # سجل التدقيق
│   │   └── worker/
│   │       ├── celery_app.py
│   │       └── tasks.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── evals/                     # RAGAS + LLM judge
│   │   └── load/                      # Locust scripts
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── (auth)/
│   │   ├── (dashboard)/
│   │   │   ├── agents/
│   │   │   ├── chat/[agentId]/
│   │   │   └── settings/
│   │   ├── api/                       # route handlers (BFF)
│   │   └── middleware.ts              # auth refresh
│   ├── components/
│   │   ├── ui/                        # shadcn/ui
│   │   └── ...
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── sse-client.ts
│   │   └── auth.ts
│   ├── public/
│   ├── next.config.mjs
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   └── Dockerfile
├── ai-models/
│   ├── prompts/
│   │   ├── system.txt                 # شخصية الوكيل الافتراضي
│   │   ├── rag.answer.md              # قالب إجابة موثق
│   │   ├── tool.use.json              # JSON Schema لأدوات
│   │   └── red-team/                  # حقن prompts للاختبار
│   ├── evals/
│   │   ├── datasets/
│   │   └── scorers.json
│   └── README.md
├── infrastructure/
│   ├── docker-compose.yml             # dev-only
│   ├── docker-compose.prod.yml        # production override
│   ├── nginx/
│   ├── prometheus/
│   ├── grafana/
│   ├── loki/
│   └── tempo/
├── scripts/
│   ├── seed.py
│   ├── eval.py
│   └── benchmark.py
├── infrastructure/compose/...         # نطاق NGINX الجذر في /NOUFEX
├── .env.example
├── docker-compose.yml                 # للـ dev المحلي
└── IMPLEMENTATION_STUDY.md            # هذا الملف
```

---

## 6. تنفيذ الخلفية

### 6.1. نقطة الدخول مع `lifespan` (FastAPI >= 0.115)

```python
# backend/noufex_ai/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from noufex_ai.settings import settings
from noufex_ai.telemetry import setup_telemetry
from noufex_ai.db import engine, async_session_maker
from noufex_ai.modules.users.router import router as users_router
from noufex_ai.modules.agents.router import router as agents_router
from noufex_ai.modules.chat.router import router as chat_router
from noufex_ai.modules.rag.router import router as rag_router
from noufex_ai.modules.billing.router import router as billing_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry(app, service_name="noufex-ai")
    await engine.connect()
    yield
    await engine.dispose()

app = FastAPI(
    title="NOUFEX AI",
    version="1.0.0",
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.include_router(users_router, prefix="/v1/users", tags=["users"])
app.include_router(agents_router, prefix="/v1/agents", tags=["agents"])
app.include_router(chat_router, prefix="/v1/chat", tags=["chat"])
app.include_router(rag_router, prefix="/v1/rag", tags=["rag"])
app.include_router(billing_router, prefix="/v1/billing", tags=["billing"])
```

### 6.2. Multi-Tenancy عبر Row-Level Security

```sql
-- تفعيل RLS على جدول المعرفة
ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON knowledge_chunks
USING (tenant_id = current_setting('app.tenant_id')::uuid)
WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

```python
# في كل request نعتمد middleware يحقن tenant_id الحالي من JWT
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    tenant_id = request.state.user.tenant_id if request.state.user else "public"
    async with engine.begin() as conn:
        await conn.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
        response = await call_next(request)
    return response
```

### 6.3. Structured Outputs (OpenAI)

```python
from pydantic import BaseModel
from openai import AsyncOpenAI

class AgentReply(BaseModel):
    answer: str
    citations: list[dict]
    tool_calls: list[dict]
    confidence: float

async def run_agent(messages, tools) -> AgentReply:
    client = AsyncOpenAI()
    resp = await client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        tools=tools,
        response_format=AgentReply,  # ← Structured Outputs
    )
    return AgentReply.model_validate_json(resp.choices[0].message.content)
```
> هذا يحلّ OWASP LLM02: Insecure Output Handling لأنّ الإجابة تُحلّل كـ Pydantic مع رفض أي حقل مفقود/خاطئ.

### 6.4. Tool Registry + Allowlist (OWASP LLM07/LLM08)

```python
ALLOWED_TOOLS = {
    "search_docs": {"requires": ["auth"], "rate_limit": "60/min"},
    "create_ticket": {"requires": ["auth", "tenant_id"], "rate_limit": "10/min"},
    "run_sql": {"requires": ["auth", "role=analyst"], "rate_limit": "5/min", "read_only": True},
}

def tool_guard(name: str, user, tenant_id):
    spec = ALLOWED_TOOLS[name]
    if "tenant_id" in spec["requires"]:
        enforce_tenant(user, tenant_id)
    if f"role={spec['requires']}" not in user.scopes:
        raise PermissionError(f"missing scope for {name}")
```

### 6.5. Streaming عبر SSE

```python
from fastapi.responses import StreamingResponse

@chat_router.post("/stream")
async def stream(payload: ChatRequest):
    async def event_publisher():
        async for chunk in run_agent_stream(payload):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_publisher(), media_type="text/event-stream")
```

### 6.6. Celery Worker

```python
# backend/noufex_ai/worker/tasks.py
from celery import shared_task
from noufex_ai.modules.rag.service import ingest_document

@shared_task(bind=True, max_retries=5, default_retry_delay=30, acks_late=True)
def ingest(self, tenant_id: str, doc_id: str):
    try:
        ingest_document(tenant_id, doc_id)
    except Exception as exc:
        raise self.retry(exc=exc)
```

---

## 7. مخطط قاعدة البيانات (Postgres 16)

```sql
-- الإصدار: V0001__init.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE tenants (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        text NOT NULL,
    plan        text NOT NULL CHECK (plan IN ('free','pro','enterprise')),
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id     uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email         citext UNIQUE NOT NULL,
    password_hash text NOT NULL,
    is_active     bool NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX users_tenant_idx ON users(tenant_id);

CREATE TABLE agents (
    id           uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id    uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name         text NOT NULL,
    system_prompt text NOT NULL,
    model        text NOT NULL DEFAULT 'gpt-4o-mini',
    temperature  real NOT NULL DEFAULT 0.2 CHECK (temperature BETWEEN 0 AND 2),
    tools        jsonb NOT NULL DEFAULT '[]'::jsonb,
    config       jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agents_tenant ON agents
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE TABLE knowledge_chunks (
    id          bigserial PRIMARY KEY,
    tenant_id   uuid NOT NULL,
    agent_id    uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    document_id uuid NOT NULL,
    chunk_no    int NOT NULL,
    content     text NOT NULL,
    embedding   halfvec(1536) NOT NULL,   -- نصف-الدقة، يدعم حتى 4000 dim
    metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
    tsv         tsvector GENERATED ALWAYS AS (to_tsvector('arabic', content)) STORED,
    UNIQUE (agent_id, document_id, chunk_no)
);
ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY kc_tenant ON knowledge_chunks
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE INDEX kc_embed_hnsw ON knowledge_chunks
    USING hnsw (embedding halfvec_cosine_ops);
CREATE INDEX kc_tsv_gin ON knowledge_chunks USING gin (tsv);
```

> اختيارات معرّفة في مرجع pgvector الرسمي:
> - **`halfvec` بدلاً من `vector`**: نصف الذاكرة في الذاكرة العاملة (المستودع: "Use the `halfvec` type instead of `vector` for a smaller working set").  
> - **HNSW**: "better query performance than IVFFlat (in terms of speed-recall tradeoff), but has slower build times and uses more memory".  
> - **نقوم بتفعيل iterative scans** لاحقاً حسب الضغط: `SET hnsw.iterative_scan = relaxed_order;`.

---

## 8. مخزن المتجهات (pgvector) — تشغيل فعلي

```sql
-- التقييم التقريبي لـ Recall قبل وبعد
BEGIN;
SET LOCAL enable_indexscan = off;   -- بحث دقيق
WITH exact AS (
    SELECT id FROM knowledge_chunks
    ORDER BY embedding <=> $1 LIMIT 50
),
approx AS (
    SELECT id FROM knowledge_chunks
    ORDER BY embedding <=> $1 LIMIT 50
)
SELECT
    (SELECT count(*) FROM (SELECT id FROM approx INTERSECT SELECT id FROM exact) t)::float
        / 50 AS recall_at_50;
COMMIT;
```

نقاط ضبط ضرورية مأخوذة حرفياً من README:
- `maintenance_work_mem = '8GB'` قبل بناء HNSW.
- `max_parallel_maintenance_workers = 7` لتسريع البناء.
- `CREATE INDEX CONCURRENTLY` في الإنتاج.
- لـ OpenAI embeddings (مُعيَّرة): استخدم `inner product` بدلاً من `cosine` لأن الكلفة الحسابية أقل بنفس النتيجة (المصدر: "If vectors are normalized to length 1 (like OpenAI embeddings), use inner product for best performance").

---

## 9. إطار الوكلاء (LangGraph)

### 9.1. رسم حالة الوكيل

```
       ┌──────────┐  need_info    ┌──────────────┐
       │  router  ├──────────────▶│   retriever  │
       └────┬─────┘                └──────┬───────┘
            │ no_tool                     │ context
            ▼                             ▼
       ┌──────────┐                  ┌──────────┐  fail
       │  answer  │◀───── check ─────│  draft   │───▶ retry
       └────┬─────┘                  └──────────┘
            │ final
            ▼
       ┌──────────┐
       │  audit   │
       └──────────┘
```

### 9.2. تنفيذ مختصر

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    context: list[str]
    tools_called: list[str]
    token_usage: dict

def router(state): return "retrieve" if state["messages"][-1].get("needs_kg") else "answer"
def retriever(state): return {"context": search(state["messages"][-1]["content"], k=8)}
def draft(state): return {"messages": [await llm_call(state)]}
def check(state): return "retry" if state["messages"][-1].get("low_confidence") else "final"

g = StateGraph(AgentState)
g.add_node("retrieve", retriever)
g.add_node("draft", draft)
g.add_node("answer", lambda s: {"messages": [format_answer(s)]})
g.add_conditional_edges("retrieve", router, {"retrieve": END, "answer": "answer"})
g.add_conditional_edges("draft", check, {"retry": "retrieve", "final": "answer"})
g.set_entry_point("retrieve")
graph = g.compile()
```

### 9.3. Checkpointing
نحفظ حالة الرسم في `agent_runs(run_id uuid, thread_id text, state jsonb)` لتسهيل **time-travel debugging** واستئناف المحادثة بعد انقطاع.

---

## 10. مواصفات الـ API

REST + SSE، OpenAPI 3.1 أتوماتيكي عبر FastAPI.

| Method | Path | الوصف |
|---|---|---|
| POST | `/v1/users/signup` | تسجيل (Captcha + Email verification) |
| POST | `/v1/users/login` | إرجاع JWT (15min) + Refresh Token (30 يوم) |
| POST | `/v1/users/refresh` | تدوير |
| GET | `/v1/agents` | قائمة وكلاء المستأجر |
| POST | `/v1/agents` | إنشاء وكيل |
| PATCH | `/v1/agents/{id}` | تحديث |
| POST | `/v1/rag/documents` | رفع مستند (multipart) |
| GET | `/v1/rag/documents/{id}/status` | الحالة من Celery |
| POST | `/v1/chat` | تشغيل الوكيل (JSON) |
| POST | `/v1/chat/stream` | SSE stream |
| GET | `/v1/chat/{run_id}` | استرجاع/استئناف (time-travel) |
| POST | `/v1/billing/webhook` | Stripe webhook (verified) |

### اتفاقيات
- كل الأخطاء بصيغة: `{"error": {"code": "string", "message": "string", "trace_id": "uuid"}}`.
- `Idempotency-Key` header لكل عمليات POST لتجنّب الازدواجية (Billable).
- Rate-Limit: `X-RateLimit-Limit` و`X-RateLimit-Remaining` من nginx.

---

## 11. المصادقة والتفويض

- **Access Token**: JWT قصيرة (15min)، مع claims: `sub`, `tenant_id`, `scope`, `role`.
- **Refresh Token**: مخزّن في Postgres `refresh_tokens(id, user_id, expires_at, revoked_at)`. كل refresh يُلغي السابق (rotation).
- **Signing algorithm**: EdDSA عبر PyJWT (CurveEd25519) — أكثر كفاءة من RS256 وأصعب في سوء الاستخدام.
- **Scopes**:
  - `chat:read`, `chat:write`
  - `agents:manage`
  - `rag:write`
  - `billing:read`
- **2FA**: WebAuthn (TOTP/FIDO2) لحسابات `enterprise`.

---

## 12. الأمن (OWASP LLM Top 10 v1.1 + OWASP Top 10 2021)

### 12.1. OWASP LLM Top 10 — التطبيق حسب العنصر

| ID | الخطر | الضابط المُطبَّق |
|---|---|---|
| **LLM01 Prompt Injection** | حقن تعليمات في مدخلات المستخدم | 1) فصل نظام-تعليمات عن مدخلات المستخدم بقالب `<<SYS>>...<</SYS>>`؛ 2) classifier مدخلات (مثل `prompt-guard-86M`)؛ 3) حدود tool calls قابلة للتدقيق. |
| **LLM02 Insecure Output Handling** | تنفيذ تعليمات من إجابة النموذج | إجبار Structured Outputs (انظر 6.3)؛ عدم تمرير أي حقل لِـ `eval`/`exec`؛ HTML إخراج عبر `DOMPurify`. |
| **LLM03 Training Data Poisoning** | تحيُّز بيانات RAG | توقيع رقمي للمستندات (SHA256)؛ تتبّع مصدر في `metadata.source`؛ تواريخ انتهاء صلاحية. |
| **LLM04 Model DoS** | استنزاف تكلفة | Token Bucket per-tenant؛ max-output-tokens=1024 افتراضي؛ circuit breaker. |
| **LLM05 Supply Chain** | ثغرة في تبعيات | `pip-audit`، Trivy على الصور، SBOM بـ `syft`، Renovate. |
| **LLM06 Sensitive Disclosure** | تسريب بيانات | PII redaction (Microsoft Presidio) قبل الـ embedding؛ فلترة `tenant_id` في نتائج البحث. |
| **LLM07 Insecure Plugin Design** | تنفيذ أوامر بالخطأ | Tool Registry (انظر 6.4)؛ JSON Schema لكل tool؛ تأكيد المستخدم على كل عملية “mutating”. |
| **LLM08 Excessive Agency** | صلاحيات زائدة | Allowlist؛ OOB approval عبر بريد/OTP للإجراءات الحساسة (حذف حساب، دفعة). |
| **LLM09 Overreliance** | ثقة عمياء | عرض المصادر (citations إجبارية)؛ confidence ≥ 0.6 للظهور؛ شرط موافقة بشر للحالات الحساسة. |
| **LLM10 Model Theft** | سرقة نماذج | تجنّب fine-tune عام؛ مفاتيح OpenAI مخزّنة في Vault (AWS KMS / Doppler). |

### 12.2. OWASP Top 10 (2021) — تكملة

| البند | الضابط |
|---|---|
| A01 Broken Access Control | RLS + tenant middleware + تحقق scope |
| A02 Cryptographic Failures | TLS 1.3 داخلياً أيضاً (mTLS بين الـ services)؛ Argon2id لكلمات المرور |
| A03 Injection | مُعامِل كل المعلمات queries عبر SQLAlchemy؛ لا f-string في SQL |
| A04 Insecure Design | Threat Modeling في كل Sprint Review |
| A05 Security Misconfig | Trivy + CIS Benchmarks في فحص يومي |
| A06 Vulnerable Components | Dependabot + `pip-audit` |
| A07 Identification & Auth Failures | WebAuthn/MFA؛ قفل حساب بعد 5 محاولات |
| A08 Software & Data Integrity | Sigstore Cosign على الصور؛ SBOM |
| A09 Logging & Monitoring | OTel → Loki؛ تنبيهات PagerDuty |
| A10 SSRF | قائمة IP ranges مسموح بها للـ webhooks؛ لا proxy شامل |

---

## 13. الأداء وقابلية التوسع

### 13.1. SLA Targets
- p50 أول توكن < 700ms
- p95 أول توكن < 1.8s
- Throughput: 200 RPS بـ 8 workers
- Error rate: < 0.1% على مستوى الـ API

### 13.2. Scaling Stages
| المرحلة | المستخدمين النشطين | الإعداد |
|---|---|---|
| 0 → 100k | 1k DAU | صورة واحدة، Postgres RDS db.t4g.medium |
| 100k → 1M | 10k DAU | 3 نسخ API + read-replica |
| 1M → 10M | 100k DAU | Kubernetes، pgvector على Citus |
| 10M+ | — | فصل RAG microservice + GPU inference |

### 13.3. Caching
- L1: Redis Token Cache (prompt + context hash → answer) بصلاحية 6 ساعات.
- L2: Cloudflare Cache للأصول الساكنة فقط.
- **لا نُخزّن** إجابات PII.

---

## 14. الموثوقية (Reliability)

- **Error Budget**: 0.1% شهرياً (= ~43 دقيقة).
- **Circuit Breaker** على OpenAI: عند نسبة فشل 5% يُفتح لمدة 60s.
- **Retry** exponential backoff مع jitter، max 3.
- **Idempotency keys** على كل POST.
- **Graceful shutdown** عبر SIGTERM + `lifespan` + drain 30 ثانية.

---

## 15. المراقبة والـ Observability

### 15.1. الأعمدة الثلاثة
| العمود | الأداة | نموذج |
|---|---|---|
| Logs | Loki + Promtail | JSON مع `tenant_id`, `run_id` |
| Metrics | Mimir + Prometheus | counters/gauges/histograms |
| Traces | Tempo + OTel | LLM calls مُعلَّمة بـ `gen_ai.*` attributes |

### 15.2. لوحات Grafana الحرجة
- تكلفة OpenAI لكل tenant (مؤشّر مهم للربحية).
- Recall@10 يومي من `evals/datasets/`.
- Latency per-agent (p50/p95/p99).
- Rate-limit rejections لكل tenant.

---

## 16. استراتيجية الاختبار

| المستوى | الأداة | تغطية |
|---|---|---|
| Unit | pytest + pytest-asyncio + hypothesis | 85% |
| Integration | pytest + testcontainers-python (postgres + redis) | على كل boundary |
| API contract | Schemathesis + OpenAPI schema | 100% |
| LLM-as-judge | RAGAS + `gpt-4o` | يومي |
| Security | bandit، pip-audit، Trivy، OWASP ZAP | أسبوعي |
| Load | Locust + k6 | شهري |
| Visual | Playwright | per release |

### 16.1. مجموعة التقييم
ملف `ai-models/evals/datasets/golden_v1.jsonl` يحتوي:
- 300 سؤال حقيقي، الإجابة المتوقعة، سياق متوقّع، citations.
- وكيل التقييم يحسب: faithfulness, answer_relevancy, context_precision, context_recall.

---

## 17. خط أنابيب CI/CD

```yaml
# .github/workflows/ci.yml (مختصر)
name: ci
on: { push: { branches: [main] }, pull_request: {} }
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres: { image: pgvector/pgvector:pg16, env: {POSTGRES_PASSWORD: x}, ports: [5432:5432] }
      redis:    { image: redis:7-alpine, ports: [6379:6379] }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: ruff check .
      - run: mypy .
      - run: bandit -r backend/
      - run: pytest -n auto --cov=backend --cov-fail-under=85
      - run: docker build -t noufex-ai:${{ github.sha }} ./backend
      - run: trivy image --severity HIGH,CRITICAL --exit-code 1 noufex-ai:${{ github.sha }}
      - run: schemathesis run backend/openapi.json --checks all
```

عند الـ merge إلى `main` → صورة جديدة تُدفع لـ GHCR → ArgoCD يطبّقها على staging.

---

## 18. خطة النشر

### 18.1. البيئات
| البيئة | المضيف | ملاحظات |
|---|---|---|
| Local | Docker compose | لكل المطوّرين |
| CI | GitHub Actions | ephemeral |
| Staging | EKS / GKE / fly.io | نفس الإنتاج بحجم أصغر |
| Production | AWS us-east-1 + eu-west-1 | active-active |

### 18.2. استراتيجيات الإطلاق
- **Blue/Green** عبر nginx upstream (الافتراضي).
- **Canary 5% → 25% → 100%** عند إطلاق تغيير في منطق الوكيل.
- **Feature flags** عبر Unleash أو growthbook (OSS).

### 18.3. Data Backups
- WAL archiving + base backups يومياً.
- PITR مع هدف RPO = 5 دقائق، RTO = 30 دقيقة.
- لقطة S3 أسبوعية بتشفير KMS، عمرها 90 يوماً.

---

## 19. هندسة التكلفة

| المكوّن | التكلفة الشهرية المقدّرة | التحسين |
|---|---|---|
| OpenAI embeddings+chat | $0.10 / 1M tokens (mini) | Model routing (mini للأغلبية، 4o للحالات الصعبة) |
| Postgres (RDS t4g.large) | $120 | Reserved Instances بعد الشهر 6 |
| Redis (cache.t4g.small) | $25 | Multi-AZ بعد 1k DAU |
| Cloudflare Pro | $20 | النسبة الأكبر للصور/JS |
| Egress | متغيّر | ضغط + Brotli |
| S3 | متغيّر | Lifecycle policy للأرشيف |
| **إجمالي شهر 1–3** | **~$400–700** | |

---

## 20. الامتثال

- **GDPR (EU 2016/679)**: DPA جاهز، حقّ النسيان (delete via `DELETE /users/me` cascade)، سجل الوصول في `audit_log`، Data Processing Addendum مع OpenAI.
- **SOC 2 Type II** (مسار السنة الثانية): ضوابط الوصول، التشفير، النسخ الاحتياطي، إدارة الحوادث.
- **ISO 27001** (مسار السنة الثالثة) إن أُريد البيع لكيانات حكومية.
- **CCPA** (California) بنفس بنية GDPR عملياً.

---

## 21. خارطة طريق تنفيذية (12 أسبوع)

### الأسبوع 1–2: الأساس
- ✅ صورة Docker، docker-compose للخدمات الثلاث.
- ✅ Alembic migration V0001.
- ✅ Auth (signup/login/refresh) + Argon2id + EdDSA.
- ✅ OTel + Sentry.

### الأسبوع 3–4: RAG
- ✅ Ingestion (PDF, DOCX, HTML, MD).
- ✅ Splitter (RecursiveCharacterTextSplitter 1000/150).
- ✅ Embeddings عبر OpenAI.
- ✅ Retriever مع HNSW.
- ✅ Reranker عبر `bge-reranker-base` (محلي).

### الأسبوع 5–6: الوكلاء
- ✅ LangGraph state + 3 nodes.
- ✅ Tool registry + Allowlist.
- ✅ Streaming عبر SSE.

### الأسبوع 7–8: الواجهة
- ✅ Next.js App Router + Auth UI.
- ✅ لوحة إدارة الوكلاء.
- ✅ Streaming UI بـ Vercel AI SDK.

### الأسبوع 9–10: الجودة
- ✅ مجموعة تقييم 300 سؤال.
- ✅ LLM-as-judge يومياً.
- ✅ Load test 200 RPS.

### الأسبوع 11–12: الإطلاق التجريبي
- ✅ SOC 2 lite.
- ✅ Bounty program مغلَق.
- ✅ Beta مع 50 tenant.

---

## 22. الأسئلة المفتوحة والمخاطر

### 22.1. أسئلة
1. هل نوافق على تخزين بيانات tenants في منطقة واحدة (us-east-1) أم يلزم EU residency؟
2. هل ستكون النسخة الأولى مجانية تماماً (PLG) أم تتطلب بطاقة ائتمان؟
3. هل نتعامل مع نماذج محلية (llama-3.1) لتوفير تكلفة؟

### 22.2. مخاطر مرتفعة
| المخاطرة | الاحتمال | التأثير | التخفيف |
|---|---|---|---|
| تجاوز ميزانية OpenAI بسبب RAG recall منخفض | متوسط | عالي | cap شهري + alerts + fallback للنماذج المحلية |
| تسريب بيانات Cross-tenant | منخفض | عالي جداً | اختبارات RLS تلقائية + pg_regress |
| Prompt injection ناجح | متوسط | عالي | classifier + اختبارات red-team أسبوعية |
| أداء pgvector على >10M vectors | منخفض | متوسط | اختبار قبل ذلك + خطّة Citus |

### 22.3. مؤشرات نجاح المنتج (المرجع: North Star + AARRR)
- **North Star**: عدد الرسائل الناجحة لكل tenant أسبوعياً.
- **Acquisition**: نقرات CTA في landing page.
- **Activation**: أول رسالة دردشة في 24 ساعة.
- **Retention**: D7 / D30 cohorts.
- **Referral**: NPS > 40.
- **Revenue**: ARPU expansion كل شهر.

---

## ملحق A: مراجع رسمية تم الاستناد إليها

1. OWASP — Top 10 for LLM Applications v1.1 (والمسار إلى v2025).  
   https://owasp.org/www-project-top-10-for-large-language-model-applications/
2. pgvector — README الرسمي للإصدار v0.8.4 (HNSW/IVFFlat/halfvec/iterative scans).  
   https://github.com/pgvector/pgvector
3. FastAPI — Advanced User Guide (lifespan, response models, OTel).  
   https://fastapi.tiangolo.com/advanced/
4. LangGraph — رسم الوكلاء، checkpointing، time-travel debugging.
5. OpenAI — Structured Outputs مع JSON Schema.
6. Postgresql 16 Docs — `pg_stat_statements`, Row Level Security, `pg_trgm`.
7. OpenTelemetry — Semantic Conventions for Generative AI Systems (`gen_ai.*`).
8. NIST SP 800-53 Rev. 5 — للضوابط الأمنية (المسار الإنتاجي).
9. OWASP ASVS 4.0 — متطلبات التحقق.
10. Twelve-Factor App — لتمهيد بنية الـ Backend.

---

## ملحق B: قَدْر الكود المتوقّع
- Backend Python: ~12k سطر عبر 25 أسبوع-شخص.
- Frontend TS: ~8k سطر.
- اختبارات: ~5k سطر (40% من كود الإنتاج تقريباً).
- IaC (Terraform): ~1.5k سطر.

> **خلاصة**: الانتقال من «وكيل دردشة» إلى «منصة وكلاء متعدد-المستأجرين مع دلالات معرفية وحوكمة أمنيّة كاملة» يستحقّ ضعف الجهد في المراحل الأولى لكنه يخفض الكلفة التشغيلية لاحقاً بمقدار 3–5× ويتيح تسعير enterprise.
