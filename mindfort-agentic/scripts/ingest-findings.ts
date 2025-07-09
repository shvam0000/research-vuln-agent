const fs = require("fs")
const path = require("path")
const { getNeo4jSession } = require("../lib/neo4j")

const ingestFindings = async () => {
  const session = getNeo4jSession()
  const rawData = fs.readFileSync(
    path.join(__dirname, "findings_data.json"),
    "utf-8"
  )
  const findings = JSON.parse(rawData)

  for (const finding of findings) {
    const {
      finding_id,
      scanner,
      scan_id,
      timestamp,
      vulnerability,
      asset,
      package: pkg,
    } = finding

    const tx = session.beginTransaction()

    try {
      await tx.run(
        `
                MERGE (f:Finding {id: $finding_id})
                SET f.scanner = $scanner, f.scan_id = $scan_id, f.timestamp = datetime($timestamp)

                MERGE (v:Vulnerability {cwe_id: $cwe_id})
                SET v.title = $title, v.description = $description, v.severity = $severity, v.vector = $vector, v.owasp_id = $owasp_id

                MERGE (a:Asset {url: $url})
                SET a.type = $type, a.service = $service

                MERGE (f)-[:HAS_VULNERABILITY]->(v)
                MERGE (f)-[:AFFECTS]->(a)
                `,
        {
          finding_id,
          scanner,
          scan_id,
          timestamp,
          cwe_id: vulnerability.cwe_id,
          owasp_id: vulnerability.owasp_id,
          title: vulnerability.title,
          description: vulnerability.description,
          severity: vulnerability.severity,
          vector: vulnerability.vector,
          type: asset.type,
          url: asset.url || asset.path || asset.image,
          service: asset.service || "unknown",
        }
      )

      if (pkg) {
        await tx.run(
          `
                    MERGE (p:Package {name: $name, version: $version})
                    MERGE (f)-[:USES_PACKAGE]->(p)
                    `,
          {
            name: pkg.name,
            version: pkg.version,
          }
        )
      }
      await tx.commit()
    } catch (e) {
      console.error("Error ingesting finding:", e)
      await tx.rollback()
    }
  }

  await session.close()
  console.log("Findings ingested successfully")
}

ingestFindings()
