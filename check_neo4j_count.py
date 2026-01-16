
from neo4j import GraphDatabase
import os

# Hardcoded for quick check based on .env content seen previously
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def print_node_counts():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            with driver.session() as session:
                # Total nodes
                result = session.run("MATCH (n) RETURN count(n) as total")
                total = result.single()["total"]
                print(f"Total Nodes: {total}")
                
                # Nodes by Label
                result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
                print("\nBreakdown by Label:")
                for record in result:
                    labels = record["labels"]
                    # labels is a list, usually one label per node in this schema but can be multiple
                    label_str = ":".join(labels) if labels else "No Label"
                    print(f" - {label_str}: {record['count']}")
                    
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

if __name__ == "__main__":
    print_node_counts()
