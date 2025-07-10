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


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
load_dotenv() # This must be called early to load environment variables
print("DEBUG: NEO4J_URI =", os.getenv("NEO4J_URI"))
print("DEBUG: NEO4J_USER =", os.getenv("NEO4J_USER"))
print("DEBUG: NEO4J_PASSWORD =", os.getenv("NEO4J_PASSWORD"))

# Define Litellm variables here, as they are not dependent on Neo4j driver
LITELLM_URL = os.getenv("LITELLM_BASE_URL").rstrip("/")
LITELLM_KEY = os.getenv("LITELLM_API_KEY")
MODEL = "gpt-4o"

driver = None # Initialize to None
try:
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("WARNING: Neo4j environment variables (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) not fully set. Database connection will likely fail.")
    else:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # Attempt to verify connectivity, this will raise an exception if connection fails
        driver.verify_connectivity()
        print("Neo4j driver initialized and connected successfully!")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Neo4j driver: {e}")
    driver = None # Ensure it's None if connection fails

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
    # Only attempt to enrich if the driver is successfully initialized
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
        # Pass the driver to the ask_agent function
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

# @app.teardown_appcontext
# def close_driver(exception):
#     # Ensure driver exists before attempting to close
#     if driver:
#         try:
#             driver.close()
#             print("Neo4j driver closed.")
#         except Exception as e:
#             print(f"Error closing Neo4j driver: {e}")

if __name__ == "__main__":
    app.run(debug=True)

