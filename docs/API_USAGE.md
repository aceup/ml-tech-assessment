# API Usage Guide

## Quick Start

### 1. Start the Server

**Local Development:**
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start with UV
uv run uvicorn app.main:app --reload --port 8000
```

**Docker:**
```bash
cp .env.docker .env
# Edit .env and add your OPENAI_API_KEY
docker-compose up -d
```

### 2. Verify Health

```bash
# Liveness probe
curl http://localhost:8000/api/v1/health/live

# Readiness probe (checks dependencies)
curl http://localhost:8000/api/v1/health/ready
```

## API Endpoints

### Base URL
- **Local:** `http://localhost:8000`
- **Docker:** `http://localhost:8000`

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 1. Analyze Single Transcript

**Endpoint:** `GET /api/v1/analyses/analyze`

**Request:**
```bash
curl "http://localhost:8000/api/v1/analyses/analyze?transcript=Patient%20reports%20persistent%20headaches%20for%203%20days%2C%20worse%20in%20the%20morning.%20No%20fever%20or%20visual%20disturbances.%20Taking%20ibuprofen%20with%20minimal%20relief." \
  -H "X-Request-ID: my-custom-id"
```

**Alternative (for readability in examples):**
```bash
TRANSCRIPT="Patient reports persistent headaches for 3 days, worse in the morning. No fever or visual disturbances. Taking ibuprofen with minimal relief."

curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=$TRANSCRIPT" \
  -H "X-Request-ID: my-custom-id"
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "Patient presents with persistent headaches for 3 days, worse in the morning. Currently managing with ibuprofen with minimal relief. No fever or visual disturbances reported.",
  "next_actions": "1. Perform neurological examination\n2. Review patient's medication history\n3. Consider imaging if symptoms persist\n4. Assess for potential migraine triggers",
  "created_at": "2024-01-15T10:30:00Z",
  "transcript": "Patient reports persistent headaches..."
}
```

**Response Headers:**
```
X-Request-ID: my-custom-id
Content-Type: application/json
```

**Validation Rules:**
- `transcript` must be 10-10,000 characters
- Cannot be empty or whitespace only

**Error Responses:**

`422 Unprocessable Entity` (Invalid Input):
```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "request_id": "my-custom-id",
  "details": {
    "errors": [
      {
        "loc": ["body", "transcript"],
        "msg": "String should have at least 10 characters",
        "type": "string_too_short"
      }
    ]
  }
}
```

`502 Bad Gateway` (OpenAI API Error):
```json
{
  "error": "ExternalServiceException",
  "message": "OpenAI error: Invalid API key",
  "request_id": "my-custom-id",
  "details": {
    "service": "OpenAI"
  }
}
```

---

## 2. Get Analysis by ID

**Endpoint:** `GET /api/v1/analyses/{analysis_id}`

**Request:**
```bash
curl "http://localhost:8000/api/v1/analyses/550e8400-e29b-41d4-a716-446655440000"
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "Patient presents with...",
  "next_actions": "1. Perform examination...",
  "created_at": "2024-01-15T10:30:00Z",
  "transcript": "Patient reports..."
}
```

**Error Responses:**

`404 Not Found`:
```json
{
  "error": "NotFoundException",
  "message": "Analysis with id '550e8400-...' not found",
  "request_id": "auto-generated-id",
  "details": {
    "resource": "Analysis",
    "identifier": "550e8400-..."
  }
}
```

---

## 3. List All Analyses

**Endpoint:** `GET /api/v1/analyses`

**Request:**
```bash
curl "http://localhost:8000/api/v1/analyses"
```

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-...",
    "summary": "...",
    "next_actions": "...",
    "created_at": "2024-01-15T10:30:00Z",
    "transcript": "..."
  },
  {
    "id": "660e9511-...",
    "summary": "...",
    "next_actions": "...",
    "created_at": "2024-01-15T10:31:00Z",
    "transcript": "..."
  }
]
```

---

## 4. Batch Analyze Transcripts

**Endpoint:** `POST /api/v1/analyses/batch`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "Patient A: headache for 2 days, no fever",
      "Patient B: chest pain, shortness of breath, radiating to left arm",
      "Patient C: fever and cough for 5 days, productive sputum"
    ]
  }'
```

**Response:** `201 Created`
```json
{
  "results": [
    {
      "id": "550e8400-...",
      "summary": "Patient A summary...",
      "next_actions": "1. Action A...",
      "created_at": "2024-01-15T10:30:00Z",
      "transcript": "Patient A: headache..."
    },
    {
      "id": "660e9511-...",
      "summary": "Patient B summary...",
      "next_actions": "1. Action B...",
      "created_at": "2024-01-15T10:30:01Z",
      "transcript": "Patient B: chest pain..."
    }
  ],
  "total": 3,
  "successful": 2,
  "failed": 1,
  "errors": [
    "Transcript 3: OpenAI API rate limit exceeded"
  ]
}
```

**Features:**
- **Concurrent Processing:** Max 5 parallel requests to OpenAI
- **Partial Success:** Returns successful results even if some fail
- **Error Details:** Lists specific errors for failed transcripts

**Validation Rules:**
- 1-100 transcripts per batch
- Each transcript: 10-10,000 characters

---

## 5. Health Checks

### Liveness Probe

**Endpoint:** `GET /api/v1/health/live`

**Request:**
```bash
curl "http://localhost:8000/api/v1/health/live"
```

**Response:** `200 OK`
```json
{
  "status": "alive",
  "checks": null
}
```

**Use Case:** Kubernetes liveness probe (is the service running?)

### Readiness Probe

**Endpoint:** `GET /api/v1/health/ready`

**Request:**
```bash
curl "http://localhost:8000/api/v1/health/ready"
```

**Response:** `200 OK` (Ready)
```json
{
  "status": "ready",
  "checks": {
    "openai_key_configured": true,
    "environment": "production"
  }
}
```

**Response:** `503 Service Unavailable` (Not Ready)
```json
{
  "status": "not_ready",
  "checks": {
    "openai_key_configured": false,
    "environment": "production"
  }
}
```

**Use Case:** Kubernetes readiness probe (can the service handle traffic?)

---

## Request Correlation

All requests automatically get a unique `X-Request-ID` header:

**Auto-Generated:**
```bash
curl http://localhost:8000/api/v1/health/live
# Response headers include: X-Request-ID: 6f84fed1-7dd8-4ef6-948d-5749c3eac747
```

**Custom ID:**
```bash
curl -H "X-Request-ID: my-custom-id" http://localhost:8000/api/v1/health/live
# Response headers include: X-Request-ID: my-custom-id
```

**Use Case:** Trace requests through logs for debugging

---

## Structured Logging

All requests are logged in JSON format (production) or colored console (development):

```json
{
  "request_id": "6f84fed1-7dd8-4ef6-948d-5749c3eac747",
  "method": "POST",
  "path": "/api/v1/analyses",
  "client_host": "127.0.0.1",
  "status_code": 201,
  "duration_ms": 1250.45,
  "event": "request_completed",
  "level": "info",
  "logger": "app.core.middleware",
  "timestamp": "2026-01-18T16:26:50.698342Z",
  "app": "transcript-analysis-api"
}
```

**Logged Information:**
- Request ID (correlation)
- Method, path, client IP
- Status code
- Duration in milliseconds
- Timestamp (ISO 8601 UTC)

---

## Python SDK Example

```python
import httpx

# Initialize client
client = httpx.Client(base_url="http://localhost:8000")

# Single analysis
transcript = "Patient reports headaches for 3 days"
response = client.get(
    "/api/v1/analyses/analyze",
    params={"transcript": transcript},
    headers={"X-Request-ID": "my-trace-id"}
)
analysis = response.json()
print(f"Analysis ID: {analysis['id']}")
print(f"Summary: {analysis['summary']}")

# Batch analysis
batch_response = client.post(
    "/api/v1/analyses/batch",
    json={
        "transcripts": [
            "Patient A: headache",
            "Patient B: chest pain",
            "Patient C: fever"
        ]
    }
)
batch_result = batch_response.json()
print(f"Successful: {batch_result['successful']}/{batch_result['total']}")
```

---

## Rate Limiting (OpenAI API)

The API respects OpenAI's rate limits:
- **Batch endpoint:** Max 5 concurrent requests (configurable via semaphore)
- **Single endpoint:** No artificial limit (relies on OpenAI tier limits)

**Recommendations:**
- Use batch endpoint for multiple transcripts
- Implement exponential backoff for 429 errors
- Monitor OpenAI usage dashboard

---

## CORS Configuration

Allowed origins configured via `CORS_ORIGINS` environment variable:

```bash
# Development
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Production
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

**Preflight Requests:**
```bash
curl -X OPTIONS "http://localhost:8000/api/v1/analyses" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
```

---

## Error Handling

All errors return consistent format:

```json
{
  "error": "ErrorClassName",
  "message": "Human-readable description",
  "request_id": "correlation-id",
  "details": {
    "additional": "context"
  }
}
```

**HTTP Status Codes:**
- `200` - Success (GET)
- `201` - Created (POST)
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `502` - External Service Error (OpenAI)
- `503` - Service Unavailable

---

## Performance Expectations

**Single Analysis:**
- Latency: 1-3 seconds (depends on OpenAI API)
- Timeout: 30 seconds (configurable)

**Batch Analysis:**
- Latency: ~2-4 seconds (5 concurrent requests)
- Timeout: 30 seconds per transcript

**Health Checks:**
- Latency: <10ms

---

## Security

1. **HTTPS:** Use reverse proxy (Nginx, Traefik) for TLS
2. **API Key:** Never expose OpenAI key in client code
3. **CORS:** Restrict origins to your domains
4. **Rate Limiting:** Implement application-level rate limits if needed
5. **Input Validation:** All inputs validated via Pydantic

---

## Monitoring

**Metrics to Track:**
- Request duration (p50, p95, p99)
- Error rate (4xx, 5xx)
- OpenAI API latency
- Concurrent requests
- Memory usage

**Log Aggregation:**
- Use ELK Stack, Datadog, or CloudWatch
- Query by `request_id` for tracing
- Alert on error rates

---

## Support

- **Documentation:** http://localhost:8000/docs
- **Logs:** Structured JSON with request correlation
- **Health:** http://localhost:8000/api/v1/health/ready
