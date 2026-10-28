import type { RunResult } from "../features/workspace/types";

const API_BASE_URL = "http://localhost:8000/api";

export const AgentAPI = {
  async executeRun(
    experimentId: string,
    query: string,
    sessionId: string = "default-session",
    useRouter: boolean = true
  ): Promise<RunResult> {
    const response = await fetch(`${API_BASE_URL}/runs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        experiment_id: experimentId,
        query: query,
        session_id: sessionId,
        use_router: useRouter,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    return response.json();
  },
};