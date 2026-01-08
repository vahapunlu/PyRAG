"""
Granular Feedback API Example

FastAPI endpoint example for collecting granular feedback.
Bu app_gui.py veya ayrı bir API sunucusuna eklenebilir.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from src.granular_feedback import get_granular_feedback_manager
from src.feedback_learner import get_feedback_learner
from loguru import logger

app = FastAPI()


# Pydantic models for request validation
class SourceFeedback(BaseModel):
    document: str
    page: Optional[str] = None
    text: Optional[str] = None
    rating: str  # 'helpful', 'not_helpful', 'irrelevant'
    stars: Optional[int] = None
    comment: Optional[str] = None


class TextHighlight(BaseModel):
    text: str
    sentiment: str = 'positive'
    source: Optional[str] = None
    comment: Optional[str] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None


class GranularFeedbackRequest(BaseModel):
    query: str
    response: str
    overall_rating: Optional[int] = None
    dimensions: Optional[Dict[str, int]] = None
    source_feedbacks: Optional[List[SourceFeedback]] = None
    highlights: Optional[List[TextHighlight]] = None
    comment: Optional[str] = None
    auto_learn: bool = True


@app.post("/api/submit_granular_feedback")
async def submit_granular_feedback(feedback: GranularFeedbackRequest):
    """
    Submit granular feedback with source ratings and text highlights
    
    Example request:
    ```json
    {
        "query": "Kablo seçimi nasıl yapılır?",
        "response": "Kablo seçimi IS 3218...",
        "overall_rating": 4,
        "dimensions": {
            "relevance": 5,
            "clarity": 4,
            "completeness": 3
        },
        "source_feedbacks": [
            {
                "document": "IS3218",
                "page": "15",
                "rating": "helpful",
                "stars": 5,
                "comment": "Çok yararlı"
            }
        ],
        "highlights": [
            {
                "text": "Kablo kesiti 2.5mm²...",
                "sentiment": "positive",
                "source": "IS3218"
            }
        ],
        "auto_learn": true
    }
    ```
    """
    try:
        manager = get_granular_feedback_manager()
        
        # Convert Pydantic models to dicts
        source_feedbacks_dict = None
        if feedback.source_feedbacks:
            source_feedbacks_dict = [sf.dict() for sf in feedback.source_feedbacks]
        
        highlights_dict = None
        if feedback.highlights:
            highlights_dict = [h.dict() for h in feedback.highlights]
        
        # Save feedback
        feedback_id = manager.add_feedback(
            query=feedback.query,
            response=feedback.response,
            overall_rating=feedback.overall_rating,
            source_feedbacks=source_feedbacks_dict,
            highlights=highlights_dict,
            dimensions=feedback.dimensions,
            comment=feedback.comment
        )
        
        # Auto-learn if enabled
        learning_stats = None
        if feedback.auto_learn and feedback.overall_rating and feedback.overall_rating >= 4:
            try:
                learner = get_feedback_learner()
                if learner:
                    learning_stats = learner.learn_from_feedback(time_window_days=7)
                    logger.info(f"🧠 Auto-learning triggered: {learning_stats['new_relationships']} new relationships")
            except Exception as e:
                logger.warning(f"⚠️ Auto-learning failed: {e}")
        
        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": "Feedback saved successfully",
            "learning_stats": learning_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/source_quality_scores")
async def get_source_quality_scores():
    """Get quality scores for all sources"""
    try:
        manager = get_granular_feedback_manager()
        scores = manager.get_source_quality_scores()
        return {
            "success": True,
            "scores": scores
        }
    except Exception as e:
        logger.error(f"❌ Error getting scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/best_sources")
async def get_best_sources(limit: int = 10):
    """Get top-rated sources"""
    try:
        manager = get_granular_feedback_manager()
        best = manager.get_best_sources(limit=limit)
        return {
            "success": True,
            "sources": best
        }
    except Exception as e:
        logger.error(f"❌ Error getting best sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/highlighted_snippets")
async def get_highlighted_snippets(limit: int = 20):
    """Get most frequently highlighted text snippets"""
    try:
        manager = get_granular_feedback_manager()
        snippets = manager.get_highlighted_snippets(limit=limit)
        return {
            "success": True,
            "snippets": snippets
        }
    except Exception as e:
        logger.error(f"❌ Error getting highlights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feedback_statistics")
async def get_feedback_statistics():
    """Get overall feedback statistics"""
    try:
        manager = get_granular_feedback_manager()
        stats = manager.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# For testing purposes
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Granular Feedback API server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
