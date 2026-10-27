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

schema_tool_instance = SchemaTool()
sql_tool_instance = SQLTool()


class IntentClassification(BaseModel):
    intent: Literal["sql_data_request", "general_chat", "off_topic"] = Field(
        description="Classify the user's intent into one of the exact literal categories."
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0"
    )

 # Fast LCEL Classifier Chain
classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an intent classifier for the NexusWorks database agent.\n"
     "Categories:\n"
     "- 'sql_data_request': Any question about projects, spend, customers, status, or data analysis.\n"
     "- 'general_chat': Greetings, pleasantries (e.g., 'hello', 'how are you', 'who are you').\n"
     "- 'off_topic': Unrelated questions (e.g., recipes, history, general coding unrelated to the DB)."
    ),
    ("human", "{query}")
])   

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
intent_chain = classifier_prompt | llm.with_structured_output(IntentClassification)

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
) -> Dict[str, Any]:
    
    # --- ROUTING PHASE ---
    # 1. Classify the user's intent using our LCEL structured output chain
    classification: IntentClassification = await intent_chain.ainvoke({"query": user_query})
    
    # 2. Handle Off-Topic (Zero-shot static rejection, extremely fast and cheap)
    if classification.intent == "off_topic":
        blocked_msg = AIMessage(content="I am a specialized data agent for NexusWorks. I can only assist with database queries, project metrics, and financial reporting. How can I help you with your data today?")
        return {
            "messages": [blocked_msg],
            "telemetry": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        }
        
    # 3. Handle General Chat (Fast LCEL LLM pipe, no tool overhead)
    elif classification.intent == "general_chat":
        chat_response: AIMessage = await fast_chat_chain.ainvoke({"query": user_query})
        return {
            "messages": [chat_response],
            "telemetry": extract_tokens(chat_response)
        }

    # --- SQL AGENT PHASE ---
    # 4. Handle SQL Data Requests (Full agent loop)
    config = {"configurable": {"thread_id": session_id}}

    prior_state = await agent_executor.aget_state(config)
    prior_messages = prior_state.values.get("messages", []) if prior_state and prior_state.values else []
    prior_count = len(prior_messages)

    final_state = await agent_executor.ainvoke(
        {"messages": [("user", user_query)]},
        config=config,
    )

    new_messages = final_state.get("messages", [])[prior_count:]

    # Aggregate telemetry for the multi-step loop
    t_in, t_out, t_tot = 0, 0, 0
    for msg in new_messages:
        tokens = extract_tokens(msg)
        t_in += tokens["input_tokens"]
        t_out += tokens["output_tokens"]
        t_tot += tokens["total_tokens"]

    return {
        "messages": new_messages,
        "telemetry": {
            "input_tokens": t_in,
            "output_tokens": t_out,
            "total_tokens": t_tot,
        },
    }