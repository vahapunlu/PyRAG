"""
Test Graph Retriever

Test cross-reference retrieval from knowledge graph
"""

from src.graph_retriever import get_graph_retriever
from loguru import logger

if __name__ == "__main__":
    logger.info("🧪 Testing Graph Retriever...")
    
    retriever = get_graph_retriever()
    
    if not retriever or not retriever.enabled:
        logger.error("❌ Graph retriever not available")
        exit(1)
    
    # Test 1: Query with standard reference
    logger.info("\n" + "="*60)
    logger.info("Test 1: Query with standard reference")
    logger.info("="*60)
    
    query1 = "EN 54-11 standardına göre alarm cihazlarının özellikleri nelerdir?"
    result1 = retriever.get_cross_references(query1, max_hops=2)
    
    logger.info(f"Query: {query1}")
    logger.info(f"Entities found: {result1['entities_found']}")
    logger.info(f"References found: {len(result1['references'])}")
    logger.info(f"Summary: {result1['summary']}")
    
    if result1['references']:
        logger.info("\nTop 5 cross-references:")
        for i, ref in enumerate(result1['references'][:5], 1):
            logger.info(f"  {i}. [{ref['type'][0]}] {ref['name']} (hops: {ref['hops']})")
    
    # Test 2: Query with section reference
    logger.info("\n" + "="*60)
    logger.info("Test 2: Query with section reference")
    logger.info("="*60)
    
    query2 = "IS3218 Bölüm 16 yangın algılama hakkında ne diyor?"
    result2 = retriever.get_cross_references(query2, max_hops=2)
    
    logger.info(f"Query: {query2}")
    logger.info(f"Entities found: {result2['entities_found']}")
    logger.info(f"References found: {len(result2['references'])}")
    logger.info(f"Summary: {result2['summary']}")
    
    if result2['references']:
        logger.info("\nTop 5 cross-references:")
        for i, ref in enumerate(result2['references'][:5], 1):
            logger.info(f"  {i}. [{ref['type'][0]}] {ref['name']} (hops: {ref['hops']})")
    
    # Test 3: Document context
    logger.info("\n" + "="*60)
    logger.info("Test 3: Document context (IS3218 2024)")
    logger.info("="*60)
    
    doc_context = retriever.get_document_context("IS3218 2024")
    logger.info(f"Document: {doc_context['document']}")
    logger.info(f"Total sections: {doc_context['total_sections']}")
    logger.info(f"Total standards: {doc_context['total_standards']}")
    
    if doc_context['standards']:
        logger.info("\nReferenced standards (top 10):")
        for i, std in enumerate(doc_context['standards'][:10], 1):
            logger.info(f"  {i}. {std}")
    
    # Test 4: Graph statistics
    logger.info("\n" + "="*60)
    logger.info("Test 4: Graph statistics")
    logger.info("="*60)
    
    stats = retriever.get_statistics()
    logger.info(f"Total nodes: {stats['total_nodes']}")
    logger.info(f"  - Documents: {stats['documents']}")
    logger.info(f"  - Sections: {stats['sections']}")
    logger.info(f"  - Standards: {stats['standards']}")
    logger.info(f"Total relationships: {stats['relationships']}")
    
    logger.success("\n✅ All tests completed!")
