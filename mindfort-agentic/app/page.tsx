"use client"

import React, { useState, useEffect } from "react"

const HomePage = () => {
  const [messages, setMessages] = useState<
    { role: "user" | "agent"; content: string }[]
  >([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  // const [showDebug, setShowDebug] = useState(true)
  // const sendMessage = async () => {
  //   if (!input.trim()) return
  //   const userMessage: { role: "user" | "agent"; content: string } = {
  //     role: "user",
  //     content: input,
  //   }
  //   setMessages([...messages, userMessage])
  //   setLoading(true)

  //   const res = await fetch("http://localhost:5000/chat", {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify({ message: input }),
  //   })

  //   const data = await res.json()

  //   setMessages((prev) => [
  //     ...prev,
  //     { role: "user", content: input },
  //     { role: "agent", content: data.response },
  //   ])
  //   setInput("")
  //   setLoading(false)
  // }

  useEffect(() => {
    const timeout = setTimeout(() => {
      const el = document.documentElement
      el.scrollTop = el.scrollHeight
    }, 100)

    return () => clearTimeout(timeout)
  }, [messages])

  const sendMessage = () => {
    if (!input.trim()) return

    const userMsg: { role: "user"; content: string } = {
      role: "user",
      content: input,
    }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setLoading(true)

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
        let agentMsg = ""

        function read() {
          reader.read().then(({ done, value }) => {
            if (done) {
              setLoading(false)
              return
            }

            const chunk = decoder.decode(value)
            agentMsg += chunk

            setMessages((prev) => {
              const newMessages = [...prev]
              if (newMessages[prev.length - 1]?.role === "agent") {
                newMessages[prev.length - 1].content = agentMsg
              } else {
                newMessages.push({ role: "agent", content: agentMsg })
              }
              return [...newMessages]
            })

            read()
          })
        }

        read()
      })
      .catch((e) => {
        console.error("Stream error", e)
        setLoading(false)
      })
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
            </div>
          ))}
          {/* {showDebug && (
            <div className="text-sm font-mono text-left mt-2 text-gray-400">
              {messages[messages.length - 1]?.content
                .split("\n")
                .map((line, j) => (
                  <div key={j} className="whitespace-pre-wrap">
                    {line}
                  </div>
                ))}
            </div>
          )} */}
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

// "use client"

// import React, { useState, useEffect, useRef } from "react"

// // Define a type for the structured data we expect from the stream
// interface AgentStep {
//   step: "Thought" | "Action" | "Final Answer" | "Error"
//   content: string
// }

// // Define the message structure for our chat state
// interface Message {
//   role: "user" | "agent"
//   content: string
// }

// const HomePage = () => {
//   const [messages, setMessages] = useState<Message[]>([])
//   const [input, setInput] = useState("")
//   const [isLoading, setIsLoading] = useState(false)

//   // A ref to the container div of the messages to handle auto-scrolling
//   const messagesEndRef = useRef<HTMLDivElement>(null)

//   // This effect will automatically scroll to the bottom of the message list
//   // whenever a new message is added.
//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
//   }, [messages])

//   const sendMessage = async () => {
//     if (!input.trim()) return

//     // 1. Add the user's message to the state immediately
//     const userMessage: Message = { role: "user", content: input }
//     // 2. Add a placeholder for the agent's response. We will stream content into this.
//     const agentPlaceholder: Message = { role: "agent", content: "" }
//     setMessages((prevMessages) => [
//       ...prevMessages,
//       userMessage,
//       agentPlaceholder,
//     ])

//     setInput("")
//     setIsLoading(true)

//     try {
//       // 3. Make the POST request to the streaming endpoint
//       const response = await fetch("http://localhost:5000/chat/stream", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ message: input }),
//       })

//       if (!response.body) {
//         throw new Error("Response body is null")
//       }

//       // 4. Get the reader and decoder to process the stream
//       const reader = response.body.getReader()
//       const decoder = new TextDecoder("utf-8")
//       let fullAgentResponse = ""

//       // 5. Define the function to read chunks from the stream
//       const readStream = async () => {
//         const { done, value } = await reader.read()

//         if (done) {
//           setIsLoading(false)
//           return
//         }

//         // The raw chunk might contain multiple "data: {...}" events.
//         const chunk = decoder.decode(value, { stream: true })

//         // Process each event in the chunk
//         const eventLines = chunk
//           .split("\n\n")
//           .filter((line) => line.startsWith("data: "))

//         for (const line of eventLines) {
//           const jsonString = line.substring(5) // Remove "data: " prefix
//           if (jsonString) {
//             try {
//               const parsedStep: AgentStep = JSON.parse(jsonString)

//               // Append the formatted step to the full response string
//               fullAgentResponse += `${parsedStep.step}: ${parsedStep.content}\n`

//               // Update the last message (the agent's placeholder) with the new content
//               setMessages((prev) => {
//                 const newMessages = [...prev]
//                 newMessages[newMessages.length - 1].content = fullAgentResponse
//                 return newMessages
//               })
//             } catch (e) {
//               console.error("Failed to parse stream data:", jsonString, e)
//             }
//           }
//         }

//         // Continue reading the stream
//         await readStream()
//       }

//       // Start reading the stream
//       await readStream()
//     } catch (e) {
//       console.error("Fetch stream error", e)
//       setMessages((prev) => {
//         const newMessages = [...prev]
//         newMessages[newMessages.length - 1].content =
//           "Sorry, I ran into an error. Please check the console."
//         return newMessages
//       })
//       setIsLoading(false)
//     }
//   }

//   return (
//     <div
//       className="min-h-screen px-6 py-10 flex flex-col"
//       style={{ backgroundColor: "var(--color-bg)" }}
//     >
//       <div className="max-w-3xl mx-auto w-full flex flex-col flex-1">
//         <h1
//           className="text-3xl font-bold mb-6 tracking-wide"
//           style={{ color: "var(--color-accent)" }}
//         >
//           ⚡ Autonomous Security Agent
//         </h1>

//         <div
//           className="flex-1 rounded-lg shadow-lg p-6 space-y-4 overflow-y-auto mb-6"
//           style={{
//             backgroundColor: "var(--color-surface)",
//             border: "1px solid var(--color-soft)",
//           }}
//         >
//           {messages.map((msg, i) => (
//             <div
//               key={i}
//               className="p-4 rounded-xl whitespace-pre-wrap"
//               style={{
//                 backgroundColor:
//                   msg.role === "user"
//                     ? "var(--color-soft)"
//                     : "rgba(255, 44, 44, 0.1)", // Agent messages now have a distinct background
//                 color:
//                   msg.role === "user"
//                     ? "var(--color-text)"
//                     : "var(--color-accent)", // Agent messages now have a distinct text color
//                 border:
//                   msg.role === "agent"
//                     ? "1px solid var(--color-accent)"
//                     : "none", // Agent messages now have a distinct border
//                 textAlign: msg.role === "user" ? "right" : "left",
//                 alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
//                 maxWidth: "90%",
//               }}
//             >
//               <div className="font-mono text-sm">
//                 {msg.content.split("\n").map((line, j) => {
//                   let highlight = ""
//                   if (line.startsWith("Thought:")) highlight = "text-yellow-400"
//                   else if (line.startsWith("Action:"))
//                     highlight = "text-blue-400"
//                   else if (line.startsWith("Final Answer:"))
//                     highlight = "text-green-400 font-bold"
//                   else if (line.startsWith("Error:"))
//                     highlight = "text-red-500 font-bold"

//                   return (
//                     <div key={j} className={highlight}>
//                       {line}
//                     </div>
//                   )
//                 })}
//               </div>
//             </div>
//           ))}
//           {isLoading && (
//             <div className="text-gray-400 animate-pulse text-left">
//               Agent is thinking...
//             </div>
//           )}
//           {/* This empty div is the target for our auto-scrolling ref */}
//           <div ref={messagesEndRef} />
//         </div>

//         <div className="mt-auto flex gap-3">
//           <input
//             className="flex-1 p-3 rounded-lg border"
//             style={{
//               backgroundColor: "var(--color-soft)",
//               borderColor: "var(--color-soft)",
//               color: "var(--color-text)",
//             }}
//             placeholder="Ask about vulnerabilities..."
//             value={input}
//             onChange={(e) => setInput(e.target.value)}
//             onKeyDown={(e) => {
//               if (e.key === "Enter" && !isLoading) {
//                 e.preventDefault()
//                 sendMessage()
//               }
//             }}
//             disabled={isLoading}
//           />
//           <button
//             onClick={sendMessage}
//             disabled={isLoading}
//             className="px-6 py-3 rounded-lg font-bold shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed"
//             style={{
//               backgroundColor: "var(--color-accent)",
//               color: "#fff",
//             }}
//           >
//             Send
//           </button>
//         </div>
//       </div>
//     </div>
//   )
// }

// export default HomePage
