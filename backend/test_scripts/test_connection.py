#!/usr/bin/env python3
"""
Test script to verify Neo4j and Litellm connections
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import requests

# Load environment variables
load_dotenv()

def test_env_variables():
    """Test if all required environment variables are set"""
    print("=== Testing Environment Variables ===")
    
    required_vars = [
        "NEO4J_URI",
        "NEO4J_USER", 
        "NEO4J_PASSWORD",
        "LITELLM_BASE_URL",
        "LITELLM_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"{var}: {value[:10]}..." if len(value) > 10 else f"{var}: {value}")
        else:
            print(f"{var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\nMissing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return False
    else:
        print("\nAll environment variables are set!")
        return True

def test_neo4j_connection():
    """Test Neo4j connection"""
    print("\n=== Testing Neo4j Connection ===")
    
    try:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, user, password]):
            print("Neo4j environment variables not set")
            return False
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Neo4j connection successful!")
        
        # Test a simple query
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print(f"Neo4j query test successful! {record}")
                # print("✅ Neo4j query test successful!")
            else:
                print("Neo4j query test failed")
                return False
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        return False

def test_litellm_connection():
    """Test Litellm connection"""
    print("\n=== Testing Litellm Connection ===")
    
    try:
        base_url = os.getenv("LITELLM_BASE_URL")
        api_key = os.getenv("LITELLM_API_KEY")
        
        if not all([base_url, api_key]):
            print("Litellm environment variables not set")
            return False
        
        # Test with a simple completion request
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("Litellm connection successful!")
            return True
        else:
            print(f"Litellm connection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Litellm connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing application connections...\n")
    
    # Test environment variables
    env_ok = test_env_variables()
    
    if not env_ok:
        print("\nEnvironment variables not properly set. Please:")
        print("1. Copy config.env to .env")
        print("2. Update .env with your actual values")
        print("3. Run this test again")
        return
    
    # Test connections
    neo4j_ok = test_neo4j_connection()
    litellm_ok = test_litellm_connection()
    
    print("\n=== Summary ===")
    if neo4j_ok and litellm_ok:
        print("All connections successful! Your application should work.")
    else:
        print("Some connections failed. Please check your configuration.")

if __name__ == "__main__":
    main() 