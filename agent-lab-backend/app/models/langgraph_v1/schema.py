from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal

class RunRequest(BaseModel):
    experiment_id: str
    query: str
    session_id: str = "default-session"
    use_router: bool = True

class ResumeRequest(BaseModel):
    experiment_id: str
    session_id: str
    action: str

class Step(BaseModel):
    step_number: int
    type: str 
    title: str
    content: Any

class RunResponse(BaseModel):
    experiment_id: str
    query: str
    final_answer: str
    steps: List[Step]
    latency_ms: float
    telemetry: Optional[Dict[str, int]] = None

class IntentClassification(BaseModel):
    intent: Literal["sql_data_request", "general_chat", "off_topic"] = Field(
        description="Classify the user's intent into one of the exact literal categories."
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0"
    )

class SQLReadInput(BaseModel):
    query: str = Field(description="A valid, read-only PostgreSQL SELECT query.")

    @field_validator("query")
    @classmethod
    def validate_readonly(cls, v:str) -> str:
        cleaned = v.strip().rstrip(";").strip()
        if not cleaned.lower().startswith("select"):
            raise ValueError("Guardrail Error: Only SELECT queries permitted here.")
        return cleaned
    
class SQLWriteInput(BaseModel):
    query: str = Field(description="A valid PostgreSQL UPDATE, DELETE, or INSERT query.")
    justification: str = Field(description="Business justification for this mutation.")

    @field_validator("query")
    @classmethod
    def validate_write(cls, v: str) -> str:
        cleaned = v.strip().rstrip(";").strip()
        if cleaned.lower().startswith("select"):
            raise ValueError("Guardrail Error: Use execute_read_query for SELECTs.")
        return cleaned

class RouteQuery(BaseModel):
    """Classifies the user query to determine the required execution path."""
    intent: Literal["general_chat", "sql_data_request", "off_topic"] = Field(
        description="The category of the user's query."
    )
    reasoning: str = Field(
        description="Brief 1-sentence explanation for why this intent was chosen."
    )