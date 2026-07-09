# الدراسة التنفيذية التفصيلية — NOUFEX_AI
## منصة وكلاء الذكاء الاصطناعي متعددة المستأجرين

**الإصدار:** 2.0.0
**التاريخ:** 2026-07-09
**الحالة:** دراسة تنفيذية محدثة بناءً على تحليل الكود الفعلي والمراجع الرسمية
**المؤلف:** فريق NOUFEX التقني

---

## جدول المحتويات

1. [الملخص التنفيذي](#1-الملخص-الに寑ي)
2. [تحليل الوضع الحالي](#2-تحليل-الوضع-الحالي)
3. [المعمارية المرجعية](#3-المعمارية-المرجعية)
4. [التحقق من الحزمة التقنية](#4-التحقق-من-الحزمة-التقنية)
5. [هيكل المستودع](#5-هيكل-المستودع)
6. [تنفيذ Backend](#6-تنفيذ-Backend)
7. [مخطط قاعدة البيانات](#7-مخطط-قاعدة-البيانات)
8. [مخزن المتجهات (pgvector)](#8-مخزن-المتجهات)
9. [إطار الوكلاء (LangGraph)](#9-إطار-الوكلاء)
10. [مواصفات API](#10-مواصفات-API)
11. [المصادقة والتفويض](#11-المصادقة-والتفويض)
12. [الأمان (OWASP LLM Top 10)](#12-الأمان)
13. [الأداء وقابلية التوسع](#13-الأداء-وقابلية-التوسع)
14. [الموثوقية](#14-الموثوقية)
15. [المراقبة وقابلية الملاحظة](#15-المراقبة)
16. [استراتيجية الاختبار](#16-استراتيجية-الاختبار)
17. [خط أنابيب CI/CD](#17-خط-أنابيب-CICD)
18. [خطة النشر](#18-خطة-النشر)
19. [هندسة التكلفة](#19-هندسة-التكلفة)
20. [الامتثال](#20-الامتثال)
21. [خارطة الطريق التنفيذية](#21-خارطة-ال الطريق)
22. [المخاطر والحلول](#22-المخاطر-والحلول)
23. [المراجع الرسمية](#23-المراجع-الرسمية)

---

## 1. الملخص التنفيذي

### 1.1 الهدف

تحويل مشروع NOUFEX_AI من مرحلة الكود الأولي إلى منصة **Agent-as-a-Service** جاهزة للإنتاج، مع التركيز على:
- إصلاح الثغرات الأمنية المكتشفة
- إكمال الملفات المفقودة
- تطبيق أفضل الممارسات من المراجع الرسمية
- ضمان الجودة والأداء والموثوقية

### 1.2 النطاق

| البند | النطاق |
|-------|--------|
| Backend | FastAPI + SQLAlchemy + pgvector + Celery |
| Frontend | Next.js 16 + Tailwind CSS + shadcn/ui |
| AI Models | OpenAI GPT-4o-mini + text-embedding-3-small |
| Infrastructure | Docker + AWS (RDS, ElastiCache, S3, EC2) |
| Monitoring | OpenTelemetry + Grafana + Sentry |
| Security | OWASP LLM Top 10 v2025 |

### 1.3 المعايير المرجعية

| المعيار | الهدف |
|---------|-------|
| وقت الاستجابة (p95 أول توكن) | ≤ 1.8 ثانية |
| Uptime الشهري | ≥ 99.9% |
| Recall@10 (RAG) | ≥ 0.92 |
| وقت البناء (CI) | < 10 دقائق |
| تغطية الاختبارات | ≥ 85% |

---

## 2. تحليل الوضع الحالي

### 2.1 ما تم تنفيذه فعلياً

#### Backend (بنية ممتازة)

| الوحدة | الحالة | الملفات | التقييم |
|--------|--------|---------|---------|
| **Users** | ✅ مكتمل | models, router, schemas, security, service | ⭐⭐⭐⭐ |
| **Tenants** | ✅ مكتمل | models, router, schemas, service | ⭐⭐⭐⭐ |
| **Agents** | ✅ مكتمل | models, router, schemas, service | ⭐⭐⭐⭐ |
| **Chat** | ✅ مكتمل | models, router, schemas, service | ⭐⭐⭐⭐ |
| **RAG** | ✅ مكتمل | router, schemas, service | ⭐⭐⭐ |
| **Billing** | ✅ مكتمل | models, router, schemas, service | ⭐⭐⭐ |
| **Computer** | ✅ مكتمل | router, schemas, service | ⭐⭐ |
| **Browser** | ✅ مكتمل | router, schemas, service | ⭐⭐⭐ |
| **Design** | ✅ ممتاز | router, schemas, service, components | ⭐⭐⭐⭐⭐ |
| **Agent Skills** | ✅ ممتاز | registry (60+ skill) | ⭐⭐⭐⭐⭐ |
| **Audit** | ⚠️ جزئي | فقط Mixins | ⭐⭐ |

#### البنية التحتية

| الملف | الحالة | الوظيفة |
|-------|--------|---------|
| `main.py` | ✅ | نقطة دخول FastAPI مع lifespan |
| `settings.py` | ✅ | Pydantic Settings متكامل |
| `db.py` | ✅ | SQLAlchemy async مع session management |
| `deps.py` | ✅ | JWT auth + scope-based authorization |
| `exceptions.py` | ✅ | معالجة أخطاء موحدة |
| `middleware.py` | ✅ | Rate limiting (IP + User) |
| `telemetry.py` | ✅ | OpenTelemetry integration |
| `docker-compose.yml` | ✅ | 5 خدمات |
| `Dockerfile` | ✅ | multi-stage build |
| `pyproject.toml` | ✅ | dependencies كاملة |

### 2.2 الملفات المفقودة المطلوبة

| الملف | الأولوية | السبب |
|-------|----------|-------|
| `requirements.txt` | 🔴 حرجة | Dockerfile سيفشل بدونه |
| `logging_config.py` | 🔴 حرجة | مستورد في `main.py` |
| `alembic/env.py` | 🔴 حرجة | لإدارة الترحيلات |
| `worker/celery_app.py` | 🟡 متوسطة | للمهام الخلفية |
| `tests/` | 🟡 متوسطة | لضمان الجودة |
| `.env.example` | 🟢 منخفضة | للتوثيق |

### 2.3 الثغرات الأمنية المكتشفة

#### عالية الخطورة

```python
# ❌ ComputerService - Command Injection
def run_command(self, command: str, timeout: int = 30):
    result = subprocess.run(command, shell=True, ...)  # shell=True!

# ❌ File Operations - Path Traversal
def read_file(self, path: str):
    p = Path(path).expanduser().resolve()  # لا يوجد validation

# ❌ BrowserService - JavaScript Injection
async def evaluate(self, script: str):
    result = await self._page.evaluate(script)  # eval أي JS
```

#### متوسطة الخطورة

1. Rate limiter يعمل decode للـ JWT مرتين
2. OpenAI client غير thread-safe
3. لا يوجد scope check على بعض endpoints
4. RAG upload يعمل synchronously
5. CORS يسمح بـ `*` methods و headers

### 2.4 مقارنة مع IMPLEMENTATION_STUDY.md

| المطلوب في الدراسة | الحالة الفعلية | الفجوة |
|-------------------|---------------|--------|
| LangGraph | ❌ غير مُستخدم | كبيرة |
| Celery workers | ❌ غير مُطبّق | كبيرة |
| RAGAS evaluation | ❌ غير مُطبّق | متوسطة |
| Row-Level Security | ❌ غير مُطبّق | كبيرة |
| Structured Outputs | ❌ يستخدم text completion | متوسطة |
| Event Sourcing | ❌ غير مُطبّق | صغيرة |
| CI/CD pipeline | ❌ غير موجود | كبيرة |
| Tests | ❌ غير موجود | كبيرة |
| Frontend pages | ❌ فقط placeholder | كبيرة |
| Reranker | ❌ غير مُطبّق | متوسطة |
| PII redaction | ❌ غير مُطبّق | متوسطة |

---

## 3. المعمارية المرجعية

### 3.1 مخطط المعمارية الشامل

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NOUFEX_AI Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Mobile    │    │    Web      │    │   API       │    │  Webhook    │  │
│  │   Client    │    │   Client    │    │  Client     │    │  (Stripe)   │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│         └──────────────────┼──────────────────┼──────────────────┘         │
│                            │                  │                            │
│                    ┌───────▼──────────────────▼───────┐                   │
│                    │        Cloudflare WAF + CDN       │                   │
│                    │     (Rate Limit + SSL + DDoS)     │                   │
│                    └───────────────┬───────────────────┘                   │
│                                    │                                       │
│                    ┌───────────────▼───────────────────┐                   │
│                    │          nginx (Envoy)             │                   │
│                    │   (Reverse Proxy + JWT Verify)     │                   │
│                    └───────────────┬───────────────────┘                   │
│                                    │                                       │
│         ┌──────────────────────────┼──────────────────────────┐           │
│         │                          │                          │           │
│  ┌──────▼──────┐           ┌───────▼───────┐          ┌──────▼──────┐    │
│  │  Frontend   │           │    Backend    │          │   Workers   │    │
│  │  Next.js 16 │◀──REST/SSE▶│   FastAPI    │──enqueue─▶│   Celery    │    │
│  │  (RSC)      │           │   (async)    │          │   + RQ      │    │
│  └─────────────┘           └───────┬───────┘          └──────┬──────┘    │
│                                     │                         │           │
│                           ┌─────────▼─────────────────────────▼─────────┐ │
│                           │              Data Plane                      │ │
│                           │  ┌───────────┐ ┌───────────┐ ┌───────────┐ │ │
│                           │  │ PostgreSQL│ │   Redis   │ │    S3     │ │ │
│                           │  │ + pgvector│ │  + Celery │ │  (Files) │ │ │
│                           │  │  (RDS)    │ │  Broker   │ │          │ │ │
│                           │  └───────────┘ └───────────┘ └───────────┘ │ │
│                           │     (RLS لكل tenant)                        │ │
│                           └─────────────────────┬───────────────────────┘ │
│                                                 │                         │
│                           ┌─────────────────────▼───────────────────────┐ │
│                           │        External / Provider Plane             │ │
│                           │  ┌───────────┐ ┌───────────┐ ┌───────────┐ │ │
│                           │  │  OpenAI   │ │  Stripe   │ │  Sentry   │ │ │
│                           │  │ (Chat +   │ │ (Billing) │ │ (Errors)  │ │ │
│                           │  │Embeddings)│ │           │ │           │ │ │
│                           │  └───────────┘ └───────────┘ └───────────┘ │ │
│                           └─────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 مبادئ التصميم

#### 12-Factor App + Beyond

| المبدأ | التطبيق في NOUFEX_AI |
|--------|---------------------|
| **Codebase** | مستودع واحد (monorepo) |
| **Dependencies** | `requirements.txt` مُولَّد من `pyproject.toml` مع hashing |
| **Config** | متغيرات بيئة فقط، تُحمَّل عبر Pydantic Settings |
| **Backing services** | Postgres / Redis / S3 موصولة كـ URLs |
| **Build / Release / Run** | فصل صارم عبر CI |
| **Processes** | stateless API، كل حالة في Postgres/Redis |
| **Port binding** | uvicorn على المنفذ 8000 |
| **Concurrency** | horizontally scaled pods |
| **Disposability** | `lifespan` handlers لإغلاق رشيق |
| **Dev/Prod parity** | صورة Docker واحدة |
| **Logs** | stdout JSON → Loki/OTLP → Grafana |
| **Admin processes** | `alembic` كـ one-off container |

#### نمط النشر: Modular Monolith

نبدأ Modular Monolith بحزم (`users`, `agents`, `rag`, `billing`, `audit`) في تطبيق FastAPI واحد. الانتقال إلى Microservices **فقط** عند:
- زمن البناء > 10 دقائق
- تعارضات Git متكررة
- حاجة scaling غير متماثل

### 3.3 تدفق البيانات

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│ Frontend │────▶│ Backend  │────▶│  OpenAI  │
│ Request  │     │ (Next.js)│     │ (FastAPI)│     │   API    │
└──────────┘     └──────────┘     └────┬─────┘     └──────────┘
                                       │
                                       ▼
                                 ┌──────────┐     ┌──────────┐
                                 │PostgreSQL│────▶│ pgvector │
                                 │  (RDS)   │     │  Search  │
                                 └──────────┘     └──────────┘
                                       │
                                       ▼
                                 ┌──────────┐
                                 │  Redis   │
                                 │ (Cache)  │
                                 └──────────┘
```

---

## 4. التحقق من الحزمة التقنية

### 4.1 جدول التقنيات المحدث

| التقنية | الإصدار الحالي | الإصدار المُوصى به | المصدر المرجعي | السبب |
|---------|---------------|-------------------|----------------|-------|
| **Python** | 3.12 | 3.11.x (LTS) | python.org | دعم Pydantic v2 كامل |
| **FastAPI** | 0.139.0 | >=0.139.0 | fastapi.tiangolo.com | أحدث ميزات Annotated، OpenAPI 3.1 |
| **Pydantic** | 2.13.4 | >=2.13.0 | docs.pydantic.dev | Polymorphic serialization |
| **SQLAlchemy** | 2.0.51 | >=2.0.50 | sqlalchemy.org | AsyncIO support كامل |
| **asyncpg** | 0.29 | >=0.29 | magicstack/asyncpg | الأسرع لـ Postgres async |
| **pgvector** | 0.8.5 | >=0.8.0 | github.com/pgvector/pgvector | HNSW + halfvec + iterative scans |
| **Postgres** | 16 | 16-alpine | postgresql.org | JSON_TABLE، SKIP LOCKED |
| **Redis** | 7.x | 7.4-alpine | redis.io | Streams + Rate limiting |
| **Celery** | 5.6.3 | >=5.4 | docs.celeryq.dev | Canvas + ETA |
| **LangGraph** | نشط | أحدث | langchain-ai/langgraph | State graphs + checkpointing |
| **Next.js** | 16.3 | >=16.0 | nextjs.org | Turbopack + AI improvements |
| **Tailwind** | 3.4 | >=3.4 | tailwindcss.com | JIT + tree-shake |
| **OpenAI** | GPT-5.4 | GPT-4o-mini+ | platform.openai.com | Structured Outputs |
| **OpenTelemetry** | 1.27 | >=1.27 | opentelemetry.io | GenAI semantic conventions |
| **Pydantic** | 2.13.4 | >=2.13.0 | docs.pydantic.dev | أداء + TypeAdapter |

### 4.2 مقارنة الإصدارات

#### FastAPI: 0.115 → 0.139

| الميزة | 0.115 | 0.139 |
|--------|-------|-------|
| Query Parameter Models | ❌ | ✅ |
| Header Parameter Models | ❌ | ✅ |
| Cookie Parameter Models | ❌ | ✅ |
| Server-Sent Events | أساسي | محسّن |
| Stream JSON Lines | ❌ | ✅ |

#### pgvector: 0.3.6 → 0.8.5

| الميزة | 0.3.6 | 0.8.5 |
|--------|-------|-------|
| HNSW | ❌ | ✅ |
| halfvec | ❌ | ✅ |
| sparsevec | ❌ | ✅ |
| Binary Quantization | ❌ | ✅ |
| Iterative Index Scans | ❌ | ✅ |

#### OWASP LLM: v1.1 → v2025

| العنصر | v1.1 (2023) | v2025 |
|--------|-------------|-------|
| Vector and Embedding Weaknesses | ❌ | ✅ (جديد) |
| System Prompt Leakage | ❌ | ✅ (جديد) |
| Training Data Poisoning | منفصل | مدمج مع Data Poisoning |

### 4.3 التوصيات بالتحديث

| الملف | التغيير المطلوب |
|-------|-----------------|
| `requirements.txt` | تحديث pgvector من 0.3.6 إلى 0.8.5 |
| `requirements.txt` | تحديث FastAPI من 0.115.0 إلى 0.139.0 |
| `requirements.txt` | تحديث Pydantic من 2.9.2 إلى 2.13.4 |
| `docker-compose.yml` | تحديث pgvector image إلى pg16 |

---

## 5. هيكل المستودع

### 5.1 الهيكل المحدث

```
NOUFEX_AI/
├── backend/
│   ├── pyproject.toml                    # ✅ موجود
│   ├── requirements.in                   # ⚠️ مفقود
│   ├── requirements.txt                  # ⚠️ مفقود (يُولَّد من pyproject.toml)
│   ├── alembic.ini                       # ✅ موجود
│   ├── alembic/
│   │   ├── env.py                        # ⚠️ مفقود
│   │   └── versions/
│   ├── noufex_ai/
│   │   ├── __init__.py                   # ✅ موجود
│   │   ├── main.py                       # ✅ موجود
│   │   ├── settings.py                   # ✅ موجود
│   │   ├── logging_config.py             # ⚠️ مفقود
│   │   ├── telemetry.py                  # ✅ موجود
│   │   ├── db.py                         # ✅ موجود
│   │   ├── deps.py                       # ✅ موجود
│   │   ├── exceptions.py                 # ✅ موجود
│   │   ├── middleware.py                  # ✅ موجود
│   │   ├── modules/
│   │   │   ├── users/                    # ✅ مكتمل
│   │   │   ├── tenants/                  # ✅ مكتمل
│   │   │   ├── agents/                   # ✅ مكتمل
│   │   │   ├── rag/                      # ✅ مكتمل
│   │   │   ├── chat/                     # ✅ مكتمل
│   │   │   ├── billing/                  # ✅ مكتمل
│   │   │   ├── computer/                 # ✅ مكتمل (يحتاج أمان)
│   │   │   ├── browser/                  # ✅ مكتمل
│   │   │   ├── design/                   # ✅ ممتاز
│   │   │   ├── audit/                    # ⚠️ جزئي
│   │   │   └── agent_skills/             # ✅ ممتاز
│   │   └── worker/
│   │       ├── celery_app.py             # ⚠️ مفقود
│   │       └── tasks.py                  # ⚠️ مفقود
│   ├── tests/
│   │   ├── conftest.py                   # ⚠️ مفقود
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── evals/
│   │   └── load/
│   ├── scripts/
│   │   ├── seed.py                       # ⚠️ مفقود
│   │   ├── eval.py                       # ⚠️ مفقود
│   │   └── benchmark.py                  # ⚠️ مفقود
│   ├── Dockerfile                        # ✅ موجود
│   └── Makefile                          # ✅ موجود
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                    # ✅ موجود
│   │   ├── page.tsx                      # ✅ موجود (placeholder)
│   │   ├── (auth)/                       # ⚠️ مفقود
│   │   ├── (dashboard)/                  # ⚠️ مفقود
│   │   └── api/                          # ⚠️ مفقود
│   ├── components/
│   │   └── ui/                           # ⚠️ مفقود
│   ├── lib/
│   │   ├── api-client.ts                 # ⚠️ مفقود
│   │   └── auth.ts                       # ⚠️ مفقود
│   ├── package.json                      # ✅ موجود
│   ├── tailwind.config.ts                # ✅ موجود
│   ├── Dockerfile                        # ✅ موجود
│   └── .env.example                      # ⚠️ مفقود
├── ai-models/
│   ├── prompts/
│   │   ├── system.txt                    # ⚠️ مفقود
│   │   ├── rag.answer.md                 # ⚠️ مفقود
│   │   └── tool.use.json                 # ⚠️ مفقود
│   └── evals/
│       ├── datasets/                     # ⚠️ مفقود
│       └── scorers.json                  # ⚠️ مفقود
├── infrastructure/
│   ├── docker-compose.yml                # ✅ موجود
│   ├── docker-compose.prod.yml           # ⚠️ مفقود
│   ├── nginx/                            # ⚠️ مفقود
│   ├── prometheus/                       # ⚠️ مفقود
│   ├── grafana/                          # ⚠️ مفقود
│   ├── loki/                             # ⚠️ مفقود
│   └── tempo/                            # ⚠️ مفقود
├── scripts/
│   ├── seed.py                           # ⚠️ مفقود
│   ├── eval.py                           # ⚠️ مفقود
│   └── benchmark.py                      # ⚠️ مفقود
├── .env.example                          # ⚠️ مفقود
├── .github/
│   └── workflows/
│       ├── ci.yml                        # ⚠️ مفقود
│       └── cd.yml                        # ⚠️ مفقود
├── FEASIBILITY_STUDY.md                  # ✅ موجود
└── IMPLEMENTATION_STUDY_V2.md            # ✅ موجود (هذا الملف)
```

### 5.2 أولوية إنشاء الملفات

| الأولوية | الملفات | الوقت المقدر |
|----------|---------|-------------|
| 🔴 P0 (حرجة) | requirements.txt, logging_config.py, alembic/env.py | يوم 1 |
| 🟡 P1 (مهمة) | worker/celery_app.py, tests/conftest.py, .env.example | أسبوع 1 |
| 🟡 P2 (مهمة) | frontend pages, components, api-client | أسبوع 2-3 |
| 🟢 P3 (تحسينية) | prompts, evals, scripts, infrastructure | أسبوع 3-4 |

---

## 6. تنفيذ Backend

### 6.1 نقطة الدخول مع lifespan

```python
# backend/noufex_ai/main.py (محدث)
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from noufex_ai.settings import settings
from noufex_ai.telemetry import setup_telemetry
from noufex_ai.db import engine, async_session_maker

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    setup_telemetry(app, service_name="noufex-ai")
    await engine.connect()
    
    yield
    
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="NOUFEX AI",
    version="2.0.0",
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)
```

**المراجع:**
- FastAPI Advanced User Guide - Lifespan Events
  https://fastapi.tiangolo.com/advanced/events/

### 6.2 Multi-Tenancy عبر Row-Level Security

```sql
-- تفعيل RLS على جميع الجداول
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON agents
USING (tenant_id = current_setting('app.tenant_id')::uuid)
WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
```

```python
# Middleware لحقن tenant_id
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    tenant_id = request.state.user.tenant_id if request.state.user else "public"
    async with engine.begin() as conn:
        await conn.execute(
            text("SET LOCAL app.tenant_id = :tid"),
            {"tid": str(tenant_id)}
        )
        response = await call_next(request)
    return response
```

**المراجع:**
- PostgreSQL Documentation - Row Level Security
  https://www.postgresql.org/docs/current/ddl-rowsecurity.html

### 6.3 Structured Outputs (OpenAI)

```python
from pydantic import BaseModel
from openai import AsyncOpenAI

class AgentReply(BaseModel):
    answer: str
    citations: list[dict]
    tool_calls: list[dict]
    confidence: float

async def run_agent(messages: list, tools: list) -> AgentReply:
    client = AsyncOpenAI()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        response_format=AgentReply,  # Structured Outputs
    )
    return AgentReply.model_validate_json(resp.choices[0].message.content)
```

**المراجع:**
- OpenAI Structured Outputs Guide
  https://platform.openai.com/docs/guides/structured-outputs

### 6.4 Tool Registry + Allowlist

```python
# OWASP LLM07: Insecure Plugin Design
# OWASP LLM08: Excessive Agency
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

**المراجع:**
- OWASP LLM Top 10 v2025 - LLM06 Excessive Agency
  https://genai.owasp.org/llm-top-10/

### 6.5 Streaming عبر SSE

```python
from fastapi.responses import StreamingResponse

@chat_router.post("/stream")
async def stream(payload: ChatRequest):
    async def event_publisher():
        async for chunk in run_agent_stream(payload):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_publisher(),
        media_type="text/event-stream"
    )
```

**المراجع:**
- FastAPI Server-Sent Events
  https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse

### 6.6 Celery Worker

```python
# backend/noufex_ai/worker/celery_app.py
from celery import Celery
from noufex_ai.settings import settings

celery_app = Celery(
    "noufex_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)

# backend/noufex_ai/worker/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=5, default_retry_delay=30, acks_late=True)
def ingest_document(self, tenant_id: str, doc_id: str):
    try:
        from noufex_ai.modules.rag.service import ingest_document
        ingest_document(tenant_id, doc_id)
    except Exception as exc:
        raise self.retry(exc=exc)
```

**المراجع:**
- Celery Documentation - Tasks
  https://docs.celeryq.dev/en/stable/userguide/tasks.html

---

## 7. مخطط قاعدة البيانات

### 7.1 المخطط الكامل (Postgres 16)

```sql
-- V0001__init.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- المستأجرين
CREATE TABLE tenants (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        text NOT NULL,
    plan        text NOT NULL CHECK (plan IN ('free','starter','pro','business','enterprise')),
    settings    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- المستخدمين
CREATE TABLE users (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id     uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email         citext UNIQUE NOT NULL,
    password_hash text NOT NULL,
    full_name     text,
    role          text NOT NULL DEFAULT 'member' CHECK (role IN ('owner','admin','member','viewer')),
    is_active     bool NOT NULL DEFAULT true,
    last_login    timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX users_tenant_idx ON users(tenant_id);
CREATE INDEX users_email_idx ON users(email);

-- الوكلاء
CREATE TABLE agents (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id     uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name          text NOT NULL,
    description   text,
    system_prompt text NOT NULL,
    model         text NOT NULL DEFAULT 'gpt-4o-mini',
    temperature   real NOT NULL DEFAULT 0.2 CHECK (temperature BETWEEN 0 AND 2),
    max_tokens    int NOT NULL DEFAULT 1024,
    tools         jsonb NOT NULL DEFAULT '[]'::jsonb,
    config        jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active     bool NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agents_tenant ON agents
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE INDEX agents_tenant_idx ON agents(tenant_id);

-- المستندات
CREATE TABLE documents (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   uuid NOT NULL,
    agent_id    uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    filename    text NOT NULL,
    file_type   text NOT NULL,
    file_size   bigint NOT NULL,
    status      text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','failed')),
    error       text,
    metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY docs_tenant ON documents
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- أجزاء المعرفة
CREATE TABLE knowledge_chunks (
    id          bigserial PRIMARY KEY,
    tenant_id   uuid NOT NULL,
    agent_id    uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_no    int NOT NULL,
    content     text NOT NULL,
    embedding   halfvec(1536) NOT NULL,
    metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
    tsv         tsvector GENERATED ALWAYS AS (
        to_tsvector('arabic', content)
    ) STORED,
    UNIQUE (agent_id, document_id, chunk_no)
);
ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY kc_tenant ON knowledge_chunks
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE INDEX kc_embed_hnsw ON knowledge_chunks
    USING hnsw (embedding halfvec_cosine_ops);
CREATE INDEX kc_tsv_gin ON knowledge_chunks USING gin (tsv);

-- المحادثات
CREATE TABLE conversations (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   uuid NOT NULL,
    agent_id    uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id     uuid REFERENCES users(id) ON DELETE SET NULL,
    title       text,
    metadata    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY conv_tenant ON conversations
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- الرسائل
CREATE TABLE messages (
    id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            text NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    content         text NOT NULL,
    tool_calls      jsonb,
    tool_call_id    text,
    metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
    token_count     int,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX messages_conv_idx ON messages(conversation_id, created_at);

-- سجل التدقيق
CREATE TABLE audit_log (
    id          bigserial PRIMARY KEY,
    tenant_id   uuid NOT NULL,
    user_id     uuid,
    action      text NOT NULL,
    resource    text NOT NULL,
    resource_id text,
    details     jsonb NOT NULL DEFAULT '{}'::jsonb,
    ip_address  inet,
    user_agent  text,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_tenant_idx ON audit_log(tenant_id, created_at);
CREATE INDEX audit_action_idx ON audit_log(action);

-- Refresh Tokens
CREATE TABLE refresh_tokens (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  text NOT NULL UNIQUE,
    expires_at  timestamptz NOT NULL,
    revoked_at  timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX refresh_tokens_user_idx ON refresh_tokens(user_id);

-- الاشتراكات
CREATE TABLE subscriptions (
    id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    stripe_sub_id   text UNIQUE,
    plan            text NOT NULL,
    status          text NOT NULL DEFAULT 'active',
    current_period_start timestamptz,
    current_period_end   timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
```

**المراجع:**
- PostgreSQL 16 Documentation
  https://www.postgresql.org/docs/16/
- pgvector v0.8.5 README
  https://github.com/pgvector/pgvector

### 7.2 ملاحظات على المخطط

1. **`halfvec(1536)`** بدلاً من `vector(1536)`: نصف الذاكرة في الذاكرة العاملة
2. **`tsvector` مُولَّد**: للبحث النصي الكامل باللغة العربية
3. **`citext`**: للبريد الإلكتروني case-insensitive
4. **`jsonb`**: للمرونة في البيانات الإضافية
5. **RLS مفعّل**: على جميع الجداول الحساسة

---

## 8. مخزن المتجهات (pgvector)

### 8.1 خيارات الفهرسة

| الخيار | السرعة | الذاكرة | Recall | البناء |
|--------|--------|---------|--------|--------|
| **HNSW** | الأفضل | أكثر | الأفضل | أبطأ |
| **IVFFlat** | أقل | أقل | أقل | أسرع |

**التوصية:** HNSW لـ NOUFEX_AI (أفضل recall مع حجم بيانات متوسط)

### 8.2 إعدادات pgvector

```sql
-- قبل بناء HNSW index
SET maintenance_work_mem = '8GB';
SET max_parallel_maintenance_workers = 7;

-- إنشاء الفهرس
CREATE INDEX CONCURRENTLY kc_embed_hnsw ON knowledge_chunks
    USING hnsw (embedding halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- تفعيل iterative scans (pgvector v0.8+)
SET hnsw.iterative_scan = relaxed_order;
```

### 8.3 قياس Recall

```sql
-- تقييم Recall قبل وبعد
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
    (SELECT count(*) FROM (
        SELECT id FROM approx INTERSECT SELECT id FROM exact
    ) t)::float / 50 AS recall_at_50;
COMMIT;
```

### 8.4 نصائح الأداء من pgvector README

1. **استخدم `halfvec`** بدلاً من `vector` لتوفير الذاكرة
2. **استخدم `inner product`** للـ embeddings المُعيَّرة (مثل OpenAI)
3. **أنشئ الفهارس بعد تحميل البيانات**
4. **استخدم `COPY`** للتحميل الجماعي
5. **استخدم `CREATE INDEX CONCURRENTLY`** في الإنتاج

**المراجع:**
- pgvector README - Performance Tips
  https://github.com/pgvector/pgvector#performance

---

## 9. إطار الوكلاء (LangGraph)

### 9.1 رسم حالة الوكيل

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

### 9.2 تنفيذ LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    context: list[str]
    tools_called: list[str]
    token_usage: dict

def router(state: AgentState) -> str:
    """يقرر ما إذا كان يحتاج معلومات من قاعدة المعرفة"""
    last_msg = state["messages"][-1]
    return "retrieve" if last_msg.get("needs_kg") else "answer"

def retriever(state: AgentState) -> dict:
    """يبحث في قاعدة المعرفة"""
    query = state["messages"][-1]["content"]
    results = search_knowledge(query, k=8)
    return {"context": results}

def draft(state: AgentState) -> dict:
    """ يولّد إجابة مسودة"""
    response = await llm_call(state)
    return {"messages": [response]}

def check(state: AgentState) -> str:
    """يتحقق من جودة الإجابة"""
    if state["messages"][-1].get("low_confidence"):
        return "retry"
    return "final"

# بناء الرسم
g = StateGraph(AgentState)
g.add_node("retrieve", retriever)
g.add_node("draft", draft)
g.add_node("answer", lambda s: {"messages": [format_answer(s)]})
g.add_conditional_edges("retrieve", router, {"retrieve": END, "answer": "answer"})
g.add_conditional_edges("draft", check, {"retry": "retrieve", "final": "answer"})
g.set_entry_point("retrieve")
graph = g.compile()
```

### 9.3 Checkpointing

```python
# حفالة الرسم في قاعدة البيانات
CREATE TABLE agent_runs (
    run_id      uuid PRIMARY KEY,
    thread_id   text NOT NULL,
    state       jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
```

**المراجع:**
- LangGraph Documentation
  https://langchain-ai.github.io/langgraph/

---

## 10. مواصفات API

### 10.1 جدول endpoints

| Method | Path | الوصف | المصادقة |
|--------|------|-------|---------|
| POST | `/v1/users/signup` | تسجيل حساب | ❌ |
| POST | `/v1/users/login` | تسجيل دخول | ❌ |
| POST | `/v1/users/refresh` | تدوير Token | ✅ |
| GET | `/v1/users/me` | بيانات المستخدم | ✅ |
| GET | `/v1/tenants` | قائمة المستأجرين | ✅ (admin) |
| POST | `/v1/tenants` | إنشاء مستأجر | ✅ (admin) |
| GET | `/v1/agents` | قائمة الوكلاء | ✅ |
| POST | `/v1/agents` | إنشاء وكيل | ✅ |
| PATCH | `/v1/agents/{id}` | تحديث وكيل | ✅ |
| DELETE | `/v1/agents/{id}` | حذف وكيل | ✅ |
| POST | `/v1/rag/documents` | رفع مستند | ✅ |
| GET | `/v1/rag/documents/{id}/status` | حالة المستند | ✅ |
| POST | `/v1/chat` | تشغيل الوكيل | ✅ |
| POST | `/v1/chat/stream` | SSE stream | ✅ |
| GET | `/v1/chat/{run_id}` | استرجاع محادثة | ✅ |
| POST | `/v1/billing/webhook` | Stripe webhook | ❌ (verified) |

### 10.2 اتفاقيات الاستجابة

#### نجاح
```json
{
    "data": { ... },
    "meta": {
        "request_id": "uuid",
        "timestamp": "ISO8601"
    }
}
```

#### خطأ
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": [...],
        "trace_id": "uuid"
    }
}
```

### 10.3 Rate Limiting

| Endpoint | الحد | النافذة |
|----------|------|---------|
| POST `/v1/users/login` | 5 | دقيقة |
| POST `/v1/chat` | 60 | دقيقة |
| POST `/v1/rag/documents` | 10 | ساعة |
| POST `/v1/billing/webhook` | 100 | دقيقة |

**المراجع:**
- FastAPI Documentation
  https://fastapi.tiangolo.com/

---

## 11. المصادقة والتفويض

### 11.1 JWT Configuration

```python
# Access Token
ACCESS_TOKEN_EXPIRE_MINUTES = 15
ALGORITHM = "EdDSA"  # Ed25519

# Refresh Token
REFRESH_TOKEN_EXPIRE_DAYS = 30
ROTATE_ON_USE = True  # كل refresh يُلغي السابق

# Claims
{
    "sub": "user_id",
    "tenant_id": "tenant_id",
    "scope": ["chat:read", "chat:write", "agents:manage"],
    "role": "admin",
    "exp": timestamp,
    "iat": timestamp,
    "jti": "unique_token_id"
}
```

### 11.2 Scopes

| Scope | الوصف |
|-------|-------|
| `chat:read` | قراءة المحادثات |
| `chat:write` | إنشاء محادثات |
| `agents:read` | قراءة الوكلاء |
| `agents:manage` | إنشاء/تعديل/حذف الوكلاء |
| `rag:read` | قراءة المستندات |
| `rag:write` | رفع مستندات |
| `billing:read` | قراءة الفواتير |
| `billing:manage` | إدارة الاشتراكات |
| `admin` | صلاحيات كاملة |

### 11.3 Password Hashing

```python
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,        # عدد التكرارات
    memory_cost=65536,   # 64MB
    parallelism=4,       # عدد الـ threads
)

# Hash
hashed = ph.hash(password)

# Verify
try:
    ph.verify(hashed, password)
except VerifyMismatchError:
    # كلمة مرور خاطئة
```

**المراجع:**
- Argon2 Specification
  https://github.com/P-H-C/phc-winner-argon2
- PyJWT Documentation
  https://pyjwt.readthedocs.io/

---

## 12. الأمان (OWASP LLM Top 10 v2025)

### 12.1 OWASP LLM Top 10 — التطبيق

| ID | التهديد | الضابط المُطبَّق |
|----|---------|-----------------|
| **LLM01** Prompt Injection | حقن تعليمات | 1) فصل system prompt عن user input بقالب `<<SYS>>...<</SYS>>`; 2) classifier مدخلات; 3) حدود tool calls |
| **LLM02** Sensitive Information Disclosure | تسريب معلومات | PII redaction (Microsoft Presidio); فلترة tenant_id في نتائج البحث |
| **LLM03** Supply Chain | ثغرات سلسلة التوريد | pip-audit; Trivy على الصور; SBOM بـ syft; Renovate |
| **LLM04** Data and Model Poisoning | تسمم البيانات | توقيع رقمي (SHA256); تتبّع مصدر في metadata; تواريخ انتهاء |
| **LLM05** Improper Output Handling | معالجة خاطئة للمخرجات | Structured Outputs (Pydantic); عدم تمرير أي حقل لـ eval/exec |
| **LLM06** Excessive Agency | صلاحيات مفرطة | Tool Registry + Allowlist; OOB approval للإجراءات الحساسة |
| **LLM07** System Prompt Leakage | تسريب System Prompt | عدم إرجاع system prompt في الاستجابات; monitoring |
| **LLM08** Vector and Embedding Weaknesses | ثغرات المتجهات | فلترة tenant_id; validation على المتجهات; monitoring |
| **LLM09** Misinformation | معلومات مضللة | عرض المصادر (citations إجبارية); confidence ≥ 0.6 |
| **LLM10** Unbounded Consumption | استهلاك غير محدود | Token Bucket per-tenant; max-output-tokens=1024; circuit breaker |

### 12.2 OWASP Top 10 (2021) — تكملة

| البند | الضابط |
|-------|--------|
| A01 Broken Access Control | RLS + tenant middleware + تحقق scope |
| A02 Cryptographic Failures | TLS 1.3; mTLS; Argon2id |
| A03 Injection | SQLAlchemy parameters; لا f-string في SQL |
| A04 Insecure Design | Threat Modeling في كل Sprint |
| A05 Security Misconfig | Trivy + CIS Benchmarks |
| A06 Vulnerable Components | Dependabot + pip-audit |
| A07 Identification & Auth Failures | WebAuthn/MFA; قفل بعد 5 محاولات |
| A08 Software & Data Integrity | Sigstore Cosign; SBOM |
| A09 Logging & Monitoring | OTel → Loki; PagerDuty alerts |
| A10 SSRF | IP ranges مسموحة; لا proxy شامل |

### 12.3 إصلاحات أمنية مطلوبة فوراً

```python
# ❌ قبل (Command Injection)
def run_command(self, command: str, timeout: int = 30):
    result = subprocess.run(command, shell=True, ...)

# ✅ بعد (آمن)
def run_command(self, command: list[str], timeout: int = 30):
    result = subprocess.run(command, shell=False, ...)

# ❌ قبل (Path Traversal)
def read_file(self, path: str):
    p = Path(path).expanduser().resolve()

# ✅ بعد (مع validation)
def read_file(self, path: str):
    p = Path(path).expanduser().resolve()
    allowed_dirs = [Path.home() / "documents", Path("/tmp")]
    if not any(p.is_relative_to(d) for d in allowed_dirs):
        raise PermissionError("Path not allowed")
```

**المراجع:**
- OWASP LLM Top 10 v2025
  https://genai.owasp.org/llm-top-10/
- OWASP Top 10 (2021)
  https://owasp.org/www-project-top-ten/

---

## 13. الأداء وقابلية التوسع

### 13.1 SLA Targets

| المعيار | الهدف |
|---------|-------|
| p50 أول توكن | < 700ms |
| p95 أول توكن | < 1.8s |
| p99 أول توكن | < 3s |
| Throughput | 200 RPS بـ 8 workers |
| Error rate | < 0.1% |
| Uptime | ≥ 99.9% |

### 13.2 Scaling Stages

| المرحلة | المستخدمين النشطين | الإعداد |
|---------|-------------------|---------|
| 0 → 100k | 1k DAU | صورة واحدة، RDS db.t4g.medium |
| 100k → 1M | 10k DAU | 3 نسخ API + read-replica |
| 1M → 10M | 100k DAU | Kubernetes، pgvector على Citus |
| 10M+ | — | فصل RAG microservice + GPU inference |

### 13.3 Caching Strategy

```python
# L1: Redis Cache
CACHE_TTL = 3600 * 6  # 6 ساعات

async def get_cached_answer(prompt_hash: str, context_hash: str) -> Optional[str]:
    key = f"answer:{prompt_hash}:{context_hash}"
    return await redis.get(key)

async def set_cached_answer(prompt_hash: str, context_hash: str, answer: str):
    key = f"answer:{prompt_hash}:{context_hash}"
    await redis.setex(key, CACHE_TTL, answer)
```

### 13.4 Circuit Breaker

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((OpenAIError, TimeoutError))
)
async def call_openai(messages: list, model: str) -> str:
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        timeout=30
    )
    return response.choices[0].message.content
```

**المراجع:**
- Tenacity Documentation
  https://tenacity.readthedocs.io/

---

## 14. الموثوقية

### 14.1 Error Budget

| المعيار | الهدف |
|---------|-------|
| Error Budget الشهري | 0.1% (~43 دقيقة) |
| MTTR | < 30 دقيقة |
| MTBF | > 720 ساعة |

### 14.2 Retry Strategy

```python
# Exponential backoff مع jitter
import random
import asyncio

async def retry_with_backoff(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
```

### 14.3 Graceful Shutdown

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    yield
    # Shutdown
    logger.info("Draining connections...")
    await asyncio.sleep(30)  # انتظار 30 ثانية
    await dispose_engine()
```

**المراجع:**
- FastAPI Lifespan Events
  https://fastapi.tiangolo.com/advanced/events/

---

## 15. المراقبة وقابلية الملاحظة

### 15.1 الأعمدة الثلاثة

| العمود | الأداة | النموذج |
|--------|--------|---------|
| **Logs** | Loki + Promtail | JSON مع tenant_id, run_id |
| **Metrics** | Mimir + Prometheus | counters/gauges/histograms |
| **Traces** | Tempo + OTel | LLM calls مُعلَّمة بـ gen_ai.* |

### 15.2 OpenTelemetry GenAI Semantic Conventions

```python
from opentelemetry import trace

tracer = trace.get_tracer("noufex-ai")

async def call_llm(messages: list, model: str):
    with tracer.start_as_current_span("llm.call") as span:
        span.set_attribute("gen_ai.client.operation.name", "chat")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.request.max_tokens", 1024)
        
        response = await openai_client.chat.completions.create(...)
        
        span.set_attribute("gen_ai.response.model", response.model)
        span.set_attribute("gen_ai.response.finish_reason", response.choices[0].finish_reason)
        span.set_attribute("gen_ai.client.token.usage.input", response.usage.prompt_tokens)
        span.set_attribute("gen_ai.client.token.usage.output", response.usage.completion_tokens)
        
        return response
```

**المراجع:**
- OpenTelemetry GenAI Semantic Conventions
  https://opentelemetry.io/docs/specs/semconv/gen-ai/

### 15.3 لوحات Grafana الحرجة

1. **تكلفة OpenAI لكل tenant** (مؤشّر مهم للربحية)
2. **Recall@10 يومي** من evals/datasets/
3. **Latency per-agent** (p50/p95/p99)
4. **Rate-limit rejections** لكل tenant
5. **Error rate** حسب endpoint

---

## 16. استراتيجية الاختبار

### 16.1 مستويات الاختبار

| المستوى | الأداة | التغطية | الهدف |
|---------|--------|---------|-------|
| **Unit** | pytest + pytest-asyncio + hypothesis | 85% | منطق الأعمال |
| **Integration** | pytest + testcontainers | على كل boundary | تكامل الخدمات |
| **API contract** | Schemathesis + OpenAPI | 100% | توافق API |
| **LLM-as-judge** | RAGAS + GPT-4o | يومي | جودة RAG |
| **Security** | bandit, pip-audit, Trivy | أسبوعي | ثغرات أمنية |
| **Load** | Locust + k6 | شهري | أداء |
| **Visual** | Playwright | per release | واجهة |

### 16.2 مجموعة التقييم

```json
// ai-models/evals/datasets/golden_v1.jsonl
{
    "question": "ما هي سياسة الإرجاع؟",
    "expected_answer": "يمكنك إرجاع المنتج خلال 30 يوم...",
    "expected_context": ["doc_id:123", "doc_id:456"],
    "expected_citations": [
        {"source": "سياسة الإرجاع", "page": 3}
    ]
}
```

### 16.3 مقاييس RAGAS

| المقياس | الوصف | الهدف |
|---------|-------|-------|
| **Faithfulness** | مدى ارتباط الإجابة بالسياق | ≥ 0.9 |
| **Answer Relevancy** | مدى صلة الإجابة بالسؤال | ≥ 0.85 |
| **Context Precision** | دقة السياق المسترجع | ≥ 0.8 |
| **Context Recall** | تغطية السياق | ≥ 0.92 |

**المراجع:**
- RAGAS Documentation
  https://docs.ragas.io/

---

## 17. خط أنابيب CI/CD

### 17.1 GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request: {}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy backend/

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: noufex_ai_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-dev.txt
      - run: pytest -n auto --cov=backend --cov-fail-under=85

  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit pip-audit
      - run: bandit -r backend/
      - run: pip-audit

  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t noufex-ai:${{ github.sha }} ./backend
      - run: docker build -t noufex-frontend:${{ github.sha }} ./frontend
      - run: |
          pip install trivy
          trivy image --severity HIGH,CRITICAL --exit-code 1 noufex-ai:${{ github.sha }}
```

### 17.2 GitHub Actions CD

```yaml
# .github/workflows/cd.yml
name: CD
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          docker tag noufex-ai:${{ github.sha }} ghcr.io/noufex/noufex-ai:staging
          docker push ghcr.io/noufex/noufex-ai:staging
      - run: kubectl rollout restart deployment/noufex-ai -n staging

  deploy-production:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    needs: deploy-staging
    steps:
      - uses: actions/checkout@v4
      - run: |
          docker tag noufex-ai:${{ github.sha }} ghcr.io/noufex/noufex-ai:latest
          docker push ghcr.io/noufex/noufex-ai:latest
      - run: kubectl rollout restart deployment/noufex-ai -n production
```

**المراجع:**
- GitHub Actions Documentation
  https://docs.github.com/en/actions

---

## 18. خطة النشر

### 18.1 البيئات

| البيئة | المضيف | الغرض |
|--------|--------|-------|
| **Local** | Docker Compose | تطوير |
| **CI** | GitHub Actions | اختبار |
| **Staging** | EKS / fly.io | معاينة |
| **Production** | AWS us-east-1 + eu-west-1 | إنتاج |

### 18.2 استراتيجيات الإطلاق

| الاستراتيجية | الاستخدام |
|--------------|----------|
| **Blue/Green** | الافتراضي |
| **Canary** | عند تغيير منطق الوكيل |
| **Feature Flags** | عبر Unleash |

### 18.3 Data Backups

| النسخة | الهدف | التكرار |
|--------|-------|---------|
| WAL archiving | PITR | مستمر |
| Base backup | كامل | يومي |
| S3 snapshot | أرشيف | أسبوعي |

**الأهداف:**
- RPO: 5 دقائق
- RTO: 30 دقيقة

---

## 19. هندسة التكلفة

### 19.1 تكاليف شهر 1-3 (MVP)

| المكوّن | التكلفة الشهرية | التحسين |
|---------|----------------|---------|
| OpenAI (mini) | $20-50 | Prompt caching |
| RDS PostgreSQL | $0-15 | Free Tier |
| ElastiCache Redis | $0-25 | Free Tier |
| S3 | $2-5 | Lifecycle policy |
| Cloudflare | $0 | Free Plan |
| **المجموع** | **$22-95** | |

### 19.2 تكاليف شهر 4-8 (النمو)

| المكوّن | التكلفة الشهرية | التحسين |
|---------|----------------|---------|
| OpenAI | $150-300 | Model routing |
| RDS PostgreSQL | $70-100 | Reserved |
| ElastiCache | $200-300 | Reserved |
| S3 | $15-30 | Intelligent-Tiering |
| EC2 | $200-400 | Savings Plans |
| Cloudflare | $20 | Pro |
| Sentry | $26 | Team |
| Grafana | $38-100 | Pro |
| **المجموع** | **$719-1,276** | |

### 19.3 تكاليف شهر 9-12+ (الإنتاج)

| المكوّن | التكلفة الشهرية | التحسين |
|---------|----------------|---------|
| OpenAI | $1,000-3,000 | Batch API |
| RDS PostgreSQL | $350-700 | Multi-AZ |
| ElastiCache | $500-1,000 | Multi-node |
| S3 | $100-200 | Intelligent-Tiering |
| EC2/EKS | $1,200-2,400 | Reserved |
| Cloudflare | $200 | Business |
| Sentry | $80 | Business |
| Grafana | $200-500 | Pro |
| SendGrid | $90-200 | Pro |
| Langfuse | $199 | Pro |
| **المجموع** | **$3,919-8,380** | |

### 19.4 نصائح لتقليل التكلفة

1. **ابدأ بالخطط المجانية** لجميع الخدمات
2. **استخدم Prompt Caching** (90% خصم على cached input)
3. **استخدم Batch API** (50% خصم للمهام غير المباشرة)
4. **استخدم نماذج أصغر** (GPT-5.4-nano للمهام البسيطة)
5. **راقب الاستخدام** مع alerts للميزانية

---

## 20. الامتثال

### 20.1 GDPR (EU 2016/679)

| المطلب | التطبيق |
|--------|---------|
| Data Processing Addendum | مع OpenAI وجميع الموردين |
| حق النسيان | DELETE /users/me مع cascade |
| سجل الوصول | audit_log جدول |
| تشفير البيانات | TLS 1.3 + AES-256 |
| نسخ احتياطي مشفر | KMS |

### 20.2 SOC 2 Type II

| الضابط | التطبيق |
|--------|---------|
| Access Control | RBAC + MFA |
| Encryption | TLS + KMS |
| Backup | WAL + PITR |
| Incident Response | PagerDuty + Runbooks |
| Monitoring | OTel + Grafana |

### 20.3 ISO 27001 (مسار السنة الثالثة)

- ISMS (Information Security Management System)
- Risk Assessment
- Security Controls
- Audit Program

---

## 21. خارطة الطريق التنفيذية

### الأسبوع 1-2: التأسيس (Foundation)

```
الهدف: إصلاح الملفات المفقودة وإعداد البنية الأساسية

المهام:
├── [P0] إنشاء requirements.txt من pyproject.toml
├── [P0] إنشاء logging_config.py
├── [P0] إنشاء alembic/env.py
├── [P0] إصلاح الثغرات الأمنية (shell=True, path traversal)
├── [P1] إنشاء .env.example
├── [P1] إعداد worker/celery_app.py
├── [P1] إنشاء tests/conftest.py
└── [P1] إعداد CI (GitHub Actions)

التسليم:
├── Docker يُبنى بنجاح
├── Alembic يعمل
├── CI يمر
└── لا ثغرات أمنية حرجة
```

### الأسبوع 3-4: RAG والوكلاء

```
الهدف: تطبيق RAG pipeline كامل مع LangGraph

المهام:
├── [P1] تحديث pgvector إلى 0.8.5
├── [P1] تفعيل HNSW + halfvec
├── [P1] تطبيق Structured Outputs
├── [P1] تطبيق LangGraph state graph
├── [P2] تطبيق Reranker
├── [P2] تطبيق PII Redaction
└── [P2] إنشاء evals/datasets/

التسليم:
├── RAG يعمل مع HNSW
├── LangGraph state graph يعمل
├── Structured Outputs يعمل
└── Recall@10 ≥ 0.85
```

### الأسبوع 5-6: واجهة المستخدم

```
الهدف: إنشاء Frontend MVP

المهام:
├── [P1] إعداد shadcn/ui
├── [P1] صفحة تسجيل/دخول
├── [P1] لوحة تحكم الوكلاء
├── [P1] واجهة دردشة مع Streaming
├── [P2] صفحة الإعدادات
├── [P2] صفحة Billing
└── [P2] RTL support

التسليم:
├── المستخدم يمكنه تسجيل حساب
├── إنشاء وكيل
├── رفع مستندات
├── محادثة مع الوكيل
└── عرض المصادر
```

### الأسبوع 7-8: الجودة والأمان

```
الهدف: ضمان الجودة والأمان

المهام:
├── [P1] اختبارات unit (85% coverage)
├── [P1] اختبارات integration
├── [P1] Security audit (bandit, pip-audit)
├── [P1] OWASP ZAP scan
├── [P2] Load testing (200 RPS)
├── [P2] RAGAS evaluation
└── [P2] Red team testing

ال⛧ليم:
├── جميع الاختبارات تمر
├── لا ثغرات أمنية عالية
├── أداء مقبول (p95 < 2s)
└── Recall@10 ≥ 0.92
```

### الأسبوع 9-10: النشر والإطلاق

```
الهدف: إعداد الإنتاج والإطلاق التجريبي

المهام:
├── [P1] إعداد production docker-compose
├── [P1] إعداد AWS infrastructure
├── [P1] إعداد monitoring (Grafana)
├── [P1] إعداد CI/CD pipeline
├── [P2] إعداد backup strategy
├── [P2] إعداد alerting
└── [P2] Beta مع 50 مستخدم

التسليم:
├── الإنتاج يعمل
├── Monitoring يعمل
├── Backups تعمل
└── 50 مستخدم beta
```

### الأسبوع 11-12: التحسين والتوسع

```
الهدف: تحسين الأداء وإعداد للتوسع

المهام:
├── [P1] تحسين الأداء بناءً على feedback
├── [P1] إصلاح bugs
├── [P2] ميزات جديدة حسب الطلب
├── [P2] تحسين RAG
├── [P3] توثيق API
├── [P3] SDK للمطورين
└── [P3] تسويق

التسليم:
├── منصة مستقرة
├── 100+ مستخدم
├── تغطية اختبارات ≥ 85%
└── أداء مقبول
```

---

## 22. المخاطر والحلول

### 22.1 مخاطر تقنية

| المخاطرة | الاحتمال | التأثير | التخفيف |
|----------|----------|---------|---------|
| تغيير OpenAI API | متوسط | عالي | دعم نماذج متعددة |
| أداء pgvector على >10M vectors | منخفض | متوسط | خطة Citus |
| Prompt Injection ناجح | متوسط | عالي | classifier + red-team |
| تسريب بيانات Cross-tenant | منخفض | عالي جداً | اختبارات RLS |
| Down Time | منخفض | عالي | Multi-AZ + Circuit Breaker |

### 22.2 مخاطر سوقية

| المخاطرة | الاحتمال | التأثير | التخفيف |
|----------|----------|---------|---------|
| دخول لاعب كبير | عالي | متوسط | التخصص في المنطقة |
| تراجع الطلب على AI | منخفض | عالي | تنويع المنتجات |
| تشديد لائحات AI | متوسط | متوسط | GDPR + SOC 2 |
| عدم تقبل العملاء | متوسط | عالي | Freemium + دعم |

### 22.3 مخاطر مالية

| المخاطرة | الاحتمال | التأثير | التخفيف |
|----------|----------|---------|---------|
| تجاوز ميزانية OpenAI | متوسط | متوسط | cap شهري |
| بطء النمو | متوسط | عالي | تنويع الإيرادات |
| صعوبة التمويل | متوسط | متوسط | bootstrapping |
| ارتفاع تكاليف البنية التحتية | منخفض | متوسط | Reserved Instances |

---

## 23. المراجع الرسمية

### 23.1 مراجع تقنية

| التقنية | المرجع | الرابط |
|---------|--------|--------|
| **FastAPI** | Official Documentation | https://fastapi.tiangolo.com/ |
| **FastAPI** | Release Notes | https://fastapi.tiangolo.com/release-notes/ |
| **Pydantic** | v2 Documentation | https://docs.pydantic.dev/ |
| **SQLAlchemy** | 2.0 Documentation | https://docs.sqlalchemy.org/en/20/ |
| **pgvector** | GitHub README | https://github.com/pgvector/pgvector |
| **pgvector** | PostgreSQL Docs | https://www.postgresql.org/docs/current/pgvector.html |
| **LangGraph** | Official Documentation | https://langchain-ai.github.io/langgraph/ |
| **OpenAI** | Structured Outputs | https://platform.openai.com/docs/guides/structured-outputs |
| **OpenAI** | API Pricing | https://openai.com/api/pricing/ |
| **Next.js** | Official Documentation | https://nextjs.org/docs |
| **Next.js** | Blog (Releases) | https://nextjs.org/blog |
| **Redis** | Official Documentation | https://redis.io/docs/ |
| **Celery** | Official Documentation | https://docs.celeryq.dev/en/stable/ |
| **OpenTelemetry** | GenAI Conventions | https://opentelemetry.io/docs/specs/semconv/gen-ai/ |
| **Stripe** | API Documentation | https://docs.stripe.com/ |
| **Sentry** | Python SDK | https://docs.sentry.io/platforms/python/ |
| **Grafana** | Cloud Documentation | https://grafana.com/docs/grafana-cloud/ |

### 23.2 مراجع أمنية

| المرجع | الرابط |
|--------|--------|
| **OWASP LLM Top 10 v2025** | https://genai.owasp.org/llm-top-10/ |
| **OWASP Top 10 (2021)** | https://owasp.org/www-project-top-ten/ |
| **OWASP ASVS 4.0** | https://owasp.org/www-project-application-security-verification-standard/ |
| **NIST SP 800-53 Rev. 5** | https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final |

### 23.3 مراجع بنية تحتية

| المرجع | الرابط |
|--------|--------|
| **PostgreSQL 16** | https://www.postgresql.org/docs/16/ |
| **Docker** | https://docs.docker.com/ |
| **AWS Pricing** | https://aws.amazon.com/pricing/ |
| **AWS RDS** | https://aws.amazon.com/rds/ |
| **AWS ElastiCache** | https://aws.amazon.com/elasticache/ |
| **Cloudflare** | https://www.cloudflare.com/ |

### 23.4 مراجع التصميم

| المرجع | الرابط |
|--------|--------|
| **12-Factor App** | https://12factor.net/ |
| **Beyond the 12-Factor App** | https://www.oreilly.com/library/view/beyond-the-twelve-factor/9781492044024/ |
| **Clean Architecture** | Robert C. Martin |
| **Domain-Driven Design** | Eric Evans |

---

**تم إعداد هذه الدراسة بناءً على:**
1. تحليل الكود الفعلي في مستودع NOUFEX_AI
2. المراجع الرسمية المذكورة أعلاه
3. أفضل الممارسات من الصناعة

**النسخة:** 2.0.0
**تاريخ الإعداد:** 2026-07-09
**الحالة:** جاهزة للمراجعة والتنفيذ
