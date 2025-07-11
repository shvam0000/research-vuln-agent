from flask import Flask, Response, json, jsonify, request, stream_with_context
import os
import time
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase
from flask_cors import CORS
from langgraph_agent import ask_agent, stream_agent_steps


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
load_dotenv()


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
LITELLM_URL = os.getenv("LITELLM_BASE_URL").rstrip("/")
LITELLM_KEY = os.getenv("LITELLM_API_KEY")
MODEL = "gpt-4o"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def call_agent(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user", "content": prompt
            }
        ]
    }
    headers = {
        "Authorization": f"Bearer {LITELLM_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(f"{LITELLM_URL}/chat/completions", json=payload, headers=headers)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def enrich_graph():
    with driver.session() as session:
        result = session.run("""
            MATCH (f1:Finding)-[:HAS_VULNERABILITY]->(v1:Vulnerability),
                  (f2:Finding)-[:HAS_VULNERABILITY]->(v2:Vulnerability)
            WHERE f1.id < f2.id AND v1.vector = v2.vector
            RETURN f1.id AS id1, f2.id AS id2, v1.vector AS vector
            LIMIT 5
        """)

        for record in result:
            id1 = record["id1"]
            id2 = record["id2"]
            vector = record["vector"]

            prompt = f"""Given two findings:\n- {id1}\n- {id2}\nBoth have a vulnerability vector of '{vector}'. Do they likely share a root cause or attack pattern? Respond with either:\n\nYES - with a reason\nNO - and why not"""

        
            try:
                reply = call_agent(prompt)
                print(f"Agent reply for {id1} and {id2}:\n{reply}\n")

                if "yes" in reply.lower():
                    session.run(
                        """
                        MATCH (f1:Finding {id: $id1}), (f2:Finding {id: $id2})
                        MERGE (f1)-[:RELATED_TO {reason: $reason}]->(f2)
                        """,
                        id1=id1,
                        id2=id2,
                        reason=reply.strip(),
                    )
                    print(f"Linked {id1} <--> {id2}")
                else:
                    print(f"No link between {id1} <--> {id2}")
            except Exception as e:
                print(f"Error processing {id1} and {id2}: {e}")
                time.sleep(1)
    
@app.route("/")
def home():
    return jsonify({"message": "Hello, Flask!"})

@app.route("/enrich-graph")
def enrich_graph_route():
    enrich_graph()
    return jsonify({"message": "Graph enriched"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message")
    if not user_msg:
        return jsonify({"error": "Message is required"}), 400

    with driver.session() as session:
        result = session.run(
            """
            MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability)
            WHERE v.title CONTAINS $term OR v.description CONTAINS $term
            RETURN f.id AS id, v.title AS title, v.severity AS severity, v.description AS description
            LIMIT 5
            """,
            term=user_msg,
        )

        context = "\n".join([
            f"[{r['severity']}] {r['title']} - {r['description']}"
            for r in result
        ])


        prompt = f"""
                You are a cybersecurity expert analyzing vulnerabilities.

                Follow this structure:
                Thought: (your reasoning)
                Action: (what you'd do next or look for)
                Observation: (result of action if applicable)
                ... (repeat as needed)
                Final Answer: (your clear, summarized response)

                Here is the context:
                {context}

                User query:
                {user_msg}
                """

        try:
            reply = call_agent(prompt)
            return jsonify({ "response": reply.replace("\\n", "\n") })
        except Exception as e:
            return jsonify({"error": str(e)}), 500


        
@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json()
    user_msg = data.get("message")
    if not user_msg:
        return {"error": "Message is required"}, 400

    context = "... your Neo4j query + formatting here ..."

    prompt = f"""Think step-by-step. Show each reasoning step before final answer.
                Context:
                {context}
                Question: {user_msg}
                """

    def event_stream():
        headers = {
            "Authorization": f"Bearer {LITELLM_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}]
        }
        with requests.post(f"{LITELLM_URL}/chat/completions", json=payload, headers=headers, stream=True) as r:
            for line in r.iter_lines():
                if line and line.startswith(b"data: "):
                    data = line.decode("utf-8")[6:]
                    if data.strip() == "[DONE]":
                        break
                    token = json.loads(data)["choices"][0]["delta"].get("content", "")
                    yield f"{token}"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@app.teardown_appcontext
def close_driver(exception):
    if driver: # Ensure driver exists before closing
        driver.close()

if __name__ == "__main__":
    app.run(debug=True)
