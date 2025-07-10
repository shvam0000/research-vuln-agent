#!/usr/bin/env python3
"""
Test script to verify the agent can connect to Neo4j and execute queries
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langgraph_agent import stream_agent_steps

# Load environment variables
load_dotenv()

def test_agent_with_neo4j():
    """Test the agent with Neo4j connection"""
    print("=== Testing Agent with Neo4j ===")
    
    try:
        # Create Neo4j driver
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        print("✅ Neo4j driver created successfully")
        
        # Test a simple query first
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"✅ Database has {count} nodes")
        
        # Test the agent
        test_query = "How many findings are in the database?"
        print(f"\n🔍 Testing agent with query: '{test_query}'")
        
        steps = list(stream_agent_steps(test_query, db_driver=driver))
        
        print("\n📋 Agent Steps:")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step['step']}: {step['content'][:100]}...")
        
        driver.close()
        print("\n✅ Agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_with_neo4j() 