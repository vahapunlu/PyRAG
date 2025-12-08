"""
Test Neo4j Graph Manager
"""

from src.graph_manager import get_graph_manager

def test_graph_manager():
    print("\n" + "="*60)
    print("NEO4J GRAPH MANAGER TEST")
    print("="*60)
    
    # Get graph manager
    print("\n1️⃣ Connecting to Neo4j...")
    manager = get_graph_manager()
    
    if not manager:
        print("❌ Failed to connect to Neo4j")
        return
    
    try:
        # Create indexes
        print("\n2️⃣ Creating indexes...")
        manager.create_indexes()
        
        # Create test data
        print("\n3️⃣ Creating test nodes...")
        
        # Document
        manager.create_document_node(
            "IS3218 2024",
            {'title': 'Fire Detection and Alarm Systems', 'year': 2024, 'pages': 120}
        )
        
        # Sections
        manager.create_section_node(
            "IS3218 2024",
            "6.5.1",
            {'title': 'Manual Call Points', 'page': 45}
        )
        
        manager.create_section_node(
            "IS3218 2024",
            "16",
            {'title': 'Definitions', 'page': 20}
        )
        
        # Standards
        manager.create_standard_node(
            "EN 54-11",
            {'organization': 'European Standard', 'title': 'Manual Call Points'}
        )
        
        manager.create_standard_node(
            "IEC 60364",
            {'organization': 'International Standard'}
        )
        
        # Relationships
        print("\n4️⃣ Creating relationships...")
        manager.create_refers_to_relationship(
            "IS3218 2024",
            "EN 54-11",
            source_type="DOCUMENT",
            properties={'context': 'MCP requirements'}
        )
        
        manager.create_refers_to_relationship(
            "6.5.1",
            "EN 54-11",
            source_type="SECTION",
            properties={'page': 45}
        )
        
        # Query cross-references
        print("\n5️⃣ Testing cross-reference queries...")
        
        refs = manager.get_cross_references("IS3218 2024", max_hops=2)
        print(f"\n📊 Cross-references from IS3218 2024:")
        for ref in refs[:5]:
            print(f"   • {ref['type']}: {ref['name']} ({ref['hops']} hops)")
            print(f"     Relationships: {' → '.join(ref['relationship_types'])}")
        
        # Document references
        doc_refs = manager.get_document_references("IS3218 2024")
        print(f"\n📄 Document IS3218 2024:")
        print(f"   Standards: {doc_refs['total_standards']}")
        for std in doc_refs['standards']:
            print(f"      • {std}")
        print(f"   Sections: {doc_refs['total_sections']}")
        for sec in doc_refs['sections'][:5]:
            print(f"      • {sec['number']}: {sec.get('title', 'N/A')}")
        
        # Statistics
        print("\n6️⃣ Graph statistics:")
        stats = manager.get_graph_statistics()
        print(f"   Documents: {stats['documents']}")
        print(f"   Sections: {stats['sections']}")
        print(f"   Standards: {stats['standards']}")
        print(f"   Total Nodes: {stats['total_nodes']}")
        print(f"   Relationships: {stats['relationships']}")
        
        print("\n✅ All tests passed!")
        
    finally:
        # Close connection
        manager.close()

if __name__ == "__main__":
    test_graph_manager()
