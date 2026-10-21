from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.run import router as runs_router
import sys
import asyncio

app = FastAPI(title="AgentLab Platform API")

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Enable CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}