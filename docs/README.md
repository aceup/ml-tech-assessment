# Transcript Analysis API

Production-grade FastAPI service for analyzing transcripts using LLM providers (OpenAI, Groq, etc.)

## Features

- ✅ **Production-ready FastAPI** - App factory, middleware, error handling
- ✅ **Structured Logging** - JSON logs with request correlation
- ✅ **Health Checks** - Kubernetes-compatible liveness/readiness probes
- ✅ **Batch Processing** - Concurrent analysis with rate limiting
- ✅ **Docker Support** - Multi-stage build, non-root user
- ✅ **Type Safety** - Pydantic models everywhere
- ✅ **LLM Agnostic** - Easy to swap OpenAI for Groq or other providers

## Quick Start

### Local Development

```bash
# 1. Setup
cp .env.example .env
# Edit .env - add your API key

# 2. Run
uv run uvicorn app.main:app --reload --port 8000

# 3. Test
curl http://localhost:8000/api/v1/health/ready
open http://localhost:8000/docs
```

### Docker

```bash
# 1. Configure
cp .env.docker .env
# Edit .env - add your API key

# 2. Build and run
docker compose up -d

# 3. Verify
curl http://localhost:8000/api/v1/health/ready
```

## API Endpoints

- `POST /api/v1/analyses` - Analyze single transcript
- `POST /api/v1/analyses/batch` - Batch analyze (max 5 concurrent)
- `GET /api/v1/analyses/{id}` - Get analysis by ID
- `GET /api/v1/analyses` - List all analyses
- `GET /api/v1/health/live` - Liveness probe
- `GET /api/v1/health/ready` - Readiness probe

## LLM Provider Support

### OpenAI (Default)

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
```

### Groq

See `docs/GROQ_INTEGRATION.md` for complete setup instructions.

### Custom Provider

Implement the `LLM` port interface in `app/ports/llm.py` and create an adapter.

## Documentation

- **API Usage**: `docs/API_USAGE.md`
- **Docker Setup**: `docs/DOCKER_SETUP.md`
- **Groq Integration**: `docs/GROQ_INTEGRATION.md`
- **Interactive Docs**: http://localhost:8000/docs

## Architecture

Hexagonal Architecture (Ports & Adapters):
- **Ports** - `app/ports/llm.py` - LLM interface
- **Adapters** - `app/adapters/openai.py` - OpenAI implementation
- **Core** - Business logic independent of infrastructure
- **API** - FastAPI endpoints and routing
- **Infrastructure** - Logging, config, middleware

## Requirements

- Python 3.12+
- UV (recommended) or pip
- Docker (optional)

## License

MIT
