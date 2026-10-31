export interface ExperimentConfig {
    id: string;
    name: string;
    description: string;
    disabled: boolean;
}

export const EXPERIMENTS: ExperimentConfig[] = [
    {
    id: "langchain-v1",
    name: "LangChain (Gemini 3.6 Flash)",
    description: "LangChain 1.x (Router + Middleware)",
    disabled: false,
  },
  {
    id: "langgraph-v1",
    name: "LangGraph (Stateful ReAct)",
    description:"Standard LangGraph (Stateful ReAct)",
    disabled: false,
  }
]

