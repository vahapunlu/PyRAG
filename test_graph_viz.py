"""
Test Graph Visualization functionality
"""

import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

from src.graph_visualizer import GraphVisualizer


def test_graph_visualization():
    """Test graph visualizer"""
    logger.info("=" * 60)
    logger.info("Testing Graph Visualizer")
    logger.info("=" * 60)
    
    # Get Neo4j credentials - hardcoded for testing
    neo4j_uri = "neo4j+s://e2f00f22.databases.neo4j.io"
    neo4j_user = "neo4j"
    neo4j_password = "UfaAcKxqGbZQUaM6bB_4g9kxrP2HWWP-FEKRp8EuZyY"
    
    if not all([neo4j_uri, neo4j_password]):
        logger.error("❌ Neo4j credentials not found")
        return
    
    # Initialize
    visualizer = GraphVisualizer(neo4j_uri, neo4j_user, neo4j_password, "visualizations/test")
    
    try:
        # Test 1: Get graph statistics
        logger.info("\n📊 Test 1: Graph statistics...")
        stats = visualizer.get_graph_statistics()
        logger.info(f"Nodes: {stats['nodes']}")
        logger.info(f"Relationships: {stats['relationships']}")
        logger.info(f"Total nodes: {stats['total_nodes']}")
        logger.info(f"Total relationships: {stats['total_relationships']}")
        
        # Test 2: Full graph visualization
        logger.info("\n🎨 Test 2: Creating full graph visualization...")
        graph_path = visualizer.visualize_graph(limit=100, show_labels=True, figsize=(20, 16))
        if graph_path:
            logger.success(f"✅ Graph visualization created: {graph_path}")
        else:
            logger.warning("⚠️ Graph visualization not available (install networkx and matplotlib)")
        
        # Test 3: Query context visualization
        logger.info("\n🎨 Test 3: Creating query context visualization...")
        
        # Sample query and sources
        query = "Bakır kablo akım taşıma kapasitesi"
        sources = [
            {
                'content': 'Tablo 4.1...',
                'metadata': {
                    'document_name': 'IS10101',
                    'section_title': 'Kablo Kapasiteleri'
                }
            },
            {
                'content': 'Madde 4.2...',
                'metadata': {
                    'document_name': 'IS10101',
                    'section_title': 'Seçim Kriterleri'
                }
            },
            {
                'content': 'Tablo 4.5...',
                'metadata': {
                    'document_name': 'IS10101',
                    'section_title': 'Sıcaklık Faktörleri'
                }
            }
        ]
        
        context_path = visualizer.visualize_query_context(query, sources, figsize=(16, 12))
        if context_path:
            logger.success(f"✅ Query context visualization created: {context_path}")
        else:
            logger.warning("⚠️ Query context visualization not available")
        
    finally:
        visualizer.close()
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ All graph visualization tests completed!")
    logger.info(f"📁 Check visualizations/test/ directory for output images")


if __name__ == "__main__":
    test_graph_visualization()
