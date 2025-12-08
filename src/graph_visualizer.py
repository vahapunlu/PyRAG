"""
Graph Visualizer

Visualize Neo4j cross-reference graph using networkx and matplotlib
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from loguru import logger

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
            
            # Create visualization
            plt.figure(figsize=figsize)
            plt.title('PyRAG Cross-Reference Graph', fontsize=20, fontweight='bold', pad=20)
            
            # Layout
            if len(G.nodes()) < 50:
                pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            else:
                pos = nx.kamada_kawai_layout(G)
            
            # Node colors based on type
            colors = [node_colors.get(G.nodes[node].get('type', 'default'), node_colors['default']) 
                     for node in G.nodes()]
            
            # Draw nodes
            nx.draw_networkx_nodes(
                G, pos,
                node_color=colors,
                node_size=1000,
                alpha=0.9,
                edgecolors='white',
                linewidths=2
            )
            
            # Draw edges
            nx.draw_networkx_edges(
                G, pos,
                edge_color='#9CA3AF',
                arrows=True,
                arrowsize=15,
                arrowstyle='->',
                width=1.5,
                alpha=0.6,
                connectionstyle='arc3,rad=0.1'
            )
            
            # Draw labels
            if show_labels:
                labels = nx.get_node_attributes(G, 'label')
                nx.draw_networkx_labels(
                    G, pos,
                    labels=labels,
                    font_size=8,
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
            plt.legend(handles=legend_elements, loc='upper left', fontsize=12)
            
            # Stats
            stats_text = (f"Nodes: {len(G.nodes())} | "
                         f"Edges: {len(G.edges())} | "
                         f"Density: {nx.density(G):.3f}")
            plt.text(0.5, 0.02, stats_text,
                    ha='center', va='bottom',
                    transform=plt.gcf().transFigure,
                    fontsize=12, color='#4B5563')
            
            plt.axis('off')
            plt.tight_layout()
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graph_viz_{timestamp}.png"
            filepath = self.viz_dir / filename
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
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
