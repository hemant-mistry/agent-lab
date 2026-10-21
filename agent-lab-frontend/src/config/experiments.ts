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
    description: "Standard LangGraph ReAct implementation.",
    disabled: false,
  },
]

