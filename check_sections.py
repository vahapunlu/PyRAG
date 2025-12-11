"""Check section structure in Neo4j"""
from src.query_engine import QueryEngine

print("Loading QueryEngine...")
qe = QueryEngine()
gm = qe.graph_retriever.graph_manager

print("\n=== SECTION DETAILS ===\n")

with gm.driver.session() as session:
    # Get all section properties
    result = session.run("""
        MATCH (d:DOCUMENT)-[:CONTAINS]->(s:SECTION)
        RETURN 
            d.name as doc_name,
            s.number as section_number,
            s.name as section_name,
            s.title as section_title,
            s.page as page,
            keys(s) as all_properties
        ORDER BY d.name, s.number
        LIMIT 20
    """)
    
    for record in result:
        print(f"📄 Document: {record['doc_name']}")
        print(f"   Section Number: {record['section_number']}")
        print(f"   Section Name: {record['section_name']}")
        print(f"   Section Title: {record['section_title']}")
        print(f"   Page: {record['page']}")
        print(f"   All Properties: {record['all_properties']}")
        print()

gm.close()
print("✅ Done!\n")
