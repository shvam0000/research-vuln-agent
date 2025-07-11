import os
from typing import TypedDict, Annotated, Any
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
from neo4j import GraphDatabase
import time
import uuid
from datetime import datetime, date

load_dotenv()

# --- Neo4j Driver Initialization ---
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
        print("Neo4j driver initialized and connected successfully in multi-agent system!")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Neo4j driver in multi-agent system: {e}")
    driver = None

# --- Shared Tools ---
@tool   
def query_neo4j(query: str, db_driver: Any = None) -> str:
    """Executes a Cypher query against the Neo4j database and returns the results."""
    query_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    def serialize_value(value):
        # Handle Neo4j DateTime objects
        if hasattr(value, 'iso_format'):
            return value.iso_format()
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: serialize_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [serialize_value(v) for v in value]
        return value
    
    print(f"---CALLING TOOL: query_neo4j with query: {query}---")
    
    # Use the passed db_driver or fall back to the global driver
    db_driver_to_use = db_driver if db_driver is not None else driver
    
    if db_driver_to_use is None:
        return "Error: Neo4j database driver not available."

    try:
        with db_driver_to_use.session() as session:
            result = session.run(query)
            records = [serialize_value(record.data()) for record in result]
        if records:
            duration = time.time() - start_time
            print(f"[QUERY-{query_id}] Completed in {duration:.3f}s")
            return json.dumps(records, indent=2)
        else:
            duration = time.time() - start_time
            print(f"[QUERY-{query_id}] No results in {duration:.3f}s")
            return "No results found for the query."
    except Exception as e:
        duration = time.time() - start_time
        print(f"[QUERY-{query_id}] Error in {duration:.3f}s: {e}")
        return f"Error executing Neo4j query: {e}"

# --- Analysis Agent Tools ---
@tool
def analyze_vulnerability_severity(finding_id: str, db_driver: Any = None) -> str:
    """Analyzes the severity and impact of a specific vulnerability finding."""
    query = f"""
    MATCH (f:Finding {{id: '{finding_id}'}})-[:HAS_VULNERABILITY]->(v:Vulnerability)
    OPTIONAL MATCH (f)-[:AFFECTS]->(a:Asset)
    RETURN f.id as finding_id, v.title as vulnerability, v.severity as severity, 
           v.description as description, v.vector as vector, 
           COALESCE(a.url, a.path, a.image, 'Unknown') as asset_url
    """
    return query_neo4j(query, db_driver)

@tool
def find_similar_vulnerabilities(cwe_id: str, db_driver: Any = None) -> str:
    """Finds vulnerabilities with the same CWE ID to identify patterns."""
    query = f"""
    MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability {{cwe_id: '{cwe_id}'}})
    RETURN f.id as finding_id, v.title as vulnerability, v.severity as severity
    ORDER BY v.severity DESC
    """
    return query_neo4j(query, db_driver)

# --- Correlation Agent Tools ---
@tool
def find_attack_chains(finding_id: str, db_driver: Any = None) -> str:
    """Identifies potential attack chains starting from a specific finding."""
    query = f"""
    MATCH (f:Finding {{id: '{finding_id}'}})-[:HAS_VULNERABILITY]->(v:Vulnerability)
    MATCH (f)-[:AFFECTS]->(a:Asset)
    OPTIONAL MATCH (a)<-[:AFFECTS]-(f2:Finding)-[:HAS_VULNERABILITY]->(v2:Vulnerability)
    WHERE f2.id <> f.id
    RETURN f.id as source_finding, v.title as source_vuln, a.url as target_asset,
           f2.id as related_finding, v2.title as related_vuln
    """
    return query_neo4j(query, db_driver)

@tool
def analyze_temporal_patterns(db_driver: Any = None) -> str:
    """Analyzes temporal patterns in vulnerability discoveries."""
    query = """
    MATCH (f:Finding)
    WITH f.timestamp as scan_time, count(f) as finding_count
    ORDER BY scan_time
    RETURN scan_time, finding_count
    LIMIT 10
    """
    return query_neo4j(query, db_driver)

# --- Risk Assessment Agent Tools ---
@tool
def calculate_risk_score(finding_id: str, db_driver: Any = None) -> str:
    """Calculates a risk score for a specific finding based on multiple factors."""
    query = f"""
    MATCH (f:Finding {{id: '{finding_id}'}})-[:HAS_VULNERABILITY]->(v:Vulnerability)
    OPTIONAL MATCH (f)-[:AFFECTS]->(a:Asset)
    WITH f, v, a,
         CASE v.severity 
           WHEN 'CRITICAL' THEN 10 
           WHEN 'HIGH' THEN 7 
           WHEN 'MEDIUM' THEN 4 
           WHEN 'LOW' THEN 1 
           ELSE 0 
         END as severity_score
    RETURN f.id as finding_id, v.title as vulnerability, v.severity as severity,
           severity_score as risk_score, 
           COALESCE(a.url, a.path, a.image, 'Unknown') as affected_asset
    """
    return query_neo4j(query, db_driver)

@tool
def assess_asset_criticality(asset_url: str, db_driver: Any = None) -> str:
    """Assesses the criticality of an asset based on vulnerability exposure."""
    query = f"""
    MATCH (f:Finding)-[:AFFECTS]->(a:Asset)
    WHERE a.url = '{asset_url}' OR a.path = '{asset_url}' OR a.image = '{asset_url}'
    MATCH (f)-[:HAS_VULNERABILITY]->(v:Vulnerability)
    WITH a, count(f) as vulnerability_count,
         sum(CASE v.severity 
               WHEN 'CRITICAL' THEN 1 
               WHEN 'HIGH' THEN 1 
               ELSE 0 
             END) as high_critical_count
    RETURN COALESCE(a.url, a.path, a.image, 'Unknown') as asset, 
           vulnerability_count, high_critical_count,
           CASE 
             WHEN high_critical_count > 0 THEN 'CRITICAL'
             WHEN vulnerability_count > 3 THEN 'HIGH'
             WHEN vulnerability_count > 1 THEN 'MEDIUM'
             ELSE 'LOW'
           END as asset_criticality
    """
    return query_neo4j(query, db_driver)

# --- Recommendation Agent Tools ---
@tool
def generate_mitigation_strategy(cwe_id: str, db_driver: Any = None) -> str:
    """Generates mitigation strategies for vulnerabilities with specific CWE IDs."""
    query = f"""
    MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability {{cwe_id: '{cwe_id}'}})
    RETURN DISTINCT v.cwe_id as cwe_id, v.title as vulnerability_title,
           v.description as description, v.vector as attack_vector
    LIMIT 1
    """
    return query_neo4j(query, db_driver)

@tool
def find_priority_remediation_order(db_driver: Any = None) -> str:
    """Finds the optimal order for remediating vulnerabilities based on risk and impact."""
    query = """
    MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability)
    OPTIONAL MATCH (f)-[:AFFECTS]->(a:Asset)
    WITH f, v, a,
         CASE v.severity 
           WHEN 'CRITICAL' THEN 4 
           WHEN 'HIGH' THEN 3 
           WHEN 'MEDIUM' THEN 2 
           WHEN 'LOW' THEN 1 
           ELSE 0 
         END as priority_score
    RETURN f.id as finding_id, v.title as vulnerability, v.severity as severity,
           priority_score, COALESCE(a.url, a.path, a.image, 'Unknown') as affected_asset
    ORDER BY priority_score DESC, f.id
    LIMIT 10
    """
    return query_neo4j(query, db_driver)

# --- Agent State ---
class MultiAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], lambda x, y: x + y]
    db_driver: Any
    trace_id: str
    user_id: str
    timestamp: str
    current_agent: str
    analysis_results: dict
    correlation_results: dict
    risk_results: dict
    recommendation_results: dict

# --- Agent Definitions ---
llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=os.getenv("LITELLM_API_KEY"),
    openai_api_base=os.getenv("LITELLM_BASE_URL").rstrip("/"),
)

# Analysis Agent
analysis_tools = [analyze_vulnerability_severity, find_similar_vulnerabilities, query_neo4j]
analysis_llm = llm.bind_tools(analysis_tools)

# Correlation Agent  
correlation_tools = [find_attack_chains, analyze_temporal_patterns, query_neo4j]
correlation_llm = llm.bind_tools(correlation_tools)

# Risk Assessment Agent
risk_tools = [calculate_risk_score, assess_asset_criticality, query_neo4j]
risk_llm = llm.bind_tools(risk_tools)

# Recommendation Agent
recommendation_tools = [generate_mitigation_strategy, find_priority_remediation_order, query_neo4j]
recommendation_llm = llm.bind_tools(recommendation_tools)

# --- Agent Functions ---
def analysis_agent(state: MultiAgentState):
    """Analysis Agent: Analyzes vulnerability details and patterns."""
    print("---ANALYSIS AGENT WORKING---")
    system_prompt = """You are a Vulnerability Analysis Agent. Your role is to:
1. Analyze vulnerability severity and impact
2. Identify patterns in similar vulnerabilities
3. Provide detailed technical analysis
4. Focus on understanding the root cause and attack vectors

Use your tools to gather comprehensive information about vulnerabilities."""
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = analysis_llm.invoke(messages)
    return {"messages": [response], "current_agent": "analysis"}

def correlation_agent(state: MultiAgentState):
    """Correlation Agent: Identifies relationships and attack chains."""
    print("---CORRELATION AGENT WORKING---")
    system_prompt = """You are a Vulnerability Correlation Agent. Your role is to:
1. Identify attack chains and relationships between findings
2. Analyze temporal patterns in vulnerability discovery
3. Connect related vulnerabilities across different assets
4. Find potential cascading effects

Use your tools to discover relationships and patterns."""
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = correlation_llm.invoke(messages)
    return {"messages": [response], "current_agent": "correlation"}

def risk_assessment_agent(state: MultiAgentState):
    """Risk Assessment Agent: Evaluates risk levels and asset criticality."""
    print("---RISK ASSESSMENT AGENT WORKING---")
    system_prompt = """You are a Risk Assessment Agent. Your role is to:
1. Calculate risk scores for vulnerabilities
2. Assess asset criticality and exposure
3. Evaluate business impact
4. Prioritize findings based on risk

Use your tools to quantify and assess risks."""
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = risk_llm.invoke(messages)
    return {"messages": [response], "current_agent": "risk"}

def recommendation_agent(state: MultiAgentState):
    """Recommendation Agent: Provides mitigation strategies and remediation plans."""
    print("---RECOMMENDATION AGENT WORKING---")
    system_prompt = """You are a Recommendation Agent. Your role is to:
1. Generate specific mitigation strategies
2. Create prioritized remediation plans
3. Provide actionable security recommendations
4. Suggest best practices and controls

Use your tools to create practical remediation guidance."""
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = recommendation_llm.invoke(messages)
    return {"messages": [response], "current_agent": "recommendation"}

def execute_tools(state: MultiAgentState):
    """Executes tools based on the current agent's response."""
    last_message = state["messages"][-1]
    tool_outputs = []
    db_driver = state.get("db_driver")
    current_agent = state.get("current_agent", "unknown")

    print(f"---DEBUG: db_driver in execute_tools: {db_driver is not None}---")

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        print(f"---{current_agent.upper()} AGENT EXECUTING TOOL: {tool_name}---")
        try:
            # Get the appropriate tool function
            tool_func = None
            if tool_name == "analyze_vulnerability_severity":
                tool_func = analyze_vulnerability_severity
            elif tool_name == "find_similar_vulnerabilities":
                tool_func = find_similar_vulnerabilities
            elif tool_name == "find_attack_chains":
                tool_func = find_attack_chains
            elif tool_name == "analyze_temporal_patterns":
                tool_func = analyze_temporal_patterns
            elif tool_name == "calculate_risk_score":
                tool_func = calculate_risk_score
            elif tool_name == "assess_asset_criticality":
                tool_func = assess_asset_criticality
            elif tool_name == "generate_mitigation_strategy":
                tool_func = generate_mitigation_strategy
            elif tool_name == "find_priority_remediation_order":
                tool_func = find_priority_remediation_order
            elif tool_name == "query_neo4j":
                tool_func = query_neo4j
            
            if tool_func:
                tool_args = tool_call["args"].copy()
                # Always add db_driver to tool_args if the tool accepts it
                if hasattr(tool_func, '__annotations__') and 'db_driver' in tool_func.__annotations__:
                    tool_args["db_driver"] = db_driver
                tool_output = tool_func.invoke(tool_args)
                tool_outputs.append(
                    ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
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

# --- Multi-Agent Orchestrator ---
def orchestrator(state: MultiAgentState):
    """Orchestrates the flow between different agents."""
    user_message = state["messages"][-1].content if state["messages"] else ""
    current_agent = state.get("current_agent", "")
    
    # Simple routing logic - can be made more sophisticated
    if not current_agent:
        # First time - start with analysis
        return {"current_agent": "analysis"}
    elif current_agent == "analysis":
        return {"current_agent": "correlation"}
    elif current_agent == "correlation":
        return {"current_agent": "risk"}
    elif current_agent == "risk":
        return {"current_agent": "recommendation"}
    else:
        # After recommendation, end
        return {"current_agent": "end"}

def should_continue(state: MultiAgentState):
    """Determines if the agent should continue or end."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "orchestrator"

def route_to_agent(state: MultiAgentState):
    """Routes to the appropriate agent based on current_agent state."""
    current_agent = state.get("current_agent", "")
    if current_agent == "analysis":
        return "analysis"
    elif current_agent == "correlation":
        return "correlation"
    elif current_agent == "risk":
        return "risk"
    elif current_agent == "recommendation":
        return "recommendation"
    else:
        return END

# --- Multi-Agent Graph ---
workflow = StateGraph(MultiAgentState)

# Add agent nodes
workflow.add_node("analysis", analysis_agent)
workflow.add_node("correlation", correlation_agent)
workflow.add_node("risk", risk_assessment_agent)
workflow.add_node("recommendation", recommendation_agent)
workflow.add_node("tools", execute_tools)
workflow.add_node("orchestrator", orchestrator)

# Set entry point
workflow.set_entry_point("orchestrator")

# Add conditional edges
workflow.add_conditional_edges(
    "orchestrator",
    route_to_agent,
    {
        "analysis": "analysis",
        "correlation": "correlation", 
        "risk": "risk",
        "recommendation": "recommendation",
        END: END
    }
)

workflow.add_conditional_edges(
    "analysis",
    should_continue,
    {"tools": "tools", "orchestrator": "orchestrator"}
)

workflow.add_conditional_edges(
    "correlation", 
    should_continue,
    {"tools": "tools", "orchestrator": "orchestrator"}
)

workflow.add_conditional_edges(
    "risk",
    should_continue,
    {"tools": "tools", "orchestrator": "orchestrator"}
)

workflow.add_conditional_edges(
    "recommendation",
    should_continue,
    {"tools": "tools", "orchestrator": "orchestrator"}
)

workflow.add_edge("tools", "orchestrator")

# Compile the multi-agent system
multi_agent_chain = workflow.compile()

# --- Streaming Function ---
def stream_multi_agent_steps(user_msg: str, db_driver=None, external_trace_id: str = None):
    """Streams the multi-agent system's steps."""
    try:
        current_run_id = external_trace_id or str(uuid.uuid4())
        print(f"Multi-Agent System using run_id: {current_run_id}")
        print(f"---DEBUG: db_driver in stream_multi_agent_steps: {db_driver is not None}---")

        # Use the passed db_driver or fall back to the global driver
        db_driver_to_use = db_driver if db_driver is not None else driver

        inputs = {
            "messages": [HumanMessage(content=user_msg)],
            "db_driver": db_driver_to_use,  # Use the available driver
            "user_id": "anonymous",
            "timestamp": datetime.now().isoformat(),
            "current_agent": "",
            "analysis_results": {},
            "correlation_results": {},
            "risk_results": {},
            "recommendation_results": {}
        }

        config = {
            "recursion_limit": 100,
            "run_id": current_run_id,
            "configurable": {"thread_id": current_run_id}
        }

        for chunk in multi_agent_chain.stream(inputs, config=config, stream_mode="updates"):
            if "analysis" in chunk:
                agent_message = chunk["analysis"]["messages"][-1]
                if agent_message.tool_calls:
                    yield {
                        "step": "Analysis Agent",
                        "content": f"🔍 Analyzing vulnerability patterns and details...",
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "analysis"
                    }
                else:
                    yield {
                        "step": "Analysis Complete",
                        "content": agent_message.content,
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "analysis"
                    }

            elif "correlation" in chunk:
                agent_message = chunk["correlation"]["messages"][-1]
                if agent_message.tool_calls:
                    yield {
                        "step": "Correlation Agent",
                        "content": f"🔗 Identifying relationships and attack chains...",
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "correlation"
                    }
                else:
                    yield {
                        "step": "Correlation Complete",
                        "content": agent_message.content,
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "correlation"
                    }

            elif "risk" in chunk:
                agent_message = chunk["risk"]["messages"][-1]
                if agent_message.tool_calls:
                    yield {
                        "step": "Risk Assessment Agent",
                        "content": f"⚠️ Calculating risk scores and assessing criticality...",
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "risk"
                    }
                else:
                    yield {
                        "step": "Risk Assessment Complete",
                        "content": agent_message.content,
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "risk"
                    }

            elif "recommendation" in chunk:
                agent_message = chunk["recommendation"]["messages"][-1]
                if agent_message.tool_calls:
                    yield {
                        "step": "Recommendation Agent",
                        "content": f"💡 Generating mitigation strategies and remediation plans...",
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "recommendation"
                    }
                else:
                    yield {
                        "step": "Recommendation Complete",
                        "content": agent_message.content,
                        "trace_id": str(current_run_id),
                        "external_trace_id": external_trace_id,
                        "agent": "recommendation"
                    }

            elif "tools" in chunk:
                action_message = chunk["tools"]["messages"][-1]
                yield {
                    "step": "Tool Execution",
                    "content": f"🛠️ {action_message.content}",
                    "trace_id": str(current_run_id),
                    "external_trace_id": external_trace_id,
                    "agent": "tools"
                }

    except Exception as e:
        print(f"[Multi-Agent STREAM ERROR] {type(e).__name__}: {e}")
        yield {
            "step": "Error",
            "content": f"An error occurred: {e}",
            "trace_id": str(current_run_id),
            "external_trace_id": external_trace_id,
            "agent": "error"
        } 