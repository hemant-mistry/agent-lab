from typing import Dict, Any, List
from app.tools.base import Tool
from app.tools.schema_tool import SchemaTool
from app.tools.sql_tool import SQLTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self.register(SchemaTool())
        self.register(SQLTool())

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name} already registered.")
        self._tools[tool.name]=tool

    def get(self, name:str)-> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found.")
        return self._tools[name]

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns OpenAI-compatible function schemas for the LLM."""
        schemas = []
        for tool in self._tools.values():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
            # Dynamically inject required parameters
            if tool.name == "execute_sql":
                schema["function"]["parameters"]["properties"] = {
                    "query": {
                        "type": "string",
                        "description": "The read-only SQL query to execute."
                    }
                }
                schema["function"]["parameters"]["required"] = ["query"]
            
            schemas.append(schema)
        return schemas

tool_registry = ToolRegistry()