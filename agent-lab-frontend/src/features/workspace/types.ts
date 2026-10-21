export interface Step {
  step_number: number;
  type: "user" | "tool_call" | "tool_result" | "final_answer" | string;
  title: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  content: any; 
}

export interface RunResult {
  experiment_id: string;
  query: string;
  final_answer: string;
  steps: Step[];
  latency_ms: number;
}