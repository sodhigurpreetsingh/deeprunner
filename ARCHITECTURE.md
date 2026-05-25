# Distributed Document Search Service - Architecture Design

## 1. High-Level System Architecture

```
┌─────────────────┐
│   API Gateway   │
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼───┐  ┌──▼──────┐
│ Redis │  │ Rate    │
│ Cache │  │ Limiter │
└───┬───┘  └─────────┘
    │
┌───▼────────────────────────────┐
│   Application Layer            │
│   - Document Service           │
│   - Search Service             │
│   - Tenant Service             │
└───┬────────────────────────┬───┘
    │                        │
┌───▼──────────┐      ┌─────▼─────────┐
│ PostgreSQL   │      │ Elasticsearch │
│ (Metadata)   │      │ (Full-Text)   │
└──────────────┘      └───────────────┘
         │
    ┌────▼───────┐
    │  RabbitMQ  │
    │  + Celery  │
    └────┬───────┘
         │
    ┌────▼────────┐
    │   Worker    │
    │   Nodes     │
    └─────────────┘
```

### Component Responsibilities

**API Gateway (FastAPI)**
- Request validation and authentication
- Tenant identification (via X-Tenant-ID header)
- Rate limiting enforcement
- Response formatting
- Health monitoring

**Redis Cache**
- Search result caching (5-minute TTL by default)
- Tenant-specific cache keys: `search:{tenant_id}:{query_hash}`
- Cache-aside pattern with automatic invalidation
- Connection pooling for high concurrency

**PostgreSQL**
- Document metadata storage (id, tenant_id, title, status, timestamps)
- Tenant configuration and rate limits
- ACID transactions for consistency
- Partitioning by tenant_id for isolation

**Elasticsearch**
- Full-text search with relevance ranking (BM25)
- Tenant isolation via separate indices: `documents_{tenant_id}`
- Inverted index for sub-second queries
- Horizontal scaling via sharding

**RabbitMQ + Celery**
- Asynchronous document indexing
- Batch operations for bulk uploads
- Dead letter queue for failed jobs
- Task retry with exponential backoff

**Worker Nodes**
- Document processing and extraction
- Elasticsearch indexing operations
- Autoscaling based on queue depth

---

## 2. Data Flow Diagrams

### Indexing Flow (Write Path)

```
User → POST /documents
  ↓
[1] Validate & Save to PostgreSQL (status=pending)
  ↓
[2] Return 202 Accepted (document_id)
  ↓
[3] Publish to RabbitMQ Queue
  ↓
[Async] Worker picks up task
  ↓
[4] Process & Index to Elasticsearch
  ↓
[5] Update PostgreSQL (status=indexed)
  ↓
[6] Invalidate related caches
```

**Design Rationale:**
- **Asynchronous indexing** decouples write from indexing latency
- **202 Accepted** provides immediate response (<50ms)
- **Status tracking** allows clients to poll for completion
- **Queue-based** architecture enables horizontal scaling

### Search Flow (Read Path)

```
User → GET /search?q=query&tenant=X
  ↓
[1] Check Redis cache: search:X:hash(query)
  ↓
  Cache HIT → Return cached results (<10ms)
  ↓
  Cache MISS ↓
  ↓
[2] Query Elasticsearch (index: documents_X)
  ↓
[3] Filter by tenant_id (defense in depth)
  ↓
[4] Apply relevance ranking & pagination
  ↓
[5] Cache results in Redis (TTL=300s)
  ↓
[6] Return results (target <500ms p95)
```

**Performance Optimizations:**
- **L1 Cache (Redis):** ~90% hit rate, <10ms latency
- **L2 (Elasticsearch):** Optimized indices, <200ms latency
- **Request coalescing:** Deduplicate concurrent identical queries

---

## 3. Database & Storage Strategy

### PostgreSQL (Metadata Store)

**Schema:**
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rate_limit_per_minute INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, indexed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (tenant_id);

CREATE INDEX idx_documents_tenant ON documents(tenant_id, created_at DESC);
CREATE INDEX idx_documents_status ON documents(status) WHERE status = 'pending';
```

**Why PostgreSQL:**
- ✅ ACID guarantees for metadata consistency
- ✅ Rich indexing and query capabilities
- ✅ JSONB for flexible metadata
- ✅ Native partitioning for tenant isolation
- ❌ Not suitable for full-text search at scale

### Elasticsearch (Search Engine)

**Index Strategy:**
- **Per-tenant indices:** `documents_{tenant_id}` 
  - Provides logical isolation
  - Allows independent scaling per tenant
  - Simplifies access control

**Index Mapping:**
```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "tenant_id": { "type": "keyword" },
      "title": { 
        "type": "text", 
        "analyzer": "standard",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "content": { 
        "type": "text",
        "analyzer": "standard"
      },
      "metadata": { "type": "object", "enabled": false },
      "indexed_at": { "type": "date" }
    }
  },
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 2,
    "refresh_interval": "1s"
  }
}
```

**Why Elasticsearch:**
- ✅ Sub-second full-text search (target <200ms)
- ✅ BM25 relevance ranking out-of-the-box
- ✅ Horizontal scalability via sharding
- ✅ Built-in highlighting and faceting
- ❌ Eventual consistency (acceptable for search)

---

## 4. API Design

### Base URL: `/api/v1`

### Endpoints

#### 1. Index Document
```http
POST /documents
X-Tenant-ID: {tenant_uuid}
Content-Type: application/json

{
  "title": "Technical Design Document",
  "content": "Full document text...",
  "metadata": {
    "author": "John Doe",
    "tags": ["architecture", "design"]
  }
}

Response: 202 Accepted
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Document queued for indexing"
}
```

#### 2. Search Documents
```http
GET /search?q={query}&tenant={tenant_id}&page=1&size=20
X-Tenant-ID: {tenant_uuid}

Response: 200 OK
{
  "total": 1247,
  "results": [
    {
      "id": "...",
      "title": "...",
      "snippet": "...highlighted text...",
      "score": 12.45,
      "metadata": {...}
    }
  ],
  "page": 1,
  "size": 20,
  "took_ms": 87
}
```

#### 3. Get Document
```http
GET /documents/{id}
X-Tenant-ID: {tenant_uuid}

Response: 200 OK
{
  "id": "...",
  "tenant_id": "...",
  "title": "...",
  "content": "...",
  "metadata": {...},
  "status": "indexed",
  "created_at": "2026-05-25T10:00:00Z"
}
```

#### 4. Delete Document
```http
DELETE /documents/{id}
X-Tenant-ID: {tenant_uuid}

Response: 204 No Content
```

#### 5. Health Check
```http
GET /health

Response: 200 OK
{
  "status": "healthy",
  "dependencies": {
    "postgres": "up",
    "elasticsearch": "up",
    "redis": "up",
    "rabbitmq": "up"
  },
  "uptime_seconds": 86400
}
```

---

## 5. Consistency Model & Trade-offs

### Consistency Model: **Eventual Consistency**

**Write Path:**
- PostgreSQL provides immediate consistency for metadata
- Elasticsearch is eventually consistent (typically <1s refresh interval)
- Clients receive 202 Accepted, poll for status if needed

**Read Path:**
- Search results may lag behind recent writes (1-2 seconds)
- Document retrieval from PostgreSQL is strongly consistent

**Trade-offs:**

| Choice | Benefit | Cost |
|--------|---------|------|
| Eventual consistency | Higher throughput, lower latency | Clients may not see recent writes |
| Async indexing | API responds <50ms | Complexity in status tracking |
| Per-tenant indices | Isolation, independent scaling | Index management overhead |
| Cache-aside pattern | 90% requests <10ms | Stale data for 5 minutes |

**When Strong Consistency is Needed:**
- Use PostgreSQL for critical metadata (tenant config, billing)
- Elasticsearch for search only (acceptable lag)

---

## 6. Caching Strategy

### Multi-Layer Caching

**Layer 1: Application-Level (In-Memory)**
- Tenant configuration (LRU cache, 1000 entries)
- Rate limit counters (sliding window)

**Layer 2: Redis (Distributed)**
- Search result caching
- Key pattern: `search:{tenant}:{query_hash}:{filters}`
- TTL: 300 seconds (5 minutes)
- Eviction: LRU policy

**Cache Invalidation:**
- **Time-based:** TTL expiration (primary method)
- **Event-based:** On document update/delete, invalidate tenant cache
- **Selective invalidation:** Only invalidate affected queries (future enhancement)

**Cache Hit Rate Target: 85-90%**

**Optimization Techniques:**
- Query normalization (lowercase, stemming)
- Popular queries pre-warmed
- Cache stampede prevention (locking)

---

## 7. Message Queue Architecture

### RabbitMQ + Celery

**Queues:**
1. **`document.index`** - Single document indexing (priority: high)
2. **`document.batch`** - Batch indexing (priority: normal)
3. **`document.delete`** - Deletion tasks (priority: high)
4. **`document.reindex`** - Full reindex operations (priority: low)

**Task Retry Strategy:**
```python
@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(ElasticsearchException,)
)
```

**Dead Letter Queue (DLQ):**
- Failed tasks after max retries → DLQ
- Alerting on DLQ depth > 100
- Manual review and reprocessing

**Scaling:**
- Workers scale based on queue depth
- Kubernetes HPA: target 50 messages/worker
- Priority queues for SLA-critical tasks

---

## 8. Multi-Tenancy & Data Isolation

### Isolation Strategy: **Index-Level Isolation**

**Approach:**
- Each tenant gets a dedicated Elasticsearch index: `documents_{tenant_id}`
- PostgreSQL uses `tenant_id` column with partitioning
- Redis keys prefixed with `tenant_id`

**Benefits:**
- ✅ Strong logical isolation
- ✅ Independent scaling per tenant
- ✅ Simplified access control
- ✅ Easy data export/deletion (GDPR)

**Drawbacks:**
- ❌ Index management overhead (100+ tenants)
- ❌ Resource allocation per index

**Security Measures:**
1. **Header-based authentication:** `X-Tenant-ID` validated on every request
2. **Defense in depth:** Elasticsearch queries filter by `tenant_id` even with per-tenant indices
3. **PostgreSQL RLS (Row-Level Security):** Future enhancement for additional safety
4. **Audit logging:** All tenant operations logged for compliance

**Rate Limiting:**
- Per-tenant rate limits stored in PostgreSQL
- Enforced at API gateway using Redis counters
- Sliding window algorithm (more accurate than fixed window)

---

## 9. Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Search latency (p50) | <100ms | Redis cache + optimized ES indices |
| Search latency (p95) | <500ms | Query timeout + circuit breaker |
| Search latency (p99) | <1000ms | Fallback to degraded mode |
| Index latency | <2s (async) | Background processing via workers |
| API response time | <50ms | Async write, immediate response |
| Throughput | 1000+ RPS | Horizontal scaling + caching |
| Cache hit rate | >85% | Smart cache keys + TTL tuning |
| Availability | 99.95% | Multi-AZ deployment + failover |

---

## 10. Technology Choices Summary

| Component | Choice | Rationale |
|-----------|--------|-----------|
| API Framework | FastAPI | Async support, auto docs, high performance |
| Primary DB | PostgreSQL | ACID, partitioning, rich features |
| Search Engine | Elasticsearch | Industry-standard, proven at scale |
| Cache | Redis | Low latency, widely supported |
| Message Queue | RabbitMQ | Reliable, priority queues, DLQ support |
| Task Queue | Celery | Python-native, mature ecosystem |
| Container | Docker | Reproducible, easy local development |
| Orchestration | docker-compose (dev) | Simplified multi-service setup |

---

## 11. Deployment Considerations (Production)

**Infrastructure (AWS Example):**
- **API:** ECS Fargate (autoscaling 3-50 instances)
- **PostgreSQL:** RDS Multi-AZ (r6g.xlarge)
- **Elasticsearch:** AWS OpenSearch Service (3-node cluster)
- **Redis:** ElastiCache (cluster mode enabled)
- **RabbitMQ:** Amazon MQ (HA pair)
- **Workers:** ECS Fargate (autoscaling 2-20 instances)

**Cost Optimization:**
- Reserved instances for baseline capacity
- Spot instances for worker burst capacity
- Elasticsearch hot/warm architecture for older data
- Cache compression for large result sets

**Monitoring:**
- Prometheus + Grafana for metrics
- ELK stack for centralized logging
- Jaeger for distributed tracing
- PagerDuty for alerting

---

*Document Version: 1.0*
*Last Updated: 2026-05-25*
*Author: Technical Assessment Submission*
