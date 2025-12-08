"""
Feedback-Based Post-Processor

Re-ranks retrieved nodes based on user feedback scores for active learning.
"""

from typing import List, Optional
from llama_index.core.schema import NodeWithScore, QueryBundle
from loguru import logger

from .feedback_manager import get_feedback_manager


class FeedbackPostProcessor:
    """
    Post-processor that adjusts node scores based on historical user feedback
    
    Nodes with positive feedback get score boost, negative feedback get penalty.
    """
    
    def __init__(
        self,
        boost_factor: float = 0.15,
        penalty_factor: float = 0.10,
        min_feedback_count: int = 1
    ):
        """
        Initialize feedback post-processor
        
        Args:
            boost_factor: Score boost for positive feedback (e.g., 0.15 = 15% boost)
            penalty_factor: Score penalty for negative feedback (e.g., 0.10 = 10% penalty)
            min_feedback_count: Minimum feedback count to apply adjustment
        """
        self.boost_factor = boost_factor
        self.penalty_factor = penalty_factor
        self.min_feedback_count = min_feedback_count
        self.feedback_manager = get_feedback_manager()
    
    def postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """
        Public interface for post-processing nodes
        
        Args:
            nodes: Retrieved nodes with scores
            query_bundle: Query information
            
        Returns:
            Re-ranked nodes
        """
        return self._postprocess_nodes(nodes, query_bundle)
    
    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """
        Re-rank nodes based on feedback scores
        
        Args:
            nodes: Retrieved nodes with scores
            query_bundle: Query information
            
        Returns:
            Re-ranked nodes
        """
        if not nodes:
            return nodes
        
        adjusted_nodes = []
        adjustments_made = 0
        
        for node_with_score in nodes:
            node = node_with_score.node
            original_score = node_with_score.score or 0.0
            
            # Extract metadata
            metadata = node.metadata
            doc_name = metadata.get('document_name', 'Unknown')
            page = str(metadata.get('page_label', metadata.get('page', 'N/A')))
            chunk_text = node.text[:500]  # First 500 chars
            
            # Get feedback score
            feedback_score = self.feedback_manager.get_source_score(
                document_name=doc_name,
                page=page,
                chunk_text=chunk_text
            )
            
            # Calculate adjustment
            if feedback_score != 0:
                if feedback_score > 0:
                    # Positive feedback: boost score
                    adjustment = original_score * self.boost_factor * min(feedback_score, 5)
                    new_score = original_score + adjustment
                    adjustments_made += 1
                    logger.debug(
                        f"📈 Boosted: {doc_name} (Page {page}) | "
                        f"Score: {original_score:.3f} → {new_score:.3f} (+{adjustment:.3f}) | "
                        f"Feedback: +{feedback_score}"
                    )
                else:
                    # Negative feedback: apply penalty
                    adjustment = original_score * self.penalty_factor * min(abs(feedback_score), 3)
                    new_score = max(original_score - adjustment, 0.0)
                    adjustments_made += 1
                    logger.debug(
                        f"📉 Penalized: {doc_name} (Page {page}) | "
                        f"Score: {original_score:.3f} → {new_score:.3f} (-{adjustment:.3f}) | "
                        f"Feedback: {feedback_score}"
                    )
                
                # Create new node with adjusted score
                adjusted_node = NodeWithScore(
                    node=node,
                    score=new_score
                )
                adjusted_nodes.append(adjusted_node)
            else:
                # No feedback, keep original
                adjusted_nodes.append(node_with_score)
        
        if adjustments_made > 0:
            logger.info(f"🎯 Feedback adjustments applied to {adjustments_made}/{len(nodes)} nodes")
        
        # Re-sort by adjusted scores
        adjusted_nodes.sort(key=lambda x: x.score or 0.0, reverse=True)
        
        return adjusted_nodes


def get_feedback_postprocessor(
    boost_factor: float = 0.15,
    penalty_factor: float = 0.10
) -> FeedbackPostProcessor:
    """
    Get feedback post-processor instance
    
    Args:
        boost_factor: Score boost multiplier for positive feedback
        penalty_factor: Score penalty multiplier for negative feedback
        
    Returns:
        FeedbackPostProcessor instance
    """
    return FeedbackPostProcessor(
        boost_factor=boost_factor,
        penalty_factor=penalty_factor
    )
