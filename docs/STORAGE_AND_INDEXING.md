# Storage and Indexing Documentation

Complete guide to how analysis responses are stored, indexed, and retrieved in the ml-tech-assessment application.

---

## Overview

The application uses an **in-memory storage** system with a simple **dictionary-based index** for storing and retrieving transcript analysis results.

**Storage Type**: In-Memory (non-persistent)
**Index Type**: Hash map (Python dict) keyed by UUID
**Thread Safety**: Yes (using threading.Lock)
**Persistence**: No - data lost on restart

---

## Storage Architecture

### 1. Repository Pattern

**File**: `app/repositories/in_memory.py`

```python
class InMemoryAnalysisRepository:
    def __init__(self):
        self._storage: Dict[str, AnalysisResponse] = {}
        self._lock = threading.Lock()
```

**Key Components**:
- `_storage`: Python dictionary mapping analysis IDs to AnalysisResponse objects
- `_lock`: Threading lock for thread-safe concurrent access
- Singleton pattern: One instance shared across entire application

---

## Data Model

### AnalysisResponse Structure

**File**: `app/models/responses.py`

```python
class AnalysisResponse(BaseModel):
    id: str                  # UUID v4 - Primary key
    summary: str             # LLM-generated summary
    next_actions: str        # Recommended next steps
    created_at: datetime     # Timestamp (UTC)
    transcript: str          # Original transcript text
```

**Example**:
```json
{
  "id": "f60501ad-84d7-4fee-b30f-15940551a4d1",
  "summary": "Patient experiencing persistent morning headaches",
  "next_actions": "1. Conduct medical history\n2. Order diagnostic tests",
  "created_at": "2026-01-19T10:37:05.671081Z",
  "transcript": "Patient reports persistent headaches for 3 days..."
}
```

---

## Indexing Strategy

### Primary Index: UUID-Based Hash Map

**Index Type**: Hash table (O(1) lookup)
**Key**: `analysis.id` (UUID v4 string)
**Value**: Complete `AnalysisResponse` object

**Benefits**:
- ✅ Fast retrieval: O(1) time complexity
- ✅ Guaranteed unique keys (UUID collision extremely unlikely)
- ✅ Simple implementation
- ✅ Thread-safe with lock

**Limitations**:
- ❌ No secondary indexes (e.g., by timestamp, summary text)
- ❌ No full-text search capability
- ❌ No sorting without loading all records
- ❌ No range queries

---

## ID Generation

**File**: `app/services/analysis_service.py:69`

```python
analysis_id = str(uuid.uuid4())
```

**Method**: UUID Version 4 (random)
**Format**: `"550e8400-e29b-41d4-a716-446655440000"`
**Collision Probability**: ~1 in 2^122 (negligible)
**Generated**: At the start of each analysis request

---

## Storage Operations

### 1. Save (Create)

**Location**: `app/repositories/in_memory.py:26`

```python
def save(self, analysis: AnalysisResponse) -> AnalysisResponse:
    with self._lock:
        self._storage[analysis.id] = analysis
    return analysis
```

**Flow**:
1. Service generates UUID
2. Calls LLM for analysis
3. Creates AnalysisResponse with UUID
4. Saves to repository
5. Returns response to client

**Thread Safety**: Lock acquired during write

---

### 2. Retrieve by ID (Read)

**Location**: `app/repositories/in_memory.py:40`

```python
def get_by_id(self, analysis_id: str) -> AnalysisResponse:
    with self._lock:
        analysis = self._storage.get(analysis_id)

    if not analysis:
        raise NotFoundException(...)

    return analysis
```

**Endpoint**: `GET /api/v1/analyses/{id}`
**Complexity**: O(1) - direct hash lookup
**Error**: HTTP 404 if ID not found

**Example**:
```bash
curl http://localhost:8000/api/v1/analyses/f60501ad-84d7-4fee-b30f-15940551a4d1
```

---

### 3. List All (Read)

**Location**: `app/repositories/in_memory.py:61`

```python
def list_all(self) -> list[AnalysisResponse]:
    with self._lock:
        return list(self._storage.values())
```

**Endpoint**: `GET /api/v1/analyses`
**Complexity**: O(n) - iterates all values
**Order**: Insertion order (Python 3.7+ dict guarantee)

**Example**:
```bash
curl http://localhost:8000/api/v1/analyses
```

**Response**:
```json
[
  {
    "id": "f60501ad-84d7-4fee-b30f-15940551a4d1",
    "summary": "...",
    "created_at": "2026-01-19T10:37:05.671081Z",
    "transcript": "..."
  },
  {
    "id": "e46611d3-7bf1-45c2-9a72-af18bf00fd4d",
    "summary": "...",
    "created_at": "2026-01-19T10:37:12.486472Z",
    "transcript": "..."
  }
]
```

---

### 4. Delete

**Location**: `app/repositories/in_memory.py:71`

```python
def delete(self, analysis_id: str) -> None:
    with self._lock:
        if analysis_id not in self._storage:
            raise NotFoundException(...)
        del self._storage[analysis_id]
```

**Note**: No DELETE endpoint currently exposed in API
**Available for**: Future implementation or testing

---

### 5. Count

**Location**: `app/repositories/in_memory.py:86`

```python
def count(self) -> int:
    with self._lock:
        return len(self._storage)
```

**Purpose**: Get total number of stored analyses
**Complexity**: O(1) - Python dict maintains length internally

---

### 6. Clear

**Location**: `app/repositories/in_memory.py:96`

```python
def clear(self) -> None:
    with self._lock:
        self._storage.clear()
```

**Purpose**: Testing only - clears all stored analyses
**Not exposed**: In production API

---

## Dependency Injection

**File**: `app/api/dependencies.py:17`

```python
@lru_cache
def get_repository() -> InMemoryAnalysisRepository:
    return InMemoryAnalysisRepository()
```

**Pattern**: Singleton via `@lru_cache`
**Lifecycle**: One instance per application lifetime
**Scope**: Shared across all requests

**Benefits**:
- Single source of truth for all analyses
- Memory efficient (one dictionary instance)
- Thread-safe with single lock

---

## Thread Safety

### Concurrency Model

```python
self._lock = threading.Lock()

# All operations wrapped in lock:
with self._lock:
    # Read or write to _storage
```

**Protection**: All CRUD operations acquire lock
**Type**: Reentrant lock (threading.Lock)
**Granularity**: Per-repository (all operations share one lock)

**Performance Consideration**:
- Lock contention can occur under high concurrent load
- Read operations block writes and vice versa
- No read-write lock optimization (all operations exclusive)

---

## Data Persistence

### Current State: Non-Persistent

**Storage Location**: Application memory (RAM)
**Lifetime**: Application process lifetime
**Data Loss Events**:
- ❌ Application restart
- ❌ Container restart
- ❌ Server crash
- ❌ Deployment/upgrade

### Container Impact

**Docker Behavior**:
```bash
docker-compose down   # All data LOST
docker-compose up     # Fresh empty storage
```

**No volumes mounted** for persistence in current setup.

---

## Query Capabilities

### Supported Queries

| Operation | Endpoint | Complexity | Indexed |
|-----------|----------|------------|---------|
| Get by ID | GET /api/v1/analyses/{id} | O(1) | ✅ Yes |
| List all | GET /api/v1/analyses | O(n) | ❌ No |

### Unsupported Queries

Currently **NOT supported** (would require additional indexes or full scan):
- ❌ Search by transcript content
- ❌ Filter by date range
- ❌ Sort by created_at
- ❌ Full-text search on summary
- ❌ Filter by keywords
- ❌ Pagination
- ❌ Aggregations (counts, averages)

To implement these, you would need:
1. Secondary indexes (by timestamp, etc.)
2. Search engine integration (Elasticsearch)
3. Database migration (PostgreSQL, MongoDB)

---

## Memory Usage

### Storage Calculation

**Per Analysis**:
- ID: ~36 bytes (UUID string)
- Summary: ~100-500 bytes (variable)
- Next Actions: ~100-300 bytes (variable)
- Created At: 28 bytes (datetime object)
- Transcript: Variable (100-10,000 bytes typical)
- Python overhead: ~200 bytes

**Estimate**: ~500-11,000 bytes per analysis (0.5-11 KB)

**Example Capacity** (512 MB container):
- Conservative: ~50,000 analyses (10 KB each)
- Optimistic: ~1,000,000 analyses (0.5 KB each)

**Real-world**: Memory limit of 512 MB allows tens of thousands of analyses.

---

## Storage Flow Diagram

```
┌─────────────────┐
│   API Request   │
│  POST /analyze  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AnalysisService │
│  - Generate ID  │ ← uuid.uuid4()
│  - Call LLM     │
│  - Create model │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Repository    │
│  .save(analysis)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  In-Memory Storage          │
│                             │
│  _storage = {               │
│    "uuid-1": AnalysisObj1,  │ ← Indexed by ID
│    "uuid-2": AnalysisObj2,  │
│    ...                      │
│  }                          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Return to API  │
│   with ID       │
└─────────────────┘
```

---

## Retrieval Flow Diagram

```
┌─────────────────────┐
│   API Request       │
│ GET /analyses/{id}  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Repository         │
│ .get_by_id(id)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│  Hash Lookup (O(1))         │
│                             │
│  _storage.get("uuid-123")   │ ← Direct dict access
│                             │
│  Returns: AnalysisResponse  │
└──────────┬──────────────────┘
           │
           ├─ Found ──────────► Return 200 + Analysis
           │
           └─ Not Found ─────► NotFoundException → 404
```

---

## Production Considerations

### Current Limitations for Production

1. **No Persistence**
   - Data lost on restart
   - Not suitable for production workloads
   - No disaster recovery

2. **No Scalability**
   - Single instance only
   - Cannot scale horizontally
   - Shared memory across all requests

3. **No Advanced Queries**
   - Only ID-based lookup
   - No search, filter, sort
   - No analytics capabilities

4. **Memory Limits**
   - Bounded by container memory (512 MB)
   - No automatic eviction/cleanup
   - Risk of OOM errors with high volume

### Recommended Upgrades for Production

**Short-term** (Quick wins):
- Add Redis for persistence + caching
- Implement TTL for automatic cleanup
- Add pagination to list endpoint

**Long-term** (Scalable):
- PostgreSQL for relational storage
- Elasticsearch for full-text search
- Separate read replicas for queries
- Object storage (S3) for large transcripts

---

## Implementation Example: PostgreSQL Migration

If migrating to PostgreSQL:

### Schema
```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY,
    summary TEXT NOT NULL,
    next_actions TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    transcript TEXT NOT NULL
);

-- Indexes
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX idx_analyses_transcript_search ON analyses
    USING gin(to_tsvector('english', transcript));
```

### Benefits
- ✅ Persistence across restarts
- ✅ ACID transactions
- ✅ Complex queries (filters, sorts, joins)
- ✅ Full-text search
- ✅ Horizontal scaling (read replicas)
- ✅ Backup and recovery

---

## Testing Storage

### Current Tests

**File**: `tests/unit/test_repository.py`

Tests cover:
- ✅ Save and retrieve by ID
- ✅ List all analyses
- ✅ Delete by ID
- ✅ Count stored analyses
- ✅ Clear all analyses
- ✅ Thread safety
- ✅ Not found exceptions

### Testing in Docker

```bash
# Start container
docker-compose up -d

# Create analysis
ANALYSIS_ID=$(curl -s -G "http://localhost:8000/api/v1/analyses/analyze" \
  --data-urlencode "transcript=Test transcript" | jq -r '.id')

# Retrieve by ID
curl http://localhost:8000/api/v1/analyses/$ANALYSIS_ID | jq .

# List all
curl http://localhost:8000/api/v1/analyses | jq .

# Restart container (data lost)
docker-compose restart

# Try to retrieve (404)
curl http://localhost:8000/api/v1/analyses/$ANALYSIS_ID
# Response: {"error": "NotFoundException", "message": "Analysis ... not found"}
```

---

## Summary

| Aspect | Current Implementation |
|--------|------------------------|
| **Storage Type** | In-memory dictionary |
| **Index** | UUID hash map (O(1)) |
| **Persistence** | None (data lost on restart) |
| **Thread Safety** | Yes (threading.Lock) |
| **Scalability** | Single instance only |
| **Query Capabilities** | ID lookup only |
| **Memory Limit** | 512 MB (container limit) |
| **Suitable For** | Development, testing, demos |
| **Production Ready** | No - requires persistence layer |

---

## Related Files

- `app/repositories/in_memory.py` - Repository implementation
- `app/models/responses.py` - Data models
- `app/services/analysis_service.py` - Business logic + ID generation
- `app/api/dependencies.py` - Dependency injection
- `tests/unit/test_repository.py` - Repository tests

---

**Last Updated**: 2026-01-19
