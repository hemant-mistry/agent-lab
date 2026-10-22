import json
from typing import Any
from app.services.supabase import supabase_service
from app.tools.base import Tool


class SQLTool(Tool):

    @property
    def name(self) -> str:
        return "execute_sql"

    @property
    def description(self) -> str:
        return (
            "Executes a read-only SQL SELECT query "
            "against the NexusWorks database."
        )

    async def execute(self, arguments: dict[str, Any]) -> str:
        query = arguments.get("query")

        if not query:
            return "Error: SQL query is required."

        # Clean trailing whitespace and semicolons
        query = query.strip().rstrip(";").strip()

        if not query.lower().startswith("select"):
            return "Error: Only SELECT queries are allowed."

        try:
            result = (
                supabase_service.client
                .rpc("execute_readonly_query", {"query_text": query})
                .execute()
            )
            return json.dumps(result.data)
        except Exception as e:
            # Return the error as text so the agent can self-correct its SQL
            return f"SQL Execution Error: {str(e)}. Please call get_schema to verify exact table and column names, then try again."