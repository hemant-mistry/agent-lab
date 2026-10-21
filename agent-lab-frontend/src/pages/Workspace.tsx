import { useState } from "react";
import { RunForm } from "../features/workspace/RunForm";
import { TraceViewer } from "../features/workspace/TraceViewer";
import { FinalAnswerCard } from "../features/workspace/FinalAnswerCard";
import { AgentAPI } from "../services/api";
import type { RunResult } from "../features/workspace/types";

export default function Workspace() {
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async (experimentId: string, query: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await AgentAPI.executeRun(experimentId, query);
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 p-6 md:p-10 text-zinc-100 min-h-screen">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">
            Experiment Console
          </h1>
          <p className="text-sm text-zinc-400 mt-2">
            Execute queries across pluggable agent architectures and trace intermediate tool states.
          </p>
        </div>

        {/* Input Section */}
        <RunForm onRun={handleRun} isLoading={loading} />
        
        {/* Error Handling */}
        {error && (
          <div className="p-4 bg-red-950/40 border border-red-900/50 text-red-300 text-sm rounded-xl">
            {error}
          </div>
        )}
        
        {/* Results Section */}
        {result && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <FinalAnswerCard answer={result.final_answer} latency={result.latency_ms} />
            <TraceViewer steps={result.steps} />
          </div>
        )}

      </div>
    </div>
  );
}