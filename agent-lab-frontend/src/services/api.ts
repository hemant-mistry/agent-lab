import type { RunResult } from "../features/workspace/types";

const API_BASE_URL = "http://localhost:8000/api";

export const AgentAPI = {
  async executeRun(
    experimentId: string,
    query: string,
    sessionId: string = "default-session",
    useRouter: boolean = true,
    onStatus?: (message: string) => void // Added optional callback for UI updates
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

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Streaming is not supported by your browser.");
    }

    const decoder = new TextDecoder("utf-8");
    let finalResult: RunResult | null = null;
    let buffer = ""; // Buffer to handle chunks that get split across TCP packets

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      
      // Pop the last element (which might be an incomplete JSON string) back into the buffer
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        if (chunk.startsWith("data: ")) {
          const dataStr = chunk.replace("data: ", "").trim();
          
          if (dataStr === "[DONE]") {
            break;
          }

          try {
            const payload = JSON.parse(dataStr);
            if (payload.type === "status" && onStatus) {
              onStatus(payload.message); // Trigger React state update
            } else if (payload.type === "result") {
              finalResult = payload.data;
            }
          } catch (e) {
            console.error("Error parsing stream chunk:", e);
          }
        }
      }
    }

    if (!finalResult) {
      throw new Error("Stream finished without returning the final result.");
    }

    return finalResult;
  },

  async resumeRun(
    experimentId: string,
    sessionId: string,
    action: "approve" | "reject"
  ): Promise<RunResult> {
    // Keeping resumeRun as a standard JSON fetch since the backend /runs/resume 
    // endpoint was not converted to SSE in the previous step.
    const response = await fetch(`${API_BASE_URL}/runs/resume`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        experiment_id: experimentId,
        session_id: sessionId,
        action: action,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    return response.json();
  },
};