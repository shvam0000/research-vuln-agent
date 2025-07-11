"use client"

import React, { useState, useEffect, useRef } from "react"

const ChatPage = () => {
  const [messages, setMessages] = useState<
    { role: "user" | "agent"; content: string; external_trace_id?: string }[]
  >([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [agentSteps, setAgentSteps] = useState<
    { step: string; content: string; trace_id?: string }[]
  >([])

  useEffect(() => {
    const timeout = setTimeout(() => {
      const el = document.documentElement
      el.scrollTop = el.scrollHeight
    }, 100)

    return () => clearTimeout(timeout)
  }, [messages])

  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, agentSteps, loading])

  const sendMessage = () => {
    if (!input.trim()) return

    setMessages((prev) => [...prev, { role: "user", content: input }])
    setInput("")
    setLoading(true)
    setAgentSteps([])

    const steps: { step: string; content: string; trace_id?: string }[] = []

    fetch("http://localhost:5000/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input }),
    })
      .then((response) => {
        if (!response.body) {
          setLoading(false)
          return
        }
        const reader = response.body.getReader()
        const decoder = new TextDecoder("utf-8")
        let buffer = ""

        function read() {
          reader.read().then(({ done, value }) => {
            if (done) {
              setLoading(false)
              setMessages((prev) => [
                ...prev,
                {
                  role: "agent",
                  content: steps
                    .map((s) => `${s.step}: ${s.content}`)
                    .join("\n\n"),
                  external_trace_id:
                    steps.length > 0
                      ? steps[steps.length - 1].trace_id
                      : undefined,
                },
              ])
              setAgentSteps([])
              return
            }
            buffer += decoder.decode(value)
            // Parse all complete data lines
            const lines = buffer.split("\n")
            let newBuffer = ""
            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const stepObj = JSON.parse(line.slice(6))
                  steps.push(stepObj)
                  setAgentSteps([...steps])
                  // eslint-disable-next-line @typescript-eslint/no-unused-vars
                } catch (e) {
                  // ignore parse errors
                }
              } else {
                newBuffer += line
              }
            }
            buffer = newBuffer
            read()
          })
        }
        read()
      })
      .catch(() => setLoading(false))
  }

  return (
    <div
      className="min-h-screen px-6 py-10"
      style={{ backgroundColor: "var(--color-bg)" }}
    >
      <div className="max-w-3xl mx-auto">
        <h1
          className="text-3xl font-bold mb-6 tracking-wide"
          style={{ color: "var(--color-accent)" }}
        >
          ⚡ Autonomous Security Agent
        </h1>

        <div
          ref={scrollRef}
          className="rounded-lg shadow-lg p-6 space-y-4 max-h-[70vh] overflow-y-auto"
          style={{
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-soft)",
          }}
        >
          {messages.map((msg, i) => (
            <div
              key={i}
              className="p-4 rounded-xl whitespace-pre-wrap"
              style={{
                backgroundColor:
                  msg.role === "user"
                    ? "var(--color-soft)"
                    : "var(--color-surface)",
                color:
                  msg.role === "user"
                    ? "var(--color-text)"
                    : "var(--color-accent)",
                border:
                  msg.role === "agent"
                    ? "1px solid var(--color-accent)"
                    : undefined,
                textAlign: msg.role === "user" ? "right" : "left",
              }}
            >
              <div className="font-mono text-sm">
                {msg.content.split("\n").map((line, j) => {
                  let highlight = ""
                  if (line.startsWith("Thought:"))
                    highlight = "text-yellow-500 font-semibold"
                  else if (line.startsWith("Action:"))
                    highlight = "text-blue-500 font-semibold"
                  else if (line.startsWith("Observation:"))
                    highlight = "text-green-500 font-semibold"
                  else if (line.startsWith("Final Answer:"))
                    highlight = "text-red-500 font-bold"

                  return (
                    <div key={j} className={highlight}>
                      {line}
                    </div>
                  )
                })}
              </div>
              {msg.role === "agent" && msg.external_trace_id && (
                <div className="mt-2 text-xs">
                  <a
                    href={`/trace/${msg.external_trace_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 underline hover:text-blue-300"
                  >
                    View Trace: {msg.external_trace_id}
                  </a>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div
              className="p-4 rounded-xl whitespace-pre-wrap"
              style={{
                backgroundColor: "var(--color-surface)",
                color: "var(--color-accent)",
                border: "1px solid var(--color-accent)",
                textAlign: "left",
                marginTop: "1rem",
              }}
            >
              <div className="font-mono text-sm space-y-2">
                {/* Pre-step animation */}
                {agentSteps.length === 0 && (
                  <div className="flex items-center gap-2 mt-2 text-gray-400">
                    <span className="animate-spin text-xl">💭</span>
                    <span className="animate-pulse">
                      Agent is preparing a plan...
                    </span>
                  </div>
                )}
                {/* Steps */}
                {agentSteps.map((step, i) => (
                  <div key={i}>
                    <span
                      style={{
                        fontWeight: "bold",
                        color:
                          step.step === "Thought"
                            ? "#eab308"
                            : step.step === "Action"
                              ? "#3b82f6"
                              : step.step === "Observation"
                                ? "#22c55e"
                                : step.step === "Final Answer"
                                  ? "#ef4444"
                                  : "inherit",
                      }}
                    >
                      {step.step}:
                    </span>
                    <span style={{ marginLeft: 8 }}>{step.content}</span>
                  </div>
                ))}
                {/* Always show thinking animation while loading */}
                <div className="flex items-center gap-2 mt-2 text-gray-400">
                  <span className="animate-bounce">⏳</span>
                  <span className="animate-pulse">Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 flex gap-3">
          <input
            className="flex-1 p-3 rounded-lg border"
            style={{
              backgroundColor: "var(--color-soft)",
              borderColor: "var(--color-soft)",
              color: "var(--color-text)",
            }}
            placeholder="Ask about vulnerabilities..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button
            onClick={sendMessage}
            className="px-6 py-3 rounded-lg font-bold shadow-md transition"
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#fff",
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
