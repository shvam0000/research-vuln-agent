import os
from typing import TypedDict, Annotated, Any
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.tracers.context import collect_runs
from dotenv import load_dotenv
import json
from neo4j import GraphDatabase
import time
import uuid
from datetime import datetime, date

load_dotenv()

# --- Tools ---
@tool   
def explain_vector(vector: str) -> str:
    """Explains typical root causes or attack patterns for a specific vulnerability vector. Use this tool when the user asks about 'code', 'network', or 'config' vulnerabilities."""
    print(f"---CALLING TOOL: explain_vector with vector: {vector}---")
    return {
        "code": "Code issue: This typically involves input validation errors, the use of insecure libraries, or general logic flaws in the application code.",
        "network": "Network issue: This often points to exposed ports, misconfigured firewalls, or weak network segmentation that allows for unauthorized access.",
        "config": "Configuration issue: This is usually caused by default credentials, unsafe file permissions, or improperly configured logging and monitoring.",
    }.get(vector.lower(), "Unknown vector. Valid options are 'code', 'network', or 'config'.")

@tool
def query_neo4j(query: str, db_driver: Any = None) -> str:
    """
    Executes a Cypher query against the Neo4j database and returns the results.
    Use this tool to retrieve information about findings, vulnerabilities, or relationships
    from the knowledge graph.
    The query should be a valid Cypher query string.
    Example: MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability) RETURN f.id, v.title LIMIT 5
    """
    query_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    def serialize_value(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: serialize_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [serialize_value(v) for v in value]
        return value
    
    print(f"---CALLING TOOL: query_neo4j with query: {query}---")
    if db_driver is None:
        return "Error: Neo4j database driver not provided to tool."

    try:
        with db_driver.session() as session:
            print(f"---DEBUG: query: {query}---")
            print(f"---DEBUG: db_driver: {db_driver}---")
            print(f"---DEBUG: session: {session}---")
            result = session.run(query)
            records = [serialize_value(record.data()) for record in result]
        if records:
            duration = time.time() - start_time
            print(f"✅ [QUERY-{query_id}] Completed in {duration:.3f}s")
            return json.dumps(records, indent=2)
        else:
            duration = time.time() - start_time
            print(f"✅ [QUERY-{query_id}] No results in {duration:.3f}s")
            return "No results found for the query."
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ [QUERY-{query_id}] Error in 0.065s: {e}") # Corrected duration here based on your log
        return f"Error executing Neo4j query: {e}"

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], lambda x, y: x + y]
    db_driver: Any
    trace_id: str
    user_id: str
    timestamp: str

# --- Agent Nodes ---
def call_model(state: AgentState):
    """Calls the LLM with the current state of messages."""
    print("---CALLING MODEL---")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def call_tool(state: AgentState, config: dict):
    """Executes tools based on the model's last response."""
    last_message = state["messages"][-1]
    tool_outputs = []
    db_driver = state.get("db_driver")
    print(f"---DEBUG: db_driver in config: {db_driver is not None}---")

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        print(f"---EXECUTING TOOL: {tool_name}---")
        try:
            if tool_name == "explain_vector":
                tool_output = explain_vector.invoke(tool_call["args"])
                tool_outputs.append(
                    ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                )
            elif tool_name == "query_neo4j":
                if db_driver:
                    tool_args = tool_call["args"].copy()
                    tool_args["db_driver"] = db_driver
                    tool_output = query_neo4j.invoke(tool_args)
                    tool_outputs.append(
                        ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                    )
                else:
                    tool_outputs.append(
                        ToolMessage(content="Error: Neo4j driver not available in config.", tool_call_id=tool_call["id"])
                    )
            else:
                tool_outputs.append(
                    ToolMessage(content=f"Unknown tool: {tool_name}", tool_call_id=tool_call["id"])
                )
        except Exception as e:
            tool_outputs.append(
                ToolMessage(content=f"Error executing tool {tool_name}: {e}", tool_call_id=tool_call["id"])
            )
    return {"messages": tool_outputs}

# --- Conditional Router ---
def should_continue(state: AgentState):
    """Router logic to decide the next step."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    return "end"

# --- Graph Definition ---
llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=os.getenv("LITELLM_API_KEY"),
    openai_api_base=os.getenv("LITELLM_BASE_URL").rstrip("/"),
)
llm_with_tools = llm.bind_tools([explain_vector, query_neo4j])

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "action", "end": END},
)
workflow.add_edge("action", "agent")
chain = workflow.compile()

# --- Public Functions ---
# def stream_agent_steps(user_msg: str, db_driver=None, external_trace_id: str = None):
#     """Streams the agent's intermediate steps, yielding a JSON object for each step."""
#     try:
#         inputs = {
#             "messages": [
#                 SystemMessage(content="""You are a helpful cybersecurity analyst.
# Your primary goal is to answer user questions about vulnerabilities and findings from a Neo4j knowledge graph.

# **DATABASE SCHEMA:**
# - Finding nodes have properties: id, scanner, scan_id, timestamp
# - Vulnerability nodes have properties: title, description, severity, vector, cwe_id, owasp_id
# - Asset nodes have properties: url, type, service
# - Relationships: (Finding)-[:HAS_VULNERABILITY]->(Vulnerability), (Finding)-[:AFFECTS]->(Asset)

# **IMPORTANT:** To get finding ID and title together, you must join Finding and Vulnerability nodes:
# MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability) RETURN f.id, v.title

# You have access to two tools:
# 1. explain_vector(vector: str): Explains typical root causes or attack patterns for 'code', 'network', or 'config' vulnerabilities.
# 2. query_neo4j(query: str, db_driver: Any): Executes a Cypher query against the Neo4j knowledge graph.

# Always think step-by-step and show your reasoning.
# """),
#                 HumanMessage(content=user_msg)
#             ],
#             "db_driver": db_driver,
#             "user_id": "anonymous",
#             "timestamp": datetime.now().isoformat()
#         }

#         # Method 1: Use external_trace_id as the thread_id for consistent run tracking
#         config = {"recursion_limit": 50}
#         if external_trace_id:
#             config["configurable"] = {"thread_id": external_trace_id}
#             print(f"🔍 [EXTERNAL-TRACE-{external_trace_id}] Using external trace ID as thread_id")

#         # Method 2: Get the run ID from the first chunk
#         current_run_id = external_trace_id or "unknown-trace"
#         run_id_extracted = False

#         # Stream response from the agent
#         for chunk in chain.stream(inputs, config, stream_mode="updates"):
#             # Extract run ID from the first chunk that contains it
#             if not run_id_extracted:
#                 # Try multiple ways to get the run ID
#                 if hasattr(chunk, '__run__') and hasattr(chunk['__run__'], 'id'):
#                     current_run_id = chunk['__run__'].id
#                     run_id_extracted = True
#                     print(f"🔍 [LANGGRAPH-RUN-{current_run_id}] Extracted from __run__.id")
#                 elif "__run" in chunk and hasattr(chunk["__run"], "id"):
#                     current_run_id = chunk["__run"].id
#                     run_id_extracted = True
#                     print(f"🔍 [LANGGRAPH-RUN-{current_run_id}] Extracted from __run.id")
#                 elif "agent" in chunk and chunk["agent"].get("messages"):
#                     # Try to extract from message IDs
#                     for msg in chunk["agent"]["messages"]:
#                         if hasattr(msg, 'id') and msg.id.startswith('run--'):
#                             try:
#                                 # Extract UUID from "run--uuid-step"
#                                 run_uuid = msg.id.split("--")[1].split("-")[0]
#                                 current_run_id = run_uuid
#                                 run_id_extracted = True
#                                 print(f"🔍 [LANGGRAPH-RUN-{current_run_id}] Extracted from message ID")
#                                 break
#                             except Exception:
#                                 continue

#             if "agent" in chunk:
#                 agent_message = chunk["agent"]["messages"][-1]
#                 if agent_message.tool_calls:
#                     yield {
#                         "step": "Thought",
#                         "content": f"I should use the tool {agent_message.tool_calls[0]['name']} with the arguments {json.dumps(agent_message.tool_calls[0]['args'])}.",
#                         "trace_id": str(current_run_id),
#                         "external_trace_id": external_trace_id
#                     }
#                 else:
#                     yield {
#                         "step": "Final Answer",
#                         "content": agent_message.content,
#                         "trace_id": str(current_run_id),
#                         "external_trace_id": external_trace_id
#                     }

#             elif "action" in chunk:
#                 action_message = chunk["action"]["messages"][-1]
#                 yield {
#                     "step": "Action",
#                     "content": f"Output of tool {action_message.name}: {action_message.content}",
#                     "trace_id": str(current_run_id),
#                     "external_trace_id": external_trace_id
#                 }

#     except Exception as e:
#         print(f"[LangGraph STREAM ERROR] {type(e).__name__}: {e}")
#         yield {"step": "Error", "content": f"An error occurred: {e}", "trace_id": current_run_id, "external_trace_id": external_trace_id}

def stream_agent_steps(user_msg: str, db_driver=None, external_trace_id: str = None):
    """Streams the agent's intermediate steps, yielding a JSON object for each step with trace_id support."""
    try:
        # Assign a consistent trace_id (either from external client or new UUID)
        current_run_id = external_trace_id or str(uuid.uuid4())
        print(f"📍 Using run_id / trace_id: {current_run_id}")

        inputs = {
            "messages": [
                SystemMessage(content="""You are a helpful cybersecurity analyst.
Your primary goal is to answer user questions about vulnerabilities and findings from a Neo4j knowledge graph.

**DATABASE SCHEMA:**
- Finding nodes have properties: id, scanner, scan_id, timestamp
- Vulnerability nodes have properties: title, description, severity, vector, cwe_id, owasp_id
- Asset nodes have properties: url, type, service
- Relationships: (Finding)-[:HAS_VULNERABILITY]->(Vulnerability), (Finding)-[:AFFECTS]->(Asset)

**IMPORTANT:** To get finding ID and title together, you must join Finding and Vulnerability nodes:
MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability) RETURN f.id, v.title

You have access to two tools:
1. explain_vector(vector: str): Explains typical root causes or attack patterns for 'code', 'network', or 'config' vulnerabilities.
2. query_neo4j(query: str, db_driver: Any): Executes a Cypher query against the Neo4j knowledge graph.

Always think step-by-step and show your reasoning.
"""),
                HumanMessage(content=user_msg)
            ],
            "db_driver": db_driver,
            "user_id": "anonymous",
            "timestamp": datetime.now().isoformat()
        }

        # Use current_run_id as both the run and thread identifier
        config = {
            "recursion_limit": 50,
            "run_id": current_run_id,
            "configurable": {"thread_id": current_run_id}
        }

        # Stream response from the agent
        for chunk in chain.stream(inputs, config=config, stream_mode="updates"):
            if "agent" in chunk:
                agent_message = chunk["agent"]["messages"][-1]
                if agent_message.tool_calls:
                    yield {
                        "step": "Thought",
                        "content": f"I should use the tool {agent_message.tool_calls[0]['name']} with the arguments {json.dumps(agent_message.tool_calls[0]['args'])}.",
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id
                    }
                else:
                    yield {
                        "step": "Final Answer",
                        "content": agent_message.content,
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id
                    }

            elif "action" in chunk:
                action_message = chunk["action"]["messages"][-1]
                yield {
                    "step": "Action",
                    "content": f"Output of tool {action_message.name}: {action_message.content}",
                    "trace_id": str(current_run_id),
                    "external_trace_id": external_trace_id
                }

            else:
                yield {
                    "step": "Unknown",
                    "content": json.dumps(chunk),
                    "trace_id": str(current_run_id),
                    "external_trace_id": external_trace_id
                }

    except Exception as e:
        print(f"[LangGraph STREAM ERROR] {type(e).__name__}: {e}")
        yield {
            "step": "Error",
            "content": f"An error occurred: {e}",
            "trace_id": str(current_run_id),
            "external_trace_id": external_trace_id
        }



def ask_agent(user_msg: str, db_driver=None):
    """Invokes the agent graph and returns the final response."""
    try:
        inputs = {"messages": [
            SystemMessage(content="You are a helpful cybersecurity analyst."),
            HumanMessage(content=user_msg)
        ]}
        final_state = chain.invoke(inputs, config={"db_driver": db_driver})
        return final_state["messages"][-1].content
    except Exception as e:
        print(f"[LangGraph ERROR] {type(e).__name__}: {e}")
        return f"An error occurred: {e}"