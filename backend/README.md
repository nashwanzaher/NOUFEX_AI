# NOUFEX AI Backend

Multi-tenant AI agent platform with RAG, structured outputs, computer control, browser automation, and UI/UX design generation.

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16 (via Docker)

### 1. Start Infrastructure

```bash
cd infrastructure
docker compose up -d db redis
```

### 2. Setup Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Run Migrations

```bash
alembic upgrade head
```

### 4. Seed Database (Optional)

```bash
python -m noufex_ai.scripts.seed
```

### 5. Start Development Server

```bash
uvicorn noufex_ai.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/users/signup` | Create new user + tenant |
| POST | `/v1/users/login` | Login and get tokens |
| POST | `/v1/users/refresh` | Refresh access token |
| POST | `/v1/users/logout` | Revoke refresh token |
| GET | `/v1/users/me` | Get current user |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/agents/` | List agents |
| POST | `/v1/agents/` | Create agent |
| GET | `/v1/agents/{id}` | Get agent |
| PATCH | `/v1/agents/{id}` | Update agent |
| DELETE | `/v1/agents/{id}` | Delete agent |

### RAG (Documents)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/rag/documents` | Upload document |
| GET | `/v1/rag/documents` | List documents |
| GET | `/v1/rag/documents/{id}` | Get document |
| DELETE | `/v1/rag/documents/{id}` | Delete document |
| POST | `/v1/rag/search` | Search knowledge base (pgvector cosine) |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/chat/` | Send message (non-streaming, tool-calling loop) |
| POST | `/v1/chat/stream` | Send message (SSE streaming) |
| GET | `/v1/chat/conversations` | List conversations |
| GET | `/v1/chat/conversations/{id}` | Get conversation with messages |
| DELETE | `/v1/chat/conversations/{id}` | Delete conversation |

### Computer Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/computer/windows` | List open windows |
| POST | `/v1/computer/windows/focus` | Focus a window |
| POST | `/v1/computer/windows/move` | Move/resize window |
| POST | `/v1/computer/windows/open` | Open window/app/URL |
| POST | `/v1/computer/windows/close` | Close window |
| GET | `/v1/computer/windows/active` | Get active window |
| GET | `/v1/computer/screen` | Get screen info |
| POST | `/v1/computer/screenshot` | Take screenshot |
| POST | `/v1/computer/mouse/move` | Move mouse |
| POST | `/v1/computer/mouse/click` | Click at position |
| POST | `/v1/computer/mouse/drag` | Drag from point A to B |
| POST | `/v1/computer/mouse/scroll` | Scroll mouse wheel |
| POST | `/v1/computer/keyboard/type` | Type text |
| POST | `/v1/computer/keyboard/hotkey` | Press hotkey combo |
| POST | `/v1/computer/keyboard/press` | Press single key |
| GET | `/v1/computer/processes` | List running processes |
| POST | `/v1/computer/processes/kill` | Kill process by PID/name |
| GET | `/v1/computer/system` | Get system info |
| POST | `/v1/computer/command` | Run shell command |
| POST | `/v1/computer/files/list` | List directory |
| POST | `/v1/computer/files/read` | Read file |
| POST | `/v1/computer/files/write` | Write file |

### Browser Automation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/browser/launch` | Launch browser |
| POST | `/v1/browser/attach` | Attach to existing browser via CDP |
| POST | `/v1/browser/close` | Close browser |
| POST | `/v1/browser/navigate` | Navigate to URL |
| GET | `/v1/browser/page` | Get page info |
| GET | `/v1/browser/content` | Get page text content |
| GET | `/v1/browser/html` | Get page HTML |
| POST | `/v1/browser/click` | Click element by selector |
| POST | `/v1/browser/click-text` | Click element by text |
| POST | `/v1/browser/type` | Type into input field |
| POST | `/v1/browser/select` | Select dropdown option |
| POST | `/v1/browser/screenshot` | Take browser screenshot |
| POST | `/v1/browser/evaluate` | Execute JavaScript |
| POST | `/v1/browser/wait` | Wait for selector |
| POST | `/v1/browser/scroll` | Scroll page |
| GET | `/v1/browser/links` | Get all page links |
| GET | `/v1/browser/forms` | Get all page forms |

### UI/UX Design
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/design/design-system` | Get current design system |
| POST | `/v1/design/design-system` | Create/update design system |
| GET | `/v1/design/design-system/css-variables` | Get CSS variables |
| GET | `/v1/design/design-system/tailwind-config` | Get Tailwind config |
| POST | `/v1/design/color-palette` | Generate color palette |
| POST | `/v1/design/components` | Generate UI component |
| POST | `/v1/design/pages/landing` | Generate landing page |
| POST | `/v1/design/pages/dashboard` | Generate dashboard |
| POST | `/v1/design/pages/from-description` | Generate page from NL description |
| POST | `/v1/design/review` | Review UI accessibility/design |
| POST | `/v1/design/review/score` | Score UI quality (0-100) |
| GET | `/v1/design/animations` | List CSS animations |
| GET | `/v1/design/animations/css` | Get animation CSS |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/billing/plans` | List available plans |
| GET | `/v1/billing/subscription` | Get current subscription |
| GET | `/v1/billing/invoices` | List invoices |
| POST | `/v1/billing/checkout` | Create Stripe checkout session |
| POST | `/v1/billing/portal` | Create Stripe customer portal |
| POST | `/v1/billing/webhook` | Stripe webhook |

## Agent Skills (50+)

The AI agent has autonomous access to 50+ skills via OpenAI function calling:

| Category | Skills |
|----------|--------|
| Computer | Window mgmt, mouse, keyboard, screenshots, processes, files, shell |
| Browser | Launch, navigate, click, type, screenshot, JS evaluate, scroll |
| Design | Components, pages, color palettes, animations, UI review |
| Web | Search (DuckDuckGo), fetch page content |

## Development

### Run Tests

```bash
# Unit tests
pytest tests/unit

# Integration tests (requires running DB)
pytest tests/integration

# All tests with coverage
pytest --cov=noufex_ai --cov-report=html
```

### Lint & Type Check

```bash
ruff check noufex_ai
ruff format noufex_ai
mypy noufex_ai
```

## Environment Variables

See `.env.example` for all available configuration options.

### Required
- `OPENAI_API_KEY` - OpenAI API key for LLM and embeddings

### Optional
- `SENTRY_DSN` - Sentry DSN for error tracking
- `STRIPE_SECRET_KEY` - Stripe secret key for billing
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OpenTelemetry collector endpoint
- `DESIGN_DEFAULT_PRIMARY_COLOR` - Default design system primary color
- `DESIGN_DEFAULT_FONT_FAMILY` - Default design system font

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      FastAPI App                          │
├──────────────────────────────────────────────────────────┤
│  Users  │  Tenants  │  Agents  │  RAG  │  Chat  │  Billing │
│  Computer Control  │  Browser Automation  │  UI/UX Design  │
├──────────────────────────────────────────────────────────┤
│                   Service Layer (50+ Skills)              │
├──────────────────────────────────────────────────────────┤
│          SQLAlchemy Async + pgvector + Redis              │
├──────────────────────────────────────────────────────────┤
│    PostgreSQL 16  │  Redis 7  │  OpenAI API  │  Playwright │
└──────────────────────────────────────────────────────────┘
```

## License

Proprietary - NOUFEX
