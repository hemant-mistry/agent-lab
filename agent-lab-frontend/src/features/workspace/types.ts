export interface Step {
  step_number: number;
  type: string;
  title: string;
  content: any; 
}

export interface RunResult {
  experiment_id: string;
  query: string;
  final_answer: string;
  steps: Step[];
  latency_ms: number;
}

// Add this new interface
export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  steps?: Step[];
  latency_ms?: number;
}