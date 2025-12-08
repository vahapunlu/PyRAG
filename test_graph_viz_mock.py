"""
Test Graph Visualization (Mock Mode - No Neo4j Required)
"""

import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_graph_visualization_mock():
    """Test graph visualizer in mock mode"""
    logger.info("=" * 60)
    logger.info("Testing Graph Visualizer (Mock Mode)")
    logger.info("=" * 60)
    
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        logger.success("✅ networkx and matplotlib installed")
    except ImportError as e:
        logger.error(f"❌ Required packages not installed: {e}")
        return
    
    # Test 1: Create simple graph
    logger.info("\n🎨 Test 1: Creating sample graph...")
    G = nx.DiGraph()
    
    # Add nodes
    nodes = [
        ('doc1', {'label': 'IS10101', 'type': 'Document'}),
        ('sec1', {'label': 'Section 4.1', 'type': 'Section'}),
        ('sec2', {'label': 'Section 4.2', 'type': 'Section'}),
        ('std1', {'label': 'IEC 60364', 'type': 'Standard'}),
        ('std2', {'label': 'EN 54-11', 'type': 'Standard'}),
    ]
    
    for node_id, attrs in nodes:
        G.add_node(node_id, **attrs)
    
    # Add edges
    edges = [
        ('doc1', 'sec1'),
        ('doc1', 'sec2'),
        ('sec1', 'std1'),
        ('sec2', 'std2'),
    ]
    
    for source, target in edges:
        G.add_edge(source, target)
    
    logger.success(f"✅ Created graph: {len(G.nodes())} nodes, {len(G.edges())} edges")
    
    # Test 2: Visualize
    logger.info("\n🎨 Test 2: Creating visualization...")
    
    plt.figure(figsize=(12, 8))
    plt.title('PyRAG Cross-Reference Graph (Sample)', fontsize=16, fontweight='bold')
    
    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Node colors
    node_colors = {
        'Document': '#3B82F6',
        'Section': '#10B981',
        'Standard': '#F59E0B'
    }
    colors = [node_colors.get(G.nodes[node].get('type'), '#6B7280') for node in G.nodes()]
    
    # Draw
    nx.draw_networkx_nodes(
        G, pos,
        node_color=colors,
        node_size=2000,
        alpha=0.9,
        edgecolors='white',
        linewidths=2
    )
    
    nx.draw_networkx_edges(
        G, pos,
        edge_color='#9CA3AF',
        arrows=True,
        arrowsize=20,
        width=2,
        alpha=0.6
    )
    
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(
        G, pos,
        labels=labels,
        font_size=10,
        font_weight='bold',
        font_color='white'
    )
    
    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor=node_colors['Document'], markersize=10, label='Document'),
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor=node_colors['Section'], markersize=10, label='Section'),
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor=node_colors['Standard'], markersize=10, label='Standard')
    ]
    plt.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    plt.axis('off')
    plt.tight_layout()
    
    # Save
    Path("visualizations/test").mkdir(parents=True, exist_ok=True)
    filepath = "visualizations/test/sample_graph.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.close()
    
    logger.success(f"✅ Graph visualization saved: {filepath}")
    
    # Test 3: Query context visualization
    logger.info("\n🎨 Test 3: Creating query context visualization...")
    
    G2 = nx.DiGraph()
    
    # Query node
    G2.add_node('query', label='Kablo kapasitesi?', type='query')
    
    # Source nodes
    sources = [
        ('src1', {'label': 'IS10101\nSection 4.1', 'type': 'source'}),
        ('src2', {'label': 'IS10101\nSection 4.2', 'type': 'source'}),
        ('src3', {'label': 'IS10101\nTable 4.5', 'type': 'source'}),
    ]
    
    for node_id, attrs in sources:
        G2.add_node(node_id, **attrs)
        G2.add_edge('query', node_id)
    
    plt.figure(figsize=(12, 8))
    plt.title('Query Context Graph (Sample)', fontsize=16, fontweight='bold')
    
    pos2 = nx.spring_layout(G2, k=3, iterations=50, seed=42)
    
    colors2 = []
    for node in G2.nodes():
        if G2.nodes[node]['type'] == 'query':
            colors2.append('#EF4444')  # Red
        else:
            colors2.append('#3B82F6')  # Blue
    
    nx.draw_networkx_nodes(
        G2, pos2,
        node_color=colors2,
        node_size=2500,
        alpha=0.9,
        edgecolors='white',
        linewidths=2
    )
    
    nx.draw_networkx_edges(
        G2, pos2,
        edge_color='#9CA3AF',
        arrows=True,
        arrowsize=20,
        width=2,
        alpha=0.6
    )
    
    labels2 = nx.get_node_attributes(G2, 'label')
    nx.draw_networkx_labels(
        G2, pos2,
        labels=labels2,
        font_size=9,
        font_weight='bold',
        font_color='white'
    )
    
    plt.axis('off')
    plt.tight_layout()
    
    filepath2 = "visualizations/test/sample_query_context.png"
    plt.savefig(filepath2, dpi=150, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    plt.close()
    
    logger.success(f"✅ Query context visualization saved: {filepath2}")
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ All graph visualization tests completed!")
    logger.info(f"📁 Check visualizations/test/ directory for output images")
    logger.info("\n💡 Note: This is mock mode. For real Neo4j graphs, ensure Neo4j is running.")


if __name__ == "__main__":
    test_graph_visualization_mock()
