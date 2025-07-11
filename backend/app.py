from flask import Flask, Response, json, jsonify, request, stream_with_context
import os
import time
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase
from flask_cors import CORS
from langgraph_agent import ask_agent, stream_agent_steps
import uuid
from datetime import datetime
from langsmith import Client


app = Flask(__name__)
CORS(app)
load_dotenv() 
print("DEBUG: NEO4J_URI =", os.getenv("NEO4J_URI"))
print("DEBUG: NEO4J_USER =", os.getenv("NEO4J_USER"))
print("DEBUG: NEO4J_PASSWORD =", os.getenv("NEO4J_PASSWORD"))

# Define Litellm variables here, as they are not dependent on Neo4j driver
LITELLM_URL = os.getenv("LITELLM_BASE_URL").rstrip("/")
LITELLM_KEY = os.getenv("LITELLM_API_KEY")
MODEL = "gpt-4o"

driver = None 
try:
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("WARNING: Neo4j environment variables (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) not fully set. Database connection will likely fail.")
    else:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("Neo4j driver initialized and connected successfully!")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Neo4j driver: {e}")
    driver = None 

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
    if driver is None:
        print("Cannot enrich graph: Neo4j driver is not available.")
        return

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

def serialize_value(value):
    if hasattr(value, "iso_format"):
        return value.iso_format()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    return value

@app.route("/")
def home():
    return jsonify({"message": "Hello, Flask!"})

@app.route("/enrich-graph")
def enrich_graph_route():
    enrich_graph()
    return jsonify({"message": "Graph enrichment process initiated. Check console for details."})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message")
    if not user_msg:
        return jsonify({"error": "Message is required"}), 400

    try:
        reply = ask_agent(user_msg, db_driver=driver)
        print(f"Agent reply: {reply}")
        return jsonify({"response": reply})
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.json
    user_msg = data.get("message")
    request_trace_id = str(uuid.uuid4())
    print(f"New incoming request with external_trace_id: {request_trace_id}")

    def generate():
        for chunk in stream_agent_steps(user_msg, db_driver=driver, external_trace_id=request_trace_id):
            yield f"data: {json.dumps(chunk)}\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route("/trace/<trace_id>")
def get_trace(trace_id):
    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        return jsonify({"error": "LANGCHAIN_API_KEY not set"}), 500

    try:
        client = Client(api_key=api_key)
        runs = list(client.list_runs(trace_id=trace_id))
        steps = []
        for run in runs:
            inputs = run.inputs if run.inputs else {}
            outputs = run.outputs if run.outputs else {}
            if outputs.get("output"):
                content = outputs["output"]
            elif outputs:
                content = str(outputs)
            elif inputs:
                content = str(inputs)
            else:
                content = "(no content)"
            steps.append({
                "step": run.name,
                "run_type": getattr(run, "run_type", ""),
                "inputs": inputs,
                "outputs": outputs,
                "content": content,
                "trace_id": run.id,
                "external_trace_id": trace_id,
                "start_time": str(getattr(run, "start_time", "")),
                "end_time": str(getattr(run, "end_time", "")),
            })
        return jsonify(steps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/graph")
def get_graph():
    if driver is None:
        return jsonify({"error": "Neo4j driver not available"}), 500

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                LIMIT 100
            """)
            nodes = {}
            links = []
            for record in result:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                def get_first_label(node):
                    return list(node.labels)[0] if node and node.labels else "Node"

                if n:
                    node_id = str(n.id)
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "label": n.get("title") or n.get("id") or get_first_label(n),
                            "group": get_first_label(n),
                            "properties": {k: serialize_value(v) for k, v in dict(n).items()}
                        }
                if m:
                    node_id = str(m.id)
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "label": m.get("title") or m.get("id") or get_first_label(m),
                            "group": get_first_label(m),
                            "properties": {k: serialize_value(v) for k, v in dict(m).items()}
                        }
                if r and n and m:
                    links.append({
                        "source": str(n.id),
                        "target": str(m.id),
                        "type": r.type,
                        "properties": {k: serialize_value(v) for k, v in dict(r).items()}
                    })
            return jsonify({
                "nodes": list(nodes.values()),
                "links": links
            })
    except Exception as e:
        print("Error in /graph:", e)
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)

