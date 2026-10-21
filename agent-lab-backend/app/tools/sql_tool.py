from typing import Any
from app.services.supabase import supabase_service
from app.tools.base import Tool

class SQLTool(Tool):

    @property
    def name(self)->str:
        return "execute_sql"

    @property
    def description(self)->str:
        return (
            "Executes a read-only SQL SELECT query "
            "against the NexusWorks database."
        )

    async def execute(self, arguments: dict[str, Any])->Any:
        query = arguments.get("query")

        if not query:
            raise ValueError("SQL query is required")

        query = query.strip().rstrip(";").strip()

        if not query.strip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed")

        result = (
            supabase_service.client
            .rpc(
                "execute_readonly_query",
                {"query_text": query}
            )
            .execute()
        )

        return result.data