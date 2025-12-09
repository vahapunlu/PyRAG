"""
Check Neo4j relationship types
"""

import os
from neo4j import GraphDatabase
from loguru import logger

def check_relationships():
    """Check what relationships exist in Neo4j"""
    
    uri = "neo4j+s://8b8287a8.databases.neo4j.io"
    user = "neo4j"
    password = "8UGy23fGvj5NJVC5aKsD5bJVBBkxv8yKhpE_FgWKvTM"
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Get all relationship types
        result = session.run("""
            CALL db.relationshipTypes()
        """)
        
        rel_types = [record[0] for record in result]
        logger.info(f"📊 Relationship types in Neo4j: {rel_types}")
        
        # Count each relationship type
        for rel_type in rel_types:
            count_result = session.run(f"""
                MATCH ()-[r:{rel_type}]->()
                RETURN count(r) as count
            """)
            count = count_result.single()['count']
            logger.info(f"   {rel_type}: {count} relationships")
        
        # Check DOCUMENT nodes
        doc_result = session.run("""
            MATCH (d:DOCUMENT)
            RETURN d.name as name
        """)
        docs = [record['name'] for record in doc_result]
        logger.info(f"\n📄 Documents in Neo4j: {docs}")
        
        # Check if DOCUMENT has CONTAINS relationships
        for doc in docs:
            contains_result = session.run("""
                MATCH (d:DOCUMENT {name: $doc})-[r:CONTAINS]->(s)
                RETURN count(r) as count
            """, doc=doc)
            count = contains_result.single()['count']
            logger.info(f"   {doc} CONTAINS {count} sections")
        
        # Check SECTION nodes
        section_result = session.run("""
            MATCH (s:SECTION)
            RETURN count(s) as count
        """)
        section_count = section_result.single()['count']
        logger.info(f"\n📑 Total SECTION nodes: {section_count}")
        
        # Sample sections
        sample_result = session.run("""
            MATCH (s:SECTION)
            RETURN s.number as number, s.document as document
            LIMIT 5
        """)
        logger.info(f"   Sample sections:")
        for record in sample_result:
            logger.info(f"      {record['number']} (doc: {record['document']})")
    
    driver.close()

if __name__ == "__main__":
    check_relationships()
