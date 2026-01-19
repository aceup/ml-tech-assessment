# Redis Persistence

## Overview

The Transcript Analysis API supports two storage backends:
- **In-Memory** (default): Fast, but data lost on restart
- **Redis**: Persistent, production-ready, distributed-friendly

This document covers Redis setup, configuration, and operations.

---

## Quick Start

### 1. Enable Redis

Update `.env`:
```bash
REPOSITORY_BACKEND=redis
REDIS_HOST=localhost  # or 'redis' in docker-compose
REDIS_PORT=6379
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts both Redis and the application with proper health checks and dependencies.

---

## Architecture

### Repository Pattern

The application uses the **Repository Pattern** with an abstract interface:

```
AnalysisService
    ↓
AnalysisRepository (abstract interface)
    ↓
    ├── InMemoryAnalysisRepository
    └── RedisAnalysisRepository → RedisAnalysisRepositorySync
```

### Key Components

1. **Abstract Interface** (`app/ports/repository.py`)
   - Defines CRUD operations
   - Allows swapping implementations

2. **Redis Client** (`app/infrastructure/redis_client.py`)
   - Connection pooling
   - Lifecycle management
   - Health checks

3. **Redis Repository** (`app/repositories/redis.py`)
   - Async implementation with JSON serialization
   - Sync wrapper for compatibility
   - Index-based listing

---

## Redis Key Structure

### Analysis Keys

```
transcript-analysis:{environment}:analysis:{uuid}
```

**Example**:
```
transcript-analysis:production:analysis:a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Index Key

```
transcript-analysis:{environment}:index
```

**Type**: Set (SADD/SMEMBERS)
**Purpose**: Track all analysis IDs for listing operations

---

## Configuration

### Environment Variables

```bash
# Backend Selection
REPOSITORY_BACKEND=redis  # or "memory"

# Redis Connection
REDIS_HOST=localhost      # Redis server hostname
REDIS_PORT=6379          # Redis server port
REDIS_DB=0               # Redis database number (0-15)
REDIS_PASSWORD=          # Optional password

# Connection Pool
REDIS_MAX_CONNECTIONS=10 # Max connections in pool

# TTL (Time To Live)
REDIS_TTL_SECONDS=       # Optional, omit for no expiration
```

### Example Configurations

**Development (local Redis)**:
```bash
REPOSITORY_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Docker Compose**:
```bash
REPOSITORY_BACKEND=redis
REDIS_HOST=redis  # Service name in docker-compose
REDIS_PORT=6379
```

**Production with Auth**:
```bash
REPOSITORY_BACKEND=redis
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=supersecret
REDIS_TTL_SECONDS=2592000  # 30 days
```

---

## Docker Compose Setup

The `docker-compose.yml` includes:

### Redis Service

```yaml
redis:
  image: redis:7.4-alpine
  command: >
    redis-server
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
    --appendonly yes
    --appendfsync everysec
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

**Features**:
- **Persistence**: AOF (Append-Only File) with `everysec` fsync
- **Memory limit**: 256MB with LRU eviction
- **Health check**: Ensures Redis is ready before app starts
- **Volume**: Data persists across container restarts

### App Dependencies

```yaml
app:
  depends_on:
    redis:
      condition: service_healthy
  environment:
    - REDIS_HOST=redis
    - REDIS_PORT=6379
```

The app waits for Redis to be healthy before starting.

---

## Operations

### Verify Connection

Check logs for successful Redis initialization:

```bash
docker-compose logs app | grep redis_connected
```

Expected output:
```json
{
  "event": "redis_connected",
  "message": "Redis connection established",
  "host": "redis"
}
```

### Inspect Data

Connect to Redis CLI:

```bash
docker-compose exec redis redis-cli
```

Commands:
```redis
# List all analysis keys
KEYS transcript-analysis:*

# Get analysis count
SCARD transcript-analysis:production:index

# Get specific analysis
GET transcript-analysis:production:analysis:<uuid>

# Check memory usage
INFO memory

# Check persistence status
INFO persistence
```

### Backup & Restore

#### Backup

```bash
# Stop writes (optional, for consistency)
docker-compose exec redis redis-cli BGSAVE

# Copy AOF file
docker-compose exec redis cat /data/appendonly.aof > backup.aof
```

#### Restore

```bash
# Stop services
docker-compose down

# Restore AOF file
docker run --rm -v redis-data:/data -v $(pwd):/backup \
  alpine cp /backup/backup.aof /data/appendonly.aof

# Start services
docker-compose up -d
```

### Clear All Data

**WARNING**: Destructive operation!

```bash
# Via API (if implemented)
curl -X DELETE http://localhost:8000/api/v1/analyses

# Via Redis CLI
docker-compose exec redis redis-cli FLUSHDB
```

---

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/api/v1/health/ready
```

Response includes Redis status:
```json
{
  "status": "healthy",
  "checks": {
    "redis": {
      "status": "healthy",
      "redis_version": "7.4.0"
    }
  }
}
```

### Metrics

Key metrics to monitor:

1. **Connection pool utilization**
   ```redis
   INFO clients
   # Look for: connected_clients
   ```

2. **Memory usage**
   ```redis
   INFO memory
   # Look for: used_memory_human
   ```

3. **Persistence status**
   ```redis
   INFO persistence
   # Look for: aof_last_write_status
   ```

4. **Evictions** (if maxmemory reached)
   ```redis
   INFO stats
   # Look for: evicted_keys
   ```

---

## Persistence Strategy

### AOF (Append-Only File)

**Configuration**:
```bash
--appendonly yes
--appendfsync everysec
```

**Behavior**:
- Every write operation appended to log
- Fsync to disk every second
- Trade-off: 1 second of data loss max vs. performance

**Alternatives**:
- `--appendfsync always`: Every write (slower, safest)
- `--appendfsync no`: OS-managed (faster, less safe)

### Memory Management

**Configuration**:
```bash
--maxmemory 256mb
--maxmemory-policy allkeys-lru
```

**Behavior**:
- When memory limit reached, evict least recently used keys
- Prevents out-of-memory crashes

**Alternatives**:
- `allkeys-lfu`: Least frequently used
- `volatile-lru`: Only evict keys with TTL

---

## Testing

### Verify Persistence

```bash
# Create analysis
ANALYSIS_ID=$(curl -s -X POST http://localhost:8000/api/v1/analyses/analyze \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Test persistence"}' | jq -r '.id')

# Restart app (Redis keeps running)
docker-compose restart app

# Retrieve analysis (should still exist)
curl http://localhost:8000/api/v1/analyses/$ANALYSIS_ID
```

**Expected**: Analysis retrieved successfully after restart.

### Load Test

```bash
# Create 100 analyses
for i in {1..100}; do
  curl -s -X POST http://localhost:8000/api/v1/analyses/analyze \
    -H "Content-Type: application/json" \
    -d "{\"transcript\": \"Load test $i\"}" &
done
wait

# Verify count
curl http://localhost:8000/api/v1/analyses | jq 'length'
```

**Expected**: 100 analyses stored in Redis.

### Failover Test

```bash
# Stop Redis
docker-compose stop redis

# Try to create analysis (should fallback to in-memory with warning)
curl -X POST http://localhost:8000/api/v1/analyses/analyze \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Failover test"}'

# Check logs
docker-compose logs app | grep redis_initialization_failed
```

---

## Performance

### Benchmarks

Typical performance (local Docker):

| Operation | In-Memory | Redis |
|-----------|-----------|-------|
| Save | ~0.1ms | ~1-2ms |
| Get | ~0.1ms | ~1-2ms |
| List 100 | ~0.5ms | ~10-15ms |

**Note**: Network latency adds overhead for Redis.

### Optimization

1. **Connection pooling**: Already configured (10 connections)
2. **Pipeline operations**: Used for atomic save/delete
3. **Indexing**: Set-based index for fast listing
4. **Serialization**: Efficient Pydantic JSON encoding

---

## Troubleshooting

### Connection Failed

**Symptoms**:
```
redis_initialization_failed: Failed to connect to Redis
```

**Solutions**:
1. Check Redis is running: `docker-compose ps redis`
2. Check network: `docker-compose exec app ping redis`
3. Verify credentials (if using password)
4. Check firewall rules

### Stale Data

**Symptoms**: Analysis not found, but ID in index

**Cause**: TTL expired or manual deletion

**Solution**:
```bash
# Clean stale index entries
docker-compose exec redis redis-cli
> SMEMBERS transcript-analysis:production:index
# For each stale ID:
> SREM transcript-analysis:production:index <uuid>
```

### Memory Limit Reached

**Symptoms**:
```
evicted_keys > 0
```

**Solutions**:
1. Increase `maxmemory` limit
2. Set `REDIS_TTL_SECONDS` to expire old data
3. Add pagination to list operations

### AOF Corruption

**Symptoms**: Redis won't start, logs show AOF errors

**Solution**:
```bash
docker-compose stop redis
docker-compose exec redis redis-check-aof --fix /data/appendonly.aof
docker-compose start redis
```

---

## Migration

### From In-Memory to Redis

1. **Enable Redis** (no data migration needed):
   ```bash
   REPOSITORY_BACKEND=redis
   docker-compose up -d
   ```

2. **Data starts fresh** (in-memory data is lost)
   - Option A: Accept data loss (for non-critical dev data)
   - Option B: Export/import via API (if many analyses)

### Export/Import Script

```python
import requests
import json

# Export from in-memory
response = requests.get("http://localhost:8000/api/v1/analyses")
analyses = response.json()

with open("export.json", "w") as f:
    json.dump(analyses, f)

# Switch to Redis
# REPOSITORY_BACKEND=redis

# Import to Redis
with open("export.json") as f:
    analyses = json.load(f)

for analysis in analyses:
    requests.post(
        "http://localhost:8000/api/v1/analyses",
        json=analysis
    )
```

---

## Production Checklist

- [ ] Set `REDIS_PASSWORD` for authentication
- [ ] Configure firewall (only allow app to access Redis)
- [ ] Set `REDIS_TTL_SECONDS` if data has limited retention
- [ ] Monitor memory usage and set alerts
- [ ] Schedule backups (AOF file snapshots)
- [ ] Use Redis Sentinel or Cluster for HA (if critical)
- [ ] Enable TLS for encrypted connections (if over network)
- [ ] Set up monitoring (Prometheus exporter)

---

## References

- [Redis Documentation](https://redis.io/documentation)
- [Redis Persistence](https://redis.io/topics/persistence)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
