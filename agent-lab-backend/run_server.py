import asyncio
import sys
import uvicorn

# Apply the Windows event loop fix BEFORE Uvicorn does anything
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)