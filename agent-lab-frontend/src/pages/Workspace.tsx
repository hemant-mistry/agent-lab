import React, { useState, useRef, useEffect } from "react"
import {
  Send,
  Bot,
  Code2,
  Sparkles,
  TerminalSquare,
  Network,
  Database,
  MessageSquare,
  Wrench,
  ShieldAlert,
  Layers,
  ShieldCheck,
} from "lucide-react"
import { EXPERIMENTS } from "../config/experiments"
import { AgentAPI } from "../services/api"
import type { ChatMessage } from "../features/workspace/types"

import { Button } from "../components/ui/button"
import {
  MessageScrollerProvider,
  MessageScroller,
  MessageScrollerItem,
} from "../components/ui/message-scroller"

const SAMPLE_PROMPTS = [
  {
    title: "Happy Path (Data Retrieval)",
    prompt:
      "What are the top 3 projects with the highest actual spend, and who are their customers?",
    icon: <Database size={16} />,
    color: "text-blue-400",
  },
  {
    title: "Test Semantic Router",
    prompt: "Hey there! How are you doing today?",
    icon: <MessageSquare size={16} />,
    color: "text-indigo-400",
  },
  {
    title: "Test Self-Healing SQL",
    prompt: "Show me all projects that have an active status.",
    icon: <Wrench size={16} />,
    color: "text-amber-400",
  },
  {
    title: "Test Human-in-the-Loop",
    prompt: "Delete all closed tickets for customer C0001.",
    icon: <ShieldAlert size={16} />,
    color: "text-rose-400",
  },
]

export default function Workspace() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [experimentId, setExperimentId] = useState(EXPERIMENTS[0]?.id || "")
  const [isLoading, setIsLoading] = useState(false)
  const [useRouter, setUseRouter] = useState(true)
  const [sessionId] = useState(() => `session-${Date.now()}`)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const sendQuery = async (queryText: string) => {
    if (!queryText.trim() || isLoading) return

    setInput("")

    const newUserMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: queryText,
    }
    setMessages((prev) => [...prev, newUserMsg])

    setIsLoading(true)

    try {
      const data = await AgentAPI.executeRun(
        experimentId,
        queryText,
        sessionId,
        useRouter
      )

      // Fallback check to ensure approval flag catches text warnings even if boolean is missing
      const requiresApprovalFlag = Boolean(
        data.requires_approval ||
        data.final_answer?.includes("Human Approval Required")
      )

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.final_answer,
        steps: data.steps,
        latency_ms: data.latency_ms,
        telemetry: data.telemetry,
        requires_approval: requiresApprovalFlag,
      }

      setMessages((prev) => [...prev, botMsg])
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "error",
        content: err.message || "An error occurred during execution.",
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    sendQuery(input)
  }

  const handleResume = async (action: "approve" | "reject") => {
    // Hide buttons immediately upon click
    setMessages((prev) =>
      prev.map((m) =>
        m.requires_approval ? { ...m, requires_approval: false } : m
      )
    )

    const newUserMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: `[System Action]: User clicked ${action.toUpperCase()}`,
    }
    setMessages((prev) => [...prev, newUserMsg])
    setIsLoading(true)

    try {
      const data = await AgentAPI.resumeRun(experimentId, sessionId, action)
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.final_answer,
        steps: data.steps,
        latency_ms: data.latency_ms,
        telemetry: data.telemetry,
        requires_approval: Boolean(data.requires_approval),
      }
      setMessages((prev) => [...prev, botMsg])
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: "error", content: err.message },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col bg-zinc-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.1),rgba(255,255,255,0))] font-sans text-zinc-100">
      {/* HEADER */}
      <header className="z-20 flex flex-none items-center justify-between border-b border-white/5 bg-zinc-950/50 px-6 py-4 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/5 shadow-sm">
            <TerminalSquare size={18} className="text-zinc-300" />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-zinc-100">
              Agent Console
            </h1>
            <p className="mt-0.5 font-mono text-[11px] text-zinc-500">
              environment: nexus-works
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {experimentId === "langchain-v1" && (
            <div className="flex items-center gap-2 rounded-lg border border-white/5 bg-zinc-900/50 p-1.5 px-3 shadow-inner">
              <Network
                size={14}
                className={useRouter ? "text-emerald-400" : "text-zinc-500"}
              />
              <label
                className="cursor-pointer text-[11px] font-medium tracking-wider text-zinc-300 uppercase select-none"
                onClick={() => setUseRouter(!useRouter)}
              >
                LCEL Router
              </label>
              <button
                type="button"
                onClick={() => setUseRouter(!useRouter)}
                className={`relative ml-1 inline-flex h-4 w-7 shrink-0 cursor-pointer items-center justify-center rounded-full border border-white/10 transition-colors duration-200 ease-in-out focus:outline-none ${useRouter ? "bg-emerald-500/80" : "bg-zinc-700"}`}
              >
                <span
                  className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${useRouter ? "translate-x-1.5" : "-translate-x-1.5"}`}
                />
              </button>
            </div>
          )}

          <div className="flex items-center gap-3 rounded-lg border border-white/5 bg-zinc-900/50 p-1.5">
            <label className="pl-2 text-[11px] font-medium tracking-wider text-zinc-400 uppercase">
              Engine
            </label>
            <select
              value={experimentId}
              onChange={(e) => setExperimentId(e.target.value)}
              className="h-7 cursor-pointer rounded-md border-none bg-zinc-800 px-3 py-0.5 text-xs text-zinc-200 focus:ring-1 focus:ring-zinc-600 focus:outline-none"
            >
              {EXPERIMENTS.map((exp) => (
                <option key={exp.id} value={exp.id} disabled={exp.disabled}>
                  {exp.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {/* CHAT THREAD */}
      <MessageScrollerProvider autoScroll>
        <MessageScroller className="flex-1 overflow-y-auto px-4 pt-8 md:px-8 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-zinc-800 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-700 [&::-webkit-scrollbar-track]:bg-transparent">
          {messages.length === 0 ? (
            <div className="mx-auto mt-[-4vh] flex h-full max-w-2xl animate-in flex-col items-center justify-center duration-1000 fade-in">
              <div className="relative mb-6">
                <div className="absolute -inset-6 rounded-full bg-emerald-500/20 blur-3xl"></div>
                <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-zinc-900/80 shadow-2xl backdrop-blur-sm">
                  <Sparkles size={28} className="text-emerald-400/80" />
                </div>
              </div>

              <h2 className="mb-2 text-2xl font-semibold tracking-tight text-zinc-100">
                Enterprise LangGraph Agent
              </h2>
              <p className="mb-8 max-w-lg text-center text-sm leading-relaxed text-zinc-400">
                State-machine graph architecture featuring human-in-the-loop
                state interruptions for secure database mutations.
              </p>

              {/* Capabilities Badges */}
              <div className="mb-12 flex flex-wrap justify-center gap-3">
                <span className="flex items-center gap-1.5 rounded-lg border border-white/5 bg-zinc-900/50 px-3 py-1.5 text-[11px] font-medium text-zinc-300 shadow-sm">
                  <ShieldCheck size={14} className="text-emerald-400" />{" "}
                  Human-in-the-Loop HITL
                </span>
                <span className="flex items-center gap-1.5 rounded-lg border border-white/5 bg-zinc-900/50 px-3 py-1.5 text-[11px] font-medium text-zinc-300 shadow-sm">
                  <Layers size={14} className="text-blue-400" /> StateGraph
                  Checkpointing
                </span>
              </div>

              {/* Interactive Prompts Grid */}
              <div className="w-full animate-in delay-150 duration-700 fill-mode-both slide-in-from-bottom-4">
                <div className="mb-3 px-1 text-[11px] font-medium tracking-wider text-zinc-500 uppercase">
                  Try a sample query
                </div>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {SAMPLE_PROMPTS.map((sp, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendQuery(sp.prompt)}
                      className="group flex flex-col rounded-xl border border-white/5 bg-zinc-900/40 p-4 text-left shadow-sm transition-all hover:border-white/10 hover:bg-zinc-800/60 hover:shadow-md"
                    >
                      <div className="mb-2 flex items-center gap-2">
                        <div className={`${sp.color}`}>{sp.icon}</div>
                        <span className="text-xs font-semibold text-zinc-300 transition-colors group-hover:text-zinc-200">
                          {sp.title}
                        </span>
                      </div>
                      <div className="text-[13px] leading-relaxed text-zinc-500 transition-colors group-hover:text-zinc-400">
                        "{sp.prompt}"
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 pb-4">
              {messages.map((msg) => (
                <MessageScrollerItem
                  key={msg.id}
                  messageId={msg.id}
                  scrollAnchor={msg.role === "user"}
                  className="w-full animate-in duration-300 fade-in slide-in-from-bottom-2"
                >
                  <div
                    className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {/* USER TURN */}
                    {msg.role === "user" ? (
                      <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-zinc-100 px-5 py-3 text-[15px] font-medium break-words text-zinc-900 shadow-sm shadow-black/20 md:max-w-[75%]">
                        {msg.content}
                      </div>
                    ) : (
                      /* AGENT TURN */
                      <div className="flex w-full max-w-[95%] flex-col gap-2 md:max-w-[85%]">
                        <div className="mb-1 flex items-center gap-3">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10 shadow-inner">
                            <Bot
                              size={14}
                              className={
                                msg.role === "error"
                                  ? "text-red-400"
                                  : "text-emerald-400"
                              }
                            />
                          </div>
                          <span className="text-[13px] font-semibold text-zinc-200">
                            {msg.role === "error" ? "System Alert" : "AgentLab"}
                          </span>
                          {msg.latency_ms && (
                            <span className="rounded-md border border-white/5 bg-white/5 px-2 py-0.5 font-mono text-[11px] text-zinc-500 shadow-sm">
                              {msg.latency_ms}ms
                            </span>
                          )}
                        </div>

                        <div
                          className={`ml-10 text-[15px] leading-relaxed break-words whitespace-pre-wrap ${msg.role === "error" ? "text-red-400" : "text-zinc-300"}`}
                        >
                          {msg.content}
                        </div>

                        {/* HITL APPROVAL BUTTONS (Explicitly bound and verified) */}
                        {Boolean(msg.requires_approval) && (
                          <div className="mt-3 ml-10 rounded-xl border border-amber-500/30 bg-zinc-900/80 p-4 shadow-lg">
                            <p className="mb-3 text-xs text-zinc-400">
                              Does this mutation query look correct to execute
                              against the production database?
                            </p>
                            <div className="flex gap-3">
                              <Button
                                type="button"
                                onClick={() => handleResume("approve")}
                                className="h-8 bg-emerald-600 text-xs text-white hover:bg-emerald-500"
                              >
                                <ShieldCheck size={14} className="mr-1.5" />{" "}
                                Approve Execution
                              </Button>
                              <Button
                                type="button"
                                onClick={() => handleResume("reject")}
                                variant="outline"
                                className="h-8 border-rose-500/50 text-xs text-rose-400 hover:bg-rose-500/10"
                              >
                                Reject & Cancel
                              </Button>
                            </div>
                          </div>
                        )}

                        {/* Telemetry Display */}
                        {msg.telemetry && (
                          <div className="mt-1 ml-10 flex flex-wrap items-center gap-2">
                            <span className="rounded border border-indigo-500/20 bg-indigo-500/10 px-2 py-0.5 font-mono text-[11px] text-indigo-400/80 shadow-sm">
                              In: {msg.telemetry.input_tokens}
                            </span>
                            <span className="rounded border border-pink-500/20 bg-pink-500/10 px-2 py-0.5 font-mono text-[11px] text-pink-400/80 shadow-sm">
                              Out: {msg.telemetry.output_tokens}
                            </span>
                            <span className="rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 font-mono text-[11px] text-emerald-400/80 shadow-sm">
                              Total Tokens: {msg.telemetry.total_tokens}
                            </span>
                          </div>
                        )}

                        {/* Execution Trace */}
                        {msg.steps && msg.steps.length > 0 && (
                          <details className="group mt-3 ml-10 overflow-hidden rounded-xl border border-white/10 bg-[#0c0c0e] text-xs shadow-lg">
                            <summary className="flex cursor-pointer items-center gap-2 p-3 font-mono text-zinc-400 transition-colors select-none hover:bg-white/5">
                              <Code2 size={14} className="text-amber-400/80" />
                              <span>[Execution Trace]</span>
                              <span className="ml-auto text-zinc-600">
                                {msg.steps.length} ops
                              </span>
                            </summary>
                            <div className="space-y-4 border-t border-white/5 bg-[#0c0c0e]/50 p-4">
                              {msg.steps.map((step) => (
                                <div
                                  key={step.step_number}
                                  className="font-mono"
                                >
                                  <div className="mb-2 flex items-center gap-2">
                                    <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-300">
                                      Step {step.step_number}
                                    </span>
                                    <span
                                      className={
                                        step.type === "tool_call"
                                          ? "text-amber-400"
                                          : "text-blue-400"
                                      }
                                    >
                                      {step.title}
                                    </span>
                                  </div>
                                  <pre className="overflow-x-auto rounded-lg border border-white/5 bg-black/40 p-3 leading-relaxed whitespace-pre-wrap text-zinc-400 shadow-inner">
                                    {typeof step.content === "object"
                                      ? JSON.stringify(step.content, null, 2)
                                      : step.content}
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

              {/* TYPING INDICATOR */}
              {isLoading && (
                <MessageScrollerItem
                  messageId="loading"
                  scrollAnchor={true}
                  className="w-full animate-in duration-300 fade-in slide-in-from-bottom-2"
                >
                  <div className="flex w-full justify-start">
                    <div className="flex w-full max-w-[90%] flex-col gap-2">
                      <div className="mb-1 flex items-center gap-3">
                        <div className="flex h-7 w-7 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10 shadow-inner">
                          <Bot size={14} className="text-emerald-400" />
                        </div>
                        <span className="text-[13px] font-semibold text-zinc-200">
                          AgentLab
                        </span>
                      </div>
                      <div className="ml-10 w-fit rounded-2xl rounded-tl-sm border border-white/5 bg-zinc-900/50 px-4 py-3 shadow-sm">
                        <div className="flex h-3 items-center gap-1.5">
                          <span
                            className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-500"
                            style={{ animationDelay: "0ms" }}
                          ></span>
                          <span
                            className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-500"
                            style={{ animationDelay: "150ms" }}
                          ></span>
                          <span
                            className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-500"
                            style={{ animationDelay: "300ms" }}
                          ></span>
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

      {/* INPUT AREA */}
      <div className="z-20 w-full flex-none bg-zinc-950 p-4 md:px-6 md:pb-6">
        <div className="mx-auto max-w-4xl">
          <form onSubmit={handleSubmit} className="group relative">
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-emerald-500/20 to-blue-500/20 opacity-0 blur-lg transition duration-500 group-focus-within:opacity-100"></div>

            <div className="relative flex min-h-[56px] w-full items-center rounded-2xl border border-white/10 bg-zinc-900/90 py-1.5 pr-2 pl-5 shadow-2xl backdrop-blur-xl focus-within:border-zinc-700 focus-within:ring-1 focus-within:ring-zinc-700">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                placeholder="Ask about projects, customers, or invoices..."
                rows={1}
                className="no-scrollbar max-h-[200px] flex-1 resize-none border-none bg-transparent py-2 pr-3 text-[15px] leading-relaxed text-zinc-100 placeholder:text-zinc-500 focus:outline-none disabled:opacity-50"
              />
              <Button
                type="submit"
                size="icon"
                disabled={!input.trim() || isLoading}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-zinc-100 text-zinc-900 shadow-md transition-all hover:scale-105 hover:bg-white disabled:opacity-40 disabled:hover:scale-100"
              >
                <Send size={17} className="-ml-0.5 translate-x-[1px]" />
              </Button>
            </div>
          </form>
          <div className="mt-3 text-center">
            <span className="font-mono text-[10px] tracking-wide text-zinc-600 uppercase">
              AgentLab Platform v1.0
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
