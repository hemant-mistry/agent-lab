import React, { useState } from "react";
import { EXPERIMENTS } from "../../config/experiments";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input"

interface RunFormProps {
  onRun: (experimentId: string, query: string) => void;
  isLoading: boolean;
}

export function RunForm({ onRun, isLoading }: RunFormProps) {
  const [query, setQuery] = useState(
    "Which 3 projects have the highest actual spend, and who are the customers for those projects?"
  );
  const [experimentId, setExperimentId] = useState(EXPERIMENTS[0]?.id || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && experimentId) {
      onRun(experimentId, query);
    }
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      className="p-5 bg-zinc-900/50 border border-zinc-800 rounded-xl space-y-4 backdrop-blur-sm"
    >
      <div className="flex flex-col md:flex-row items-center gap-4">
        {/* Architecture Dropdown */}
        <div className="w-full md:w-1/3">
          <label className="block text-xs font-medium text-zinc-400 mb-1.5">
            Architecture
          </label>
          {/* Using a Tailwind-styled native select since Shadcn 'Select' isn't in your UI folder yet */}
          <select
            value={experimentId}
            onChange={(e) => setExperimentId(e.target.value)}
            className="flex h-9 w-full items-center justify-between rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {EXPERIMENTS.map((exp) => (
              <option key={exp.id} value={exp.id} disabled={exp.disabled} className="bg-zinc-950">
                {exp.name}
              </option>
            ))}
          </select>
        </div>
        
        {/* Prompt Input */}
        <div className="w-full md:flex-1">
          <label className="block text-xs font-medium text-zinc-400 mb-1.5">
            Query Prompt
          </label>
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about projects, spend, tickets..."
            className="bg-zinc-950 border-zinc-800 text-zinc-200 focus-visible:ring-zinc-700 h-9"
          />
        </div>
      </div>

      <div className="flex justify-end pt-2 border-t border-zinc-800/50 mt-4">
        <Button
          type="submit"
          disabled={isLoading}
          variant="secondary"
          className="bg-zinc-100 text-zinc-900 hover:bg-zinc-200"
        >
          {isLoading ? "Running Agent..." : "Run Experiment"}
        </Button>
      </div>
    </form>
  );
}