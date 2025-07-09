"use client"

import React, { useState } from "react"

const HomePage = () => {
  const [messages, setMessages] = useState<
    { role: "user" | "agent"; content: string }[]
  >([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMessage: { role: "user" | "agent"; content: string } = {
      role: "user",
      content: input,
    }
    setMessages([...messages, userMessage])
    setLoading(true)

    const res = await fetch("http://localhost:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input }),
    })

    const data = await res.json()

    setMessages((prev) => [
      ...prev,
      { role: "user", content: input },
      { role: "agent", content: data.response },
    ])
    setInput("")
    setLoading(false)
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
                    : "rgba(255, 44, 44, 0.1)",
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
              {msg.content}
            </div>
          ))}
          {loading && (
            <div className="text-gray-400 animate-pulse">
              Agent is thinking...
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

export default HomePage
