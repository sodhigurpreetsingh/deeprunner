# 🚀 Quick Start Guide - Document Search Service

## Prerequisites Check

Before starting, make sure you have:

1. **Docker Desktop** installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Minimum: 8GB RAM, 10GB disk space

2. **Verify Docker is running**:
   ```bash
   docker --version
   docker-compose --version
   ```

   Expected output:
   ```
   Docker version 24.x.x or higher
   Docker Compose version 2.x.x or higher
   ```

---

## Step 1: Navigate to Project Directory

```bash
cd /Users/momentum/PROJECTS/deeprunner
```

---

## Step 2: Start All Services

This will start 6 services: PostgreSQL, Elasticsearch, Redis, RabbitMQ, API, and Worker

```bash
docker-compose up -d
```

**What this does:**
- `-d` = Run in detached mode (background)
- Pulls Docker images (first time only, ~5 minutes)
- Starts all services
- Waits for health checks

**Expected output:**
```
Creating network "deeprunner_default"
Creating docsearch-postgres ... done
Creating docsearch-elasticsearch ... done
Creating docsearch-redis ... done
Creating docsearch-rabbitmq ... done
Creating docsearch-api ... done
Creating docsearch-worker ... done
```

---

## Step 3: Wait for Services to Be Ready

Services need 30-60 seconds to start up. Check status:

```bash
docker-compose ps
```

**Healthy output** (all services should show "Up" and "healthy"):
```
NAME                      STATUS              PORTS
docsearch-api             Up (healthy)        0.0.0.0:8000->8000/tcp
docsearch-elasticsearch   Up (healthy)        0.0.0.0:9200->9200/tcp
docsearch-postgres        Up (healthy)        0.0.0.0:5432->5432/tcp
docsearch-rabbitmq        Up (healthy)        0.0.0.0:5672->5672/tcp
docsearch-redis           Up (healthy)        0.0.0.0:6379->6379/tcp
docsearch-worker          Up                  
```

**If not healthy yet**, wait 30 more seconds and check again.

---

## Step 4: Verify Services Are Working

### Test the health endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "up",
    "elasticsearch": "up",
    "redis": "up",
    "rabbitmq": "up"
  },
  "uptime_seconds": 10.5
}
```

✅ **If you see this, you're ready to go!**

---

## Step 5: Test the API (Create Your First Document)

### Set tenant ID for convenience:
```bash
export TENANT_A="550e8400-e29b-41d4-a716-446655440000"
```

### Create a document:
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
  }'
```

**Expected response (202 Accepted):**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "pending",
  "message": "Document queued for indexing"
}
```

**Save the document ID** for next steps:
```bash
export DOC_ID="<paste-the-id-from-response>"
```

---

## Step 6: Wait for Indexing (2 seconds)

The document is being indexed in the background by the worker.

```bash
sleep 2
```

---

## Step 7: Search for Your Document

```bash
curl -X GET "http://localhost:8000/api/v1/search?q=distributed" \
  -H "X-Tenant-ID: $TENANT_A"
```

**Expected response:**
```json
{
  "total": 1,
  "results": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "title": "Introduction to Distributed Systems",
      "snippet": "<mark>Distributed</mark> systems are collections...",
      "score": 12.45,
      "metadata": {
        "author": "John Doe",
        "category": "Technology"
      }
    }
  ],
  "page": 1,
  "size": 20,
  "took_ms": 87.3
}
```

🎉 **Success! Your document search service is working!**

---

## Step 8: Access the Interactive API Documentation

Open your browser and go to:

**Swagger UI**: http://localhost:8000/docs

This provides an interactive interface where you can:
- See all API endpoints
- Test them directly from the browser
- View request/response schemas

---

## Common Commands

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f elasticsearch
```

### Stop services (but keep data):
```bash
docker-compose stop
```

### Start services again:
```bash
docker-compose start
```

### Stop and remove everything (including data):
```bash
docker-compose down -v
```

### Restart a single service:
```bash
docker-compose restart api
```

---

## Useful Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| **API (Swagger)** | http://localhost:8000/docs | Interactive API testing |
| **API (ReDoc)** | http://localhost:8000/redoc | Beautiful docs |
| **API Health** | http://localhost:8000/api/v1/health | Check status |
| **Elasticsearch** | http://localhost:9200 | Search engine |
| **RabbitMQ Management** | http://localhost:15672 | Queue monitoring (guest/guest) |

---

## More Examples

For comprehensive API examples with curl commands, see:

📖 **[API_EXAMPLES.md](./API_EXAMPLES.md)** - Complete API usage guide

This includes:
- Creating multiple documents
- Advanced search queries
- Multi-tenancy testing
- Rate limiting
- Cache behavior
- Edge cases

---

## Troubleshooting

### Problem: Docker daemon not running

**Error**: `Cannot connect to the Docker daemon`

**Solution**:
1. Open Docker Desktop application
2. Wait for it to start (whale icon in menu bar)
3. Try `docker ps` to verify it's running

---

### Problem: Port already in use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change the port in docker-compose.yml:
# ports:
#   - "8001:8000"  # Change 8000 to 8001
```

---

### Problem: Services stuck in "starting" state

**Solution**:
```bash
# Check logs for errors
docker-compose logs

# Restart services
docker-compose restart

# If still stuck, rebuild
docker-compose down
docker-compose up -d --build
```

---

### Problem: Elasticsearch fails with memory error

**Error**: `max virtual memory areas vm.max_map_count [65530] is too low`

**Solution (Mac)**:
```bash
# This is handled automatically by Docker Desktop on Mac
# If you still see this error, increase Docker Desktop memory:
# Docker Desktop → Preferences → Resources → Memory (set to 8GB)
```

**Solution (Linux)**:
```bash
sudo sysctl -w vm.max_map_count=262144
```

---

### Problem: Worker not processing documents

**Check worker logs**:
```bash
docker-compose logs worker
```

**Restart worker**:
```bash
docker-compose restart worker
```

**Verify RabbitMQ is running**:
```bash
curl http://localhost:15672
# Should show RabbitMQ management login
```

---

### Problem: Search returns no results

**Possible causes**:
1. **Indexing not complete** - Wait 2-3 seconds after creating document
2. **Wrong tenant ID** - Use the same tenant ID for create and search
3. **Elasticsearch not ready** - Check health endpoint

**Debug steps**:
```bash
# 1. Check document status
curl -X GET "http://localhost:8000/api/v1/documents/$DOC_ID" \
  -H "X-Tenant-ID: $TENANT_A"

# Status should be "indexed", not "pending" or "failed"

# 2. Check Elasticsearch directly
curl http://localhost:9200/_cat/indices?v

# Should see indices like: documents_550e8400_e29b_41d4_a716_446655440000

# 3. Check worker logs
docker-compose logs worker | grep -i error
```

---

## Next Steps

Once you have the service running:

1. **Try the examples** - See [API_EXAMPLES.md](./API_EXAMPLES.md)
2. **Test multi-tenancy** - Create documents with different tenant IDs
3. **Test caching** - Run the same search twice, observe performance
4. **Test rate limiting** - Send 105 requests rapidly
5. **Explore Swagger UI** - http://localhost:8000/docs

---

## Stopping the Services

When you're done:

```bash
# Stop but keep data
docker-compose stop

# Or stop and remove everything (including data)
docker-compose down -v
```

---

## Performance Tips

**For better performance on Mac**:

1. **Increase Docker memory**:
   - Docker Desktop → Preferences → Resources
   - Memory: 8GB (minimum), 12GB (recommended)

2. **Increase CPU**:
   - CPUs: 4 cores (minimum), 6 cores (recommended)

3. **Use VirtioFS** (Docker Desktop 4.6+):
   - Docker Desktop → Preferences → General
   - Enable "VirtioFS" for better file sharing

---

## Need Help?

- **Documentation**: Check [README.md](./README.md) for full guide
- **Architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for design details
- **Testing**: See [TEST_PLAN.md](./TEST_PLAN.md) for comprehensive tests
- **API Examples**: See [API_EXAMPLES.md](./API_EXAMPLES.md) for all endpoints

---

**You're all set! Enjoy building with the Document Search Service! 🚀**
