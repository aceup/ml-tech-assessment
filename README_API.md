# ML Tech Assessment - API Documentation

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Error Handling](#error-handling)
- [Testing](#testing)

## Overview

This API provides LLM-powered text summarization and call-to-action (CTA) generation services. Built with FastAPI, it offers both synchronous and asynchronous endpoints for processing single and batch text summarization requests.

**Key Features:**
- Generate summaries and actionable CTAs from text
- Retrieve previously generated summaries by ID
- Batch processing with async support
- In-memory storage for generated summaries
- Built-in error handling for LLM service failures

**Technology Stack:**
- Python 3.12
- FastAPI
- OpenAI API
- Poetry (dependency management)
- Pydantic (data validation)

## Prerequisites

### Install Conda

Conda is recommended for managing the Python environment. Choose one of the following:

#### Option 1: Miniconda (Minimal installation)
```bash
# Linux/Mac
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Follow the installation prompts
# Restart your terminal after installation
```

#### Option 2: Anaconda (Full distribution)
Download and install from [Anaconda's website](https://www.anaconda.com/products/distribution)

Verify installation:
```bash
conda --version
```

## Environment Setup

### 1. Create Conda Environment

Create a new conda environment with Python 3.12 (matching the project requirement):

```bash
conda create -n ml-assessment python=3.12
```

**Note:** This creates an isolated Python environment. The actual project dependencies will be synced from `pyproject.toml` in the next steps.

### 2. Activate Environment

```bash
conda activate ml-assessment
```

**Note:** You'll need to activate this environment every time you work on the project.

### 3. Install Poetry

Poetry is used for dependency management:

```bash
pip install poetry
```

### 4. Sync Project Dependencies from Configuration

Poetry will read the `pyproject.toml` and `poetry.lock` files to replicate the exact environment configuration:

```bash
poetry install
```

This command **syncs your environment** with the project's dependency specifications, installing:
- `fastapi[standard]` - Web framework with standard dependencies
- `openai` - OpenAI API client
- `pydantic-settings` - Settings management
- `redis[hiredis]` - Redis client with C parser
- `pytest` - Testing framework
- Development dependencies (ruff, pytest-cov, pre-commit)

**Important:**
- The `poetry.lock` file ensures you get the **exact same versions** used in development
- This replicates the working environment, not creating a new configuration from scratch
- Poetry reads from the existing `pyproject.toml` to sync all dependencies

**Verify Installation:**
```bash
# Check installed packages
poetry show

# Verify key packages
poetry show fastapi openai pydantic-settings
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

```bash
# Required: OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo, gpt-4-turbo, etc.

# Optional: API Configuration
HOST=0.0.0.0
PORT=8000
```

**Important:** Never commit the `.env` file to version control. It's already included in `.gitignore`.

## Running the Application

### Development Mode

Start the FastAPI development server:

```bash
# Make sure your conda environment is activated
conda activate ml-assessment

# Run with uvicorn (included in fastapi[standard])
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base URL:** `http://localhost:8000`
- **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
- **Alternative API Docs (ReDoc):** `http://localhost:8000/redoc`

### Production Mode

For production deployment:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Base URL
```
http://localhost:8000
```

---

### 1. Root Endpoint

**GET** `/`

Simple health check endpoint.

**Response:**
```json
{
  "Hello": "World"
}
```

---

### 2. Generate Summary and CTAs

**GET** `/summary_maker/get_summary_and_ctas`

Generates a summary and calls to action (CTAs) for a given text using the LLM service.

**Parameters:**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `text_to_summary` | string | Query | Yes | The transcript text to analyze (min 10 characters, whitespace trimmed) |

**Request Example:**
```bash
curl -X GET "http://localhost:8000/summary_maker/get_summary_and_ctas?text_to_summary=This%20is%20a%20sample%20transcript%20discussing%20project%20goals%20and%20next%20steps"
```

**Response Example:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "summary": "A comprehensive summary of the provided text content",
  "ctas": [
    "Review and approve the project timeline",
    "Schedule follow-up meeting with stakeholders",
    "Document technical requirements"
  ]
}
```

**Response Schema:**
- `id` (string): Unique identifier for the generated summary
- `summary` (string): Generated summary of the input text
- `ctas` (array of strings): List of actionable calls to action

**Status Codes:**
- `200 OK` - Successfully generated summary
- `400 Bad Request` - Invalid input (text too short or invalid format)
- `401 Unauthorized` - Invalid OpenAI API credentials
- `503 Service Unavailable` - LLM service error

---

### 3. Retrieve Summary by ID

**GET** `/summary_maker/get_summary_and_ctas_by_id`

Retrieves a previously generated summary and its associated CTAs using the summary ID.

**Parameters:**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | string | Query | Yes | The unique ID of the summary to retrieve |

**Request Example:**
```bash
curl -X GET "http://localhost:8000/summary_maker/get_summary_and_ctas_by_id?id=123e4567-e89b-12d3-a456-426614174000"
```

**Response Example:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "A comprehensive summary of the provided text content",
  "ctas": [
    "Review and approve the project timeline",
    "Schedule follow-up meeting with stakeholders"
  ]
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved summary
- `404 Not Found` - Summary with given ID does not exist

---

### 4. Batch Async Summary Generation

**POST** `/summary_maker/async_get_summary_and_ctas`

Asynchronously generates summaries and CTAs for a batch of texts. Processes multiple texts in parallel and returns results in the same order as the input.

**Request Body:**

Array of text strings (each min 10 characters):

```json
[
  "First transcript text to summarize with at least 10 characters",
  "Second transcript text to summarize with sufficient length",
  "Third transcript text for batch processing"
]
```

**Request Example:**
```bash
curl -X POST "http://localhost:8000/summary_maker/async_get_summary_and_ctas" \
  -H "Content-Type: application/json" \
  -d '[
    "This is the first meeting transcript discussing quarterly goals",
    "Second transcript about technical architecture decisions",
    "Third transcript covering team collaboration improvements"
  ]'
```

**Response Example:**
```json
{
  "items": [
    {
      "summary": {
        "id": "uuid-1",
        "summary": "Summary of first text",
        "ctas": ["Action 1", "Action 2"]
      },
      "error": null
    },
    {
      "summary": {
        "id": "uuid-2",
        "summary": "Summary of second text",
        "ctas": ["Action 1"]
      },
      "error": null
    },
    {
      "summary": null,
      "error": "Error processing this item: rate limit exceeded"
    }
  ]
}
```

**Response Schema:**
- `items` (array): Array of results, one per input text (maintains order)
  - `summary` (object or null): Summary response object if successful
    - `id` (string): Unique identifier
    - `summary` (string): Generated summary
    - `ctas` (array): List of CTAs
  - `error` (string or null): Error message if processing failed

**Status Codes:**
- `200 OK` - Batch processing completed (check individual items for errors)
- `400 Bad Request` - Invalid request body format
- `401 Unauthorized` - Invalid OpenAI API credentials

**Notes:**
- Individual items can fail while others succeed
- Results maintain the same order as input
- All items are processed concurrently for optimal performance

---

### 5. List All Summary IDs

**GET** `/extras/get_summaries_ids`

Retrieves a list of all summary IDs that have been generated and stored in the repository.

**Request Example:**
```bash
curl -X GET "http://localhost:8000/extras/get_summaries_ids"
```

**Response Example:**
```json
[
  "123e4567-e89b-12d3-a456-426614174000",
  "987fcdeb-51a2-43f7-b890-123456789abc",
  "456789ab-cdef-0123-4567-89abcdef0123"
]
```

**Response Schema:**
- Array of strings containing all summary IDs

**Status Codes:**
- `200 OK` - Successfully retrieved list (may be empty array if no summaries exist)

---

## Error Handling

The API includes comprehensive error handling for OpenAI service errors:

### Error Response Format

```json
{
  "detail": "Error description message"
}
```

### Common Error Codes

| Status Code | Error Type | Description | Resolution |
|-------------|------------|-------------|------------|
| `400` | Bad Request | Invalid request format or parameters | Check request body/query parameters |
| `401` | Authentication Error | Invalid OpenAI API credentials | Verify `OPENAI_API_KEY` in `.env` file |
| `404` | Not Found | Summary ID does not exist | Check the ID or use `/extras/get_summaries_ids` |
| `503` | Service Unavailable | LLM service error (rate limits, timeouts) | Retry the request after a delay |

### OpenAI-Specific Errors

The API automatically catches and handles:
- **AuthenticationError**: Invalid API key → 401 response
- **BadRequestError**: Invalid LLM request → 400 response
- **OpenAIError**: General service errors → 503 response

## Testing

### Run All Tests

```bash
# Activate environment
conda activate ml-assessment

# Run tests
pytest
```

### Verbose Test Output

```bash
pytest -v
```

### Coverage Report

```bash
pytest --cov
```

### Test Structure

Tests are located in the `tests/` directory:
- `tests/adapters/` - Tests for OpenAI adapter
- `tests/adapters/mock_data.py` - Mock data for testing

## API Usage Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Generate a summary
response = requests.get(
    f"{BASE_URL}/summary_maker/get_summary_and_ctas",
    params={"text_to_summary": "Your long text content here..."}
)
summary_data = response.json()
print(f"Summary ID: {summary_data['id']}")
print(f"Summary: {summary_data['summary']}")
print(f"CTAs: {summary_data['ctas']}")

# Retrieve by ID
response = requests.get(
    f"{BASE_URL}/summary_maker/get_summary_and_ctas_by_id",
    params={"id": summary_data['id']}
)
retrieved = response.json()
```

### JavaScript/Node.js Example

```javascript
const BASE_URL = "http://localhost:8000";

// Generate a summary
async function generateSummary(text) {
  const response = await fetch(
    `${BASE_URL}/summary_maker/get_summary_and_ctas?text_to_summary=${encodeURIComponent(text)}`
  );
  const data = await response.json();
  return data;
}

// Batch processing
async function batchProcess(texts) {
  const response = await fetch(
    `${BASE_URL}/summary_maker/async_get_summary_and_ctas`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(texts)
    }
  );
  const data = await response.json();
  return data;
}
```

### cURL Examples

```bash
# Generate summary
curl -X GET "http://localhost:8000/summary_maker/get_summary_and_ctas?text_to_summary=Your%20text%20here"

# Retrieve by ID
curl -X GET "http://localhost:8000/summary_maker/get_summary_and_ctas_by_id?id=YOUR_ID_HERE"

# Batch processing
curl -X POST "http://localhost:8000/summary_maker/async_get_summary_and_ctas" \
  -H "Content-Type: application/json" \
  -d '["Text one", "Text two", "Text three"]'

# List all IDs
curl -X GET "http://localhost:8000/extras/get_summaries_ids"
```

## Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **OpenAI API Documentation:** https://platform.openai.com/docs/
- **Poetry Documentation:** https://python-poetry.org/docs/
- **Interactive API Documentation:** http://localhost:8000/docs (when server is running)

## Notes

- The application uses **in-memory storage** by default. All summaries are lost when the server restarts.
- For production use, consider implementing persistent storage (database, Redis, etc.).
- The API uses OpenAI's LLM models. Ensure you have sufficient API credits and respect rate limits.
- All text inputs are validated (minimum 10 characters, whitespace trimmed).
- The batch endpoint processes requests concurrently for optimal performance.

## Support

For issues or questions, refer to the main [README.md](./README.md) or check the interactive API documentation at http://localhost:8000/docs when the server is running.
