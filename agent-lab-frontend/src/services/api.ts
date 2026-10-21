import type { RunResult } from "../features/workspace/types";

const API_BASE = "http://localhost:8000/api";

export const AgentAPI = {
  executeRun: async (experimentId: string, query: string): Promise<RunResult> => {
    const response = await fetch(`${API_BASE}/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ experiment_id: experimentId, query }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Run failed");
    }

    return response.json();
  }
};