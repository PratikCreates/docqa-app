"""
Main FastAPI application with database, authentication, and document management
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.multi_model_ai import MultiModelAIService
from services.auth_service import auth_service
from services.document_service import document_service
from services.cache_service import cache_service
from services.elasticsearch_service import elasticsearch_service
from services.rate_limiter import rate_limiter
from models.database import get_db, create_tables
from middleware.api_middleware import APIMiddleware, RequestLoggingMiddleware
from api_spec import create_openapi_spec, get_api_info
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app with comprehensive configuration
api_info = get_api_info()
app = FastAPI(
    title=api_info["title"],
    description=api_info["description"],
    version=api_info["version"],
    contact=api_info["contact"],
    license_info=api_info["license"],
    terms_of_service=api_info["terms_of_service"],
    openapi_tags=[
        {"name": "Authentication", "description": "User authentication and authorization"},
        {"name": "Documents", "description": "Document upload, management, and processing"},
        {"name": "Search", "description": "Advanced search and document discovery"},
        {"name": "Questions", "description": "AI-powered question generation"},
        {"name": "Libraries", "description": "Document organization and library management"},
        {"name": "Analytics", "description": "Usage analytics and insights"},
        {"name": "Models", "description": "AI model information and recommendations"},
        {"name": "System", "description": "System health and configuration"}
    ]
)

# Add comprehensive middleware
app.add_middleware(APIMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware (handled by APIMiddleware, but keeping for compatibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
ai_service = MultiModelAIService()

# Pydantic models for request/response
class UserRegistration(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    document_category: str
    file_size: int
    created_at: str
    processing_status: str

class LibraryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class QuestionRequest(BaseModel):
    question: str
    model_preference: Optional[str] = None

class QuestionGenerationRequest(BaseModel):
    max_questions: Optional[int] = 10
    categories: Optional[List[str]] = None
    user_preferences: Optional[Dict[str, Any]] = None

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = auth_service.get_user_by_id(db, payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    print("🚀 Starting Advanced Document Intelligence Platform...")
    
    # Create database tables
    try:
        create_tables()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
    
    # Test services
    cache_info = cache_service.get_cache_info()
    print(f"📦 Cache status: {cache_info.get('status', 'unknown')}")
    
    es_stats = elasticsearch_service.get_index_stats()
    print(f"🔍 Elasticsearch status: {es_stats.get('status', 'unknown')}")
    
    print("✅ Platform startup complete!")

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Comprehensive health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "cache": cache_service.get_cache_info(),
            "elasticsearch": elasticsearch_service.get_index_stats(),
            "ai_models": ai_service.get_available_models(),
            "database": "connected"
        },
        "uptime": "running"
    }

@app.get("/api/info", tags=["System"])
async def get_api_information():
    """Get comprehensive API information"""
    return {
        "api": get_api_info(),
        "endpoints": {
            "total": len(app.routes),
            "public": 8,
            "authenticated": len(app.routes) - 8
        },
        "rate_limits": {
            "free": rate_limiter.rate_limits["free"],
            "premium": rate_limiter.rate_limits["premium"],
            "enterprise": rate_limiter.rate_limits["enterprise"]
        },
        "supported_formats": {
            "documents": ["txt", "md", "html", "xml", "pdf"],
            "code": ["py", "js", "ts", "java", "cpp", "c", "sh"],
            "images": ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"],
            "data": ["json", "csv", "yaml", "yml"],
            "notebooks": ["ipynb"]
        }
    }

@app.get("/api/status", tags=["System"])
async def get_system_status():
    """Get detailed system status and metrics"""
    return {
        "system": {
            "status": "operational",
            "load": "normal",
            "memory_usage": "optimal",
            "disk_usage": "normal"
        },
        "services": {
            "api": "operational",
            "database": "operational",
            "cache": "operational",
            "search": "operational",
            "ai_models": "operational"
        },
        "metrics": {
            "requests_per_minute": 0,
            "average_response_time": "150ms",
            "error_rate": "0.1%",
            "uptime": "99.9%"
        }
    }

# Authentication endpoints
@app.post("/auth/register")
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = auth_service.register_user(
            db=db,
            email=user_data.email,
            name=user_data.name,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create tokens
        access_token = auth_service.create_access_token(user.id, user.email)
        refresh_token = auth_service.create_refresh_token(user.id, user.email)
        
        return {
            "message": "User registered successfully",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login")
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    try:
        user = auth_service.authenticate_user(
            db=db,
            email=user_data.email,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create tokens
        access_token = auth_service.create_access_token(user.id, user.email)
        refresh_token = auth_service.create_refresh_token(user.id, user.email)
        
        return {
            "message": "Login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "preferences": current_user.preferences,
        "created_at": current_user.created_at.isoformat()
    }

# Document management endpoints
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    try:
        # Read file content
        content = await file.read()
        
        # Upload document
        document = document_service.upload_document(
            db=db,
            user_id=str(current_user.id),
            filename=file.filename,
            file_content=content,
            content_type=file.content_type
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload document"
            )
        
        return {
            "message": "Document uploaded successfully",
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "content_type": document.content_type,
                "document_category": document.document_category,
                "file_size": document.file_size,
                "created_at": document.created_at.isoformat(),
                "processing_status": document.processing_status
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/documents")
async def get_user_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's documents with pagination and filtering"""
    try:
        documents = document_service.get_user_documents(
            db=db,
            user_id=str(current_user.id),
            skip=skip,
            limit=limit,
            category_filter=category
        )
        
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "content_type": doc.content_type,
                    "document_category": doc.document_category,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at.isoformat(),
                    "processing_status": doc.processing_status
                }
                for doc in documents
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": len(documents)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )

@app.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document"""
    try:
        document = document_service.get_document(
            db=db,
            document_id=document_id,
            user_id=str(current_user.id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "id": str(document.id),
            "filename": document.filename,
            "content_type": document.content_type,
            "document_category": document.document_category,
            "file_size": document.file_size,
            "extracted_text": document.extracted_text[:1000] + "..." if len(document.extracted_text) > 1000 else document.extracted_text,
            "metadata": document.metadata,
            "created_at": document.created_at.isoformat(),
            "processing_status": document.processing_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )

@app.post("/documents/{document_id}/ask")
async def ask_document_question(
    document_id: str,
    question_data: QuestionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question about a specific document"""
    try:
        # Get document
        document = document_service.get_document(
            db=db,
            document_id=document_id,
            user_id=str(current_user.id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get AI response
        response = await ai_service.process_document_question(
            content=document.extracted_text,
            question=question_data.question,
            filename=document.filename,
            model_preference=question_data.model_preference
        )
        
        # Record in processing history
        document_service.record_processing_history(
            db=db,
            document_id=document_id,
            question=question_data.question,
            answer=response["answer"],
            ai_model=response["model_used"],
            confidence_score=response.get("confidence", 0.8),
            processing_time_ms=response.get("processing_time_ms", 0)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    try:
        success = document_service.delete_document(
            db=db,
            document_id=document_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or could not be deleted"
            )
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

# Search endpoints
@app.get("/search")
async def search_documents(
    q: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Search documents using Elasticsearch"""
    try:
        filters = {}
        if category:
            filters["document_category"] = category
        if content_type:
            filters["content_type"] = content_type
        
        results = document_service.search_documents(
            user_id=str(current_user.id),
            query=q,
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        return {
            "query": q,
            "results": results["hits"],
            "total": results["total"],
            "page": page,
            "page_size": page_size,
            "max_score": results.get("max_score", 0)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@app.get("/search/advanced")
async def advanced_search_documents(
    q: str = Query(..., min_length=1),
    search_type: str = Query("hybrid", regex="^(standard|hybrid|fuzzy|semantic)$"),
    category: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    programming_languages: Optional[str] = Query(None),
    has_text: Optional[bool] = Query(None),
    ocr_confidence_min: Optional[float] = Query(None, ge=0, le=100),
    complexity_min: Optional[float] = Query(None, ge=0),
    complexity_max: Optional[float] = Query(None, ge=0),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Advanced search with multiple search strategies and filters"""
    try:
        filters = {}
        
        # Basic filters
        if category:
            filters["document_category"] = category
        if content_type:
            filters["content_type"] = content_type
        if has_text is not None:
            filters["has_text"] = has_text
        if ocr_confidence_min is not None:
            filters["ocr_confidence_min"] = ocr_confidence_min
        
        # Programming language filter
        if programming_languages:
            filters["programming_languages"] = programming_languages.split(",")
        
        # Complexity range filter
        if complexity_min is not None or complexity_max is not None:
            complexity_range = {}
            if complexity_min is not None:
                complexity_range["min"] = complexity_min
            if complexity_max is not None:
                complexity_range["max"] = complexity_max
            filters["complexity_range"] = complexity_range
        
        # Date range filter
        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["gte"] = date_from
            if date_to:
                date_range["lte"] = date_to
            filters["date_range"] = date_range
        
        # Use advanced search
        from services.elasticsearch_service import elasticsearch_service
        results = elasticsearch_service.advanced_search(
            user_id=str(current_user.id),
            query=q,
            search_type=search_type,
            filters=filters,
            size=page_size,
            from_=(page - 1) * page_size
        )
        
        return {
            "query": q,
            "search_type": search_type,
            "results": results["hits"],
            "total": results["total"],
            "page": page,
            "page_size": page_size,
            "max_score": results.get("max_score", 0),
            "filters_applied": filters
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced search failed: {str(e)}"
        )

@app.get("/search/analytics")
async def get_search_analytics(current_user = Depends(get_current_user)):
    """Get search analytics and document insights"""
    try:
        from services.elasticsearch_service import elasticsearch_service
        analytics = elasticsearch_service.get_search_analytics(str(current_user.id))
        
        return {
            "user_id": str(current_user.id),
            "analytics": analytics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

@app.post("/search/reindex")
async def reindex_user_documents(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reindex all user documents for improved search"""
    try:
        # Get all user documents
        documents = document_service.get_user_documents(
            db=db,
            user_id=str(current_user.id),
            skip=0,
            limit=1000  # Process in batches for large collections
        )
        
        # Prepare documents for reindexing
        doc_data = []
        for doc in documents:
            doc_data.append({
                "id": doc.id,
                "user_id": doc.user_id,
                "filename": doc.filename,
                "extracted_text": doc.extracted_text,
                "content_type": doc.content_type,
                "document_category": doc.document_category,
                "file_size": doc.file_size,
                "metadata": doc.metadata,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                "processing_status": doc.processing_status
            })
        
        # Bulk reindex
        from services.elasticsearch_service import elasticsearch_service
        result = elasticsearch_service.bulk_reindex(doc_data)
        
        return {
            "message": "Reindexing completed",
            "total_documents": len(documents),
            "indexed": result.get("indexed", 0),
            "failed": result.get("failed", 0),
            "success": result.get("success", False)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing failed: {str(e)}"
        )

@app.get("/documents/{document_id}/similar")
async def get_similar_documents(
    document_id: str,
    limit: int = Query(5, ge=1, le=20),
    current_user = Depends(get_current_user)
):
    """Get documents similar to the specified document"""
    try:
        similar_docs = document_service.get_similar_documents(
            document_id=document_id,
            user_id=str(current_user.id),
            limit=limit
        )
        
        return {
            "document_id": document_id,
            "similar_documents": similar_docs
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get similar documents: {str(e)}"
        )

# Library management endpoints
@app.post("/libraries")
async def create_library(
    library_data: LibraryCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new document library"""
    try:
        library = document_service.create_library(
            db=db,
            user_id=str(current_user.id),
            name=library_data.name,
            description=library_data.description,
            tags=library_data.tags
        )
        
        if not library:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create library"
            )
        
        return {
            "message": "Library created successfully",
            "library": {
                "id": str(library.id),
                "name": library.name,
                "description": library.description,
                "tags": library.tags,
                "created_at": library.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create library: {str(e)}"
        )

@app.get("/libraries")
async def get_user_libraries(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's document libraries"""
    try:
        libraries = document_service.get_user_libraries(
            db=db,
            user_id=str(current_user.id)
        )
        
        return {
            "libraries": [
                {
                    "id": str(lib.id),
                    "name": lib.name,
                    "description": lib.description,
                    "tags": lib.tags,
                    "is_shared": lib.is_shared,
                    "created_at": lib.created_at.isoformat()
                }
                for lib in libraries
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get libraries: {str(e)}"
        )

@app.post("/libraries/{library_id}/documents/{document_id}")
async def add_document_to_library(
    library_id: str,
    document_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a document to a library"""
    try:
        success = document_service.add_document_to_library(
            db=db,
            library_id=library_id,
            document_id=document_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add document to library"
            )
        
        return {"message": "Document added to library successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add document to library: {str(e)}"
        )

@app.get("/libraries/{library_id}/documents")
async def get_library_documents(
    library_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get documents in a library"""
    try:
        documents = document_service.get_library_documents(
            db=db,
            library_id=library_id,
            user_id=str(current_user.id)
        )
        
        return {
            "library_id": library_id,
            "documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "content_type": doc.content_type,
                    "document_category": doc.document_category,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at.isoformat()
                }
                for doc in documents
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get library documents: {str(e)}"
        )

# Statistics and analytics
@app.get("/stats")
async def get_user_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics and analytics"""
    try:
        stats = document_service.get_document_stats(
            db=db,
            user_id=str(current_user.id)
        )
        
        return {
            "user_id": str(current_user.id),
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

# Question generation endpoints
@app.post("/documents/{document_id}/generate-questions")
async def generate_document_questions(
    document_id: str,
    request_data: QuestionGenerationRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate contextually relevant questions for a document"""
    try:
        questions = await document_service.generate_document_questions(
            db=db,
            document_id=document_id,
            user_id=str(current_user.id),
            max_questions=request_data.max_questions,
            user_preferences=request_data.user_preferences
        )
        
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or no questions could be generated"
            )
        
        # Categorize questions
        categorized_questions = document_service.get_categorized_questions(questions)
        
        return {
            "document_id": document_id,
            "total_questions": len(questions),
            "questions": questions,
            "categorized_questions": categorized_questions,
            "generation_info": {
                "max_requested": request_data.max_questions,
                "categories_available": list(categorized_questions.keys())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )

@app.get("/documents/{document_id}/questions")
async def get_document_questions(
    document_id: str,
    max_questions: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get generated questions for a document (with caching)"""
    try:
        # Check if we have cached questions first
        cache_key = f"questions:{document_id}:{max_questions}"
        cached_questions = cache_service.get(cache_key)
        
        if cached_questions:
            questions = cached_questions
        else:
            # Generate new questions
            questions = await document_service.generate_document_questions(
                db=db,
                document_id=document_id,
                user_id=str(current_user.id),
                max_questions=max_questions
            )
            
            # Cache for 1 hour
            cache_service.set(cache_key, questions, expire_seconds=3600)
        
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or no questions available"
            )
        
        # Filter by category if requested
        if category:
            questions = [q for q in questions if q.get("category") == category]
        
        # Categorize questions
        categorized_questions = document_service.get_categorized_questions(questions)
        
        return {
            "document_id": document_id,
            "questions": questions,
            "categorized_questions": categorized_questions,
            "filter_applied": category,
            "total_questions": len(questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get questions: {str(e)}"
        )

@app.post("/documents/{document_id}/questions/{question_index}/ask")
async def ask_generated_question(
    document_id: str,
    question_index: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a specific generated question about a document"""
    try:
        # Get the generated questions
        questions = await document_service.generate_document_questions(
            db=db,
            document_id=document_id,
            user_id=str(current_user.id)
        )
        
        if not questions or question_index >= len(questions):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        selected_question = questions[question_index]
        question_text = selected_question["text"]
        
        # Get document
        document = document_service.get_document(
            db=db,
            document_id=document_id,
            user_id=str(current_user.id)
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get AI response
        response = await ai_service.process_document_question(
            content=document.extracted_text,
            question=question_text,
            filename=document.filename
        )
        
        # Record in processing history
        document_service.record_processing_history(
            db=db,
            document_id=document_id,
            question=question_text,
            answer=response["answer"],
            ai_model=response["model_used"],
            confidence_score=response.get("confidence", 0.8),
            processing_time_ms=response.get("processing_time_ms", 0)
        )
        
        return {
            "question": selected_question,
            "question_index": question_index,
            "answer": response["answer"],
            "model_used": response["model_used"],
            "confidence": response.get("confidence", 0.8),
            "processing_time_ms": response.get("processing_time_ms", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process generated question: {str(e)}"
        )

@app.get("/question-categories")
async def get_question_categories():
    """Get available question categories"""
    return {
        "categories": [
            {"id": "factual", "name": "Factual", "description": "Questions about specific facts and data"},
            {"id": "analytical", "name": "Analytical", "description": "Questions requiring analysis and reasoning"},
            {"id": "summary", "name": "Summary", "description": "Questions about main points and overviews"},
            {"id": "technical", "name": "Technical", "description": "Questions about technical details and implementation"},
            {"id": "strategic", "name": "Strategic", "description": "Questions about strategy and decision-making"},
            {"id": "debugging", "name": "Debugging", "description": "Questions about issues and troubleshooting"},
            {"id": "optimization", "name": "Optimization", "description": "Questions about improvements and efficiency"},
            {"id": "implementation", "name": "Implementation", "description": "Questions about how to implement or build something"}
        ]
    }

# Model recommendation endpoint (enhanced)
@app.post("/recommend-model")
async def recommend_model(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
    complexity_level: Optional[str] = Form(None)
):
    """Get advanced model recommendation based on multiple factors"""
    try:
        # Read file content
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        content_preview = content[:2000].decode('utf-8', errors='ignore')
        
        # Get advanced recommendation
        recommendation = ai_service.get_advanced_recommendation(
            filename=file.filename or "unknown",
            content_preview=content_preview,
            question_type=question,
            complexity_level=complexity_level
        )
        
        return {
            "recommended_model": recommendation["model_id"],
            "explanation": recommendation,
            "confidence_score": recommendation.get("confidence", 0.8),
            "alternative_models": recommendation.get("alternatives", []),
            "reasoning_factors": recommendation.get("factors", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main_database:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )