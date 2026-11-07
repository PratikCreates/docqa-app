"""
OpenAPI Specification Generator for Advanced Document Intelligence Platform
Generates comprehensive API documentation with authentication, rate limiting, and examples
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class OpenAPISpecGenerator:
    """Generates OpenAPI 3.0 specification for the platform"""
    
    def __init__(self):
        """Initialize the OpenAPI spec generator"""
        self.spec_version = "3.0.3"
        self.api_version = "2.0.0"
        self.base_spec = self._create_base_spec()
    
    def generate_complete_spec(self) -> Dict[str, Any]:
        """Generate the complete OpenAPI specification"""
        spec = self.base_spec.copy()
        
        # Add all endpoint paths
        spec["paths"] = {
            **self._get_health_endpoints(),
            **self._get_auth_endpoints(),
            **self._get_document_endpoints(),
            **self._get_search_endpoints(),
            **self._get_comparison_endpoints(),
            **self._get_analysis_endpoints(),
            **self._get_ai_endpoints()
        }
        
        # Add components (schemas, security schemes, etc.)
        spec["components"] = self._get_components()
        
        return spec
    
    def _create_base_spec(self) -> Dict[str, Any]:
        """Create the base OpenAPI specification structure"""
        return {
            "openapi": self.spec_version,
            "info": {
                "title": "Advanced Document Intelligence Platform API",
                "description": """
# Advanced Document Intelligence Platform API

A comprehensive API for document analysis, search, comparison, and intelligence extraction.

## Features

- **Multi-format Document Processing**: Support for text, code, markdown, and more
- **AI-Powered Analysis**: Multiple AI models for optimal document understanding
- **Advanced Search**: Full-text search with filtering and correlation analysis
- **Document Comparison**: Side-by-side comparison with similarity detection
- **Cross-Document Analysis**: Relationship mapping and trend analysis
- **Real-time Processing**: Fast document processing and analysis

## Authentication

All API endpoints require authentication using API keys or JWT tokens.
Include your API key in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- **Free Tier**: 100 requests per hour
- **Pro Tier**: 1,000 requests per hour  
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid document format",
    "details": {
      "field": "file_type",
      "expected": ["txt", "pdf", "docx"],
      "received": "xyz"
    }
  }
}
```

## Webhooks

Configure webhooks to receive real-time notifications about document processing:

1. Register webhook endpoints via `/webhooks/register`
2. Verify webhook signatures for security
3. Handle retry logic for failed deliveries

## SDKs

Official SDKs are available for popular programming languages:
- **Python**: `pip install docai-python`
- **JavaScript**: `npm install docai-js`
- **Java**: Maven/Gradle integration available
- **Go**: `go get github.com/docai/go-sdk`
                """,
                "version": self.api_version,
                "contact": {
                    "name": "API Support",
                    "email": "api-support@docai.com",
                    "url": "https://docs.docai.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                },
                "termsOfService": "https://docai.com/terms"
            },
            "servers": [
                {
                    "url": "https://api.docai.com/v2",
                    "description": "Production server"
                },
                {
                    "url": "https://staging-api.docai.com/v2", 
                    "description": "Staging server"
                },
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                }
            ],
            "security": [
                {"ApiKeyAuth": []},
                {"BearerAuth": []}
            ],
            "tags": [
                {
                    "name": "Health",
                    "description": "System health and status endpoints"
                },
                {
                    "name": "Authentication", 
                    "description": "User authentication and authorization"
                },
                {
                    "name": "Documents",
                    "description": "Document upload, processing, and management"
                },
                {
                    "name": "Search",
                    "description": "Advanced search and discovery"
                },
                {
                    "name": "Comparison",
                    "description": "Document comparison and similarity analysis"
                },
                {
                    "name": "Analysis",
                    "description": "Cross-document analysis and relationship mapping"
                },
                {
                    "name": "AI Models",
                    "description": "AI model management and processing"
                },
                {
                    "name": "Webhooks",
                    "description": "Webhook registration and management"
                }
            ]
        }
    
    def _get_health_endpoints(self) -> Dict[str, Any]:
        """Get health check endpoints"""
        return {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Health check",
                    "description": "Check the health status of the API and its dependencies",
                    "operationId": "getHealth",
                    "responses": {
                        "200": {
                            "description": "System is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"},
                                    "example": {
                                        "status": "healthy",
                                        "timestamp": "2024-01-15T10:30:00Z",
                                        "version": "2.0.0",
                                        "database": "postgresql",
                                        "services": {
                                            "api": "operational",
                                            "ai_models": "operational",
                                            "search": "operational"
                                        }
                                    }
                                }
                            }
                        },
                        "503": {
                            "description": "System is unhealthy",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_auth_endpoints(self) -> Dict[str, Any]:
        """Get authentication endpoints"""
        return {
            "/auth/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Register new user",
                    "description": "Create a new user account",
                    "operationId": "registerUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserRegistration"},
                                "example": {
                                    "email": "user@example.com",
                                    "name": "John Doe",
                                    "password": "securePassword123"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User registered successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuthResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid registration data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "User login",
                    "description": "Authenticate user and return access token",
                    "operationId": "loginUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserLogin"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuthResponse"}
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid credentials",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_document_endpoints(self) -> Dict[str, Any]:
        """Get document management endpoints"""
        return {
            "/documents/upload": {
                "post": {
                    "tags": ["Documents"],
                    "summary": "Upload document",
                    "description": "Upload and process a document for analysis",
                    "operationId": "uploadDocument",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary",
                                            "description": "Document file to upload"
                                        },
                                        "title": {
                                            "type": "string",
                                            "description": "Optional document title"
                                        },
                                        "tags": {
                                            "type": "string",
                                            "description": "Comma-separated tags"
                                        }
                                    },
                                    "required": ["file"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Document uploaded successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/DocumentResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid file format or size",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/documents": {
                "get": {
                    "tags": ["Documents"],
                    "summary": "List documents",
                    "description": "Get a list of user's documents with pagination",
                    "operationId": "listDocuments",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "description": "Page number",
                            "schema": {"type": "integer", "default": 1}
                        },
                        {
                            "name": "limit",
                            "in": "query", 
                            "description": "Items per page",
                            "schema": {"type": "integer", "default": 20, "maximum": 100}
                        },
                        {
                            "name": "tags",
                            "in": "query",
                            "description": "Filter by tags",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Documents retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/DocumentListResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/ask": {
                "post": {
                    "tags": ["Documents"],
                    "summary": "Ask question about document",
                    "description": "Ask a question about an uploaded document using AI",
                    "operationId": "askQuestion",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary"
                                        },
                                        "question": {
                                            "type": "string",
                                            "description": "Question to ask about the document"
                                        },
                                        "model": {
                                            "type": "string",
                                            "description": "AI model to use",
                                            "enum": ["meta-llama", "deepseek-r1", "qwen3-coder"]
                                        }
                                    },
                                    "required": ["file", "question"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Question answered successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/QuestionResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_search_endpoints(self) -> Dict[str, Any]:
        """Get search endpoints"""
        return {
            "/search": {
                "get": {
                    "tags": ["Search"],
                    "summary": "Basic document search",
                    "description": "Search documents with basic filtering",
                    "operationId": "searchDocuments",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "description": "Search query",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "document_type",
                            "in": "query",
                            "description": "Filter by document type",
                            "schema": {"type": "string", "enum": ["text", "code", "pdf", "markdown"]}
                        },
                        {
                            "name": "date_from",
                            "in": "query",
                            "description": "Filter by creation date (from)",
                            "schema": {"type": "string", "format": "date"}
                        },
                        {
                            "name": "size",
                            "in": "query",
                            "description": "Number of results",
                            "schema": {"type": "integer", "default": 20, "maximum": 100}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Search completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SearchResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/search/advanced": {
                "get": {
                    "tags": ["Search"],
                    "summary": "Advanced document search",
                    "description": "Advanced search with multiple strategies and options",
                    "operationId": "advancedSearch",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "description": "Search query",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "search_type",
                            "in": "query",
                            "description": "Search strategy",
                            "schema": {"type": "string", "enum": ["standard", "fuzzy", "semantic", "code"], "default": "standard"}
                        },
                        {
                            "name": "sort_by",
                            "in": "query",
                            "description": "Sort results by",
                            "schema": {"type": "string", "enum": ["relevance", "date", "title", "size"], "default": "relevance"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Advanced search completed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AdvancedSearchResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_comparison_endpoints(self) -> Dict[str, Any]:
        """Get document comparison endpoints"""
        return {
            "/documents/compare": {
                "post": {
                    "tags": ["Comparison"],
                    "summary": "Compare two documents",
                    "description": "Perform side-by-side comparison of two documents",
                    "operationId": "compareDocuments",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "document1_id": {"type": "string"},
                                        "document2_id": {"type": "string"},
                                        "comparison_type": {
                                            "type": "string",
                                            "enum": ["comprehensive", "content", "structure", "semantic"],
                                            "default": "comprehensive"
                                        }
                                    },
                                    "required": ["document1_id", "document2_id"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Comparison completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ComparisonResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/documents/batch-compare": {
                "post": {
                    "tags": ["Comparison"],
                    "summary": "Batch compare documents",
                    "description": "Compare multiple documents simultaneously",
                    "operationId": "batchCompareDocuments",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "document_ids": {
                                            "type": "string",
                                            "description": "Comma-separated document IDs"
                                        },
                                        "comparison_mode": {
                                            "type": "string",
                                            "enum": ["all_pairs", "clustering", "outlier_detection"],
                                            "default": "all_pairs"
                                        }
                                    },
                                    "required": ["document_ids"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Batch comparison completed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/BatchComparisonResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_analysis_endpoints(self) -> Dict[str, Any]:
        """Get cross-document analysis endpoints"""
        return {
            "/documents/analyze-relationships": {
                "post": {
                    "tags": ["Analysis"],
                    "summary": "Analyze document relationships",
                    "description": "Analyze relationships between a collection of documents",
                    "operationId": "analyzeRelationships",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "document_ids": {
                                            "type": "string",
                                            "description": "Comma-separated document IDs"
                                        },
                                        "relationship_types": {
                                            "type": "string",
                                            "description": "Types of relationships to analyze",
                                            "default": "all"
                                        }
                                    },
                                    "required": ["document_ids"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Relationship analysis completed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RelationshipAnalysisResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/documents/create-clusters": {
                "post": {
                    "tags": ["Analysis"],
                    "summary": "Create document clusters",
                    "description": "Create clusters of related documents",
                    "operationId": "createClusters",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "document_ids": {"type": "string"},
                                        "clustering_method": {
                                            "type": "string",
                                            "enum": ["topic", "temporal", "author", "similarity"],
                                            "default": "topic"
                                        },
                                        "max_clusters": {
                                            "type": "integer",
                                            "default": 10,
                                            "maximum": 50
                                        }
                                    },
                                    "required": ["document_ids"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Clustering completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ClusteringResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_ai_endpoints(self) -> Dict[str, Any]:
        """Get AI model endpoints"""
        return {
            "/models": {
                "get": {
                    "tags": ["AI Models"],
                    "summary": "List available AI models",
                    "description": "Get list of available AI models and their capabilities",
                    "operationId": "listModels",
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Models retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ModelsResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/generate-questions": {
                "post": {
                    "tags": ["AI Models"],
                    "summary": "Generate questions from document",
                    "description": "Auto-generate relevant questions based on document content",
                    "operationId": "generateQuestions",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"},
                                        "max_questions": {
                                            "type": "integer",
                                            "default": 10,
                                            "maximum": 20
                                        },
                                        "document_category": {
                                            "type": "string",
                                            "enum": ["general", "code", "research", "documentation"],
                                            "default": "general"
                                        }
                                    },
                                    "required": ["file"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Questions generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/QuestionGenerationResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_components(self) -> Dict[str, Any]:
        """Get OpenAPI components (schemas, security schemes, etc.)"""
        return {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for authentication"
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token for authentication"
                }
            },
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "version": {"type": "string"},
                        "database": {"type": "string"},
                        "services": {
                            "type": "object",
                            "additionalProperties": {"type": "string"}
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "message": {"type": "string"},
                                "details": {"type": "object"}
                            }
                        }
                    }
                },
                "UserRegistration": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "name": {"type": "string", "minLength": 2, "maxLength": 100},
                        "password": {"type": "string", "minLength": 8}
                    },
                    "required": ["email", "name", "password"]
                },
                "UserLogin": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string"}
                    },
                    "required": ["email", "password"]
                },
                "AuthResponse": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "token_type": {"type": "string", "default": "bearer"},
                        "expires_in": {"type": "integer"},
                        "user": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "email": {"type": "string"},
                                "name": {"type": "string"}
                            }
                        }
                    }
                },
                "DocumentResponse": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "filename": {"type": "string"},
                        "content_type": {"type": "string"},
                        "size": {"type": "integer"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "processing_status": {"type": "string", "enum": ["pending", "processing", "completed", "failed"]}
                    }
                },
                "DocumentListResponse": {
                    "type": "object",
                    "properties": {
                        "documents": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/DocumentResponse"}
                        },
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "page": {"type": "integer"},
                                "limit": {"type": "integer"},
                                "total": {"type": "integer"},
                                "pages": {"type": "integer"}
                            }
                        }
                    }
                },
                "QuestionResponse": {
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "model_used": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "processing_time": {"type": "string"},
                        "extracted_text": {"type": "string"}
                    }
                },
                "SearchResponse": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "total_hits": {"type": "integer"},
                        "took_ms": {"type": "integer"},
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "document_id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "content_preview": {"type": "string"},
                                    "score": {"type": "number"},
                                    "highlights": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "aggregations": {"type": "object"},
                        "suggestions": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "AdvancedSearchResponse": {
                    "allOf": [
                        {"$ref": "#/components/schemas/SearchResponse"},
                        {
                            "type": "object",
                            "properties": {
                                "search_type": {"type": "string"},
                                "sort_by": {"type": "string"},
                                "search_info": {"type": "object"}
                            }
                        }
                    ]
                },
                "ComparisonResponse": {
                    "type": "object",
                    "properties": {
                        "comparison_id": {"type": "string"},
                        "similarity_scores": {
                            "type": "object",
                            "properties": {
                                "overall": {"type": "number"},
                                "content": {"type": "number"},
                                "structure": {"type": "number"},
                                "semantic": {"type": "number"}
                            }
                        },
                        "differences": {"type": "array", "items": {"type": "object"}},
                        "common_sections": {"type": "array", "items": {"type": "object"}},
                        "recommendations": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "BatchComparisonResponse": {
                    "type": "object",
                    "properties": {
                        "batch_comparison_id": {"type": "string"},
                        "summary": {
                            "type": "object",
                            "properties": {
                                "total_documents": {"type": "integer"},
                                "comparisons_performed": {"type": "integer"},
                                "clusters_found": {"type": "integer"}
                            }
                        },
                        "similarity_matrix": {"type": "object"},
                        "clusters": {"type": "array", "items": {"type": "object"}}
                    }
                },
                "RelationshipAnalysisResponse": {
                    "type": "object",
                    "properties": {
                        "analysis_id": {"type": "string"},
                        "relationships_found": {"type": "integer"},
                        "relationships": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source_document": {"type": "string"},
                                    "target_document": {"type": "string"},
                                    "relationship_type": {"type": "string"},
                                    "strength": {"type": "number"},
                                    "evidence": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        }
                    }
                },
                "ClusteringResponse": {
                    "type": "object",
                    "properties": {
                        "clustering_id": {"type": "string"},
                        "clusters_created": {"type": "integer"},
                        "clusters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "cluster_id": {"type": "string"},
                                    "cluster_name": {"type": "string"},
                                    "document_count": {"type": "integer"},
                                    "coherence_score": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "ModelsResponse": {
                    "type": "object",
                    "properties": {
                        "available_models": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "capabilities": {"type": "array", "items": {"type": "string"}},
                                    "best_for": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "default_model": {"type": "string"}
                    }
                },
                "QuestionGenerationResponse": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "total_questions": {"type": "integer"},
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {"type": "string"},
                                    "category": {"type": "string"},
                                    "confidence": {"type": "number"},
                                    "importance": {"type": "number"}
                                }
                            }
                        },
                        "categorized_questions": {"type": "object"}
                    }
                }
            }
        }
    
    def save_spec_to_file(self, filename: str = "openapi.json"):
        """Save the OpenAPI specification to a JSON file"""
        spec = self.generate_complete_spec()
        with open(filename, 'w') as f:
            json.dump(spec, f, indent=2)
        print(f"OpenAPI specification saved to {filename}")
    
    def get_spec_yaml(self) -> str:
        """Get the OpenAPI specification in YAML format"""
        import yaml
        spec = self.generate_complete_spec()
        return yaml.dump(spec, default_flow_style=False)

# Global OpenAPI spec generator instance
openapi_generator = OpenAPISpecGenerator()