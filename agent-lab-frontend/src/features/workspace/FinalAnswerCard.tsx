import { Separator } from "../../components/ui/separator";

interface FinalAnswerCardProps {
  answer: string;
  latency: number;
}

export function FinalAnswerCard({ answer, latency }: FinalAnswerCardProps) {
  return (
    <div className="p-5 bg-zinc-900/50 border border-zinc-800 rounded-xl backdrop-blur-sm">
      <div className="flex items-center justify-between pb-4">
        <span className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
          Final Answer
        </span>
        <span className="text-xs text-zinc-400 font-mono">
          {latency} ms
        </span>
      </div>
      
      <Separator className="bg-zinc-800/60 mb-4" />
      
      <div className="text-sm leading-relaxed whitespace-pre-wrap text-zinc-200">
        {answer}
      </div>
    </div>
  );
}