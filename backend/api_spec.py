"""
OpenAPI specification for the Advanced Document Intelligence Platform
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def create_openapi_spec(app: FastAPI) -> dict:
    """Create comprehensive OpenAPI specification"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Advanced Document Intelligence Platform API",
        version="2.0.0",
        description="""
# Advanced Document Intelligence Platform API

A comprehensive API for document processing, analysis, and intelligent search with multi-model AI support.

## Features

- **Multi-Format Support**: Process text, code, images, PDFs, and more
- **AI-Powered Analysis**: Multiple AI models for optimal document understanding
- **Advanced Search**: Hybrid search with filtering and analytics
- **OCR Integration**: Extract text from images and scanned documents
- **Question Generation**: Auto-generate contextual questions
- **Document Management**: Full CRUD operations with libraries and organization
- **Real-time Processing**: Async document processing with status tracking

## Authentication

All API endpoints require authentication via JWT tokens:

```
Authorization: Bearer <your-jwt-token>
```

Get your token by registering or logging in through the `/auth/register` or `/auth/login` endpoints.

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- **Free Tier**: 100 requests per hour
- **Premium Tier**: 1000 requests per hour
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Webhooks

Configure webhooks to receive real-time notifications about document processing events:
- Document upload completed
- Processing finished
- Analysis results available
- Error notifications

## SDKs

Official SDKs are available for:
- Python
- JavaScript/Node.js
- Java
- C#
- Go

## Support

- **Documentation**: [https://docs.docai.example.com](https://docs.docai.example.com)
- **Support**: support@docai.example.com
- **Status Page**: [https://status.docai.example.com](https://status.docai.example.com)
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.docai.example.com", "description": "Production server"},
            {"url": "https://staging-api.docai.example.com", "description": "Staging server"}
        ],
        tags=[
            {
                "name": "Authentication",
                "description": "User authentication and authorization endpoints"
            },
            {
                "name": "Documents",
                "description": "Document upload, management, and processing operations"
            },
            {
                "name": "Search",
                "description": "Advanced search and document discovery endpoints"
            },
            {
                "name": "Questions",
                "description": "AI-powered question generation and management"
            },
            {
                "name": "Libraries",
                "description": "Document organization and library management"
            },
            {
                "name": "Analytics",
                "description": "Usage analytics and insights endpoints"
            },
            {
                "name": "Models",
                "description": "AI model information and recommendations"
            },
            {
                "name": "Webhooks",
                "description": "Webhook configuration and management"
            },
            {
                "name": "System",
                "description": "System health, status, and configuration endpoints"
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login or /auth/register"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for server-to-server authentication"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]
    
    # Add response schemas
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "detail": {"type": "string", "description": "Error description"},
                "error_code": {"type": "string", "description": "Specific error code"},
                "timestamp": {"type": "string", "format": "date-time"},
                "request_id": {"type": "string", "description": "Unique request identifier"}
            },
            "required": ["detail"]
        },
        "RateLimitResponse": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "limit": {"type": "integer"},
                "remaining": {"type": "integer"},
                "reset_time": {"type": "string", "format": "date-time"}
            }
        },
        "DocumentMetadata": {
            "type": "object",
            "properties": {
                "format": {"type": "string"},
                "file_size": {"type": "integer"},
                "word_count": {"type": "integer"},
                "complexity_score": {"type": "number"},
                "ocr_confidence": {"type": "number"},
                "programming_languages": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "entities": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "ProcessingStatus": {
            "type": "string",
            "enum": ["pending", "processing", "completed", "failed"],
            "description": "Document processing status"
        }
    })
    
    # Add example responses
    openapi_schema["components"]["examples"] = {
        "DocumentUploadSuccess": {
            "summary": "Successful document upload",
            "value": {
                "message": "Document uploaded successfully",
                "document": {
                    "id": "doc_123456789",
                    "filename": "research_paper.pdf",
                    "content_type": "application/pdf",
                    "document_category": "research",
                    "file_size": 2048576,
                    "created_at": "2024-01-15T10:30:00Z",
                    "processing_status": "completed"
                }
            }
        },
        "SearchResults": {
            "summary": "Search results example",
            "value": {
                "query": "machine learning",
                "search_type": "hybrid",
                "results": [
                    {
                        "document_id": "doc_123456789",
                        "filename": "ml_research.pdf",
                        "score": 0.95,
                        "highlights": {
                            "content": ["<mark>machine learning</mark> algorithms..."]
                        }
                    }
                ],
                "total": 42,
                "page": 1,
                "page_size": 20
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def get_api_info():
    """Get API information for documentation"""
    return {
        "title": "Advanced Document Intelligence Platform API",
        "version": "2.0.0",
        "description": "Comprehensive API for document processing and AI-powered analysis",
        "contact": {
            "name": "API Support",
            "email": "support@docai.example.com",
            "url": "https://docs.docai.example.com"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "terms_of_service": "https://docai.example.com/terms"
    }