import Link from "next/link"
import React from "react"

const HomePage = () => {
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--color-bg)] via-[var(--color-surface)] to-[var(--color-bg)]"></div>

        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-72 h-72 bg-[var(--color-accent)] rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-40 right-20 w-96 h-96 bg-[var(--color-glowing)] rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-pulse delay-1000"></div>
          <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-[var(--color-accent)] rounded-full mix-blend-multiply filter blur-xl opacity-15 animate-pulse delay-2000"></div>
        </div>

        <div className="relative z-10 px-4 py-20 mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
              <span className="block">MindFort</span>
              <span className="block text-[var(--color-accent)]">Agentic</span>
            </h1>
            <p className="max-w-2xl mx-auto mt-6 text-xl text-gray-300 sm:text-2xl">
              Advanced vulnerability research powered by AI agents. Discover,
              analyze, and understand security threats with intelligent
              automation.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 mt-10 sm:flex-row">
              <Link
                href="/chat"
                className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white transition-all duration-300 bg-[var(--color-accent)] rounded-lg hover:bg-[var(--color-glowing)] hover:scale-105 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)]"
              >
                Start Research
                <svg
                  className="w-5 h-5 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </Link>

              <Link
                href="/graph"
                className="inline-flex items-center px-8 py-4 text-lg font-semibold text-white transition-all duration-300 bg-[var(--color-surface)] border border-[var(--color-accent)] rounded-lg hover:bg-[var(--color-soft)] hover:scale-105 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:ring-offset-2 focus:ring-offset-[var(--color-bg)]"
              >
                View Knowledge Graph
                <svg
                  className="w-5 h-5 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3"
                  />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 py-20 mx-auto max-w-7xl sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Powerful Research Capabilities
          </h2>
          <p className="max-w-2xl mx-auto mt-4 text-lg text-gray-400">
            Leverage advanced AI agents to enhance your vulnerability research
            workflow
          </p>
        </div>

        <div className="grid gap-8 mt-16 sm:grid-cols-2 lg:grid-cols-3">
          <div className="p-6 transition-all duration-300 bg-[var(--color-surface)] rounded-xl hover:bg-[var(--color-soft)] hover:scale-105">
            <div className="flex items-center justify-center w-12 h-12 mb-4 bg-[var(--color-accent)] rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">
              Intelligent Analysis
            </h3>
            <p className="text-gray-400">
              AI-powered agents that understand context and provide deep
              insights into security vulnerabilities.
            </p>
          </div>

          <div className="p-6 transition-all duration-300 bg-[var(--color-surface)] rounded-xl hover:bg-[var(--color-soft)] hover:scale-105">
            <div className="flex items-center justify-center w-12 h-12 mb-4 bg-[var(--color-accent)] rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">
              Real-time Processing
            </h3>
            <p className="text-gray-400">
              Instant analysis and response capabilities for time-sensitive
              security research tasks.
            </p>
          </div>

          <div className="p-6 transition-all duration-300 bg-[var(--color-surface)] rounded-xl hover:bg-[var(--color-soft)] hover:scale-105">
            <div className="flex items-center justify-center w-12 h-12 mb-4 bg-[var(--color-accent)] rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">
              Data Visualization
            </h3>
            <p className="text-gray-400">
              Interactive graphs and visual representations of vulnerability
              relationships and patterns.
            </p>
          </div>

          <div className="p-6 transition-all duration-300 bg-[var(--color-surface)] rounded-xl hover:bg-[var(--color-soft)] hover:scale-105">
            <div className="flex items-center justify-center w-12 h-12 mb-4 bg-[var(--color-accent)] rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">
              Secure Environment
            </h3>
            <p className="text-gray-400">
              Built with security in mind, ensuring your research data and
              findings remain protected.
            </p>
          </div>

          <div className="p-6 transition-all duration-300 bg-[var(--color-surface)] rounded-xl hover:bg-[var(--color-soft)] hover:scale-105">
            <div className="flex items-center justify-center w-12 h-12 mb-4 bg-[var(--color-accent)] rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">
              Interactive Chat
            </h3>
            <p className="text-gray-400">
              Natural language interface for querying vulnerabilities and
              getting detailed explanations.
            </p>
          </div>

          <div className="p-6 transition-all duration-300 bg-[var(--color-surface)] rounded-xl hover:bg-[var(--color-soft)] hover:scale-105">
            <div className="flex items-center justify-center w-12 h-12 mb-4 bg-[var(--color-accent)] rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
                />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">
              Knowledge Graph
            </h3>
            <p className="text-gray-400">
              Connected data model that reveals relationships between
              vulnerabilities and attack vectors.
            </p>
          </div>
        </div>
      </div>

      <div className="px-4 py-20 mx-auto max-w-7xl sm:px-6 lg:px-8">
        <div className="p-8 text-center bg-[var(--color-surface)] rounded-2xl">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ready to Start Your Research?
          </h2>
          <p className="max-w-2xl mx-auto mt-4 text-lg text-gray-400">
            Join the next generation of vulnerability research with AI-powered
            insights and analysis.
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center px-8 py-4 mt-8 text-lg font-semibold text-white transition-all duration-300 bg-[var(--color-accent)] rounded-lg hover:bg-[var(--color-glowing)] hover:scale-105 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] focus:ring-offset-2 focus:ring-offset-[var(--color-surface)]"
          >
            Launch Research Agent
            <svg
              className="w-5 h-5 ml-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </Link>
        </div>
      </div>

      <footer className="px-4 py-12 mx-auto max-w-7xl sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="text-gray-500">
            © 2025 MindFort Agentic. Advanced vulnerability research powered by
            AI.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default HomePage
