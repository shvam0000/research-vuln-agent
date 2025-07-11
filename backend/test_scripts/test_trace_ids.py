#!/usr/bin/env python3
"""
Test script to demonstrate trace ID handling and parent run ID extraction.
"""

import os
import sys
import uuid
from datetime import datetime

# Add the backend directory to the path
sys.path.append('backend')

from langgraph_agent import stream_agent_steps, ask_agent
from neo4j import GraphDatabase

def test_trace_ids():
    """Test trace ID generation and extraction."""
    
    # Initialize Neo4j driver
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
    )
    
    # Test 1: Streaming with external trace ID
    print("=" * 60)
    print("TEST 1: Streaming with external trace ID")
    print("=" * 60)
    
    external_trace_id = str(uuid.uuid4())
    print(f"External Trace ID: {external_trace_id}")
    
    user_msg = "What vulnerabilities are in finding F-101?"
    
    print(f"\nUser Message: {user_msg}")
    print("\nStreaming response:")
    
    for step in stream_agent_steps(user_msg, db_driver=driver, external_trace_id=external_trace_id):
        print(f"  Step: {step['step']}")
        print(f"  Trace ID: {step.get('trace_id', 'N/A')}")
        print(f"  External Trace ID: {step.get('external_trace_id', 'N/A')}")
        print(f"  Content: {step['content'][:100]}...")
        print()
    
    # Test 2: Non-streaming with external trace ID
    print("=" * 60)
    print("TEST 2: Non-streaming with external trace ID")
    print("=" * 60)
    
    external_trace_id_2 = str(uuid.uuid4())
    print(f"External Trace ID: {external_trace_id_2}")
    
    user_msg_2 = "How many findings are there?"
    
    print(f"\nUser Message: {user_msg_2}")
    
    response = ask_agent(user_msg_2, db_driver=driver, external_trace_id=external_trace_id_2)
    print(f"\nResponse: {response[:200]}...")
    
    # Test 3: Without external trace ID (LangGraph generates one)
    print("=" * 60)
    print("TEST 3: Without external trace ID (LangGraph generates one)")
    print("=" * 60)
    
    user_msg_3 = "What is the most common vulnerability type?"
    
    print(f"\nUser Message: {user_msg_3}")
    print("\nStreaming response:")
    
    for step in stream_agent_steps(user_msg_3, db_driver=driver):
        print(f"  Step: {step['step']}")
        print(f"  Trace ID: {step.get('trace_id', 'N/A')}")
        print(f"  External Trace ID: {step.get('external_trace_id', 'N/A')}")
        print(f"  Content: {step['content'][:100]}...")
        print()
    
    driver.close()
    print("Test completed!")

if __name__ == "__main__":
    test_trace_ids() 