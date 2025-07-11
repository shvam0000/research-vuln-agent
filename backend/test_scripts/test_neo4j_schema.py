#!/usr/bin/env python3
"""
Test script to explore the Neo4j database schema and properties
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

def explore_neo4j_schema():
    """Explore the actual schema and properties in Neo4j"""
    print("=== Exploring Neo4j Schema ===")
    
    try:
        # Create Neo4j driver
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        print("Neo4j driver created successfully")
        
        with driver.session() as session:
            # Get all Finding nodes and their properties
            print("\n--- Finding Nodes ---")
            result = session.run("MATCH (f:Finding) RETURN f LIMIT 3")
            for record in result:
                finding = record["f"]
                print(f"Finding properties: {dict(finding)}")
            
            # Get all Vulnerability nodes and their properties
            print("\n--- Vulnerability Nodes ---")
            result = session.run("MATCH (v:Vulnerability) RETURN v LIMIT 3")
            for record in result:
                vuln = record["v"]
                print(f"Vulnerability properties: {dict(vuln)}")
            
            # Get all Asset nodes and their properties
            print("\n--- Asset Nodes ---")
            result = session.run("MATCH (a:Asset) RETURN a LIMIT 3")
            for record in result:
                asset = record["a"]
                print(f"Asset properties: {dict(asset)}")
            
            # Test the correct query
            print("\n--- Correct Query Test ---")
            result = session.run("MATCH (f:Finding)-[:HAS_VULNERABILITY]->(v:Vulnerability) RETURN f.id, v.title LIMIT 5")
            for record in result:
                print(f"Finding ID: {record['f.id']}, Title: {record['v.title']}")
        
        driver.close()
        print("\nSchema exploration completed!")
        
    except Exception as e:
        print(f"Schema exploration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    explore_neo4j_schema() 