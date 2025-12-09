"""
Graph Visualizer

Visualize Neo4j cross-reference graph using networkx and matplotlib
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from loguru import logger
import webbrowser

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("⚠️ networkx/matplotlib not installed - Graph visualization disabled")

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False
    logger.warning("⚠️ pyvis not installed - Interactive HTML visualization disabled")

from neo4j import GraphDatabase


class GraphVisualizer:
    """
    Visualize cross-reference graph from Neo4j
    
    Features:
    - Network graph visualization
    - Document and section nodes
    - Reference relationships
    - Filtering options
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 viz_dir: str = "visualizations"):
        """Initialize graph visualizer"""
        self.viz_dir = Path(viz_dir)
        self.viz_dir.mkdir(parents=True, exist_ok=True)
        
        # Neo4j connection
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        logger.info(f"✅ Graph Visualizer initialized")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def _fetch_graph_data(self, limit: int = 100) -> Tuple[List[Dict], List[Dict]]:
        """
        Fetch graph data from Neo4j
        
        Args:
            limit: Maximum nodes to fetch
            
        Returns:
            (nodes, relationships)
        """
        with self.driver.session() as session:
            # Fetch nodes
            nodes_result = session.run("""
                MATCH (n)
                RETURN 
                    id(n) as id,
                    labels(n)[0] as label,
                    n.name as name,
                    n.title as title,
                    n.standard_id as standard_id
                LIMIT $limit
            """, limit=limit)
            
            nodes = []
            for record in nodes_result:
                nodes.append({
                    'id': record['id'],
                    'label': record['label'],
                    'name': record['name'] or record['title'] or record['standard_id'] or f"Node-{record['id']}"
                })
            
            # Fetch relationships
            rels_result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN 
                    id(a) as source,
                    id(b) as target,
                    type(r) as type
                LIMIT $limit
            """, limit=limit)
            
            relationships = []
            for record in rels_result:
                relationships.append({
                    'source': record['source'],
                    'target': record['target'],
                    'type': record['type']
                })
            
            logger.debug(f"📊 Fetched {len(nodes)} nodes, {len(relationships)} relationships")
            return nodes, relationships
    
    def visualize_graph(self, limit: int = 100, show_labels: bool = True,
                       figsize: Tuple[int, int] = (20, 16)) -> Optional[str]:
        """
        Create and save graph visualization
        
        Args:
            limit: Maximum nodes to include
            show_labels: Show node labels
            figsize: Figure size (width, height)
            
        Returns:
            Path to saved image or None if failed
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("❌ Graph visualization not available - install networkx and matplotlib")
            return None
        
        try:
            # Fetch data
            nodes, relationships = self._fetch_graph_data(limit)
            
            if not nodes:
                logger.warning("⚠️ No nodes found in graph")
                return None
            
            # Create NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes
            node_colors = {
                'Document': '#3B82F6',      # Blue
                'Section': '#10B981',       # Green
                'Standard': '#F59E0B',      # Orange
                'default': '#6B7280'        # Gray
            }
            
            for node in nodes:
                G.add_node(
                    node['id'],
                    label=node['name'][:30],  # Truncate long labels
                    type=node['label']
                )
            
            # Add edges
            for rel in relationships:
                if rel['source'] in G and rel['target'] in G:
                    G.add_edge(rel['source'], rel['target'], type=rel['type'])
            
            # Create visualization with high DPI
            plt.figure(figsize=figsize, dpi=100)
            plt.title('PyRAG Cross-Reference Graph', fontsize=28, fontweight='bold', pad=30)
            
            # Layout
            if len(G.nodes()) < 50:
                pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            else:
                pos = nx.kamada_kawai_layout(G)
            
            # Node colors based on type
            colors = [node_colors.get(G.nodes[node].get('type', 'default'), node_colors['default']) 
                     for node in G.nodes()]
            
            # Draw nodes - larger and more visible
            nx.draw_networkx_nodes(
                G, pos,
                node_color=colors,
                node_size=2000,  # Doubled size
                alpha=0.9,
                edgecolors='white',
                linewidths=3
            )
            
            # Draw edges - thicker and more visible
            nx.draw_networkx_edges(
                G, pos,
                edge_color='#4B5563',  # Darker gray
                arrows=True,
                arrowsize=20,  # Larger arrows
                arrowstyle='->',
                width=2.5,  # Thicker lines
                alpha=0.7,
                connectionstyle='arc3,rad=0.1'
            )
            
            # Draw labels with better visibility
            if show_labels:
                labels = nx.get_node_attributes(G, 'label')
                nx.draw_networkx_labels(
                    G, pos,
                    labels=labels,
                    font_size=12,  # Larger font
                    font_weight='bold',
                    font_color='white',
                    font_family='sans-serif'
                )
            
            # Legend - larger and more visible
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor=node_colors['Document'], markersize=15, label='Document'),
                plt.Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor=node_colors['Section'], markersize=15, label='Section'),
                plt.Line2D([0], [0], marker='o', color='w', 
                          markerfacecolor=node_colors['Standard'], markersize=15, label='Standard')
            ]
            plt.legend(handles=legend_elements, loc='upper left', fontsize=16, framealpha=0.9)
            
            # Stats - larger text
            stats_text = (f"Nodes: {len(G.nodes())} | "
                         f"Edges: {len(G.edges())} | "
                         f"Density: {nx.density(G):.3f}")
            plt.text(0.5, 0.02, stats_text,
                    ha='center', va='bottom',
                    transform=plt.gcf().transFigure,
                    fontsize=16, color='#1F2937', fontweight='bold')
            
            plt.axis('off')
            plt.tight_layout()
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graph_viz_{timestamp}.png"
            filepath = self.viz_dir / filename
            
            plt.savefig(filepath, dpi=200, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')  # Higher DPI for sharper image
            plt.close()
            
            logger.info(f"📊 Graph visualization saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Graph visualization failed: {e}")
            return None
    
    def visualize_query_context(self, query: str, sources: List[Dict],
                               figsize: Tuple[int, int] = (16, 12)) -> Optional[str]:
        """
        Visualize query context - query + related sources
        
        Args:
            query: User query
            sources: Source documents from query
            figsize: Figure size
            
        Returns:
            Path to saved image or None if failed
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("❌ Graph visualization not available")
            return None
        
        try:
            # Create simple graph
            G = nx.DiGraph()
            
            # Query node (center)
            G.add_node('query', label=query[:50] + '...', type='query')
            
            # Source nodes
            for i, source in enumerate(sources[:10]):  # Limit to 10 sources
                source_id = f"source_{i}"
                
                # Get metadata
                meta = source.get('metadata', {})
                doc_name = meta.get('document_name', 'Unknown')
                section = meta.get('section_title', 'Unknown')
                
                label = f"{doc_name}\n{section[:30]}"
                G.add_node(source_id, label=label, type='source')
                G.add_edge('query', source_id)
            
            # Layout
            pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
            
            # Visualization
            plt.figure(figsize=figsize)
            plt.title(f'Query Context Graph', fontsize=18, fontweight='bold', pad=20)
            
            # Node colors
            node_colors = []
            for node in G.nodes():
                if G.nodes[node]['type'] == 'query':
                    node_colors.append('#EF4444')  # Red
                else:
                    node_colors.append('#3B82F6')  # Blue
            
            # Draw
            nx.draw_networkx_nodes(
                G, pos,
                node_color=node_colors,
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
                font_size=9,
                font_weight='bold',
                font_color='white'
            )
            
            plt.axis('off')
            plt.tight_layout()
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_context_{timestamp}.png"
            filepath = self.viz_dir / filename
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()
            
            logger.info(f"📊 Query context visualization saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Query context visualization failed: {e}")
            return None
    
    def visualize_graph_interactive(self, limit: int = 100, output_file: str = None, 
                                   auto_open: bool = True) -> Optional[str]:
        """
        Create interactive HTML graph visualization using Pyvis
        
        Args:
            limit: Maximum number of nodes to include
            output_file: Output HTML file path (auto-generated if None)
            auto_open: Automatically open in browser
            
        Returns:
            Path to HTML file or None on error
        """
        if not PYVIS_AVAILABLE:
            logger.error("❌ Pyvis not installed - run: pip install pyvis")
            return None
        
        try:
            logger.info(f"🎨 Creating interactive graph visualization (limit={limit})...")
            
            # Create Pyvis network
            net = Network(
                height="900px",
                width="100%",
                bgcolor="#1a1a1a",
                font_color="#ffffff",
                directed=True
            )
            
            # Configure physics and styling for better layout
            net.set_options("""
            {
                "physics": {
                    "enabled": true,
                    "barnesHut": {
                        "gravitationalConstant": -30000,
                        "centralGravity": 0.3,
                        "springLength": 150,
                        "springConstant": 0.04,
                        "damping": 0.09,
                        "avoidOverlap": 0.5
                    },
                    "stabilization": {
                        "enabled": true,
                        "iterations": 200
                    }
                },
                "interaction": {
                    "hover": true,
                    "tooltipDelay": 100,
                    "navigationButtons": true,
                    "keyboard": true
                },
                "configure": {
                    "enabled": false
                }
            }
            """)
            
            # Fetch graph data from Neo4j
            with self.driver.session() as session:
                # Get nodes with labels - prioritize Documents, then connected nodes
                nodes_query = f"""
                // First get all Documents
                MATCH (d:DOCUMENT)
                WITH collect(d) as documents
                
                // Then get connected Sections and Standards
                MATCH (d:DOCUMENT)-[:CONTAINS]->(s:SECTION)
                OPTIONAL MATCH (s)-[:REFERS_TO]->(st:STANDARD)
                WITH documents, collect(DISTINCT s) as sections, collect(DISTINCT st) as standards
                
                // Combine and limit
                WITH documents + sections + standards as all_nodes
                UNWIND all_nodes as n
                WITH DISTINCT n
                LIMIT {limit}
                
                RETURN id(n) as id, labels(n) as labels, properties(n) as props
                """
                
                nodes_result = session.run(nodes_query)
                node_ids = set()
                
                for record in nodes_result:
                    node_id = record['id']
                    labels = record['labels']
                    props = record['props']
                    node_ids.add(node_id)
                    
                    # Determine node type and color
                    label = labels[0] if labels else 'Unknown'
                    
                    if label == 'Document':
                        color = '#3B82F6'  # Blue
                        size = 40
                        shape = 'box'
                        title = f"📄 Document\n{props.get('name', props.get('doc_name', 'Unknown'))}"
                    elif label == 'Section':
                        color = '#10B981'  # Green
                        size = 30
                        shape = 'ellipse'
                        section_text = props.get('text', props.get('name', props.get('section_name', 'Unknown')))[:50]
                        title = f"📑 Section\n{section_text}"
                    elif label == 'Standard' or label == 'STANDARD':
                        color = '#F59E0B'  # Orange
                        size = 35
                        shape = 'diamond'
                        # Standard nodes use 'name' property (e.g., "EN 54-11")
                        std_number = props.get('name', props.get('number', props.get('standard_number', 'Unknown')))
                        title = f"📏 Standard\n{std_number}"
                    else:
                        color = '#8B5CF6'  # Purple
                        size = 25
                        shape = 'dot'
                        title = f"{label}\n{str(props)[:50]}"
                    
                    # Display name
                    if label == 'Document':
                        display_name = props.get('name', props.get('doc_name', f'Doc {node_id}'))[:30]
                    elif label == 'Section':
                        display_name = props.get('name', props.get('section_name', f'Section {node_id}'))[:25]
                    elif label == 'Standard' or label == 'STANDARD':
                        # Standard nodes use 'name' property
                        display_name = props.get('name', props.get('number', f'Standard {node_id}'))
                    else:
                        display_name = f"{label} {node_id}"
                    
                    # Add node
                    net.add_node(
                        node_id,
                        label=display_name,
                        title=title,
                        color=color,
                        size=size,
                        shape=shape
                    )
                
                # Get relationships between fetched nodes
                if node_ids:
                    edges_query = """
                    MATCH (a)-[r]->(b)
                    WHERE id(a) IN $node_ids AND id(b) IN $node_ids
                    RETURN id(a) as source, id(b) as target, type(r) as type
                    """
                    
                    edges_result = session.run(edges_query, node_ids=list(node_ids))
                    
                    for record in edges_result:
                        source = record['source']
                        target = record['target']
                        rel_type = record['type']
                        
                        # Edge color by type
                        if rel_type == 'REFERS_TO':
                            edge_color = '#F59E0B'  # Orange for references
                            width = 2
                        elif rel_type == 'CONTAINS':
                            edge_color = '#10B981'  # Green for containment
                            width = 3
                        elif rel_type == 'HAS_SECTION':
                            edge_color = '#10B981'  # Green
                            width = 2
                        else:
                            edge_color = '#6B7280'  # Gray for others
                            width = 1
                        
                        net.add_edge(
                            source,
                            target,
                            title=rel_type,
                            color=edge_color,
                            width=width,
                            arrows='to'
                        )
            
            # Generate output path
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.viz_dir / f"interactive_graph_{timestamp}.html"
            else:
                output_file = Path(output_file)
            
            # Save HTML
            net.save_graph(str(output_file))
            
            # Customize HTML styling (fix ugly button colors)
            self._customize_html_styling(output_file)
            
            logger.info(f"✅ Interactive graph saved: {output_file}")
            
            # Open in browser
            if auto_open:
                webbrowser.open(f"file:///{output_file.absolute()}")
                logger.info("🌐 Opened in browser")
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ Interactive visualization failed: {e}")
            return None
    
    def _customize_html_styling(self, html_path: Path):
        """Customize HTML file styling - fix ugly button colors"""
        try:
            # Read HTML
            html_content = html_path.read_text(encoding='utf-8')
            
            # Add custom CSS for better button styling
            custom_css = """
<style>
    /* Override Pyvis ugly button colors */
    .vis-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .vis-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
    }
    
    .vis-button:active {
        transform: translateY(0px) !important;
    }
    
    /* Navigation buttons container */
    .vis-network div.vis-navigation {
        background: rgba(26, 26, 26, 0.8) !important;
        border-radius: 12px !important;
        padding: 8px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Add title to page */
    body::before {
        content: '🎨 Interactive Knowledge Graph';
        display: block;
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(26, 26, 26, 0.95);
        color: white;
        padding: 12px 24px;
        border-radius: 12px;
        font-size: 20px;
        font-weight: bold;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
    }
</style>
"""
            
            # Insert before </head>
            html_content = html_content.replace('</head>', f'{custom_css}\n</head>')
            
            # Write back
            html_path.write_text(html_content, encoding='utf-8')
            
        except Exception as e:
            logger.warning(f"⚠️ Could not customize HTML styling: {e}")
    
    def get_graph_statistics(self) -> Dict:
        """Get graph statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WITH labels(n)[0] as label, count(*) as count
                RETURN label, count
            """)
            
            node_counts = {record['label']: record['count'] for record in result}
            
            rel_result = session.run("""
                MATCH ()-[r]->()
                WITH type(r) as type, count(*) as count
                RETURN type, count
            """)
            
            rel_counts = {record['type']: record['count'] for record in rel_result}
            
            return {
                'nodes': node_counts,
                'relationships': rel_counts,
                'total_nodes': sum(node_counts.values()),
                'total_relationships': sum(rel_counts.values())
            }


# Singleton instance
_graph_visualizer = None

def get_graph_visualizer(neo4j_uri: str = None, neo4j_user: str = None, 
                        neo4j_password: str = None) -> Optional[GraphVisualizer]:
    """Get or create graph visualizer singleton"""
    global _graph_visualizer
    
    if _graph_visualizer is None and all([neo4j_uri, neo4j_user, neo4j_password]):
        _graph_visualizer = GraphVisualizer(neo4j_uri, neo4j_user, neo4j_password)
    
    return _graph_visualizer
