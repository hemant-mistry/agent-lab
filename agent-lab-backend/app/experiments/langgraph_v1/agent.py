from typing import Any, Dict, Annotated, TypedDict, Literal
from pydantic import BaseModel, Field, field_validator
import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.core.config import settings
from app.tools.schema_tool import SchemaTool
from app.tools.sql_tool import SQLTool
from app.models.langgraph_v1.schema import SQLReadInput, SQLWriteInput, RouteDecision

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
    next_node: str

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    api_key=settings.GOOGLE_API_KEY,
).bind_tools(all_tools)

supervisor_prompt = SystemMessage(
    content=(
        "You are the Supervisor Agent for NexusWorks. Route user queries to the specialized agents.\n"
        "- 'sql_agent': For anything involving databases, tickets, customers, or projects.\n"
        "- 'general_agent': For greetings, semantic routing tests, core values, or conversational fallback.\n"
        "- 'FINISH': ONLY use this if EVERY part of the user's request has been fully resolved.\n\n"
        "CRITICAL: If the user asks a multi-part question (e.g., a greeting AND a database query), "
        "you must route to one agent at a time. Review the conversation history. If an agent answered one part "
        "but another part remains unanswered, route to the next relevant agent. Do NOT output FINISH until all parts are answered."
    )
)
async def supervisor_node(state: AgentState):
    """The brain of the agent. Reads state and decides whether to answer or call a tool."""
    
    # Create a local copy of messages so we don't accidentally save this routing prompt to the database
    current_messages = list(state["messages"])
    
    # Gemini API strict rule: The conversation cannot end with an AI message.
    # If a worker agent just finished, the last message in state is an AIMessage.
    if current_messages and current_messages[-1].type == "ai":
        # Inject a temporary human message to prompt the Supervisor for its next decision
        current_messages.append(
            HumanMessage(
                content="Evaluate the progress above. If the user's original request is completely resolved, output FINISH. Otherwise, route to the next appropriate agent."
            )
        )
        
    messages_to_send = [supervisor_prompt] + current_messages
    
    router_llm = llm.with_structured_output(RouteDecision)
    decision = await router_llm.ainvoke(messages_to_send)
    
    return {"next_node": decision.next_node}

# ==========================================
# 3. THE WORKER NODES
# ==========================================
sql_prompt = SystemMessage(
    content=(
        "You are the SQL Database Expert for NexusWorks.\n"
        "1. Never guess table names. Call 'get_schema' first if unsure.\n"
        "2. For mutations, use 'execute_write_query'."
    )
)

async def sql_agent_node(state: AgentState):
    messages_to_send = [sql_prompt] + list(state["messages"])
    
    # Inject a bridging HumanMessage if the General Agent spoke first
    if messages_to_send[-1].type == "ai":
        messages_to_send.append(
            HumanMessage(content="Please execute the necessary database actions for my request.")
        )
        
    response = await llm.bind_tools(all_tools).ainvoke(messages_to_send)
    return {"messages": [response]}
general_prompt = SystemMessage(
    content="You are a helpful conversational assistant for NexusWorks. Handle greetings and general chat without calling tools."
)

async def general_agent_node(state: AgentState):
    messages_to_send = [general_prompt] + list(state["messages"])
    
    # If the previous agent (like sql_agent) just answered, the history ends in an AIMessage.
    # Inject a bridging HumanMessage so Gemini accepts the request.
    if messages_to_send[-1].type == "ai":
        messages_to_send.append(
            HumanMessage(content="Please address any remaining conversational parts or greetings from my original request.")
        )
        
    response = await llm.ainvoke(messages_to_send)
    return {"messages": [response]}

def route_sql_tools(state: AgentState) -> Literal["read_tools", "write_tools", "supervisor"]:
    last_msg = state["messages"][-1]
    if getattr(last_msg, "tool_calls", None):
        first_tool = last_msg.tool_calls[0]["name"]
        if first_tool == "execute_write_query":
            return "write_tools"
        return "read_tools"
    return "supervisor"

builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("sql_agent", sql_agent_node)
builder.add_node("general_agent", general_agent_node)
builder.add_node("read_tools", ToolNode(read_tools))
builder.add_node("write_tools", ToolNode(write_tools))

builder.add_edge(START, "supervisor")

builder.add_conditional_edges("supervisor", lambda state: state["next_node"], {
    "sql_agent": "sql_agent",
    "general_agent": "general_agent",
    "FINISH": END
})
builder.add_conditional_edges("sql_agent", route_sql_tools)
builder.add_edge("read_tools", "sql_agent")
builder.add_edge("write_tools", "sql_agent")
builder.add_edge("general_agent", "supervisor")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["write_tools"])

# =====================================================================
# 5. Execution Entrypoint & UI State Translation
# =====================================================================

async def extract_ui_state(config, compiled_graph):
    """Extracts telemetry, final answers, and pause states for the React UI."""
    state = await compiled_graph.aget_state(config)
    is_interrupted = bool(state.next and "write_tools" in state.next)
    
    raw_messages = state.values.get("messages", [])
    if not isinstance(raw_messages, (list, tuple)):
        all_messages = [raw_messages]
    else:
        all_messages = list(raw_messages)
    
    # 1. ROBUST HUMAN MESSAGE DETECTION (Database Agnostic)
    last_human_idx = 0
    for i, msg in enumerate(all_messages):
        # Use .type instead of strict __class__.__name__
        if getattr(msg, "type", "") == "human" or msg.__class__.__name__ == "HumanMessage":
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
        # 2. ROBUST AI MESSAGE DETECTION (Multi-Agent Support)
        ai_responses = []
        # Iterate forward through the current turn to preserve chronological order
        for msg in current_turn_messages:
            is_ai = getattr(msg, "type", "") == "ai" or msg.__class__.__name__ == "AIMessage"
            
            # Only extract final text messages (ignore intermediate tool calls)
            if is_ai and not getattr(msg, "tool_calls", None):
                content = getattr(msg, "content", "")
                text_content = ""
                
                if isinstance(content, list):
                    text_content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
                else:
                    text_content = str(content)
                
                if text_content.strip():
                    ai_responses.append(text_content.strip())
                    
        # Stitch multiple agent responses together cleanly
        final_answer = "\n\n---\n\n".join(ai_responses)

    # 3. ROBUST TOKEN EXTRACTION
    input_tokens = 0
    output_tokens = 0
    
    for m in current_turn_messages:
        # Check both LangChain v0.2 usage_metadata and legacy response_metadata
        usage = getattr(m, "usage_metadata", {}) or {}
        resp_meta = getattr(m, "response_metadata", {}) or {}
        
        if usage:
            input_tokens += usage.get("input_tokens", 0)
            output_tokens += usage.get("output_tokens", 0)
        elif resp_meta and "token_usage" in resp_meta:
            input_tokens += resp_meta["token_usage"].get("prompt_tokens", 0)
            output_tokens += resp_meta["token_usage"].get("completion_tokens", 0)

    total_tokens = input_tokens + output_tokens

    return {
        "final_answer": final_answer,
        "requires_approval": requires_approval,
        "telemetry": {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens},
    }

async def run_langgraph_agent(
    user_query: str, 
    session_id: str, 
    memory: BaseCheckpointSaver
) -> Dict[str, Any]:
    
    graph = builder.compile(checkpointer=memory, interrupt_before=["write_tools"])
    config = {"configurable": {"thread_id": session_id}}
    
    await graph.ainvoke({"messages": [("user", user_query)]}, config=config)
    
    return await extract_ui_state(config, graph)

async def resume_langgraph_agent(
    session_id: str, 
    action: Literal["approve", "reject"], 
    memory: BaseCheckpointSaver
) -> Dict[str, Any]:
    
    graph = builder.compile(checkpointer=memory, interrupt_before=["write_tools"])
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
        
    return await extract_ui_state(config, graph)


async def stream_langgraph_agent(
    user_query: str, 
    session_id: str, 
    memory: BaseCheckpointSaver
):
    graph = builder.compile(checkpointer=memory, interrupt_before=["write_tools"])
    config = {"configurable": {"thread_id": session_id}}
    
    # Send initial connection status
    yield f"data: {json.dumps({'type': 'status', 'node': 'system', 'message': 'Initializing AgentLab environment...'})}\n\n"

    # Stream the graph step-by-step
    async for chunk in graph.astream({"messages": [("user", user_query)]}, config=config, stream_mode="updates"):
        
        # 'chunk' is a dictionary where the key is the name of the node that just finished
        for node_name, node_state in chunk.items():
            
            if node_name == "supervisor":
                next_node = node_state.get("next_node")
                if next_node == "sql_agent":
                    msg = "Supervisor analyzing intent... Routing to SQL Database Expert."
                elif next_node == "general_agent":
                    msg = "Supervisor analyzing intent... Routing to Conversational Agent."
                else:
                    msg = "Supervisor finished routing."
                yield f"data: {json.dumps({'type': 'status', 'node': node_name, 'message': msg})}\n\n"

            elif node_name == "sql_agent":
                yield f"data: {json.dumps({'type': 'status', 'node': node_name, 'message': 'SQL Agent is constructing and evaluating query...'})}\n\n"

            elif node_name == "general_agent":
                yield f"data: {json.dumps({'type': 'status', 'node': node_name, 'message': 'Conversational Agent is drafting response...'})}\n\n"

            elif node_name == "read_tools":
                yield f"data: {json.dumps({'type': 'status', 'node': node_name, 'message': 'Executing secure database read operation...'})}\n\n"

    # Once the stream is complete, extract the final state for the UI to render
    final_state = await extract_ui_state(config, graph)
    
    # Send the final result payload
    yield f"data: {json.dumps({'type': 'result', 'data': final_state})}\n\n"
    
    # Close the SSE connection
    yield "data: [DONE]\n\n"