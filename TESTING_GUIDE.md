# 🧪 Testing Guide - Document Search Service

## Current Status: ✅ ALL SERVICES RUNNING

All services are healthy and ready to test!

```
✅ API (port 8000)          - healthy
✅ PostgreSQL (port 5432)    - healthy  
✅ Elasticsearch (port 9200) - healthy
✅ Redis (port 6379)         - healthy
✅ RabbitMQ (port 5672)      - healthy
✅ Worker                    - processing tasks
```

---

## Quick Test (2 minutes)

Copy and paste these commands in your terminal:

### 1. Set tenant ID for all tests
```bash
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"
```

### 2. Check health
```bash
curl http://localhost:8000/api/v1/health | jq .
```

**Expected:** Status "healthy" with all dependencies "up"

---

### 3. Create a document
```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_A" \
  -d '{
    "title": "Introduction to Distributed Systems",
    "content": "Distributed systems are collections of independent computers that appear to users as a single coherent system. Key challenges include consistency, availability, and partition tolerance.",
    "metadata": {
      "author": "John Doe",
      "category": "Technology",
      "tags": ["distributed-systems", "architecture"]
    }
  }' | jq .
```

**Expected:**
```json
{
  "id": "<some-uuid>",
  "status": "pending",
  "message": "Document queued for indexing"
}
```

**Save the document ID:**
```bash
export DOC_ID="<paste-the-id-from-above>"
```

---

### 4. Wait for indexing (3 seconds)
```bash
sleep 3
echo "Indexing complete!"
```

---

### 5. Search for your document
```bash
curl -X GET "http://localhost:8000/api/v1/search?q=distributed" \
  -H "X-Tenant-ID: $TENANT_A" | jq .
```

**Expected:** 1 result with highlighted snippet like `"<mark>Distributed</mark> systems..."`

---

### 6. Retrieve document details
```bash
curl -X GET "http://localhost:8000/api/v1/documents/$DOC_ID" \
  -H "X-Tenant-ID: $TENANT_A" | jq .
```

**Expected:** Full document with status "indexed"

---

## Comprehensive Test Suite (10 minutes)

### Test 1: Multi-Tenancy Isolation

Create documents for different tenants and verify isolation:

```bash
# Tenant A document
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_A" \
  -d '{"title":"Tenant A Document","content":"This belongs to tenant A","metadata":{}}' | jq .

# Create another tenant (first add to database)
docker-compose exec api python -c "
from app.core.database import SyncSessionLocal
from app.models.tenant import Tenant
from uuid import UUID
db = SyncSessionLocal()
tenant_b_id = UUID('650e8400-e29b-41d4-a716-446655440001')
if not db.query(Tenant).filter(Tenant.id == tenant_b_id).first():
    db.add(Tenant(id=tenant_b_id, name='tenant_b', rate_limit_per_minute=100))
    db.commit()
    print('Created Tenant B')
db.close()
"

# Tenant B document
export TENANT_B="650e8400-e29b-41d4-a716-446655440001"
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_B" \
  -d '{"title":"Tenant B Document","content":"This belongs to tenant B","metadata":{}}' | jq .

# Wait for indexing
sleep 3

# Search as Tenant A - should only see Tenant A documents
curl -X GET "http://localhost:8000/api/v1/search?q=tenant" \
  -H "X-Tenant-ID: $TENANT_A" | jq '.results[].title'

# Search as Tenant B - should only see Tenant B documents  
curl -X GET "http://localhost:8000/api/v1/search?q=tenant" \
  -H "X-Tenant-ID: $TENANT_B" | jq '.results[].title'
```

**Expected:** Each tenant only sees their own documents

---

### Test 2: Full-Text Search Features

```bash
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"

# Create test documents
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_A" \
  -d '{
    "title": "Machine Learning Fundamentals",
    "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
    "metadata": {"category": "AI", "tags": ["ml", "ai"]}
  }' | jq .

curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_A" \
  -d '{
    "title": "Deep Learning Neural Networks",
    "content": "Deep learning uses neural networks with multiple layers to progressively extract higher-level features from raw input.",
    "metadata": {"category": "AI", "tags": ["deep-learning", "neural-nets"]}
  }' | jq .

sleep 3

# Test 1: Simple search
curl -X GET "http://localhost:8000/api/v1/search?q=machine+learning" \
  -H "X-Tenant-ID: $TENANT_A" | jq '{total, first_result: .results[0].title}'

# Test 2: Fuzzy search (should find "learning" even with typo)
curl -X GET "http://localhost:8000/api/v1/search?q=lerning" \
  -H "X-Tenant-ID: $TENANT_A" | jq '.total'

# Test 3: Phrase search
curl -X GET "http://localhost:8000/api/v1/search?q=neural+networks" \
  -H "X-Tenant-ID: $TENANT_A" | jq '.results[].title'

# Test 4: Pagination
curl -X GET "http://localhost:8000/api/v1/search?q=learning&page=1&size=1" \
  -H "X-Tenant-ID: $TENANT_A" | jq '{total, results_on_page: (.results | length)}'
```

---

### Test 3: Caching Performance

```bash
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"

# First search (cache miss)
echo "=== First search (cache miss) ==="
curl -X GET "http://localhost:8000/api/v1/search?q=machine+learning" \
  -H "X-Tenant-ID: $TENANT_A" | jq '.took_ms'

# Second search (cache hit - should be much faster)
echo "=== Second search (cache hit) ==="
curl -X GET "http://localhost:8000/api/v1/search?q=machine+learning" \
  -H "X-Tenant-ID: $TENANT_A" | jq '.took_ms'
```

**Expected:** Second search should be significantly faster (< 10ms)

---

### Test 4: Rate Limiting

```bash
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"

# Send 105 requests rapidly (tenant limit is 100/minute)
for i in {1..105}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X GET "http://localhost:8000/api/v1/search?q=test" \
    -H "X-Tenant-ID: $TENANT_A"
done | tail -10
```

**Expected:** Last few requests should return `429` (Too Many Requests)

---

### Test 5: Error Handling

```bash
# Test 1: Missing tenant header
curl -X GET "http://localhost:8000/api/v1/search?q=test" -w "\nHTTP Status: %{http_code}\n"

# Test 2: Invalid tenant ID format
curl -X GET "http://localhost:8000/api/v1/search?q=test" \
  -H "X-Tenant-ID: invalid-uuid" -w "\nHTTP Status: %{http_code}\n"

# Test 3: Empty search query
curl -X GET "http://localhost:8000/api/v1/search?q=" \
  -H "X-Tenant-ID: $TENANT_A" -w "\nHTTP Status: %{http_code}\n"

# Test 4: Document not found
curl -X GET "http://localhost:8000/api/v1/documents/00000000-0000-0000-0000-000000000000" \
  -H "X-Tenant-ID: $TENANT_A" -w "\nHTTP Status: %{http_code}\n"
```

**Expected:** Proper HTTP error codes (400, 404, 422)

---

### Test 6: Document Deletion

```bash
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"

# Create a document
DOC_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_A" \
  -d '{"title":"Document to Delete","content":"This will be deleted","metadata":{}}')

DOC_ID=$(echo $DOC_RESPONSE | jq -r '.id')
echo "Created document: $DOC_ID"

sleep 3

# Verify it exists
curl -X GET "http://localhost:8000/api/v1/search?q=deleted" \
  -H "X-Tenant-ID: $TENANT_A" | jq '.total'

# Delete it
curl -X DELETE "http://localhost:8000/api/v1/documents/$DOC_ID" \
  -H "X-Tenant-ID: $TENANT_A" -w "\nHTTP Status: %{http_code}\n"

sleep 3

# Verify it's gone from search
curl -X GET "http://localhost:8000/api/v1/search?q=deleted" \
  -H "X-Tenant-ID: $TENANT_A" | jq '.total'

# Verify it's gone from database
curl -X GET "http://localhost:8000/api/v1/documents/$DOC_ID" \
  -H "X-Tenant-ID: $TENANT_A" -w "\nHTTP Status: %{http_code}\n"
```

**Expected:** Document should be removed from both search and database

---

## Interactive API Documentation

### Swagger UI (Recommended for Manual Testing)

1. Open your browser
2. Go to: **http://localhost:8000/docs**
3. You'll see all endpoints with "Try it out" buttons
4. For endpoints requiring `X-Tenant-ID`, add it in the header section:
   - Key: `X-Tenant-ID`
   - Value: `550e8400-e29b-41d4-a716-446655440000`

### ReDoc (Alternative Documentation)

- Go to: **http://localhost:8000/redoc**
- Beautiful, readable API documentation

---

## Monitoring Services

### RabbitMQ Management Console
- URL: http://localhost:15672
- Username: `guest`
- Password: `guest`
- View queues, messages, and worker connections

### Elasticsearch
```bash
# Check cluster health
curl http://localhost:9200/_cluster/health | jq .

# List all indices
curl http://localhost:9200/_cat/indices?v

# Check document count for tenant
curl http://localhost:9200/documents_550e8400_e29b_41d4_a716_446655440000/_count | jq .
```

### Redis
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# In Redis CLI:
KEYS *                    # List all keys
GET "search:550e8400..."  # Get cached search result
TTL "search:550e8400..."  # Check time-to-live
```

### PostgreSQL
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d docsearch

# In psql:
\dt                                  # List tables
SELECT COUNT(*) FROM documents;      # Count documents
SELECT * FROM tenants;               # View tenants
SELECT id, title, status FROM documents LIMIT 5;  # View documents
\q                                   # Quit
```

---

## Viewing Logs

### All services
```bash
docker-compose logs -f
```

### Specific service
```bash
docker-compose logs -f api          # API logs
docker-compose logs -f worker       # Worker logs
docker-compose logs -f elasticsearch # Elasticsearch logs
```

### Search logs for errors
```bash
docker-compose logs api | grep -i error
docker-compose logs worker | grep -i "error\|failed"
```

---

## Performance Testing

### Simple load test with Apache Bench (if installed)
```bash
# Install: brew install apache-bench (Mac) or apt-get install apache2-utils (Linux)

# Test search endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  "http://localhost:8000/api/v1/search?q=test"
```

### Manual timing
```bash
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"

time curl -X GET "http://localhost:8000/api/v1/search?q=machine+learning" \
  -H "X-Tenant-ID: $TENANT_A" -o /dev/null -s
```

---

## Troubleshooting

### If services aren't responding

```bash
# Check status
docker-compose ps

# Restart specific service
docker-compose restart api
docker-compose restart worker

# Restart all services
docker-compose restart

# View logs for errors
docker-compose logs api --tail=50
docker-compose logs worker --tail=50
```

### If worker isn't processing tasks

```bash
# Check worker logs
docker-compose logs worker --tail=50

# Check RabbitMQ queues
docker-compose exec rabbitmq rabbitmqctl list_queues

# Restart worker
docker-compose restart worker
```

### If search returns no results

```bash
# Check if documents are indexed
curl http://localhost:9200/documents_*/_count | jq .

# Check document status in database
docker-compose exec postgres psql -U postgres -d docsearch -c \
  "SELECT id, title, status, error_message FROM documents LIMIT 10;"

# Restart worker to retry failed documents
docker-compose restart worker
```

---

## Requirements Verification Checklist

According to the PDF requirements, verify:

- ✅ **POST /documents** - Index a new document
- ✅ **GET /search?q={query}&tenant={tenantId}** - Search documents (tenant via header)
- ✅ **GET /documents/{id}** - Retrieve document details
- ✅ **DELETE /documents/{id}** - Remove a document
- ✅ **Basic multi-tenant support** - Header-based with X-Tenant-ID
- ✅ **Search functionality** - Elasticsearch with full-text search
- ✅ **Simple caching layer** - Redis with TTL
- ✅ **Basic rate limiting per tenant** - SlowAPI rate limiter
- ✅ **Health check endpoint** - With dependency status

---

## Expected Performance

Based on the prototype:

- **Search response time (cache hit)**: < 10ms
- **Search response time (cache miss)**: < 500ms (p95)
- **Document indexing**: Async, typically 1-3 seconds
- **API throughput**: 1000+ req/sec (with proper scaling)

---

## Next Steps

1. **Run the Quick Test** (above) to verify everything works
2. **Try the Swagger UI** at http://localhost:8000/docs for interactive testing
3. **Review the comprehensive test suite** for production-readiness validation
4. **Check the documentation**:
   - `ARCHITECTURE.md` - System design and trade-offs
   - `PRODUCTION_READINESS.md` - Production deployment guide
   - `API_EXAMPLES.md` - More API usage examples
   - `ENTERPRISE_EXPERIENCE.md` - Real-world scenarios

---

## Clean Up (When Done Testing)

### Stop services but keep data
```bash
docker-compose stop
```

### Stop and remove everything (including data)
```bash
docker-compose down -v
```

### Restart fresh
```bash
docker-compose down -v
docker-compose up -d
# Wait 30 seconds
docker-compose exec api python init_db.py
docker-compose exec api python seed_tenant.py
```

---

**🎉 Happy Testing!**
