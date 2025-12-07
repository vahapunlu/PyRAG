"""
PyRAG - FastAPI REST API Server

HTTP API endpoints for React, Flutter, or other frontends
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uvicorn

from loguru import logger
from src.utils import get_settings, setup_logger
from src.query_engine import QueryEngine
from src.ingestion import DocumentIngestion


# Pydantic models (Request/Response schemas)

class QueryRequest(BaseModel):
    """Query request"""
    question: str = Field(..., min_length=3, description="User's question")
    return_sources: bool = Field(True, description="Return source documents?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the current carrying capacity for 2.5mm² cable?",
                "return_sources": True
            }
        }


class SourceDocument(BaseModel):
    """Source document information"""
    rank: int
    text: str
    score: Optional[float] = None
    metadata: Dict


class QueryResponse(BaseModel):
    """Query response"""
    answer: str
    sources: List[SourceDocument] = []
    metadata: Dict
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check"""
    status: str
    version: str
    index_stats: Dict


class IndexRequest(BaseModel):
    """Indexing request"""
    force_reindex: bool = Field(False, description="Delete existing index and rebuild")


# FastAPI application

app = FastAPI(
    title="PyRAG - Engineering Standards API",
    description="RAG engine for IS10101 and other electrical standards",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS settings (for React/Flutter access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global variables
query_engine: Optional[QueryEngine] = None
ingestion: Optional[DocumentIngestion] = None
settings = get_settings()


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    global query_engine, ingestion
    
    setup_logger(settings.log_level)
    logger.info("🚀 Starting PyRAG API server...")
    
    try:
        # Load query engine
        query_engine = QueryEngine()
        logger.success("✅ Query Engine ready")
        
        # Prepare ingestion (lazy loading)
        ingestion = DocumentIngestion()
        logger.success("✅ Ingestion Engine ready")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        logger.warning("⚠️  API started but query engine is not ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("👋 Shutting down PyRAG API server...")


# ==================== ENDPOINTS ====================

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint - API information"""
    return {
        "name": "PyRAG - Engineering Standards API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "query": "/api/query",
            "search": "/api/search",
            "index": "/api/index"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check - System status
    """
    try:
        stats = ingestion.get_index_stats() if ingestion else {}
        
        return HealthResponse(
            status="healthy" if query_engine else "degraded",
            version="1.0.0",
            index_stats=stats
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.post("/api/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Main query endpoint - Send user question, get AI answer
    
    **Example usage:**
    ```json
    {
        "question": "What is the current carrying capacity for 2.5mm² copper cable?",
        "return_sources": true
    }
    ```
    """
    if not query_engine:
        raise HTTPException(
            status_code=503,
            detail="Query engine not ready yet. Please wait or check /health."
        )
    
    try:
        logger.info(f"📥 API Query: {request.question}")
        
        result = query_engine.query(
            question=request.question,
            return_sources=request.return_sources
        )
        
        # Build response model
        sources = [
            SourceDocument(**source) for source in result.get("sources", [])
        ]
        
        response = QueryResponse(
            answer=result.get("response", result.get("answer", "")),  # Support both keys for backward compatibility
            sources=sources,
            metadata=result.get("metadata", {})
        )
        
        logger.success(f"✅ Response returned: {len(response.answer)} characters")
        return response
        
    except Exception as e:
        logger.error(f"❌ Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search_endpoint(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results")
):
    """
    Search similar documents (without AI interpretation)
    
    **Parameters:**
    - query: Search term
    - top_k: How many results to return (1-20)
    """
    if not query_engine:
        raise HTTPException(status_code=503, detail="Query engine not ready")
    
    try:
        logger.info(f"🔍 Search: '{query}' (top_k={top_k})")
        
        results = query_engine.get_similar_docs(query, top_k=top_k)
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index")
async def index_endpoint(
    request: IndexRequest,
    background_tasks: BackgroundTasks
):
    """
    Index documents
    
    **Warning:** This operation may take several minutes and uses OpenAI API.
    
    **Parameters:**
    - force_reindex: If true, deletes existing index and starts from scratch
    """
    if not ingestion:
        raise HTTPException(status_code=503, detail="Ingestion engine not ready")
    
    try:
        logger.info(f"📥 Indexing request (force={request.force_reindex})")
        
        # Run in background (async)
        def index_task():
            try:
                ingestion.ingest_documents(force_reindex=request.force_reindex)
                logger.success("✅ Indexing completed")
            except Exception as e:
                logger.error(f"❌ Indexing error: {e}")
        
        background_tasks.add_task(index_task)
        
        return {
            "status": "started",
            "message": "Indexing started. Process continues in background.",
            "force_reindex": request.force_reindex
        }
        
    except Exception as e:
        logger.error(f"❌ Index endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def stats_endpoint():
    """
    Index statistics
    """
    if not ingestion:
        raise HTTPException(status_code=503, detail="Ingestion engine not ready")
    
    try:
        stats = ingestion.get_index_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MAIN ====================

def start_server():
    """Start API server"""
    logger.info("=" * 60)
    logger.info("PyRAG API Server")
    logger.info("=" * 60)
    
    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Development mode (auto-restart on code changes)
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    start_server()
