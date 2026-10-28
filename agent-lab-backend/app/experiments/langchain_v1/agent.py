from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any, Callable, Dict, Literal
from app.core.config import settings
from app.tools.schema_tool import SchemaTool
from app.tools.sql_tool import SQLTool
from app.models.langchain_v1.schema import SQLQueryInput, IntentClassification
from app.models.langchain_v1.schema import RouteQuery

schema_tool_instance = SchemaTool()
sql_tool_instance = SQLTool()


router_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a strict intent classification router for a database AI. "
     "You MUST accurately classify the user's intent based on these rules:\n"
     "- 'general_chat': The user is making small talk, saying hello, or asking how you are (e.g., 'hey', 'hi', 'hello').\n"
     "- 'off_topic': The user is asking for general knowledge, coding help, or anything unrelated to the database.\n"
     "- 'sql_data_request': The user is specifically asking for data, metrics, projects, invoices, or database analysis.\n\n"
     "CRITICAL: If the user just says 'hey' or 'hello', you MUST classify it as 'general_chat'."
    ),
    ("human", "{query}")
])

@tool
async def get_schema() -> str:
    """Returns the NexusWorks database schema, including tables, columns and relationships."""
    return await schema_tool_instance.execute({})

@tool("execute_sql", args_schema=SQLQueryInput)
async def execute_sql(query: str) -> str:
    """Executes a read-only SQL SELECT query against the NexusWorks database."""
    return await sql_tool_instance.execute({"query": query})

tools = [get_schema, execute_sql]

@wrap_tool_call
async def graceful_tool_error_middleware(request:Any, handler:Callable) -> Any:
    """
    Intercepts tool execution. If a tool fails (validation or database error),
    returns a ToolMessage observation so the LLM can self-heal.
    """
    try:
        return await handler(request)
    except Exception as exc:
        tool_call = getattr(request, "tool_call", {}) or {}
        tool_name = tool_call.get("name", "unknown_tool")
        tool_id = tool_call.get("id", "error_id")
        return ToolMessage(
            content = (
                f"Tool '{tool_name}' failed with error: {str(exc)}. "
                "Please verify the schema using 'get_schema' and adjust your query."
            ),
            name=tool_name,
            tool_call_id = tool_id
        )

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    api_key=settings.GOOGLE_API_KEY
)

system_message = SystemMessage(
    content=(
        "You are an enterprise AI data analyst for NexusWorks.\n"
        "You have access to a PostgreSQL database.\n"
        "CRITICAL RULES:\n"
        "1. If you have not yet inspected the schema in this thread, call 'get_schema' first before calling 'execute_sql'.\n"
        "2. Never guess table or column names.\n"
        "3. If 'execute_sql' returns an error, read it, check the schema, and run a corrected query."
    )
)

# Attach structured output to our classifier chain
classifier_chain = router_prompt | llm.with_structured_output(RouteQuery, include_raw=True)

fast_chat_chain = ChatPromptTemplate.from_template(
    "You are AgentLab, a helpful database assistant for NexusWorks. "
    "Respond warmly and briefly to this user message: {query}"
) | llm


memory_checkpointer = InMemorySaver()

agent_executor = create_agent(
    model = llm,
    tools = tools,
    system_prompt=system_message,
    middleware=[graceful_tool_error_middleware],
    checkpointer=memory_checkpointer
)


def extract_tokens(message: Any) -> Dict[str, int]:
    """Helper to extract token counts from an AIMessage."""
    usage = getattr(message, "usage_metadata", None)
    if usage and isinstance(usage, dict):
        return {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

async def run_langchain_agent(
    user_query: str,
    session_id: str = "default-session",
    use_router: bool = True,
) -> Dict[str, Any]:

    if use_router:
        try:
            result = await classifier_chain.ainvoke({"query": user_query})
            classification = result.get("parsed")
            raw_msg = result.get("raw")
            
            r_usage = getattr(raw_msg, "usage_metadata", {}) or {}
            r_in = r_usage.get("input_tokens", 0)
            r_out = r_usage.get("output_tokens", 0)
            r_total = r_usage.get("total_tokens", 0)

            if classification:
                print(f"[LCEL Router] Intent: {classification.intent} | Reasoning: {classification.reasoning}")

                # Format the router's thought process for the UI
                router_trace_step = {
                    "type": "tool_call",
                    "title": "LCEL Semantic Router",
                    "content": {
                        "action": "bypassed_heavy_agent_loop",
                        "intent": classification.intent,
                        "reasoning": classification.reasoning
                    }
                }

                if classification.intent == "off_topic":
                    msg = AIMessage(content="I can only assist with NexusWorks database queries, projects, and invoices. How can I help you with your data today?")
                    return {
                        "messages": [msg],
                        "steps": [router_trace_step],
                        "telemetry": {"input_tokens": r_in, "output_tokens": r_out, "total_tokens": r_total},
                    }

                if classification.intent == "general_chat":
                    msg = AIMessage(content="Hello! I'm the NexusWorks data agent. I'm here to help you query your database and analyze projects. What would you like to know?")
                    return {
                        "messages": [msg],
                        "steps": [router_trace_step],
                        "telemetry": {"input_tokens": r_in, "output_tokens": r_out, "total_tokens": r_total},
                    }
        except Exception as e:
            print(f"[LCEL Router Error] Falling back to heavy agent. Error: {e}")


    config = {"configurable": {"thread_id": session_id}}

    prior_state = await agent_executor.aget_state(config)
    prior_messages = prior_state.values.get("messages", []) if prior_state and prior_state.values else []
    prior_count = len(prior_messages)

    final_state = await agent_executor.ainvoke(
        {"messages": [("user", user_query)]},
        config=config,
    )

    all_messages = final_state.get("messages", [])
    new_messages = all_messages[prior_count:]

    input_tokens = 0
    output_tokens = 0
    total_tokens = 0

    for msg in new_messages:
        usage = getattr(msg, "usage_metadata", None)
        if usage and isinstance(usage, dict):
            input_tokens += usage.get("input_tokens", 0)
            output_tokens += usage.get("output_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)

    return {
        "messages": new_messages,
        "telemetry": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        },
    }