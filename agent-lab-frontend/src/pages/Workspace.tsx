import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, Code2, Sparkles, TerminalSquare } from "lucide-react";
import { EXPERIMENTS } from "../config/experiments";
import { AgentAPI } from "../services/api";
import type { ChatMessage } from "../features/workspace/types";

import { Button } from "../components/ui/button";
import { 
  MessageScrollerProvider,
  MessageScroller, 
  MessageScrollerItem 
} from "../components/ui/message-scroller";

export default function Workspace() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [experimentId, setExperimentId] = useState(EXPERIMENTS[0]?.id || "");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    setInput(""); 
    
    const newUserMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: userQuery,
    };
    setMessages((prev) => [...prev, newUserMsg]);
    
    setIsLoading(true);

    try {
      const data = await AgentAPI.executeRun(experimentId, userQuery);
      
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.final_answer,
        steps: data.steps,
        latency_ms: data.latency_ms,
      };
      
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "error",
        content: err.message || "An error occurred during execution.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] bg-zinc-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.1),rgba(255,255,255,0))] text-zinc-100 font-sans">
      
      {/* HEADER */}
      <header className="flex-none px-6 py-4 border-b border-white/5 bg-zinc-950/50 backdrop-blur-xl flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shadow-sm">
            <TerminalSquare size={18} className="text-zinc-300" />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-zinc-100">Agent Console</h1>
            <p className="text-[11px] text-zinc-500 font-mono mt-0.5">environment: nexus-works</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3 bg-zinc-900/50 p-1.5 rounded-lg border border-white/5">
          <label className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider pl-2">Engine</label>
          <select
            value={experimentId}
            onChange={(e) => setExperimentId(e.target.value)}
            className="h-7 rounded-md border-none bg-zinc-800 px-3 py-0.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-zinc-600 cursor-pointer"
          >
            {EXPERIMENTS.map((exp) => (
              <option key={exp.id} value={exp.id} disabled={exp.disabled}>
                {exp.name}
              </option>
            ))}
          </select>
        </div>
      </header>

      {/* CHAT THREAD: Added custom dark scrollbar classes (replace with 'no-scrollbar' to hide completely) */}
      <MessageScrollerProvider autoScroll>
        <MessageScroller className="flex-1 px-4 md:px-8 pt-8 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-zinc-800 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-zinc-700">
          
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center space-y-6 max-w-sm mx-auto text-center mt-[-10vh] animate-in fade-in duration-1000">
              <div className="relative">
                <div className="absolute -inset-6 bg-emerald-500/20 blur-3xl rounded-full"></div>
                <div className="h-20 w-20 rounded-3xl bg-zinc-900/80 backdrop-blur-sm border border-white/10 flex items-center justify-center relative shadow-2xl">
                  <Sparkles size={32} className="text-emerald-400/80" />
                </div>
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-zinc-200 tracking-tight">Ready for analysis</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">
                  Enter a natural language query below. The agent will autonomously write and execute SQL against the database.
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto w-full pb-4 flex flex-col gap-6">
              {messages.map((msg) => (
                <MessageScrollerItem 
                  key={msg.id} 
                  messageId={msg.id} 
                  scrollAnchor={msg.role === "user"}
                  className="w-full animate-in slide-in-from-bottom-2 fade-in duration-300"
                >
                  <div className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    
                    {/* USER TURN (Right) */}
                    {msg.role === "user" ? (
                      <div className="max-w-[85%] md:max-w-[75%] bg-zinc-100 text-zinc-900 shadow-sm shadow-black/20 font-medium text-[15px] px-5 py-3 rounded-2xl rounded-tr-sm break-words">
                        {msg.content}
                      </div>
                    ) : (
                      
                      /* AGENT TURN (Left) */
                      <div className="flex flex-col gap-2 w-full max-w-[95%] md:max-w-[85%]">
                        <div className="flex items-center gap-3 mb-1">
                           <div className="h-7 w-7 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-inner">
                             <Bot size={14} className={msg.role === "error" ? "text-red-400" : "text-emerald-400"} />
                           </div>
                           <span className="text-[13px] font-semibold text-zinc-200">
                              {msg.role === "error" ? "System Alert" : "AgentLab"}
                           </span>
                           {msg.latency_ms && (
                              <span className="text-[11px] font-mono text-zinc-500 bg-white/5 px-2 py-0.5 rounded-md border border-white/5 shadow-sm">
                                {msg.latency_ms}ms
                              </span>
                           )}
                        </div>

                        <div className={`text-[15px] leading-relaxed whitespace-pre-wrap ml-10 break-words ${msg.role === "error" ? "text-red-400" : "text-zinc-300"}`}>
                          {msg.content}
                        </div>

                        {/* Execution Trace */}
                        {msg.steps && msg.steps.length > 0 && (
                          <details className="mt-4 ml-10 text-xs bg-[#0c0c0e] border border-white/10 rounded-xl overflow-hidden group shadow-lg">
                            <summary className="flex items-center gap-2 p-3 text-zinc-400 font-mono cursor-pointer hover:bg-white/5 transition-colors select-none">
                               <Code2 size={14} className="text-amber-400/80" />
                               <span>[Execution Trace]</span>
                               <span className="text-zinc-600 ml-auto">{msg.steps.length} ops</span>
                            </summary>
                            <div className="p-4 border-t border-white/5 space-y-4 bg-[#0c0c0e]/50">
                              {msg.steps.map((step) => (
                                <div key={step.step_number} className="font-mono">
                                  <div className="mb-2 flex items-center gap-2">
                                     <span className="bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded text-[10px]">Step {step.step_number}</span>
                                     <span className={step.type === "tool_call" ? "text-amber-400" : "text-blue-400"}>{step.title}</span>
                                  </div>
                                  <pre className="p-3 bg-black/40 rounded-lg border border-white/5 overflow-x-auto text-zinc-400 whitespace-pre-wrap leading-relaxed shadow-inner">
                                    {typeof step.content === "object" ? JSON.stringify(step.content, null, 2) : step.content}
                                  </pre>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    )}
                  </div>
                </MessageScrollerItem>
              ))}

              {/* TYPING INDICATOR BUBBLE */}
              {isLoading && (
                <MessageScrollerItem 
                  messageId="loading" 
                  scrollAnchor={true} 
                  className="w-full animate-in fade-in slide-in-from-bottom-2 duration-300"
                >
                  <div className="flex w-full justify-start">
                    <div className="flex flex-col gap-2 w-full max-w-[90%]">
                      <div className="flex items-center gap-3 mb-1">
                         <div className="h-7 w-7 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-inner">
                           <Bot size={14} className="text-emerald-400" />
                         </div>
                         <span className="text-[13px] font-semibold text-zinc-200">
                            AgentLab
                         </span>
                      </div>
                      <div className="ml-10 bg-zinc-900/50 border border-white/5 w-fit px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm">
                        <div className="flex items-center gap-1.5 h-3">
                          <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '0ms' }}></span>
                          <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                          <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </div>
                      </div>
                    </div>
                  </div>
                </MessageScrollerItem>
              )}

              <div ref={messagesEndRef} className="h-1 w-full" />
            </div>
          )}
        </MessageScroller>
      </MessageScrollerProvider>

      {/* INPUT AREA: Unified Flex Wrapper for centered button alignment */}
      <div className="flex-none w-full p-4 md:px-6 md:pb-6 bg-zinc-950 z-20">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-100 transition duration-500"></div>
            
            <div className="relative flex items-center w-full min-h-[56px] pl-5 pr-2 py-1.5 rounded-2xl bg-zinc-900/90 backdrop-blur-xl border border-white/10 focus-within:border-zinc-700 focus-within:ring-1 focus-within:ring-zinc-700 shadow-2xl">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                placeholder="Ask about projects, customers, or invoices..."
                rows={1}
                className="flex-1 max-h-[200px] bg-transparent border-none text-[15px] text-zinc-100 placeholder:text-zinc-500 focus:outline-none resize-none py-2 pr-3 leading-relaxed disabled:opacity-50 no-scrollbar"
              />
              <Button 
                type="submit" 
                size="icon"
                disabled={!input.trim() || isLoading}
                className="h-10 w-10 shrink-0 bg-zinc-100 hover:bg-white hover:scale-105 transition-all text-zinc-900 rounded-xl shadow-md disabled:opacity-40 disabled:hover:scale-100 flex items-center justify-center"
              >
                <Send size={17} className="-ml-0.5 translate-x-[1px]" />
              </Button>
            </div>
          </form>
          <div className="text-center mt-3">
             <span className="text-[10px] text-zinc-600 font-mono tracking-wide uppercase">
               AgentLab Platform v1.0
             </span>
          </div>
        </div>
      </div>
      
    </div>
  );
}