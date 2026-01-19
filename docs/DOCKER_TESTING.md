# Docker Testing Guide for ml-tech-assessment

Complete guide for running and testing the FastAPI application in Docker containers.

## Table of Contents
- [Quick Start](#quick-start)
- [Build and Run](#build-and-run)
- [Health Check Tests](#health-check-tests)
- [API Endpoint Tests](#api-endpoint-tests)
- [Batch Processing Tests](#batch-processing-tests)
- [Error Handling Tests](#error-handling-tests)
- [Advanced Testing](#advanced-testing)
- [Mock Data Examples](#mock-data-examples)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Valid OpenAI API key

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env
# Replace: OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 2. Build and Run

```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# View logs
docker-compose logs -f app
```

### 3. Verify Health

```bash
# Check liveness
curl http://localhost:8000/api/v1/health/live

# Expected: {"status":"healthy"}
```

---

## Build and Run

### Option 1: Docker Compose (Recommended)

```bash
# Build image
docker-compose build

# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# View logs
docker-compose logs -f app

# Check status
docker-compose ps

# Stop and remove
docker-compose down
```

### Option 2: Docker CLI

```bash
# Build image
docker build -t ml-tech-assessment:latest .

# Run container
docker run -d \
  --name ml-tech-assessment \
  -p 8000:8000 \
  --env-file .env \
  ml-tech-assessment:latest

# View logs
docker logs -f ml-tech-assessment

# Stop container
docker stop ml-tech-assessment
docker rm ml-tech-assessment
```

### Verify Container Health

```bash
# Check container status
docker ps

# Inspect health
docker inspect ml-tech-assessment | jq '.[0].State.Health'

# Or with docker-compose
docker-compose ps
```

---

## Health Check Tests

### 1. Liveness Check

Tests if the application is running.

```bash
curl http://localhost:8000/api/v1/health/live
```

**Expected Response:**
```json
{"status":"healthy"}
```

### 2. Readiness Check

Tests if the application is ready to handle requests (requires valid OpenAI API key).

```bash
curl http://localhost:8000/api/v1/health/ready
```

**Expected Response:**
```json
{
  "status": "ready",
  "checks": {
    "llm_adapter": "healthy"
  },
  "timestamp": "2026-01-19T12:00:00.000000Z"
}
```

**Note:** Readiness check will fail if `OPENAI_API_KEY` is invalid or missing.

---

## API Endpoint Tests

### 1. Single Transcript Analysis (GET)

#### Medical Transcript Example

```bash
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Patient reports persistent headaches for 3 days, worse in the morning. No fever or visual disturbances. Taking ibuprofen with minimal relief. Past medical history includes hypertension controlled with medication."
```

#### Coaching Session Example

```bash
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Mark: Hey Liam, I've been reviewing our Python codebase, and I noticed we're not following PEP 8 consistently. What's your take on enforcing style guidelines? Liam: That's a great point, Mark. I think we should definitely adopt PEP 8. It makes the code more readable and maintainable, especially as our team grows. We could use tools like Black or autopep8 to automate the formatting."
```

#### Short Business Meeting Example

```bash
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Manager: We need to discuss the Q4 budget proposals. Sarah: I've prepared three scenarios - conservative, moderate, and aggressive. The moderate plan shows 15% growth potential. Manager: Let's review the moderate plan details and identify key risk factors."
```

**Expected Response Structure:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "Discussion about enforcing Python PEP 8 style guidelines...",
  "next_actions": "1. Implement Black or autopep8 for automated formatting\n2. Set up pre-commit hooks\n3. Document style guidelines in team wiki",
  "created_at": "2026-01-19T12:00:00.000000Z",
  "transcript": "Mark: Hey Liam..."
}
```

### 2. Retrieve Analysis by ID

```bash
# First, analyze a transcript and capture the response
RESPONSE=$(curl -s -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Patient reports fever and cough for 3 days")

# Extract ID using jq (requires jq installed)
ANALYSIS_ID=$(echo $RESPONSE | jq -r '.id')

# Retrieve the analysis
curl "http://localhost:8000/api/v1/analyses/${ANALYSIS_ID}"
```

**Alternative without jq:**
```bash
# Manually copy the ID from the response and use it
curl "http://localhost:8000/api/v1/analyses/550e8400-e29b-41d4-a716-446655440000"
```

### 3. List All Analyses

```bash
curl http://localhost:8000/api/v1/analyses
```

**Expected Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "summary": "...",
    "next_actions": "...",
    "created_at": "2026-01-19T12:00:00Z",
    "transcript": "..."
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "summary": "...",
    "next_actions": "...",
    "created_at": "2026-01-19T12:05:00Z",
    "transcript": "..."
  }
]
```

---

## Batch Processing Tests

### 1. Small Batch (3 Transcripts)

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "Patient A reports headache for 2 days, improving with rest and hydration.",
      "Patient B has chest pain and shortness of breath for 1 hour. Emergency evaluation needed.",
      "Patient C presents with fever of 101°F and dry cough for 3 days. No difficulty breathing."
    ]
  }'
```

### 2. Medium Batch (10 Transcripts)

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "Patient 1 reports symptoms for 1 day including mild headache.",
      "Patient 2 reports symptoms for 2 days with moderate severity.",
      "Patient 3 reports symptoms for 3 days showing improvement.",
      "Patient 4 reports symptoms for 4 days requiring follow-up.",
      "Patient 5 reports symptoms for 5 days with stable condition.",
      "Patient 6 reports symptoms for 6 days needing specialist referral.",
      "Patient 7 reports symptoms for 7 days with complications.",
      "Patient 8 reports symptoms for 8 days responding to treatment.",
      "Patient 9 reports symptoms for 9 days requiring reassessment.",
      "Patient 10 reports symptoms for 10 days with chronic presentation."
    ]
  }'
```

### 3. Large Batch (20 Transcripts)

Test the concurrent processing limit (default: 5 concurrent analyses).

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "Meeting 1: Q1 planning session - budget approved",
      "Meeting 2: Product roadmap review - priorities set",
      "Meeting 3: Engineering standup - blockers identified",
      "Meeting 4: Sales pipeline review - targets on track",
      "Meeting 5: Customer feedback session - action items assigned",
      "Meeting 6: Marketing campaign planning - launch date confirmed",
      "Meeting 7: HR policy update - employee handbook revised",
      "Meeting 8: Security audit review - vulnerabilities addressed",
      "Meeting 9: Performance review cycle - feedback collected",
      "Meeting 10: Budget variance analysis - adjustments needed",
      "Meeting 11: Vendor contract negotiation - terms agreed",
      "Meeting 12: Project retrospective - lessons learned",
      "Meeting 13: Team building planning - activities selected",
      "Meeting 14: Office space planning - layout finalized",
      "Meeting 15: Technology stack review - upgrades scheduled",
      "Meeting 16: Customer support metrics - SLAs reviewed",
      "Meeting 17: Compliance training - certification completed",
      "Meeting 18: Innovation brainstorm - prototypes proposed",
      "Meeting 19: Partnership discussion - MOU drafted",
      "Meeting 20: Board presentation prep - slides reviewed"
    ]
  }'
```

**Expected Response Structure:**
```json
{
  "results": [
    {
      "id": "...",
      "summary": "...",
      "next_actions": "...",
      "created_at": "...",
      "transcript": "..."
    }
  ],
  "total": 20,
  "successful": 20,
  "failed": 0,
  "errors": null
}
```

### 4. Batch with Realistic Medical Transcripts

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "45-year-old male with type 2 diabetes presents with increased thirst and urination for 2 weeks. Current HbA1c 9.2%. Patient non-compliant with metformin.",
      "28-year-old female, 32 weeks pregnant, reports decreased fetal movement since yesterday evening. Fetal heart rate monitoring shows non-reassuring pattern.",
      "67-year-old with COPD experiencing increased dyspnea and productive cough with yellow-green sputum for 5 days. Current O2 saturation 88% on room air.",
      "15-year-old athlete with acute knee pain after soccer practice. Swelling and inability to bear weight. History of previous ACL injury 2 years ago.",
      "52-year-old presenting with crushing substernal chest pain radiating to left arm for 30 minutes. Diaphoretic, BP 160/95, history of hypertension and smoking."
    ]
  }'
```

---

## Error Handling Tests

### 1. Empty Transcript (422 Validation Error)

```bash
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=   "
```

**Expected Response:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["query", "transcript"],
      "msg": "Transcript cannot be empty or whitespace",
      "input": "   "
    }
  ]
}
```

### 2. Too Short Transcript (422 Validation Error)

```bash
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Too short"
```

**Expected Response:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["query", "transcript"],
      "msg": "Transcript must be at least 20 characters",
      "input": "Too short"
    }
  ]
}
```

### 3. Nonexistent Analysis ID (404 Not Found)

```bash
curl http://localhost:8000/api/v1/analyses/nonexistent-id-12345
```

**Expected Response:**
```json
{
  "detail": "Analysis not found"
}
```

### 4. Invalid JSON in Batch Request (422)

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": "not-an-array"
  }'
```

### 5. Empty Array in Batch Request (422)

```bash
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": []
  }'
```

---

## Advanced Testing

### 1. Test with Request ID Tracking

```bash
# Send request with custom request ID
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  -H "X-Request-ID: test-request-123" \
  --data-urlencode "transcript=Patient reports fever and cough for 3 days"

# Check logs for request ID
docker-compose logs app | grep "test-request-123"
```

### 2. Test Response Times

```bash
# Time a single analysis
time curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Patient reports symptoms for assessment"

# Time a batch analysis
time curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "Transcript 1 for performance testing",
      "Transcript 2 for performance testing",
      "Transcript 3 for performance testing",
      "Transcript 4 for performance testing",
      "Transcript 5 for performance testing"
    ]
  }'
```

### 3. Test CORS Headers

```bash
# Preflight OPTIONS request
curl -X OPTIONS "http://localhost:8000/api/v1/analyses/analyze" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -i

# Check response headers for CORS configuration
```

### 4. Load Testing with Parallel Requests

```bash
# Install GNU parallel if not available
# sudo apt-get install parallel

# Run 20 requests with 5 concurrent workers
seq 1 20 | parallel -j 5 'curl -s -G "http://localhost:8000/api/v1/analyses/analyze" --data-urlencode "transcript=Patient {} reports symptoms for {} days" > /dev/null'

# With timing
seq 1 20 | parallel -j 5 'time curl -s -G "http://localhost:8000/api/v1/analyses/analyze" --data-urlencode "transcript=Patient {} reports symptoms for {} days" > /dev/null'
```

### 5. Test Concurrent Batch Processing

The API uses asyncio.Semaphore to limit concurrent analyses (default: 5).

```bash
# Send a batch larger than the semaphore limit
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10",
      "T11", "T12", "T13", "T14", "T15"
    ]
  }'

# Watch logs to see semaphore limiting (processes 5 at a time)
docker-compose logs -f app
```

### 6. Test GZip Compression

```bash
# Request with gzip encoding
curl -H "Accept-Encoding: gzip" "http://localhost:8000/api/v1/analyses" -i

# Check for Content-Encoding: gzip header in response
```

---

## Mock Data Examples

### Using Test Data Files

The project includes realistic mock data in `tests/adapters/mock_data.py` and test factories.

#### Extract Full Coaching Transcript

```bash
# Python script to extract mock transcript
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/martineserios/ml-tech-assessment')
from tests.adapters.mock_data import TRANSCRIPT

# Use in curl (save to file first)
with open('/tmp/test_transcript.txt', 'w') as f:
    f.write(TRANSCRIPT)

print(TRANSCRIPT)
EOF

# Use the extracted transcript
TRANSCRIPT=$(cat /tmp/test_transcript.txt)
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=$TRANSCRIPT"
```

#### Use Medical Transcript from Tests

```bash
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Patient with persistent headaches for 3 days. Describes throbbing pain in temporal region, worse in morning. No associated nausea, vomiting, or photophobia. Taking over-the-counter ibuprofen with minimal relief. No recent head trauma. Blood pressure today 145/92."
```

---

## Interactive Testing with Swagger UI

### Access Documentation

```bash
# Open Swagger UI in browser
# Linux
xdg-open http://localhost:8000/docs

# macOS
open http://localhost:8000/docs

# Or manually navigate to: http://localhost:8000/docs
```

### Access ReDoc

```bash
# Open ReDoc in browser
# Linux
xdg-open http://localhost:8000/redoc

# macOS
open http://localhost:8000/redoc

# Or manually navigate to: http://localhost:8000/redoc
```

### Features Available in Swagger UI

- Interactive API testing
- Request/response examples
- Schema validation
- Try out all endpoints
- View authentication requirements
- Download OpenAPI specification

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Port 8000 already in use
sudo lsof -i :8000
# Kill process or use different port in docker-compose.yml

# 2. .env file missing
cp .env.example .env
```

### Readiness Check Fails

```bash
# Check if OpenAI API key is configured
docker-compose exec app printenv | grep OPENAI_API_KEY

# If missing, add to .env file
echo "OPENAI_API_KEY=sk-your-actual-key" >> .env
docker-compose restart
```

### 500 Internal Server Error

```bash
# Check application logs
docker-compose logs -f app

# Common causes:
# 1. Invalid OpenAI API key
# 2. Network issues reaching OpenAI API
# 3. Rate limiting from OpenAI

# Test OpenAI connectivity from container
docker-compose exec app curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### Container Exits Immediately

```bash
# Check exit code
docker ps -a

# View full logs
docker logs ml-tech-assessment

# Common causes:
# 1. Syntax error in application code
# 2. Missing dependencies
# 3. Port binding failure

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### High Memory Usage

```bash
# Check resource usage
docker stats ml-tech-assessment

# Set memory limits in docker-compose.yml
# Uncomment the deploy.resources section
docker-compose up -d
```

### Slow Response Times

```bash
# Check if it's an OpenAI API delay
time curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Test" -v

# Monitor container resources
docker stats ml-tech-assessment

# Check concurrent request limit
# Default is MAX_CONCURRENT_ANALYSES=10
# Adjust in .env if needed
```

---

## Complete Testing Checklist

### Build and Run
- [ ] Docker image builds successfully
- [ ] Container starts without errors
- [ ] Container health check passes
- [ ] Application logs show successful startup

### Health Endpoints
- [ ] GET /api/v1/health/live returns 200
- [ ] GET /api/v1/health/ready returns 200 (with valid API key)

### Single Analysis
- [ ] GET /api/v1/analyses/analyze with medical transcript works
- [ ] GET /api/v1/analyses/analyze with coaching transcript works
- [ ] GET /api/v1/analyses/analyze with business transcript works
- [ ] Response includes id, summary, next_actions, created_at, transcript

### Batch Analysis
- [ ] POST /api/v1/analyses/batch with 3 transcripts works
- [ ] POST /api/v1/analyses/batch with 10 transcripts works
- [ ] POST /api/v1/analyses/batch with 20 transcripts works
- [ ] Response includes results array with total, successful, failed counts

### CRUD Operations
- [ ] GET /api/v1/analyses/{id} retrieves analysis by ID
- [ ] GET /api/v1/analyses lists all analyses

### Error Handling
- [ ] Empty transcript returns 422
- [ ] Too short transcript returns 422
- [ ] Nonexistent ID returns 404
- [ ] Invalid JSON returns 422
- [ ] Empty batch array returns 422

### Documentation
- [ ] Swagger UI accessible at /docs
- [ ] ReDoc accessible at /redoc
- [ ] All endpoints documented
- [ ] Interactive testing works

### Performance
- [ ] Concurrent batch processing respects semaphore limit
- [ ] Request ID tracking works in logs
- [ ] CORS headers present in responses
- [ ] GZip compression enabled for large responses

---

## Quick Reference Commands

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f app

# Health check
curl http://localhost:8000/api/v1/health/live

# Simple test
curl -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Patient reports fever for 3 days"

# Batch test
curl -X POST "http://localhost:8000/api/v1/analyses/batch" \
  -H "Content-Type: application/json" \
  -d '{"transcripts":["Test 1","Test 2","Test 3"]}'

# List all
curl http://localhost:8000/api/v1/analyses

# Stop
docker-compose down
```

---

## Additional Resources

- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Spec: http://localhost:8000/openapi.json
- Project README: [README.md](README.md)
- Environment Config: [.env.example](.env.example)

---

**Last Updated:** 2026-01-19
