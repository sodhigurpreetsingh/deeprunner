# API Usage Examples

Base URL: `http://localhost:8000/api/v1`

All requests (except health) require the `X-Tenant-ID` header for multi-tenancy.

## Sample Tenant IDs

For testing, use these sample UUIDs:
- Tenant A: `550e8400-e29b-41d4-a716-446655440000`
- Tenant B: `660e8400-e29b-41d4-a716-446655440001`

---

## 1. Health Check

Check system health and dependencies:

```bash
curl -X GET http://localhost:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "up",
    "elasticsearch": "up",
    "redis": "up",
    "rabbitmq": "up"
  },
  "uptime_seconds": 123.45
}
```

---

## 2. Index a Document

Create and index a new document (async operation):

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "title": "Introduction to Distributed Systems",
    "content": "Distributed systems are collections of independent computers that appear to users as a single coherent system. Key challenges include consistency, availability, and partition tolerance (CAP theorem). Modern architectures often employ microservices, message queues, and distributed databases.",
    "metadata": {
      "author": "John Doe",
      "category": "Technology",
      "tags": ["distributed-systems", "architecture", "scalability"]
    }
  }'
```

**Response (202 Accepted):**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "pending",
  "message": "Document queued for indexing"
}
```

---

## 3. Index Multiple Documents (Bulk)

```bash
# Document 1: Database Design
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "title": "Database Design Best Practices",
    "content": "Effective database design requires understanding normalization, indexing strategies, and query optimization. Choose between SQL and NoSQL based on your consistency and scalability needs. PostgreSQL offers ACID guarantees while MongoDB provides flexible schemas.",
    "metadata": {
      "author": "Jane Smith",
      "category": "Databases",
      "tags": ["database", "sql", "nosql", "design"]
    }
  }'

# Document 2: API Design
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "title": "RESTful API Design Principles",
    "content": "RESTful APIs should follow HTTP semantics, use proper status codes, and implement versioning. Key principles include statelessness, resource-based URLs, and standard HTTP methods (GET, POST, PUT, DELETE). Authentication typically uses JWT tokens or OAuth2.",
    "metadata": {
      "author": "Bob Johnson",
      "category": "APIs",
      "tags": ["rest", "api", "http", "design"]
    }
  }'

# Document 3: Caching Strategies
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "title": "Caching Strategies for High Performance",
    "content": "Caching is essential for high-performance systems. Redis and Memcached are popular choices. Implement cache-aside pattern with proper TTL management. Consider cache invalidation strategies: time-based, event-driven, or manual. Monitor cache hit rates to optimize effectiveness.",
    "metadata": {
      "author": "Alice Williams",
      "category": "Performance",
      "tags": ["caching", "redis", "performance", "optimization"]
    }
  }'

# Document 4: Elasticsearch Guide
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "title": "Elasticsearch Full-Text Search Guide",
    "content": "Elasticsearch is a distributed search engine built on Apache Lucene. It provides powerful full-text search with relevance ranking using BM25 algorithm. Features include fuzzy matching, faceted search, and highlighting. Scale horizontally with sharding and replication for high availability.",
    "metadata": {
      "author": "Charlie Brown",
      "category": "Search",
      "tags": ["elasticsearch", "search", "lucene", "full-text"]
    }
  }'
```

---

## 4. Search Documents

Full-text search with pagination:

```bash
# Search for "distributed"
curl -X GET "http://localhost:8000/api/v1/search?q=distributed&page=1&size=20" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "total": 1,
  "results": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "title": "Introduction to Distributed Systems",
      "snippet": "<mark>Distributed</mark> systems are collections of independent computers...",
      "score": 12.45,
      "metadata": {
        "author": "John Doe",
        "category": "Technology",
        "tags": ["distributed-systems", "architecture", "scalability"]
      }
    }
  ],
  "page": 1,
  "size": 20,
  "took_ms": 87.3
}
```

**More search examples:**

```bash
# Search for "caching"
curl -X GET "http://localhost:8000/api/v1/search?q=caching" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"

# Search for "database design"
curl -X GET "http://localhost:8000/api/v1/search?q=database%20design" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"

# Search for "API" with pagination
curl -X GET "http://localhost:8000/api/v1/search?q=API&page=1&size=10" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"

# Search for "elasticsearch performance"
curl -X GET "http://localhost:8000/api/v1/search?q=elasticsearch%20performance" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"
```

---

## 5. Retrieve Document by ID

Get complete document details:

```bash
curl -X GET http://localhost:8000/api/v1/documents/7c9e6679-7425-40de-944b-e07fc1f90ae7 \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Introduction to Distributed Systems",
  "content": "Distributed systems are collections of independent computers...",
  "metadata": {
    "author": "John Doe",
    "category": "Technology",
    "tags": ["distributed-systems", "architecture", "scalability"]
  },
  "status": "indexed",
  "error_message": null,
  "created_at": "2026-05-25T10:30:00Z",
  "updated_at": "2026-05-25T10:30:02Z"
}
```

---

## 6. Delete Document

Remove a document:

```bash
curl -X DELETE http://localhost:8000/api/v1/documents/7c9e6679-7425-40de-944b-e07fc1f90ae7 \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**Response: 204 No Content**

---

## 7. Multi-Tenancy Test

Documents are isolated by tenant:

```bash
# Create document for Tenant A
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"title": "Tenant A Document", "content": "Only visible to Tenant A"}'

# Create document for Tenant B
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 660e8400-e29b-41d4-a716-446655440001" \
  -d '{"title": "Tenant B Document", "content": "Only visible to Tenant B"}'

# Search as Tenant A (won't see Tenant B's documents)
curl -X GET "http://localhost:8000/api/v1/search?q=document" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"

# Search as Tenant B (won't see Tenant A's documents)
curl -X GET "http://localhost:8000/api/v1/search?q=document" \
  -H "X-Tenant-ID: 660e8400-e29b-41d4-a716-446655440001"
```

---

## 8. Rate Limiting Test

The API implements per-tenant rate limiting (default: 100 requests/minute):

```bash
# This will eventually hit rate limit after 100 requests
for i in {1..105}; do
  curl -X GET "http://localhost:8000/api/v1/search?q=test" \
    -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"
  echo "Request $i"
done
```

**Rate Limit Response (429 Too Many Requests):**
```json
{
  "error": "Rate limit exceeded: 100 per 1 minute"
}
```

---

## Performance Expectations

| Operation | Target Latency (p95) | Notes |
|-----------|---------------------|-------|
| Index Document | <50ms | Returns immediately (async processing) |
| Search (cache hit) | <10ms | Redis cache |
| Search (cache miss) | <500ms | Elasticsearch query |
| Get Document | <100ms | PostgreSQL query |
| Delete Document | <50ms | Returns immediately (async processing) |

---

## Troubleshooting

### Document not appearing in search results?

Wait 1-2 seconds after indexing for Elasticsearch to refresh. Check document status:

```bash
curl -X GET http://localhost:8000/api/v1/documents/{document_id} \
  -H "X-Tenant-ID: {your-tenant-id}"
```

Status should be "indexed" (not "pending" or "failed").

### Cache not working?

Check Redis health:

```bash
curl -X GET http://localhost:8000/api/v1/health
```

### Rate limited unexpectedly?

Rate limits reset every minute. Check your request count or wait 60 seconds.
