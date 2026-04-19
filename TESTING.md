# NIST 800-53 RAG Chatbot - Testing Guide

## Pre-Test Setup

### 1. Add NIST PDF
Download NIST 800-53 Revision 5 from https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
Place it at: `data/nist.pdf`

### 2. Configure API Keys
```bash
cp .env.example .env
```
Edit `.env` with actual keys:
- GEMINI_API_KEY from https://makersuite.google.com/app/apikey
- GROQ_API_KEY from https://console.groq.com/keys
- ADMIN_TOKEN (any secure string)

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Test Suite

### Test 1: Ingestion Pipeline
**Purpose**: Verify PDF processing and vector storage

```bash
# Delete existing database
rm -rf chroma_db/

# Run ingestion
python main.py --ingest
```

**Expected Output**:
- Loading PDF with XXX pages...
- Extracted XXXXXX characters
- Created 300-800 chunks using NIST-aware splitting
- Processing XXX/XXX chunks...
- Ingestion complete!

**Validation**:
- [ ] Chunk count between 300-800
- [ ] ChromaDB directory created
- [ ] No errors during embedding

### Test 2: Retrieval Test
**Purpose**: Verify MMR search and reranking

```bash
python main.py --test
```

**Expected Output**:
- Retrieved 6 documents
- Reranked to top 3 documents
- Retrieved chunks with control IDs
- Coherent answer about AC-1

**Validation**:
- [ ] Exactly 3 chunks after reranking
- [ ] Control IDs in metadata (AC-1, etc.)
- [ ] Answer cites NIST content accurately

### Test 3: API Health Endpoint
**Purpose**: Verify service is running

```bash
# Start server
uvicorn api.server:app --reload

# In another terminal
curl http://localhost:8000/api/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "collection_count": 542,
  "model": "llama-3.3-70b-versatile"
}
```

**Validation**:
- [ ] Status code 200
- [ ] collection_count > 0
- [ ] model matches config

### Test 4: API Ask (Non-Streaming)
**Purpose**: Test question answering

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is AC-1?","stream":false}'
```

**Expected Response**:
```json
{
  "answer": "AC-1 is the access control policy...",
  "sources": [
    {"text": "...", "control_id": "AC-1"}
  ]
}
```

**Validation**:
- [ ] Answer contains NIST content
- [ ] Sources array not empty
- [ ] control_id present

### Test 5: API Ask (Streaming)
**Purpose**: Test SSE streaming

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is least privilege?","stream":true}'
```

**Expected Output**:
```
data: {"type":"start","sources":[...]}
data: {"type":"token","content":"Least"}
data: {"type":"token","content":" privilege"}
...
data: {"type":"end"}
```

**Validation**:
- [ ] SSE format correct
- [ ] Tokens arrive progressively
- [ ] Final end event sent

### Test 6: API Ingest (Admin)
**Purpose**: Test admin-protected endpoint

```bash
# Without token (should fail)
curl -X POST http://localhost:8000/api/ingest

# With token (should succeed)
curl -X POST http://localhost:8000/api/ingest \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Validation**:
- [ ] 401 without token
- [ ] 200 with valid token
- [ ] chunks_processed in response

### Test 7: Frontend UI
**Purpose**: Test chat interface

1. Open http://localhost:8000
2. Verify green status dot
3. Click each starter question
4. Verify streaming responses
5. Check source chips appear

**Validation**:
- [ ] Green status dot (online)
- [ ] All 4 starter questions work
- [ ] Streaming works (tokens appear progressively)
- [ ] Source chips with control IDs
- [ ] Markdown rendering (bold, code blocks)
- [ ] Typing indicator shows

### Test 8: Edge Cases

**Empty Question**:
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"","stream":false}'
```
Expected: 400 "Question cannot be empty"

**Unknown Topic**:
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the meaning of life?","stream":false}'
```
Expected: "I don't have that information in my knowledge base"

**Long Question** (>500 chars):
Should be truncated to 500 chars

### Test 9: Docker Build
**Purpose**: Verify containerization

```bash
docker build -t nist-rag .
docker run -p 8000:8000 --env-file .env nist-rag
```

**Validation**:
- [ ] Build completes in < 5 min
- [ ] Container starts in < 60s
- [ ] /api/health returns 200
- [ ] Frontend accessible

### Test 10: Mobile Responsiveness
**Purpose**: Test mobile layout

1. Open browser DevTools
2. Set viewport to 375x667 (iPhone SE)
3. Test all features

**Validation**:
- [ ] Header visible
- [ ] Messages scrollable
- [ ] Input accessible
- [ ] Starter questions stacked vertically

## Performance Benchmarks

**Target Metrics**:
- Ingestion: < 5 min for NIST PDF
- First retrieval: < 2s (includes model loading)
- Subsequent retrievals: < 500ms
- Time to first token: < 1s
- Container startup: < 60s

## Troubleshooting

**Import errors**: Ensure all dependencies installed
**CORS errors**: Check browser console for API URL
**Empty responses**: Verify ChromaDB has data
**Slow startup**: CrossEncoder downloads on first run

## Sign-Off Checklist

- [ ] All 10 test suites pass
- [ ] Edge cases handled gracefully
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Docker image builds successfully
- [ ] Ready for Render deployment
