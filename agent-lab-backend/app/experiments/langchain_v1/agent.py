from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langchain.agents import create_agent

from app.core.config import settings
from app.tools.schema_tool import SchemaTool
from app.tools.sql_tool import SQLTool

schema_tool_instance = SchemaTool()
sql_tool_instance = SQLTool()

@tool
async def get_schema() -> str:
    """Returns the NexusWorks database schema, including tables, columns and relationships."""
    return await schema_tool_instance.execute({})

@tool
async def execute_sql(query: str) -> str:
    """Executes a read-only SQL SELECT query against the NexusWorks database."""
    return await sql_tool_instance.execute({"query": query})

tools = [get_schema, execute_sql]

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

agent_executor = create_agent(
    model = llm,
    tools = tools,
    system_prompt=system_message
)

async def run_langchain_agent(user_query: str) -> dict:
    """
    Runs the agent and returns the final state.
    """
    inputs = {"messages": [("user", user_query)]}
    final_state = await agent_executor.ainvoke(inputs)
    return final_state