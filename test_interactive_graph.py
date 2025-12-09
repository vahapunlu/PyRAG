"""
Test interactive graph visualization with Pyvis
"""

import os
from dotenv import load_dotenv
from src.graph_visualizer import GraphVisualizer
from loguru import logger

# Load environment
load_dotenv()

def main():
    """Test interactive graph visualization"""
    
    # Get Neo4j credentials - use hardcoded for testing
    neo4j_uri = "neo4j+s://8b8287a8.databases.neo4j.io"
    neo4j_user = "neo4j"
    neo4j_password = "8UGy23fGvj5NJVC5aKsD5bJVBBkxv8yKhpE_FgWKvTM"
    
    if not all([neo4j_uri, neo4j_password]):
        logger.error("❌ Neo4j credentials not found")
        return
    
    logger.info("🎨 Testing interactive graph visualization...")
    
    # Create visualizer
    visualizer = GraphVisualizer(neo4j_uri, neo4j_user, neo4j_password)
    
    # Get statistics
    stats = visualizer.get_graph_statistics()
    logger.info(f"📊 Graph stats: {stats}")
    
    # Generate interactive HTML
    html_path = visualizer.visualize_graph_interactive(
        limit=200,  # Show up to 200 nodes
        auto_open=True  # Open in browser automatically
    )
    
    if html_path:
        logger.info(f"✅ Interactive graph created: {html_path}")
        logger.info("🌐 Graph opened in your default browser")
        logger.info("\n💡 Interactive features:")
        logger.info("  • Zoom: Mouse wheel")
        logger.info("  • Pan: Click and drag background")
        logger.info("  • Move nodes: Drag individual nodes")
        logger.info("  • Details: Hover over nodes and edges")
        logger.info("  • Navigation: Use buttons in bottom right")
    else:
        logger.error("❌ Failed to create interactive graph")

if __name__ == "__main__":
    main()
