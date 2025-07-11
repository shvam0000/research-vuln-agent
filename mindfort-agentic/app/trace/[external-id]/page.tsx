"use client"

import React, { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import ReactMarkdown from "react-markdown"
import Link from "next/link"

interface Step {
  step: string
  content: unknown
  trace_id?: string
  external_trace_id?: string
}

function extractLLMContent(raw: unknown): string | undefined {
  let content = raw

  // Step 1: Try to parse stringified JSON
  if (typeof content === "string") {
    try {
      content = JSON.parse(content.replace(/'/g, '"'))
    } catch {
      return content as string // plain string like "end"
    }
  }

  // Step 2: outputs.generations
  if (
    typeof content === "object" &&
    content !== null &&
    "outputs" in content &&
    typeof (content as { outputs: unknown }).outputs === "object" &&
    (content as { outputs: unknown }).outputs !== null
  ) {
    const outputs = (content as { outputs: Record<string, unknown> }).outputs

    if (
      outputs &&
      "generations" in outputs &&
      Array.isArray((outputs as { generations?: unknown[] }).generations) &&
      Array.isArray(
        ((outputs as { generations: unknown[] }).generations as unknown[])[0]
      )
    ) {
      const generations = (outputs as { generations: unknown[] })
        .generations as unknown[]
      const firstGenArr = generations[0] as unknown[]
      const gen =
        firstGenArr &&
        typeof firstGenArr[0] === "object" &&
        firstGenArr[0] !== null
          ? (firstGenArr[0] as {
              text?: string
              message?: { content?: string }
            })
          : undefined
      if (gen?.text) return gen.text
      if (gen?.message?.content) return gen.message.content
    }

    if (Array.isArray(outputs.messages)) {
      for (const msg of outputs.messages) {
        if (msg?.content) return msg.content
      }
    }

    if (typeof outputs.output === "string") {
      return outputs.output
    }
  }

  // Step 3: top-level messages
  if (
    typeof content === "object" &&
    content !== null &&
    "messages" in content &&
    Array.isArray((content as { messages?: unknown }).messages)
  ) {
    const messages = (content as { messages?: unknown }).messages
    if (Array.isArray(messages)) {
      for (const msg of messages) {
        if (msg?.content) return msg.content
      }
    }
  }

  // Step 4: top-level generations
  if (
    typeof content === "object" &&
    content !== null &&
    "generations" in content &&
    Array.isArray((content as { generations?: unknown }).generations)
  ) {
    const gens = (content as { generations?: unknown }).generations
    if (Array.isArray(gens) && Array.isArray(gens[0])) {
      const gen = gens[0][0]
      if (gen?.text) return gen.text
      if (gen?.message?.content) return gen.message.content
    }
  }

  return undefined
}

const TracePage: React.FC = () => {
  const params = useParams()
  const external_id = params["external-id"] as string
  const [steps, setSteps] = useState<Step[]>([])

  useEffect(() => {
    const fetchTrace = async () => {
      const res = await fetch(`https://mindfort-a36d7c2f9939.herokuapp.com/trace/${external_id}`)
      const data = await res.json()

      const parsedSteps: Step[] = data.map(
        (item: {
          step?: string
          run_type?: string
          inputs?: Record<string, unknown>
          outputs?: Record<string, unknown>
          content?: unknown
          trace_id?: string
          external_trace_id?: string
        }) => ({
          content: item,
          step: item.step || item.run_type || "Message",
          trace_id: item.trace_id,
          external_trace_id: item.external_trace_id,
        })
      )

      setSteps(parsedSteps)
    }
    fetchTrace()
  }, [external_id])

  const getStepColor = (step: string) => {
    switch (step.toLowerCase()) {
      case "thought":
        return "#eab308"
      case "action":
        return "#3b82f6"
      case "observation":
        return "#22c55e"
      case "final answer":
        return "#ef4444"
      case "llm":
        return "#a855f7"
      case "agent":
        return "#0ea5e9"
      default:
        return "inherit"
    }
  }

  return (
    <div
      className="min-h-screen px-6 py-10"
      style={{ backgroundColor: "var(--color-bg)" }}
    >
      <Link
        href="/chat"
        className="mb-4 px-4 py-2 rounded-md text-white font-semibold shadow"
        style={{ backgroundColor: "var(--color-accent)" }}
      >
        ← Chat
      </Link>
      <div className="max-w-3xl mx-auto">
        <h1
          className="text-3xl font-bold mb-6 tracking-wide"
          style={{ color: "var(--color-accent)" }}
        >
          🧾 Trace Details
        </h1>
        <div
          className="rounded-lg shadow-lg p-6 space-y-4 max-h-[70vh] overflow-y-auto"
          style={{
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-soft)",
          }}
        >
          {steps.length === 0 ? (
            <div className="text-gray-400 animate-pulse">Loading trace...</div>
          ) : (
            steps.map((step, i) => {
              const extracted = extractLLMContent(step.content)
              return (
                <div
                  key={i}
                  className="p-4 rounded-xl whitespace-pre-wrap"
                  style={{
                    backgroundColor: "var(--color-surface)",
                    color: "var(--color-accent)",
                    border: "1px solid var(--color-accent)",
                    textAlign: "left",
                  }}
                >
                  <div
                    className="font-mono text-sm mb-2 font-bold"
                    style={{ color: getStepColor(step.step) }}
                  >
                    {step.step}
                  </div>
                  {extracted ? (
                    <div className="prose prose-invert text-sm text-red-300">
                      <ReactMarkdown>{extracted}</ReactMarkdown>
                    </div>
                  ) : (
                    <pre className="text-red-300 text-xs overflow-x-auto">
                      {JSON.stringify(step.content, null, 2)}
                    </pre>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}

export default TracePage
