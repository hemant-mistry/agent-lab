import time
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any, Optional, Dict
from app.experiments.langchain_v1.agent import run_langchain_agent
from app.models.langchain_v1.schema import RunRequest, RunResponse, Step

router = APIRouter()

@router.post("/runs", response_model=RunResponse)
async def execute_run(req: RunRequest):
    if req.experiment_id != "langchain-v1":
        raise HTTPException(
            status_code=400, 
            detail=f"Experiment '{req.experiment_id}' is not registered."
        )

    start_time = time.time()
    
    try:
        # 1. Execute Agent
        state = await run_langchain_agent(user_query=req.query, session_id=req.session_id, use_router=req.use_router)
        
        # 2. Safely extract messages
        messages = state.get("messages", [])
        telemetry = state.get("telemetry", None)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # 3. Parse execution trace safely
        steps: List[Step] = []
        final_answer = ""
        step_counter = 1

        # 1. Extract the final text response from the AIMessage
        for msg in messages:
            if msg.__class__.__name__ == "AIMessage" and not getattr(msg, "tool_calls", None):
                content = getattr(msg, "content", "")
                if isinstance(content, list):
                    final_answer = "".join(item.get("text", "") for item in content if isinstance(item, dict))
                else:
                    final_answer = str(content)

        # 2. Extract explicit router steps (Fast Path)
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

        # 3. Extract LangChain agent loop steps (Heavy Path)
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

        return RunResponse(
            experiment_id=req.experiment_id,
            query=req.query,
            final_answer=final_answer,
            steps=steps,
            latency_ms=latency_ms,
            telemetry=telemetry
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))