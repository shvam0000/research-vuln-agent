import { getNeo4jSession } from "../lib/neo4j.ts"
import { callAgent } from "../lib/litellm.ts"

import dotenv from "dotenv"
dotenv.config()

const enrichGraph = async () => {
  const session = getNeo4jSession()

  try {
    const result = await session.run(
      `
            MATCH (f1:Finding)-[:HAS_VULNERABILITY]->(v1:Vulnerability),
                  (f2:Finding)-[:HAS_VULNERABILITY]->(v2:Vulnerability)
            WHERE f1.id < f2.id AND v1.vector = v2.vector
            RETURN f1.id AS id1, f2.id AS id2, v1.vector AS vector
            LIMIT 5
            `
    )

    for (const record of result.records) {
      const id1 = record.get("id1")
      const id2 = record.get("id2")
      const vector = record.get("vector")

      const prompt = `Given two findings:\n- ${id1}\n- ${id2}\nBoth have a vulnerability vector of '${vector}'. Do they likely share a root cause or attack pattern? Respond with either:\n\nYES - with a reason\nNO - and why not`

      const agentReply = await callAgent(prompt)
      console.log(`Agent reply for ${id1} and ${id2}:\n${agentReply}`)

      if (agentReply.toLowerCase().includes("yes")) {
        await session.run(
          `
                    MATCH (f1:Finding {id: $id1}), (f2:Finding {id: $id2})
                    MERGE (f1)-[:RELATED_TO {reason: $reason}]->(f2)
                    `,
          {
            id1,
            id2,
            reason: agentReply,
          }
        )

        console.log(`Linked ${id1} <--> ${id2}`)
      }
    }

    console.log("Graph enrichment complete")
  } catch (error) {
    console.error("Error enriching graph:", error)
  } finally {
    await session.close()
  }
}

enrichGraph()
