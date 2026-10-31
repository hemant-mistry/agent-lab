export interface Step {
  step_number: number;
  type: string;
  title: string;
  content: any;
}

// 1. Define the Telemetry object structure
export interface Telemetry {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  llm_calls?: number;
}

export interface RunResult {
  experiment_id: string;
  query: string;
  final_answer: string;
  steps: Step[];
  latency_ms: number;
  telemetry?: Telemetry;
  requires_approval?:boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  steps?: Step[];
  latency_ms?: number;
  telemetry?: Telemetry; 
  requires_approval?:boolean;
}