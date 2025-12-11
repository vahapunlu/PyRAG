"""Quick Neo4j content checker"""
from src.query_engine import QueryEngine

print("Loading QueryEngine (this will initialize Neo4j)...")
qe = QueryEngine()

gm = qe.graph_retriever.graph_manager

print("\n=== NEO4J DATABASE CONTENTS ===\n")

with gm.driver.session() as session:
    # Count by label
    result = session.run("""
        MATCH (n) 
        RETURN labels(n)[0] as label, count(*) as count 
        ORDER BY count DESC
    """)
    
    print("Node counts by label:")
    for record in result:
        print(f"  {record['label']}: {record['count']}")
    
    # Check for SECTION nodes specifically
    section_check = session.run("""
        MATCH (s:SECTION)
        RETURN count(s) as section_count
    """)
    section_count = section_check.single()['section_count']
    print(f"\n📋 SECTION nodes found: {section_count}")
    
    # Sample DOCUMENT nodes
    doc_check = session.run("""
        MATCH (d:DOCUMENT)
        RETURN d.name as name
        LIMIT 5
    """)
    print(f"\n📄 Sample documents in Neo4j:")
    for record in doc_check:
        print(f"  - {record['name']}")

gm.close()
print("\n✅ Done!\n")
