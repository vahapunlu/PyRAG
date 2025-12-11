#!/usr/bin/env python3
"""Check Neo4j document names and sections"""

from src.graph_manager import GraphManager
from src.utils import get_settings

def main():
    settings = get_settings()
    gm = GraphManager(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password
    )
    
    # Get all documents
    with gm.driver.session(database='neo4j') as session:
        result = session.run('MATCH (d:DOCUMENT) RETURN d.name ORDER BY d.name')
        docs = [r['d.name'] for r in result]
    
    print("\n📄 Documents in Neo4j:")
    for doc in docs:
        print(f"  - '{doc}'")
    
    # Check sections for each
    print("\n📑 Sections per document:")
    for doc in docs:
        with gm.driver.session(database='neo4j') as session:
            result = session.run('''
                MATCH (d:DOCUMENT {name: $doc_name})-[:CONTAINS]->(s:SECTION)
                RETURN count(s) as section_count
            ''', doc_name=doc)
            count = result.single()['section_count']
            print(f"  - {doc}: {count} sections")
            
            if count > 0:
                # Show first 5 sections
                result = session.run('''
                    MATCH (d:DOCUMENT {name: $doc_name})-[:CONTAINS]->(s:SECTION)
                    RETURN s.number as number, s.title as title
                    LIMIT 5
                ''', doc_name=doc)
                for r in result:
                    print(f"      • {r['number']} - {r['title']}")

if __name__ == "__main__":
    main()
