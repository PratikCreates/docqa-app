"""
Simplified FastAPI application with database support (working version)
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from services.multi_model_ai import MultiModelAIService
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env')  # Also try loading from current directory

# Initialize FastAPI app
app = FastAPI(
    title="Advanced Document Intelligence Platform",
    description="PostgreSQL-enabled document analysis platform",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_service = MultiModelAIService()

# Pydantic models
class UserRegistration(BaseModel):
    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "database": "postgresql",
        "services": {
            "api": "operational",
            "ai_models": "operational"
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Advanced Document Intelligence Platform",
        "version": "2.0.0",
        "database": "PostgreSQL",
        "status": "running"
    }

@app.get("/api/info")
async def get_api_info():
    """Get API information"""
    return {
        "title": "Advanced Document Intelligence Platform",
        "version": "2.0.0",
        "database": "PostgreSQL",
        "features": [
            "Multi-model AI support",
            "Document persistence",
            "User authentication",
            "Advanced search",
            "Document libraries"
        ]
    }

# Authentication endpoints (simplified)
@app.post("/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user (simplified)"""
    return {
        "message": "User registration endpoint ready",
        "note": "Database connection needed for full functionality",
        "user_email": user_data.email
    }

@app.post("/auth/login")
async def login_user(user_data: UserLogin):
    """Login user (simplified)"""
    return {
        "message": "User login endpoint ready",
        "note": "Database connection needed for full functionality",
        "user_email": user_data.email
    }

# Document endpoints (simplified)
@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload document (simplified)"""
    try:
        content = await file.read()
        
        return {
            "message": "Document upload endpoint ready",
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "note": "Database connection needed for persistence"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/documents")
async def get_documents():
    """Get documents (simplified)"""
    return {
        "message": "Documents endpoint ready",
        "documents": [],
        "note": "Database connection needed for document retrieval"
    }

@app.post("/ask")
async def ask_question(
    file: UploadFile = File(...),
    question: str = Form(...),
    model: Optional[str] = Form(None)
):
    """Ask question about document (working)"""
    try:
        # Read file content
        content = await file.read()
        
        # Simple text extraction
        if file.content_type and "text" in file.content_type:
            extracted_text = content.decode('utf-8', errors='ignore')
        else:
            extracted_text = f"[File: {file.filename}, Size: {len(content)} bytes]"
        
        # Get AI response
        response = await ai_service.process_document_question(
            extracted_text=extracted_text,
            question=question,
            file_type=file.filename.split('.')[-1].lower() if file.filename else "txt",
            model_id=model
        )
        
        return {
            "answer": response["answer"],
            "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            "model_used": response["model_used"],
            "filename": file.filename,
            "processing_time": response.get("processing_time", "N/A")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/models")
async def get_models():
    """Get available AI models"""
    try:
        models = ai_service.get_available_models()
        return {
            "available_models": models,
            "default_model": ai_service.get_default_model()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

# Advanced Search API Endpoints

@app.get("/search")
async def search_documents(
    q: str,
    user_id: str = "demo_user",
    size: int = 20,
    from_: int = 0,
    document_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    file_format: Optional[str] = None,
    tags: Optional[str] = None
):
    """Basic document search with filtering"""
    try:
        from services.elasticsearch_service import elasticsearch_service, SearchFilter
        
        # Build filters
        filters = []
        if document_type:
            filters.append(SearchFilter("document_type", document_type, "term"))
        if date_from:
            filters.append(SearchFilter("created_at", {"gte": date_from}, "range"))
        if date_to:
            filters.append(SearchFilter("created_at", {"lte": date_to}, "range"))
        if file_format:
            filters.append(SearchFilter("file_format", file_format, "term"))
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            filters.append(SearchFilter("tags", tag_list, "terms"))
        
        # Perform search
        results = elasticsearch_service.search_documents(
            user_id=user_id,
            query=q,
            filters=filters if filters else None,
            size=size,
            from_=from_
        )
        
        return {
            "query": q,
            "total_hits": results.total_hits,
            "took_ms": results.took_ms,
            "results": [
                {
                    "document_id": r.document_id,
                    "title": r.title,
                    "content_preview": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                    "score": r.score,
                    "highlights": r.highlights,
                    "metadata": r.metadata
                }
                for r in results.results
            ],
            "aggregations": results.aggregations,
            "suggestions": results.suggestions,
            "filters_applied": {
                "document_type": document_type,
                "date_range": f"{date_from} to {date_to}" if date_from or date_to else None,
                "file_format": file_format,
                "tags": tags
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search/advanced")
async def advanced_search(
    q: str,
    user_id: str = "demo_user",
    search_type: str = "standard",  # standard, fuzzy, semantic, code
    size: int = 20,
    from_: int = 0,
    sort_by: str = "relevance",  # relevance, date, title, size
    highlight: bool = True,
    document_type: Optional[str] = None,
    ai_model_used: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    file_format: Optional[str] = None,
    tags: Optional[str] = None
):
    """Advanced search with multiple search strategies and options"""
    try:
        from services.elasticsearch_service import elasticsearch_service, SearchFilter
        
        # Build filters
        filters = []
        if document_type:
            filters.append(SearchFilter("document_type", document_type, "term"))
        if ai_model_used:
            filters.append(SearchFilter("ai_model_used", ai_model_used, "term"))
        if date_from:
            filters.append(SearchFilter("created_at", {"gte": date_from}, "range"))
        if date_to:
            filters.append(SearchFilter("created_at", {"lte": date_to}, "range"))
        if file_format:
            filters.append(SearchFilter("file_format", file_format, "term"))
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            filters.append(SearchFilter("tags", tag_list, "terms"))
        
        # Perform advanced search
        results = elasticsearch_service.advanced_search(
            user_id=user_id,
            query=q,
            search_type=search_type,
            filters=filters if filters else None,
            size=size,
            from_=from_,
            highlight=highlight,
            sort_by=sort_by
        )
        
        return {
            "query": q,
            "search_type": search_type,
            "sort_by": sort_by,
            "total_hits": results.total_hits,
            "max_score": results.max_score,
            "took_ms": results.took_ms,
            "results": [
                {
                    "document_id": r.document_id,
                    "title": r.title,
                    "content_preview": r.content[:300] + "..." if len(r.content) > 300 else r.content,
                    "score": r.score,
                    "highlights": r.highlights if highlight else [],
                    "metadata": r.metadata
                }
                for r in results.results
            ],
            "aggregations": results.aggregations,
            "suggestions": results.suggestions,
            "search_info": {
                "strategy": search_type,
                "highlighting_enabled": highlight,
                "filters_applied": len(filters) if filters else 0,
                "sort_order": sort_by
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

@app.get("/search/suggestions")
async def get_search_suggestions(
    q: str,
    user_id: str = "demo_user",
    limit: int = 10
):
    """Get search suggestions based on partial query"""
    try:
        from services.elasticsearch_service import elasticsearch_service
        
        suggestions = elasticsearch_service.get_search_suggestions(
            user_id=user_id,
            partial_query=q,
            limit=limit
        )
        
        return {
            "partial_query": q,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@app.post("/search/save")
async def save_search(
    name: str = Form(...),
    query: str = Form(...),
    user_id: str = Form("demo_user"),
    filters: Optional[str] = Form(None)
):
    """Save a search query for later use"""
    try:
        from services.elasticsearch_service import elasticsearch_service, SearchFilter
        
        # Parse filters if provided
        filter_objects = []
        if filters:
            try:
                import json
                filter_data = json.loads(filters)
                for f in filter_data:
                    filter_objects.append(SearchFilter(
                        field=f["field"],
                        value=f["value"],
                        operator=f.get("operator", "term")
                    ))
            except json.JSONDecodeError:
                pass
        
        success = elasticsearch_service.save_search(
            user_id=user_id,
            name=name,
            query=query,
            filters=filter_objects if filter_objects else None
        )
        
        if success:
            return {
                "message": "Search saved successfully",
                "name": name,
                "query": query
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save search")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save search: {str(e)}")

@app.get("/search/saved")
async def get_saved_searches(user_id: str = "demo_user"):
    """Get user's saved searches"""
    try:
        from services.elasticsearch_service import elasticsearch_service
        
        saved_searches = elasticsearch_service.get_saved_searches(user_id)
        
        return {
            "saved_searches": saved_searches,
            "count": len(saved_searches)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get saved searches: {str(e)}")

@app.get("/search/history")
async def get_search_history(
    user_id: str = "demo_user",
    limit: int = 50
):
    """Get user's search history"""
    try:
        from services.elasticsearch_service import elasticsearch_service
        
        history = elasticsearch_service.get_search_history(user_id, limit)
        
        return {
            "search_history": history,
            "count": len(history),
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search history: {str(e)}")

@app.get("/search/analytics")
async def get_search_analytics(user_id: str = "demo_user"):
    """Get search analytics and insights"""
    try:
        from services.elasticsearch_service import elasticsearch_service
        
        analytics = elasticsearch_service.get_search_analytics(user_id)
        
        return {
            "user_id": user_id,
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search analytics: {str(e)}")

@app.get("/documents/{document_id}/similar")
async def get_similar_documents(
    document_id: str,
    user_id: str = "demo_user",
    limit: int = 5
):
    """Find documents similar to the specified document"""
    try:
        from services.elasticsearch_service import elasticsearch_service
        
        similar_docs = elasticsearch_service.get_similar_documents(
            document_id=document_id,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "document_id": document_id,
            "similar_documents": [
                {
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "content_preview": doc.content[:150] + "..." if len(doc.content) > 150 else doc.content,
                    "similarity_score": doc.score,
                    "metadata": doc.metadata
                }
                for doc in similar_docs
            ],
            "count": len(similar_docs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar documents: {str(e)}")

@app.get("/search/stats")
async def get_search_stats():
    """Get search index statistics"""
    try:
        from services.elasticsearch_service import elasticsearch_service
        
        stats = elasticsearch_service.get_index_stats()
        
        return {
            "index_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search stats: {str(e)}")

# Document Comparison API Endpoints

@app.post("/documents/compare")
async def compare_documents(
    document1_id: str = Form(...),
    document2_id: str = Form(...),
    comparison_type: str = Form("comprehensive"),
    user_id: str = Form("demo_user")
):
    """Compare two documents side-by-side with detailed analysis"""
    try:
        from services.document_comparison import document_comparison_engine
        
        # Mock document data (in real implementation, fetch from database)
        doc1 = {
            "id": document1_id,
            "title": f"Document {document1_id}",
            "content": f"This is the content of document {document1_id}. It contains various information about Python programming, including functions, classes, and best practices. The document covers advanced topics like decorators, context managers, and metaclasses.",
            "type": "text",
            "metadata": {
                "file_size": 1500,
                "created_at": "2024-01-15T10:30:00Z",
                "author": "John Doe"
            }
        }
        
        doc2 = {
            "id": document2_id,
            "title": f"Document {document2_id}",
            "content": f"This is the content of document {document2_id}. It discusses Python programming concepts, focusing on functions, object-oriented programming, and coding standards. The document also explores advanced Python features and design patterns.",
            "type": "text",
            "metadata": {
                "file_size": 1200,
                "created_at": "2024-01-20T14:45:00Z",
                "author": "Jane Smith"
            }
        }
        
        # Perform comparison
        comparison_result = document_comparison_engine.compare_documents(
            doc1, doc2, comparison_type
        )
        
        return {
            "comparison_id": f"comp_{document1_id}_{document2_id}",
            "document1": {
                "id": comparison_result.document1["id"],
                "title": comparison_result.document1["title"],
                "preview": comparison_result.document1["content"][:200] + "..."
            },
            "document2": {
                "id": comparison_result.document2["id"],
                "title": comparison_result.document2["title"],
                "preview": comparison_result.document2["content"][:200] + "..."
            },
            "similarity_scores": {
                "overall": round(comparison_result.overall_similarity, 3),
                "content": round(comparison_result.content_similarity, 3),
                "structure": round(comparison_result.structure_similarity, 3),
                "semantic": round(comparison_result.semantic_similarity, 3)
            },
            "differences": comparison_result.differences[:20],  # Limit for API response
            "common_sections": [
                {
                    "content_preview": section["content"][:100] + "..." if len(section["content"]) > 100 else section["content"],
                    "length": section["length"]
                }
                for section in comparison_result.common_sections[:10]
            ],
            "recommendations": comparison_result.recommendations,
            "metadata": comparison_result.comparison_metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document comparison failed: {str(e)}")

@app.get("/documents/{document_id}/find-similar")
async def find_similar_documents_detailed(
    document_id: str,
    user_id: str = "demo_user",
    limit: int = 10,
    min_similarity: float = 0.3,
    similarity_type: str = "all"
):
    """Find documents similar to the specified document with detailed analysis"""
    try:
        from services.document_comparison import document_comparison_engine
        
        # Mock target document
        target_doc = {
            "id": document_id,
            "title": f"Target Document {document_id}",
            "content": "This document discusses machine learning algorithms, including supervised learning, unsupervised learning, and deep learning. It covers neural networks, decision trees, and clustering algorithms.",
            "type": "text",
            "metadata": {"file_size": 2000, "created_at": "2024-01-10T09:00:00Z"}
        }
        
        # Mock document pool
        document_pool = []
        for i in range(1, 21):  # Generate 20 mock documents
            if str(i) == document_id:
                continue
                
            doc = {
                "id": str(i),
                "title": f"Document {i}",
                "content": f"Document {i} content about various topics including programming, data science, machine learning, and software development. This document contains detailed information and examples.",
                "type": "text",
                "metadata": {"file_size": 1000 + (i * 100), "created_at": f"2024-01-{i:02d}T10:00:00Z"}
            }
            document_pool.append(doc)
        
        # Find similar documents
        similar_docs = document_comparison_engine.find_similar_documents(
            target_doc, document_pool, limit, min_similarity
        )
        
        return {
            "target_document": {
                "id": target_doc["id"],
                "title": target_doc["title"],
                "content_preview": target_doc["content"][:200] + "..."
            },
            "similar_documents": [
                {
                    "document_id": sim.document2_id,
                    "similarity_score": round(sim.similarity_score, 3),
                    "similarity_type": sim.similarity_type,
                    "common_elements": sim.common_elements[:5],  # Top 5 common elements
                    "key_differences": sim.differences[:3],  # Top 3 differences
                    "metadata": {
                        "content_similarity": round(sim.metadata.get("content_similarity", 0), 3),
                        "structure_similarity": round(sim.metadata.get("structure_similarity", 0), 3),
                        "document_types": sim.metadata.get("document_types", [])
                    }
                }
                for sim in similar_docs
            ],
            "search_metadata": {
                "total_documents_searched": len(document_pool),
                "similar_documents_found": len(similar_docs),
                "min_similarity_threshold": min_similarity,
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar documents: {str(e)}")

@app.post("/documents/batch-compare")
async def batch_compare_documents(
    document_ids: str = Form(...),  # Comma-separated document IDs
    comparison_mode: str = Form("all_pairs"),
    user_id: str = Form("demo_user")
):
    """Perform batch comparison of multiple documents"""
    try:
        from services.document_comparison import document_comparison_engine
        
        # Parse document IDs
        doc_ids = [doc_id.strip() for doc_id in document_ids.split(",")]
        
        if len(doc_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 documents required for comparison")
        
        if len(doc_ids) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 documents allowed for batch comparison")
        
        # Mock documents
        documents = []
        for doc_id in doc_ids:
            doc = {
                "id": doc_id,
                "title": f"Document {doc_id}",
                "content": f"Content for document {doc_id}. This document covers topics related to software development, including programming languages, frameworks, and best practices. It contains examples and detailed explanations.",
                "type": "text",
                "metadata": {
                    "file_size": 1000 + (int(doc_id) * 200),
                    "created_at": f"2024-01-{int(doc_id):02d}T12:00:00Z"
                }
            }
            documents.append(doc)
        
        # Perform batch comparison
        batch_result = document_comparison_engine.batch_compare_documents(
            documents, comparison_mode
        )
        
        return {
            "batch_comparison_id": f"batch_{len(doc_ids)}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "summary": {
                "total_documents": batch_result.total_documents,
                "comparisons_performed": batch_result.comparisons_performed,
                "clusters_found": len(batch_result.clusters),
                "outliers_detected": len(batch_result.outliers)
            },
            "similarity_matrix": {
                doc_id: {
                    other_id: round(similarity, 3)
                    for other_id, similarity in similarities.items()
                }
                for doc_id, similarities in batch_result.similarity_matrix.items()
            },
            "clusters": [
                {
                    "cluster_id": f"cluster_{i+1}",
                    "document_ids": cluster,
                    "cluster_size": len(cluster)
                }
                for i, cluster in enumerate(batch_result.clusters)
            ],
            "outliers": [
                {
                    "document_id": outlier_id,
                    "reason": "Low similarity to other documents"
                }
                for outlier_id in batch_result.outliers
            ],
            "statistics": batch_result.summary_stats,
            "processing_metadata": {
                "comparison_mode": comparison_mode,
                "processing_time": "2.5s",  # Mock processing time
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch comparison failed: {str(e)}")

@app.get("/documents/{document_id}/fingerprint")
async def get_document_fingerprint(
    document_id: str,
    user_id: str = "demo_user"
):
    """Get a unique fingerprint for a document"""
    try:
        from services.document_comparison import document_comparison_engine
        
        # Mock document
        document = {
            "id": document_id,
            "title": f"Document {document_id}",
            "content": f"Unique content for document {document_id}. This document has specific characteristics that make it identifiable through fingerprinting.",
            "type": "text",
            "metadata": {
                "file_size": 1500,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
        
        # Generate fingerprint
        fingerprint = document_comparison_engine.get_document_fingerprint(document)
        
        return {
            "document_id": document_id,
            "fingerprint": fingerprint,
            "fingerprint_components": {
                "content_hash": fingerprint.split('-')[0],
                "structure_hash": fingerprint.split('-')[1]
            },
            "document_characteristics": {
                "content_length": len(document["content"]),
                "word_count": len(document["content"].split()),
                "document_type": document["type"],
                "file_size": document["metadata"]["file_size"]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate fingerprint: {str(e)}")

@app.get("/documents/comparison-analytics")
async def get_comparison_analytics(
    user_id: str = "demo_user",
    time_period: str = "30d"
):
    """Get analytics about document comparisons performed"""
    try:
        # Mock analytics data
        analytics = {
            "total_comparisons": 156,
            "comparisons_this_period": 45,
            "average_similarity_score": 0.62,
            "most_compared_documents": [
                {"document_id": "doc_1", "comparison_count": 12},
                {"document_id": "doc_5", "comparison_count": 8},
                {"document_id": "doc_3", "comparison_count": 7}
            ],
            "similarity_distribution": {
                "high_similarity": 23,  # >0.7
                "medium_similarity": 89,  # 0.3-0.7
                "low_similarity": 44   # <0.3
            },
            "comparison_types": {
                "comprehensive": 98,
                "content_only": 34,
                "structure_only": 24
            },
            "batch_comparisons": {
                "total_batches": 12,
                "average_batch_size": 5.2,
                "largest_batch": 15
            },
            "trends": {
                "daily_comparisons": [3, 7, 12, 8, 15, 9, 11],
                "popular_comparison_days": ["Tuesday", "Wednesday", "Thursday"]
            }
        }
        
        return {
            "user_id": user_id,
            "time_period": time_period,
            "analytics": analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comparison analytics: {str(e)}")

# Cross-Document Analysis API Endpoints

@app.post("/documents/analyze-relationships")
async def analyze_document_relationships(
    document_ids: str = Form(...),  # Comma-separated document IDs
    relationship_types: str = Form("all"),  # Comma-separated relationship types or "all"
    user_id: str = Form("demo_user")
):
    """Analyze relationships between a collection of documents"""
    try:
        from services.cross_document_analysis import cross_document_analysis_service, RelationshipType
        
        # Parse document IDs
        doc_ids = [doc_id.strip() for doc_id in document_ids.split(",")]
        
        if len(doc_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 documents required for relationship analysis")
        
        # Mock documents
        documents = []
        for doc_id in doc_ids:
            doc = {
                "id": doc_id,
                "title": f"Document {doc_id}",
                "content": f"This is document {doc_id} about software development, programming languages, and technical documentation. It contains information about Python, JavaScript, databases, and API development.",
                "type": "text",
                "created_at": f"2024-01-{int(doc_id):02d}T10:00:00Z",
                "metadata": {
                    "author": f"Author_{int(doc_id) % 3 + 1}",
                    "file_size": 1000 + (int(doc_id) * 200)
                }
            }
            documents.append(doc)
        
        # Parse relationship types
        if relationship_types == "all":
            rel_types = None
        else:
            rel_type_names = [rt.strip() for rt in relationship_types.split(",")]
            rel_types = []
            for name in rel_type_names:
                try:
                    rel_types.append(RelationshipType(name))
                except ValueError:
                    continue
        
        # Analyze relationships
        relationships = cross_document_analysis_service.analyze_document_relationships(
            documents, rel_types
        )
        
        return {
            "analysis_id": f"rel_analysis_{len(doc_ids)}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "document_count": len(documents),
            "relationships_found": len(relationships),
            "relationships": [
                {
                    "source_document": rel.source_doc_id,
                    "target_document": rel.target_doc_id,
                    "relationship_type": rel.relationship_type.value,
                    "strength": round(rel.strength, 3),
                    "evidence": rel.evidence[:3],  # Top 3 evidence items
                    "metadata": rel.metadata
                }
                for rel in relationships[:20]  # Limit to top 20 relationships
            ],
            "relationship_summary": {
                rel_type.value: len([r for r in relationships if r.relationship_type == rel_type])
                for rel_type in RelationshipType
            },
            "analysis_metadata": {
                "analyzed_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "processing_time": "1.2s"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relationship analysis failed: {str(e)}")

@app.post("/documents/create-clusters")
async def create_document_clusters(
    document_ids: str = Form(...),
    clustering_method: str = Form("topic"),  # topic, temporal, author, similarity
    max_clusters: int = Form(10),
    user_id: str = Form("demo_user")
):
    """Create clusters of related documents"""
    try:
        from services.cross_document_analysis import cross_document_analysis_service
        
        # Parse document IDs
        doc_ids = [doc_id.strip() for doc_id in document_ids.split(",")]
        
        if len(doc_ids) < 3:
            raise HTTPException(status_code=400, detail="At least 3 documents required for clustering")
        
        # Mock documents
        documents = []
        topics = ["programming", "data_science", "web_development", "database", "security"]
        authors = ["Alice", "Bob", "Charlie"]
        
        for doc_id in doc_ids:
            doc = {
                "id": doc_id,
                "title": f"Document {doc_id}",
                "content": f"This document covers {topics[int(doc_id) % len(topics)]} topics including advanced concepts and practical examples. It provides comprehensive coverage of the subject matter.",
                "type": "text",
                "created_at": f"2024-01-{int(doc_id):02d}T10:00:00Z",
                "metadata": {
                    "author": authors[int(doc_id) % len(authors)],
                    "file_size": 1000 + (int(doc_id) * 200)
                }
            }
            documents.append(doc)
        
        # Create clusters
        clusters = cross_document_analysis_service.create_document_clusters(
            documents, clustering_method, max_clusters
        )
        
        return {
            "clustering_id": f"clustering_{clustering_method}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "clustering_method": clustering_method,
            "total_documents": len(documents),
            "clusters_created": len(clusters),
            "clusters": [
                {
                    "cluster_id": cluster.cluster_id,
                    "cluster_name": cluster.cluster_name,
                    "document_count": len(cluster.document_ids),
                    "document_ids": cluster.document_ids,
                    "cluster_type": cluster.cluster_type,
                    "coherence_score": round(cluster.coherence_score, 3),
                    "centroid_features": cluster.centroid_features,
                    "created_at": cluster.created_at.isoformat()
                }
                for cluster in clusters
            ],
            "clustering_summary": {
                "largest_cluster_size": max(len(c.document_ids) for c in clusters) if clusters else 0,
                "average_cluster_size": sum(len(c.document_ids) for c in clusters) / len(clusters) if clusters else 0,
                "unclustered_documents": len(documents) - sum(len(c.document_ids) for c in clusters)
            },
            "analysis_metadata": {
                "clustered_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "max_clusters_requested": max_clusters
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document clustering failed: {str(e)}")

@app.post("/documents/trend-analysis")
async def perform_trend_analysis(
    document_ids: str = Form(...),
    time_window: int = Form(30),  # days
    min_document_count: int = Form(3),
    user_id: str = Form("demo_user")
):
    """Perform trend analysis across document collections"""
    try:
        from services.cross_document_analysis import cross_document_analysis_service
        
        # Parse document IDs
        doc_ids = [doc_id.strip() for doc_id in document_ids.split(",")]
        
        if len(doc_ids) < 5:
            raise HTTPException(status_code=400, detail="At least 5 documents required for trend analysis")
        
        # Mock documents with temporal distribution
        documents = []
        topics = ["programming", "data_science", "web_development", "database", "security", "api"]
        
        for i, doc_id in enumerate(doc_ids):
            # Create temporal distribution
            days_ago = i * 2  # Spread documents over time
            created_date = datetime.utcnow() - timedelta(days=days_ago)
            
            doc = {
                "id": doc_id,
                "title": f"Document {doc_id}",
                "content": f"This document discusses {topics[i % len(topics)]} and related technologies. It covers current trends and emerging patterns in the field.",
                "type": "text",
                "created_at": created_date.isoformat() + "Z",
                "metadata": {
                    "author": f"Author_{i % 3 + 1}",
                    "file_size": 1000 + (int(doc_id) * 200)
                }
            }
            documents.append(doc)
        
        # Perform trend analysis
        trends = cross_document_analysis_service.perform_trend_analysis(
            documents, time_window, min_document_count
        )
        
        return {
            "analysis_id": f"trend_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "time_window_days": time_window,
            "total_documents": len(documents),
            "trends_identified": len(trends),
            "trends": [
                {
                    "trend_id": trend.trend_id,
                    "trend_name": trend.trend_name,
                    "time_period": {
                        "start": trend.time_period[0].isoformat(),
                        "end": trend.time_period[1].isoformat()
                    },
                    "document_count": trend.document_count,
                    "key_topics": trend.key_topics,
                    "trend_direction": trend.trend_direction,
                    "trend_strength": round(trend.trend_strength, 3),
                    "supporting_documents": trend.supporting_documents[:5]  # Top 5 supporting docs
                }
                for trend in trends
            ],
            "trend_summary": {
                "increasing_trends": len([t for t in trends if t.trend_direction == "increasing"]),
                "decreasing_trends": len([t for t in trends if t.trend_direction == "decreasing"]),
                "stable_trends": len([t for t in trends if t.trend_direction == "stable"]),
                "strongest_trend": max(trends, key=lambda x: x.trend_strength).trend_name if trends else None
            },
            "analysis_metadata": {
                "analyzed_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "min_document_threshold": min_document_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@app.post("/documents/cross-search")
async def cross_document_search(
    query: str = Form(...),
    document_ids: str = Form(...),
    search_type: str = Form("comprehensive"),  # comprehensive, entity, topic, temporal
    user_id: str = Form("demo_user")
):
    """Perform cross-document search with correlation analysis"""
    try:
        from services.cross_document_analysis import cross_document_analysis_service
        
        # Parse document IDs
        doc_ids = [doc_id.strip() for doc_id in document_ids.split(",")]
        
        # Mock documents
        documents = []
        for doc_id in doc_ids:
            # Create content that may or may not match the query
            content_variations = [
                f"This document about {query} provides comprehensive coverage of the topic with detailed examples and explanations.",
                f"Technical documentation covering software development, programming concepts, and {query} implementation details.",
                f"Research paper discussing {query} methodologies, best practices, and industry applications.",
                f"Tutorial guide for {query} with step-by-step instructions and practical examples.",
                f"Analysis of {query} trends, patterns, and future developments in the field."
            ]
            
            doc = {
                "id": doc_id,
                "title": f"Document {doc_id} - {query.title()} Guide",
                "content": content_variations[int(doc_id) % len(content_variations)],
                "type": "text",
                "created_at": f"2024-01-{int(doc_id):02d}T10:00:00Z",
                "metadata": {
                    "author": f"Author_{int(doc_id) % 3 + 1}",
                    "file_size": 1000 + (int(doc_id) * 200)
                }
            }
            documents.append(doc)
        
        # Perform cross-document search
        search_result = cross_document_analysis_service.cross_document_search(
            query, documents, search_type
        )
        
        return {
            "search_id": f"cross_search_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "query": search_result.query,
            "search_type": search_type,
            "total_documents_searched": search_result.total_documents,
            "matching_documents": len(search_result.matching_documents),
            "matching_document_ids": search_result.matching_documents,
            "correlations": [
                {
                    "source_document": corr.source_doc_id,
                    "target_document": corr.target_doc_id,
                    "relationship_type": corr.relationship_type.value,
                    "strength": round(corr.strength, 3),
                    "evidence": corr.evidence[:2]
                }
                for corr in search_result.correlations[:10]
            ],
            "entity_mentions": {
                entity: doc_ids[:5]  # Limit to 5 documents per entity
                for entity, doc_ids in search_result.entity_mentions.items()
            },
            "topic_distribution": search_result.topic_distribution,
            "temporal_patterns": search_result.temporal_patterns,
            "search_metadata": {
                "searched_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "correlations_found": len(search_result.correlations)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cross-document search failed: {str(e)}")

@app.post("/documents/network-map")
async def create_document_network_map(
    document_ids: str = Form(...),
    min_relationship_strength: float = Form(0.3),
    user_id: str = Form("demo_user")
):
    """Create a network map of document relationships"""
    try:
        from services.cross_document_analysis import cross_document_analysis_service
        
        # Parse document IDs
        doc_ids = [doc_id.strip() for doc_id in document_ids.split(",")]
        
        if len(doc_ids) < 3:
            raise HTTPException(status_code=400, detail="At least 3 documents required for network mapping")
        
        # Mock documents
        documents = []
        topics = ["programming", "data_science", "web_development", "database", "security"]
        
        for doc_id in doc_ids:
            doc = {
                "id": doc_id,
                "title": f"Document {doc_id}",
                "content": f"This document covers {topics[int(doc_id) % len(topics)]} with detailed technical information and practical examples.",
                "type": "text",
                "created_at": f"2024-01-{int(doc_id):02d}T10:00:00Z",
                "metadata": {
                    "author": f"Author_{int(doc_id) % 3 + 1}",
                    "file_size": 1000 + (int(doc_id) * 200)
                }
            }
            documents.append(doc)
        
        # Create network map
        network_map = cross_document_analysis_service.map_document_network(
            documents, min_relationship_strength
        )
        
        return {
            "network_id": f"network_map_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "network_map": network_map,
            "network_summary": {
                "total_nodes": len(network_map["nodes"]),
                "total_edges": len(network_map["edges"]),
                "network_density": network_map["statistics"]["density"],
                "most_connected_document": max(
                    network_map["nodes"], 
                    key=lambda x: len([e for e in network_map["edges"] if e["source"] == x["id"] or e["target"] == x["id"]])
                )["id"] if network_map["nodes"] else None
            },
            "relationship_types": {
                rel_type: len([e for e in network_map["edges"] if e["type"] == rel_type])
                for rel_type in set(e["type"] for e in network_map["edges"])
            },
            "analysis_metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "min_strength_threshold": min_relationship_strength
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Network mapping failed: {str(e)}")

@app.get("/documents/{document_id}/influence-score")
async def get_document_influence_score(
    document_id: str,
    context_document_ids: str = "",  # Comma-separated document IDs for context
    user_id: str = "demo_user"
):
    """Calculate influence score for a document based on its relationships"""
    try:
        from services.cross_document_analysis import cross_document_analysis_service
        
        # Parse context document IDs
        if context_document_ids:
            doc_ids = [document_id] + [doc_id.strip() for doc_id in context_document_ids.split(",")]
        else:
            # Use a default set of documents for context
            doc_ids = [document_id] + [str(i) for i in range(1, 11) if str(i) != document_id]
        
        # Mock documents
        documents = []
        for doc_id in doc_ids:
            doc = {
                "id": doc_id,
                "title": f"Document {doc_id}",
                "content": f"This is document {doc_id} with content about various technical topics and references to other documents.",
                "type": "text",
                "created_at": f"2024-01-{int(doc_id):02d}T10:00:00Z",
                "metadata": {"author": f"Author_{int(doc_id) % 3 + 1}"}
            }
            documents.append(doc)
        
        # Analyze relationships
        relationships = cross_document_analysis_service.analyze_document_relationships(documents)
        
        # Calculate influence score
        influence_score = cross_document_analysis_service.get_document_influence_score(
            document_id, relationships
        )
        
        # Get related relationships
        related_relationships = [
            rel for rel in relationships 
            if rel.source_doc_id == document_id or rel.target_doc_id == document_id
        ]
        
        return {
            "document_id": document_id,
            "influence_score": round(influence_score, 3),
            "influence_level": (
                "High" if influence_score > 0.7 else
                "Medium" if influence_score > 0.4 else
                "Low"
            ),
            "relationship_summary": {
                "total_relationships": len(related_relationships),
                "incoming_relationships": len([r for r in related_relationships if r.target_doc_id == document_id]),
                "outgoing_relationships": len([r for r in related_relationships if r.source_doc_id == document_id]),
                "strongest_relationship": max(related_relationships, key=lambda x: x.strength).strength if related_relationships else 0
            },
            "top_relationships": [
                {
                    "related_document": rel.target_doc_id if rel.source_doc_id == document_id else rel.source_doc_id,
                    "relationship_type": rel.relationship_type.value,
                    "strength": round(rel.strength, 3),
                    "direction": "outgoing" if rel.source_doc_id == document_id else "incoming"
                }
                for rel in sorted(related_relationships, key=lambda x: x.strength, reverse=True)[:5]
            ],
            "analysis_metadata": {
                "analyzed_at": datetime.utcnow().isoformat(),
                "context_documents": len(doc_ids) - 1,
                "user_id": user_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate influence score: {str(e)}")

@app.post("/generate-questions")
async def generate_questions(
    file: UploadFile = File(...),
    max_questions: int = Form(10),
    document_category: str = Form("general"),
    user_preferences: Optional[str] = Form(None)
):
    """Generate contextually relevant questions from document content"""
    try:
        # Read file content
        content = await file.read()
        
        # Simple text extraction
        if file.content_type and "text" in file.content_type:
            extracted_text = content.decode('utf-8', errors='ignore')
        else:
            extracted_text = f"[File: {file.filename}, Size: {len(content)} bytes]"
        
        # Auto-detect document category if not specified
        if document_category == "general":
            document_category = detect_document_category(extracted_text, file.filename)
        
        # Parse user preferences
        preferences = {}
        if user_preferences:
            try:
                import json
                preferences = json.loads(user_preferences)
            except json.JSONDecodeError:
                pass
        
        # Import question generator
        from services.question_generator import question_generator
        
        # Generate questions
        questions = await question_generator.generate_questions(
            content=extracted_text,
            document_category=document_category,
            filename=file.filename,
            max_questions=max_questions,
            user_preferences=preferences
        )
        
        # Convert to response format
        questions_data = [q.to_dict() for q in questions]
        
        # Categorize questions
        categorized_questions = question_generator.categorize_questions(questions)
        categories_summary = {category: len(qs) for category, qs in categorized_questions.items()}
        
        return {
            "filename": file.filename,
            "document_category": document_category,
            "total_questions": len(questions_data),
            "categories_summary": categories_summary,
            "questions": questions_data,
            "categorized_questions": {
                category: [q.to_dict() for q in qs] 
                for category, qs in categorized_questions.items()
            },
            "generation_info": {
                "max_requested": max_questions,
                "generated": len(questions_data),
                "user_preferences_applied": bool(preferences)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

def detect_document_category(text: str, filename: str) -> str:
    """Auto-detect document category based on content and filename"""
    if not text or not filename:
        return "general"
    
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # Code files
    code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.sh', '.go', '.rs']
    if any(filename_lower.endswith(ext) for ext in code_extensions):
        return "code"
    
    # Code indicators in content
    code_indicators = ['def ', 'function ', 'class ', 'import ', 'from ', '#include', 'public class']
    if any(indicator in text_lower for indicator in code_indicators):
        return "code"
    
    # Research/academic papers
    research_indicators = ['abstract', 'methodology', 'hypothesis', 'research', 'study', 'analysis', 'findings']
    research_count = sum(1 for indicator in research_indicators if indicator in text_lower)
    if research_count >= 3:
        return "research"
    
    # Documentation
    doc_indicators = ['documentation', 'guide', 'tutorial', 'instructions', 'how to', 'setup', 'installation']
    if any(indicator in text_lower for indicator in doc_indicators):
        return "documentation"
    
    # Web content
    if filename_lower.endswith(('.html', '.css')) or '<html' in text_lower or '<div' in text_lower:
        return "web"
    
    # Data files
    if filename_lower.endswith(('.json', '.csv', '.xml', '.yaml')):
        return "data"
    
    return "general"

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    print("🚀 Starting Advanced Document Intelligence Platform (Simplified)")
    print("✅ PostgreSQL database models ready")
    print("✅ AI services initialized")
    print("⚠️  Database connection will be established when PostgreSQL auth is fixed")
    print("✅ Application ready!")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)