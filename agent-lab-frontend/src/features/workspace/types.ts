export interface Step {
  step_number: number;
  type: string;
  title: string;
  content: any;
}

export interface Telemetry {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  llm_calls?: number;
}

export interface RunResult {
  final_answer: string;
  
  // Fallback fields for LCEL compatibility
  answer?: string;
  content?: string;
  output?: string;
  result?: string;
  
  requires_approval?: boolean;
  steps?: any[];
  latency_ms?: number;
  telemetry?: Telemetry;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  content: string;
  steps?: Step[];
  latency_ms?: number;
  telemetry?: Telemetry; 
  requires_approval?: boolean;
}