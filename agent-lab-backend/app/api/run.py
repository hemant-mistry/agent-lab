import time
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any, Optional, Dict
from app.experiments.langchain_v1.agent import run_langchain_agent
from app.experiments.langgraph_v1.agent import run_langgraph_agent, resume_langgraph_agent, stream_langgraph_agent
from fastapi.responses import StreamingResponse
from app.models.langchain_v1.schema import RunRequest, RunResponse, Step
from app.models.langgraph_v1.schema import ResumeRequest
from app.core.checkpointer import get_postgres_checkpointer

router = APIRouter()


def format_run_response(experiment_id: str, query: str, state: dict, start_time: float) -> RunResponse:
    messages = state.get("messages", [])
    steps: List[Step] = []
    step_counter = 1

    # Extract LCEL Router Trace if present
    explicit_steps = state.get("steps", [])
    if explicit_steps:
        for es in explicit_steps:
            steps.append(Step(
                step_number=step_counter,
                type=es.get("type", "tool_call"),
                title=es.get("title", "Trace"),
                content=es.get("content", {})
            ))
            step_counter += 1

    # Extract Tool Steps
    for msg in messages:
        msg_type = msg.__class__.__name__
        if msg_type == "AIMessage" and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                steps.append(Step(
                    step_number=step_counter,
                    type="tool_call",
                    title=f"Tool Call: {tc.get('name', 'unknown')}",
                    content=tc.get("args", {})
                ))
                step_counter += 1
        elif msg_type == "ToolMessage":
            steps.append(Step(
                step_number=step_counter,
                type="tool_result",
                title=f"Tool Result: {getattr(msg, 'name', 'unknown')}",
                content=str(getattr(msg, "content", ""))
            ))
            step_counter += 1

    # --- THE FIX IS HERE ---
    # Extract the actual text from the last AI Message
    extracted_answer = state.get("final_answer", "")
    if not extracted_answer and messages:
        last_msg = messages[-1]
        if last_msg.__class__.__name__ == "AIMessage":
            extracted_answer = getattr(last_msg, "content", "")
    # -----------------------

    return RunResponse(
        experiment_id=experiment_id,
        query=query,
        final_answer=extracted_answer, # Pass the extracted text here
        steps=steps,
        latency_ms=round((time.time() - start_time) * 1000, 2),
        requires_approval=state.get("requires_approval", False),
        telemetry=state.get("telemetry")
    )

@router.post("/runs", response_model=RunResponse)
async def execute_run(req: RunRequest):
    if req.experiment_id not in ["langchain-v1", "langgraph-v1"]:
        raise HTTPException(status_code=400, detail="Invalid experiment ID.")

    start_time = time.time()
    try:
        if req.experiment_id == "langgraph-v1":
        
            # Create an async generator for Server-Sent Events (SSE)
            async def event_generator():
                async with get_postgres_checkpointer() as memory:
                    # Yield chunks directly from the LangGraph streaming function
                    async for chunk in stream_langgraph_agent(req.query, req.session_id, memory):
                        yield chunk
                        
            # Return the stream with the standard SSE media type
            return StreamingResponse(event_generator(), media_type="text/event-stream")
    
        else:
            state = await run_langchain_agent(
                req.query, req.session_id, req.use_router
            )
        return format_run_response(req.experiment_id, req.query, state, start_time)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/runs/resume", response_model=RunResponse)
async def execute_resume(req: ResumeRequest):
    start_time = time.time()
    try:
        if req.experiment_id != "langgraph-v1":
            raise HTTPException(
                status_code=400,
                detail="Only LangGraph supports state resumption.",
            )
        
        async with get_postgres_checkpointer() as memory:
            state = await resume_langgraph_agent(req.session_id, req.action, memory)

        return format_run_response(
            req.experiment_id,
            f"Human Action: {req.action.upper()}",
            state,
            start_time,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))