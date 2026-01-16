
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def check_relationships():
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            with driver.session() as session:
                # Get all relationship types
                result = session.run("CALL db.relationshipTypes()")
                types = [record["relationshipType"] for record in result]
                print(f"Relationship Types Found: {types}")
                
                # Check for specific interesting cross-doc relationships
                print("\nSample Relationships:")
                query = """
                MATCH (a)-[r]->(b) 
                RETURN distinct type(r) as type, labels(a)[0] as source_label, labels(b)[0] as target_label 
                LIMIT 10
                """
                result = session.run(query)
                for rec in result:
                    print(f" - ({rec['source_label']}) -[{rec['type']}]-> ({rec['target_label']})")
                    
                # Check if there are any REFERS_TO relationships between different documents
                # This would confirm "Inter-document" relationships
                print("\nChecking for Inter-Document Links (REFERS_TO):")
                query_refs = """
                MATCH (d1:Document)<-[:PART_OF]-(n1)-[:REFERS_TO]->(n2)-[:PART_OF]->(d2:Document)
                WHERE d1 <> d2
                RETURN d1.name, type(r), d2.name LIMIT 5
                """
                # Note: The schema might link chunks directly or via standard nodes. 
                # Let's just look for any REFERS_TO
                res_refs = session.run("MATCH ()-[r:REFERS_TO]->() RETURN count(r) as count")
                print(f"REFERS_TO count: {res_refs.single()['count']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_relationships()
