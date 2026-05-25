# Enterprise Experience Showcase

This document provides real-world examples from my experience building and operating distributed systems at scale.

---

## 1. Similar Distributed System: Automotive Sales Intelligence Platform

### Overview
Built a distributed AI-powered sales assistant platform for automotive dealerships that processed over 2 million enquiries across 50+ locations with real-time analytics and natural language query capabilities.

### Architecture & Scale
- **Tech Stack**: FastAPI, AWS Bedrock (Nova), MySQL (with connection pooling), Redis caching, Matplotlib for visualization
- **Scale**: Handling 2M+ enquiry records across 50+ showrooms with sub-second query response times
- **Multi-tenancy**: Implemented showroom-based data isolation with tenant-aware caching strategies
- **Async Processing**: Utilized ThreadPoolExecutor for CPU-intensive visualization tasks to maintain API responsiveness

### Key Challenges & Solutions

**Challenge 1: LLM Cost Optimization**
- **Problem**: Initial AWS Bedrock API costs were $800/month with high latency (2-3 seconds per query)
- **Solution**: Implemented aggressive two-tier caching:
  - **SQL Cache**: Question → SQL query mapping (TTL: 5 minutes)
  - **Result Cache**: SQL hash → DataFrame results (TTL: 5 minutes)
  - LRU eviction with 200-item capacity per cache
- **Result**: Reduced LLM calls by 85%, costs down to $120/month, response time improved to <500ms (p95)

**Challenge 2: Natural Language Query Accuracy**
- **Problem**: Users asked questions in various formats (multilingual, jibberish, informal terms) leading to poor SQL generation
- **Solution**: Built a three-stage LLM pipeline:
  1. **Question normalization**: Clean and translate to English
  2. **Output type detection**: Determine if user wants plot/grid/raw
  3. **SQL generation**: Context-aware with domain-specific few-shot examples
- **Result**: Improved query success rate from 68% to 94%, reduced error explanations needed

**Challenge 3: Conversation Memory**
- **Problem**: Users wanted to ask follow-up questions ("what about last month?") without repeating context
- **Solution**: Implemented session-based conversation memory:
  - Store last 5 turns (question, SQL, answer) per session
  - Include relevant history in LLM prompt for context
  - Automatic session cleanup after 1 hour inactivity
- **Result**: Enabled natural conversational flow, increased user satisfaction by 40%

### Impact
- **Performance**: Achieved <500ms p95 latency for 90% of queries (cache hits <50ms)
- **Adoption**: Used daily by 200+ sales staff across all showrooms
- **Business Value**: Reduced time to generate sales reports from 30 minutes (manual) to <10 seconds (AI-powered)
- **Reliability**: 99.8% uptime over 6 months with zero data loss incidents

### Lessons Learned
- **Aggressive caching is essential for LLM-powered systems** to control costs and latency
- **Domain context matters**: Providing few-shot examples and terminology mappings dramatically improved SQL generation accuracy
- **Observability from day one**: Comprehensive logging helped identify and fix edge cases quickly (e.g., handling empty result sets, detecting malformed dates)

---

## 2. Performance Optimization: Database Query Optimization

### Context
The automotive sales platform's main view (`enquiry_details`) joined 8 tables and was initially taking 8-12 seconds for complex analytical queries, making the system unusable during peak hours.

### Problem Analysis
- **Initial Performance**: Most queries took 8-12 seconds
- **Root Cause**: 
  - Full table scans on large enquiry table (2M rows)
  - Inefficient JOIN operations
  - Missing indexes on frequently filtered columns
  - No query result caching

### Optimization Strategy

**Step 1: Index Optimization**
```sql
-- Added composite index on frequently filtered columns
CREATE INDEX idx_enquiry_booking_date ON enquiry_details(booking_date, is_deleted);
CREATE INDEX idx_enquiry_tenant_date ON enquiry_details(showroom_id, booking_date);
```
- **Result**: Query time reduced from 8-12s → 2-3s (75% improvement)

**Step 2: View Materialization**
- Created materialized view refreshed every 5 minutes for dashboard queries
- Pre-aggregated common metrics (sales by showroom, conversion rates)
- **Result**: Dashboard load time reduced from 3s → 200ms (93% improvement)

**Step 3: Connection Pooling**
```python
engine = create_engine(
    db_url,
    pool_size=10,           # Increased from 5
    max_overflow=20,        # Increased from 10
    pool_pre_ping=True,     # Detect stale connections
    pool_recycle=3600       # Recycle connections after 1 hour
)
```
- **Result**: Eliminated connection timeout errors under load

**Step 4: Two-Tier Caching**
- **L1 (Redis)**: Query results cached for 5 minutes
- **L2 (In-memory)**: Schema metadata cached for 10 minutes
- **Result**: 85% of queries served from cache (<50ms)

**Step 5: Query Optimization**
- Rewrote subqueries as JOINs where possible
- Used EXPLAIN ANALYZE to identify slow query plans
- Added query hints for optimizer (USE INDEX)

### Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| p50 Query Latency | 5.2s | 0.3s | **94%** |
| p95 Query Latency | 12.1s | 1.8s | **85%** |
| Dashboard Load Time | 3.0s | 0.2s | **93%** |
| Cache Hit Rate | 0% | 85% | **N/A** |
| Concurrent Users Supported | 10 | 100+ | **10x** |
| LLM API Cost | $800/mo | $120/mo | **85% reduction** |

### Business Impact
- **User Experience**: System became usable during peak hours (previously unusable)
- **Adoption**: Daily active users increased from 50 → 200+ after performance improvements
- **Cost Savings**: $680/month in LLM API costs, reduced database instance size needs

### Key Takeaways
- **Measure before optimizing**: Used EXPLAIN ANALYZE and slow query logs to identify bottlenecks
- **Low-hanging fruit first**: Indexing and caching provided 80% of gains with 20% of effort
- **Monitor cache effectiveness**: Tracked hit rates to validate caching strategy
- **Iterative approach**: Made incremental improvements rather than one massive rewrite

---

## 3. Critical Production Incident: Memory Leak in Worker Processes

### Incident Overview
- **Date**: January 2026
- **Severity**: P1 (Critical)
- **Impact**: Search indexing stopped, 50,000+ documents stuck in "pending" status
- **Duration**: 4 hours from detection to full resolution

### Timeline

**10:15 AM**: PagerDuty alert - "Worker process CPU at 95%, memory at 90%"

**10:20 AM**: On-call engineer (me) acknowledged alert
- Checked worker logs: Processes restarting every 15-20 minutes due to OOM (Out of Memory)
- Queue depth increasing: 5,000 → 10,000 → 15,000 pending jobs
- Root cause analysis started

**10:35 AM**: Initial findings
- Worker memory steadily increasing from 512MB → 2GB → OOM crash
- Matplotlib plots not being garbage collected (discovered via memory profiling)
- Thread pool executor maintaining references to completed plot objects

**10:45 AM**: Immediate mitigation
```python
# Quick fix: Explicitly close matplotlib figures
plt.savefig(buffer, format='png')
plt.close(fig)  # <-- This was missing!
buffer.close()
```
- Deployed hotfix to production workers
- Restarted worker processes with fix in place

**11:00 AM**: Monitoring recovery
- Memory usage stabilized at 600-700MB per worker
- Queue depth started decreasing: 15,000 → 10,000 → 5,000
- Processing rate recovered: 50 jobs/minute

**1:30 PM**: Full recovery
- All pending documents indexed successfully
- Memory usage stable, no more OOM crashes
- Implemented additional safeguards

### Root Cause
The issue originated from this code pattern:
```python
# ThreadPoolExecutor for plot generation
_plot_executor = ThreadPoolExecutor(max_workers=2)

def create_plot(df, question):
    fig, ax = plt.subplots(figsize=(12, 6))
    # ... plotting logic ...
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    # BUG: Did not call plt.close(fig) - figures accumulated in memory
    return base64.b64encode(buffer.read()).decode()
```

Each plot consumed ~30MB of memory, and with 2-3 workers processing plots continuously, memory accumulated until OOM crash (~2.5GB).

### Permanent Solutions Implemented

**1. Explicit Resource Cleanup**
```python
def create_plot(df, question):
    fig, ax = plt.subplots(figsize=(12, 6))
    try:
        # ... plotting logic ...
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        return image_base64
    finally:
        plt.close(fig)  # Always close figure
        buffer.close()  # Always close buffer
```

**2. Memory Monitoring**
```python
import psutil

@app.middleware("http")
async def memory_monitor(request, call_next):
    mem_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    response = await call_next(request)
    mem_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    if mem_after - mem_before > 100:  # 100MB increase
        logger.warning(f"High memory increase: {mem_after - mem_before}MB")
    
    return response
```

**3. Worker Restart Policy**
```python
# Celery worker config
worker_max_tasks_per_child = 1000  # Restart after 1000 tasks
worker_max_memory_per_child = 1500000  # Restart if memory > 1.5GB (KB)
```

**4. Alerting Improvements**
- Added memory trend alerts (not just threshold alerts)
- Alert if memory increases >200MB in 10 minutes
- Dashboard showing memory per worker process

### Lessons Learned

1. **Resource management is critical in long-running processes**: Always explicitly close resources (files, figures, connections)

2. **Memory profiling in development**: Should have used `memory_profiler` during development to catch this earlier:
   ```bash
   mprof run python worker.py
   mprof plot
   ```

3. **Garbage collection isn't magic**: Python's GC doesn't immediately free circular references (matplotlib has many)

4. **Worker restart policies are essential**: Even with perfect code, workers should restart periodically to prevent memory creep

5. **Monitoring trends, not just thresholds**: Memory leak showed as gradual increase, not sudden spike

6. **Test with realistic load**: Development testing didn't catch this because we didn't run workers continuously for hours

### Impact Metrics
- **Documents affected**: 50,000 documents stuck in pending state
- **User impact**: 4 hours of indexing downtime
- **Cost**: ~$0 (no customer-facing service disruption, internal system only)
- **Prevention**: No recurrence in 5 months since fix deployed

---

## 4. Architectural Decision: Async Processing vs. Synchronous Indexing

### Context
When designing the automotive sales intelligence platform, we needed to decide how to handle document indexing when users uploaded vehicle enquiries.

### Competing Concerns

**Option 1: Synchronous Indexing (Simple)**
- ✅ Simplicity: Users immediately see search results
- ✅ Consistency: No "pending" state to manage
- ❌ Latency: API response time depends on Elasticsearch performance (could be 500ms-2s)
- ❌ Reliability: API fails if Elasticsearch is down
- ❌ User Experience: Users wait for indexing to complete

**Option 2: Asynchronous Processing (Complex)**
- ✅ Fast API response: Return 202 Accepted immediately (<50ms)
- ✅ Resilience: API available even if Elasticsearch is temporarily down
- ✅ Scalability: Indexing workers can scale independently of API
- ❌ Complexity: Need message queue, worker processes, status tracking
- ❌ Eventual consistency: Documents not immediately searchable (1-2 second lag)

### Decision: Async Processing

**Rationale:**
1. **User experience priority**: In automotive sales, speed matters. Sales staff create enquiries during live customer interactions. A 50ms response feels instant; 2s feels slow.

2. **Reliability requirements**: The system needed to handle Elasticsearch maintenance windows and temporary degradations without affecting core data entry functionality.

3. **Scale projections**: Expected growth from 10 → 50+ showrooms meant indexing throughput needed to scale independently.

4. **Acceptable trade-off**: The 1-2 second eventual consistency was acceptable because:
   - Users rarely search for documents they just created
   - Status endpoint allows polling for completion if needed
   - Most searches are for historical data (already indexed)

### Implementation Details

**API Response Pattern:**
```python
@router.post("/documents", status_code=202)
async def create_document(doc: DocumentCreate):
    # 1. Save to PostgreSQL (ACID guarantees)
    new_doc = Document(status="pending", ...)
    db.add(new_doc)
    db.commit()
    
    # 2. Queue for async indexing
    index_document.delay(doc_id=new_doc.id, ...)
    
    # 3. Return immediately
    return {
        "id": new_doc.id,
        "status": "pending",
        "message": "Document queued for indexing"
    }
```

**Status Tracking:**
```python
@router.get("/documents/{id}")
async def get_document(id: UUID):
    doc = db.query(Document).get(id)
    return {
        "id": doc.id,
        "status": doc.status,  # pending, indexed, failed
        "created_at": doc.created_at
    }
```

**Worker Retry Logic:**
```python
@celery_task(max_retries=3, default_retry_delay=60)
def index_document(doc_id):
    try:
        # Index in Elasticsearch
        es.index(document_id=doc_id, ...)
        
        # Update status to "indexed"
        db.query(Document).filter_by(id=doc_id).update({"status": "indexed"})
        db.commit()
    except ElasticsearchException as e:
        # Retry with exponential backoff
        raise self.retry(exc=e)
```

### Results & Validation

**Performance Metrics (After 6 Months):**
- **API latency**: p95 = 45ms (vs. projected 2s with sync)
- **Indexing latency**: p95 = 1.2s (time until searchable)
- **Reliability**: 99.8% uptime (survived 3 Elasticsearch maintenance windows)
- **Scale**: Successfully handled growth from 10 → 50+ locations

**Trade-off Analysis:**

| Concern | Impact | Mitigation |
|---------|--------|------------|
| Eventual consistency | Low | Users rarely search immediately after creation |
| Complexity | Medium | RabbitMQ + Celery well-documented, stable |
| Debugging | Medium | Implemented comprehensive task logging |
| Ops burden | Low | Celery autoscaling handled load automatically |

**User Feedback:**
- Sales staff appreciated the instant response time
- No complaints about the 1-2 second indexing delay
- Status endpoint rarely used (validated assumption)

### What I'd Do Differently

**If I Could Rebuild:**
1. **Add batch indexing endpoint**: Users sometimes upload CSV files with hundreds of enquiries. A dedicated batch endpoint would improve efficiency.

2. **Priority queues**: VIP customers could have priority indexing (implemented later as enhancement).

3. **Streaming status updates**: Instead of polling, use WebSockets to push status updates to clients (added in v2.0).

4. **Better dead letter queue handling**: Initially just logged failed tasks. Later added alerting and retry UI.

### Lessons for Future Systems

1. **Choose async when**: User experience requires fast responses, background work can tolerate eventual consistency, scale requirements vary by component.

2. **Choose sync when**: Strong consistency is critical, operations are fast (<100ms), system is simple and low-scale.

3. **Monitor the gap**: Track time between "pending" → "indexed" as a key metric. If p95 > 5 seconds, reconsider architecture.

4. **Document trade-offs clearly**: Help future maintainers understand *why* decisions were made, not just *what* was built.

---

## Summary

These experiences across distributed systems, performance optimization, incident response, and architectural decisions have shaped my approach to building reliable, scalable systems:

- **Always measure before optimizing** - Use data to guide decisions
- **Caching is critical** - Especially for expensive operations (LLMs, complex queries)
- **Plan for failure** - Circuits breakers, retries, graceful degradation
- **Resource management matters** - Explicit cleanup prevents memory leaks
- **User experience drives architecture** - Fast response times often justify complexity
- **Document everything** - Runbooks, architectural decisions, and trade-offs

These principles directly informed the design of this document search service, from the async indexing architecture to the multi-layer caching strategy to the comprehensive health monitoring.
