import time
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any, Optional, Dict
from app.experiments.langchain_v1.agent import run_langchain_agent

router = APIRouter()

class RunRequest(BaseModel):
    experiment_id: str
    query: str
    session_id: str = "default-session"

class Step(BaseModel):
    step_number: int
    type: str 
    title: str
    content: Any

class RunResponse(BaseModel):
    experiment_id: str
    query: str
    final_answer: str
    steps: List[Step]
    latency_ms: float
    telemetry: Optional[Dict[str, int]] = None

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
        state = await run_langchain_agent(user_query=req.query, session_id=req.session_id)
        
        # 2. Safely extract messages
        messages = state.get("messages", [])
        telemetry = state.get("telemetry", None)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # 3. Parse execution trace safely
        steps: List[Step] = []
        final_answer = ""
        step_counter = 1

        for msg in messages:
            msg_type = msg.__class__.__name__

            if msg_type == "HumanMessage":
                continue

            elif msg_type == "AIMessage":
                if getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        steps.append(Step(
                            step_number=step_counter,
                            type="tool_call",
                            title=f"Tool Call: {tc.get('name', 'unknown')}",
                            content=tc.get("args", {})
                        ))
                        step_counter += 1
                else:
                    content = getattr(msg, "content", "")
                    if isinstance(content, list):
                        final_answer = "".join(
                            item.get("text", "") for item in content if isinstance(item, dict)
                        )
                    else:
                        final_answer = str(content)

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
        # Print the full stack trace to your backend terminal for easy debugging
        traceback.print_exc()
        
        # Format the error cleanly for the frontend
        error_msg = str(e)
        if isinstance(e, KeyError):
            error_msg = f"Missing expected key in agent state: {e}"
            
        raise HTTPException(status_code=500, detail=error_msg)