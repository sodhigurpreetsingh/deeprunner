# Backend Server - Quick Start Guide

## ✅ All Errors Fixed!

The validation error has been resolved by adding the missing `BEDROCK_MODEL_ID_VISION` field to the Settings class.

## 🚀 How to Start the Server

**Method 1: Direct Python Execution (Recommended)**
```bash
cd /Users/momentum/PROJECTS/agentic_ai/rag2/backend-brite
python3 main.py
```

**Method 2: Using uvicorn module**
```bash
cd /Users/momentum/PROJECTS/agentic_ai/rag2/backend-brite
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Test the API

The server is currently running with PID: 51337

Test the brite endpoint:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/brite/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me the total count of users"}'
```

## 📚 API Documentation

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🛑 Stop the Server

```bash
kill 51337
# Or press CTRL+C in the terminal where server is running
```

## ✨ What Was Fixed

1. ✅ Added `BEDROCK_MODEL_ID_VISION` field to `Settings` class in `config.py`
2. ✅ Fixed `db.sql` path loading in `brite_service.py` - uses absolute paths
3. ✅ Added all missing `@staticmethod` decorators
4. ✅ Removed unused imports and code
5. ✅ Fixed type hints for better compatibility
6. ✅ Updated requirements.txt with all dependencies
7. ✅ All dependencies installed successfully

## 📁 Key Files

- **Main Entry Point**: `/Users/momentum/PROJECTS/agentic_ai/rag2/backend-brite/main.py`
- **Brite Service**: `/Users/momentum/PROJECTS/agentic_ai/rag2/backend-brite/app/services/brite_service.py`
- **Brite Routes**: `/Users/momentum/PROJECTS/agentic_ai/rag2/backend-brite/app/api/routes/brite.py`
- **Config**: `/Users/momentum/PROJECTS/agentic_ai/rag2/backend-brite/app/core/config.py`
