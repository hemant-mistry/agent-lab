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

        is_select = query.lower().startswith("select")

        try:
            if is_select:
                result = (
                    supabase_service.client
                    .rpc("execute_readonly_query", {"query_text": query})
                    .execute()
                )
                return json.dumps(result.data) if result.data is not None else "[]"
            else:
                result = (
                    supabase_service.client
                    .rpc("execute_sql", {"query_text": query})
                    .execute()
                )
                return f"Success: Mutation query executed successfully. Affected rows/data: {json.dumps(result.data)}"
        except Exception as e:
            
            return f"SQL Execution Error: {str(e)}. Please check the database function or schema."