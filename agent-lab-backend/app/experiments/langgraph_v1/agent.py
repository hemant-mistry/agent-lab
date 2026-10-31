from typing import Any, Dict, Annotated, TypedDict, Literal
from pydantic import BaseModel, Field, field_validator

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.tools.schema_tool import SchemaTool
from app.tools.sql_tool import SQLTool
from app.models.langgraph_v1.schema import SQLReadInput, SQLWriteInput

schema_tool_instance = SchemaTool()
sql_tool_instance = SQLTool()

@tool
async def get_schema() -> str:
    """Returns the NexusWorks database schema. Call this before execute_sql."""
    return await schema_tool_instance.execute({})

@tool("execute_read_query", args_schema=SQLReadInput)
async def execute_read_query(query: str) -> str:
    """Executes a validated read-only PostgreSQL SELECT query."""
    try:
        return await sql_tool_instance.execute({"query": query})
    except Exception as exc:
        return f"Database Error: {str(exc)}. Please check the schema and try again."

@tool("execute_write_query", args_schema=SQLWriteInput)
async def execute_write_query(query: str, justification: str) -> str:
    """Executes a mutating PostgreSQL query (UPDATE/DELETE). REQUIRES HUMAN APPROVAL."""
    try:
        return await sql_tool_instance.execute({"query": query})
    except Exception as exc:
        return f"Database Error: {str(exc)}"

read_tools = [get_schema, execute_read_query]
write_tools = [execute_write_query]
all_tools = read_tools + write_tools

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=settings.GOOGLE_API_KEY,
    temperature=0,
).bind_tools(all_tools)

system_prompt = SystemMessage(
    content=(
        "You are a LangGraph-powered data assistant for NexusWorks.\n"
        "You have access to a PostgreSQL database.\n"
        "CRITICAL RULES:\n"
        "1. Never guess table or column names. Call 'get_schema' first if unsure.\n"
        "2. If 'execute_sql' returns an error, read it and self-correct your query.\n"
        "3. For mutations (DELETE/UPDATE), use 'execute_write_query'."
    )
)

async def reasoner_node(state: AgentState):
    """The brain of the agent. Reads state and decides whether to answer or call a tool."""
    messages = [system_prompt] + state["messages"]
    response = await llm.ainvoke(messages)
    return {"messages": [response]}

read_tool_node = ToolNode(read_tools)
write_tool_node = ToolNode(write_tools)

def route_tools(state: AgentState) -> Literal["read_tools", "write_tools", "__end__"]:
    last_msg = state["messages"][-1]
    if getattr(last_msg, "tool_calls", None):
        first_tool = last_msg.tool_calls[0]["name"]
        if first_tool == "execute_write_query":
            return "write_tools"
        return "read_tools"
    return "__end__"

builder = StateGraph(AgentState)

builder.add_node("reasoner", reasoner_node)
builder.add_node("read_tools", read_tool_node)
builder.add_node("write_tools", write_tool_node)

builder.add_edge(START, "reasoner")
builder.add_conditional_edges("reasoner", route_tools)
builder.add_edge("read_tools", "reasoner")
builder.add_edge("write_tools", "reasoner")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["write_tools"])

# =====================================================================
# 5. Execution Entrypoint & UI State Translation
# =====================================================================

async def extract_ui_state(config):
    """Extracts telemetry, final answers, and pause states for the React UI."""
    state = await graph.aget_state(config)
    is_interrupted = bool(state.next and "write_tools" in state.next)
    
    raw_messages = state.values.get("messages", [])
    if not isinstance(raw_messages, (list, tuple)):
        all_messages = [raw_messages]
    else:
        all_messages = list(raw_messages)
    
    last_human_idx = 0
    for i, msg in enumerate(all_messages):
        if msg.__class__.__name__ == "HumanMessage":
            last_human_idx = i
            
    current_turn_messages = all_messages[last_human_idx:]
    
    final_answer = ""
    requires_approval = False
    
    if is_interrupted:
        requires_approval = True
        last_msg = all_messages[-1]
        if getattr(last_msg, "tool_calls", None):
            tc = last_msg.tool_calls[0]
            args = tc.get("args", {})
            final_answer = (
                f"⚠️ **Human Approval Required** ⚠️\n\n"
                f"I need permission to mutate the database.\n\n"
                f"**Query:** `{args.get('query', 'N/A')}`\n"
                f"**Reason:** {args.get('justification', 'N/A')}"
            )
    else:
        for msg in reversed(current_turn_messages):
            if msg.__class__.__name__ == "AIMessage" and not getattr(msg, "tool_calls", None):
                content = getattr(msg, "content", "")
                if isinstance(content, list):
                    final_answer = "".join(item.get("text", "") for item in content if isinstance(item, dict))
                else:
                    final_answer = str(content)
                break

    input_tokens = sum(getattr(m, "usage_metadata", {}).get("input_tokens", 0) for m in current_turn_messages if hasattr(m, "usage_metadata") and getattr(m, "usage_metadata", None))
    output_tokens = sum(getattr(m, "usage_metadata", {}).get("output_tokens", 0) for m in current_turn_messages if hasattr(m, "usage_metadata") and getattr(m, "usage_metadata", None))
    total_tokens = sum(getattr(m, "usage_metadata", {}).get("total_tokens", 0) for m in current_turn_messages if hasattr(m, "usage_metadata") and getattr(m, "usage_metadata", None))

    return {
        "messages": current_turn_messages,
        "final_answer": final_answer,
        "requires_approval": requires_approval,
        "telemetry": {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens},
    }

async def run_langgraph_agent(user_query: str, session_id: str = "default-session") -> Dict[str, Any]:
    config = {"configurable": {"thread_id": session_id}}
    await graph.ainvoke({"messages": [("user", user_query)]}, config=config)
    return await extract_ui_state(config)

async def resume_langgraph_agent(session_id: str, action: Literal["approve", "reject"]) -> Dict[str, Any]:
    config = {"configurable": {"thread_id": session_id}}
    state = await graph.aget_state(config)
    
    if not state.next or "write_tools" not in state.next:
        raise ValueError("No pending approval found for this session.")

    if action == "approve":
        await graph.ainvoke(None, config)
    elif action == "reject":
        last_msg = state.values["messages"][-1]
        tc = last_msg.tool_calls[0]
        rejection_msg = ToolMessage(
            tool_call_id=tc["id"],
            name=tc["name"],
            content="System: The user REJECTED this action. Do not execute it. Apologize to the user."
        )
        await graph.aupdate_state(config, {"messages": [rejection_msg]}, as_node="write_tools")
        await graph.ainvoke(None, config)
        
    return await extract_ui_state(config)