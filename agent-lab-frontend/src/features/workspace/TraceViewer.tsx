import type { Step } from "./types";

interface TraceViewerProps {
  steps: Step[];
}

export function TraceViewer({ steps }: TraceViewerProps) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="mt-8">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-4">
        Execution Trace ({steps.length} Steps)
      </h2>
      
      <div className="space-y-4">
        {steps.map((step) => (
          <div
            key={step.step_number}
            className="p-4 bg-zinc-900/30 border border-zinc-800/80 rounded-lg text-sm space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="px-2 py-1 rounded-md bg-zinc-800 text-zinc-300 text-xs font-mono">
                  Step {step.step_number}
                </span>
                <span className={`font-medium ${step.type === "tool_call" ? "text-amber-400" : "text-blue-400"}`}>
                  {step.title}
                </span>
              </div>
            </div>

            <div className="bg-zinc-950/80 p-3 rounded-md border border-zinc-800/50 overflow-x-auto text-zinc-300 font-mono text-xs">
              {typeof step.content === "object" ? (
                <pre>{JSON.stringify(step.content, null, 2)}</pre>
              ) : (
                <pre className="whitespace-pre-wrap">{step.content}</pre>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}