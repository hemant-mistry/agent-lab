from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from pydantic import BaseModel, Field, field_validator
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any, Callable, Dict
from app.core.config import settings
from app.tools.schema_tool import SchemaTool
from app.tools.sql_tool import SQLTool

schema_tool_instance = SchemaTool()
sql_tool_instance = SQLTool()


# ARGS - acts like guardrails
class SQLQueryInput(BaseModel):
    query: str = Field(
        description= "A valid, read-only PostgreSQL SELECT query to run against NexusWorks"
    )

    @field_validator("query")
    @classmethod
    def validate_readonly_select(cls, v:str) -> str:
        cleaned = v.strip().rstrip(";").strip()
        if not cleaned.lower().startswith("select"):
            raise ValueError("Guardrail Error: Only read-only SELECT queries are permitted.")


        forbidden = {"drop", "delete", "update", "insert", "alter", "truncate"}
        tokens = set(cleaned.lower().split())
        if tokens.intersection(forbidden):
            raise ValueError(
                f"Guardrail Error: Query contains forbidden keywords: {tokens.intersection(forbidden)}"
            )
        return cleaned
    
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

system_message = SystemMessage(content=(
    "You are an AI data assistant for NexusWorks. "
    "You have access to a PostgreSQL database. "
    "CRITICAL RULE: You MUST call 'get_schema' as your very first step on every request before writing any SQL. "
    "Never guess or assume column names (such as 'status' or 'id'). "
    "If 'execute_sql' returns an error, read the error message, check the schema, and run a corrected SQL query."
))

memory_checkpointer = InMemorySaver()

agent_executor = create_agent(
    model = llm,
    tools = tools,
    system_prompt=system_message,
    middleware=[graceful_tool_error_middleware],
    checkpointer=memory_checkpointer
)

async def run_langchain_agent(
    user_query: str,
    session_id: str = "default-session",
) -> Dict[str, Any]:
    config = {
        "configurable": {"thread_id": session_id},
    }

    # Inspect prior thread state to isolate new messages generated this turn
    prior_state = await agent_executor.aget_state(config)
    prior_messages = prior_state.values.get("messages", []) if prior_state and prior_state.values else []
    prior_count = len(prior_messages)

    final_state = await agent_executor.ainvoke(
        {"messages": [("user", user_query)]},
        config=config,
    )

    all_messages = final_state.get("messages", [])
    new_messages = all_messages[prior_count:]

    # Extract token usage metadata natively from response messages if available
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