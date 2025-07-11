"use client"

import React, { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import cytoscape from "cytoscape"

const CytoscapeComponent = dynamic(() => import("react-cytoscapejs"), {
  ssr: false,
})

const CytoscapeGraphPage = () => {
  const [cy, setCy] = useState<cytoscape.Core | null>(null)
  const [selectedElement, setSelectedElement] = useState<{
    id: string
    label: string
    group?: string
    properties?: Record<string, unknown>
  } | null>(null)
  const [graphData, setGraphData] = useState<{
    nodes: {
      id: string
      label: string
      group?: string
      properties?: Record<string, unknown>
    }[]
    links: {
      source: string
      target: string
      type?: string
      properties?: Record<string, unknown>
    }[]
  }>({
    nodes: [],
    links: [],
  })

  useEffect(() => {
    fetch("https://mindfort-a36d7c2f9939.herokuapp.com/graph")
      .then((res) => res.json())
      .then((data) => {
        setGraphData(data)
      })
  }, [])

  const elements = [
    ...graphData.nodes.map(
      (node: {
        id: string
        label: string
        group?: string
        properties?: Record<string, unknown>
      }) => ({
        data: {
          ...(node.properties || {}),
          id: node.id,
          label: node.label,
          group: node.group,
        },
      })
    ),
    ...graphData.links.map(
      (link: {
        source: string
        target: string
        type?: string
        properties?: Record<string, unknown>
      }) => ({
        data: {
          ...(link.properties || {}),
          source: link.source,
          target: link.target,
          type: link.type,
        },
      })
    ),
  ]

  const stylesheet: cytoscape.StylesheetCSS[] = [
    {
      selector: "node",
      css: {
        label: "data(label)",
        width: "60px",
        height: "60px",
        "font-size": "10px",
        "text-valign": "center",
        "text-halign": "center",
        "background-color": "#888",
        color: "#fff",
        "text-outline-width": 2,
        "text-outline-color": "#888",
      },
    },
    {
      selector: 'node[group="Finding"]',
      css: { "background-color": "#ff2c2c", "text-outline-color": "#ff2c2c" },
    },
    {
      selector: 'node[group="Vulnerability"]',
      css: { "background-color": "#ff6b6b", "text-outline-color": "#ff6b6b" },
    },
    {
      selector: 'node[group="Asset"]',
      css: { "background-color": "#4ecdc4", "text-outline-color": "#4ecdc4" },
    },
    {
      selector: 'node[group="Package"]',
      css: { "background-color": "#45b7d1", "text-outline-color": "#45b7d1" },
    },
    {
      selector: "edge",
      css: {
        width: 2,
        "line-color": "#ccc",
        "target-arrow-color": "#ccc",
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
      },
    },
    { selector: 'edge[type="RELATED_TO"]', css: { "line-color": "#4444ff" } },
    {
      selector: 'edge[type="HAS_VULNERABILITY"]',
      css: { "line-color": "#ff4444" },
    },
    { selector: 'edge[type="AFFECTS"]', css: { "line-color": "#44ff44" } },
    {
      selector: ":selected",
      css: { "border-width": 3, "border-color": "#00ffff" },
    },
  ]

  useEffect(() => {
    if (cy) {
      cy.on("tap", "node, edge", (event) => {
        setSelectedElement(event.target.data())
      })
      cy.on("tap", (event) => {
        if (event.target === cy) {
          setSelectedElement(null)
        }
      })
    }
  }, [cy])

  return (
    <div style={{ display: "flex", fontFamily: "sans-serif", height: "100vh" }}>
      <div style={{ flex: 1, position: "relative", border: "1px solid #ddd" }}>
        <CytoscapeComponent
          elements={elements}
          stylesheet={stylesheet}
          style={{ width: "100%", height: "100%" }}
          layout={{
            name: "cose",
            animate: true,
            padding: 50,
            randomize: true,
            nodeDimensionsIncludeLabels: true,
            fit: true,
            componentSpacing: 100,
            nodeRepulsion: 4500,
            nodeOverlap: 20,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0,
          }}
          cy={(cyInstance) => setCy(cyInstance)}
        />
      </div>

      {selectedElement && (
        <div
          style={{
            width: "350px",
            padding: "16px",
            borderLeft: "1px solid #ddd",
            backgroundColor: "#f7f7f7",
            overflowY: "auto",
          }}
        >
          <button
            onClick={() => setSelectedElement(null)}
            style={{
              float: "right",
              border: "none",
              background: "transparent",
              fontSize: "1.2em",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
          <h2 style={{ marginTop: 0, color: "#333" }}>
            {selectedElement.label || "Details"}
          </h2>
          <strong style={{ color: "#555" }}>
            Type:{" "}
            {selectedElement.group
              ? selectedElement.group
              : selectedElement.label
                ? "Node"
                : "Edge"}
          </strong>
          <hr
            style={{
              border: "none",
              borderTop: "1px solid #eee",
              margin: "16px 0",
            }}
          />
          <h4 style={{ color: "#333" }}>Properties:</h4>
          <div style={{ fontSize: "14px", wordBreak: "break-word" }}>
            {Object.entries(selectedElement).map(
              ([key, value]) =>
                !["id", "label", "group", "source", "target", "type"].includes(
                  key
                ) && (
                  <div key={key} style={{ marginBottom: "8px" }}>
                    <strong style={{ color: "#555" }}>{key}:</strong>{" "}
                    {String(value)}
                  </div>
                )
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CytoscapeGraphPage
