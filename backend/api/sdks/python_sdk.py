"""
Python SDK for Advanced Document Intelligence Platform API
Official Python client library for easy integration
"""

import requests
import json
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
import os
from dataclasses import dataclass
from enum import Enum

class SearchType(Enum):
    """Search types"""
    STANDARD = "standard"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    CODE = "code"

class ComparisonType(Enum):
    """Document comparison types"""
    COMPREHENSIVE = "comprehensive"
    CONTENT = "content"
    STRUCTURE = "structure"
    SEMANTIC = "semantic"

class ClusteringMethod(Enum):
    """Document clustering methods"""
    TOPIC = "topic"
    TEMPORAL = "temporal"
    AUTHOR = "author"
    SIMILARITY = "similarity"

@dataclass
class APIResponse:
    """Standard API response wrapper"""
    success: bool
    data: Dict[str, Any]
    status_code: int
    headers: Dict[str, str]
    error: Optional[str] = None

class DocumentAIClient:
    """
    Official Python client for the Advanced Document Intelligence Platform API
    
    Example usage:
        client = DocumentAIClient(api_key="your_api_key")
        
        # Upload and analyze document
        with open("document.pdf", "rb") as f:
            result = client.upload_document(f, title="My Document")
        
        # Ask questions about documents
        answer = client.ask_question("document.txt", "What is this document about?")
        
        # Search documents
        results = client.search("python programming", document_type="code")
    """
    
    def __init__(self, api_key: str = None, base_url: str = "http://localhost:8000"):
        """
        Initialize the DocumentAI client
        
        Args:
            api_key: Your API key (can also be set via DOCAI_API_KEY env var)
            base_url: API base URL (default: http://localhost:8000)
        """
        self.api_key = api_key or os.getenv("DOCAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set DOCAI_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "User-Agent": "DocumentAI-Python-SDK/1.0.0"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {"message": response.text}
            
            return APIResponse(
                success=response.status_code < 400,
                data=data,
                status_code=response.status_code,
                headers=dict(response.headers),
                error=data.get("error", {}).get("message") if response.status_code >= 400 else None
            )
            
        except requests.exceptions.RequestException as e:
            return APIResponse(
                success=False,
                data={},
                status_code=0,
                headers={},
                error=str(e)
            )
    
    def health_check(self) -> APIResponse:
        """Check API health status"""
        return self._make_request("GET", "/health")
    
    def list_models(self) -> APIResponse:
        """Get list of available AI models"""
        return self._make_request("GET", "/models")
    
    def upload_document(self, file: Union[str, BinaryIO], title: str = None, 
                       tags: List[str] = None) -> APIResponse:
        """
        Upload a document for processing
        
        Args:
            file: File path (string) or file-like object
            title: Optional document title
            tags: Optional list of tags
        """
        files = {}
        data = {}
        
        # Handle file input
        if isinstance(file, str):
            files["file"] = open(file, "rb")
        else:
            files["file"] = file
        
        # Add optional parameters
        if title:
            data["title"] = title
        if tags:
            data["tags"] = ",".join(tags)
        
        try:
            return self._make_request("POST", "/documents/upload", files=files, data=data)
        finally:
            # Close file if we opened it
            if isinstance(file, str) and "file" in files:
                files["file"].close()
    
    def list_documents(self, page: int = 1, limit: int = 20, tags: List[str] = None) -> APIResponse:
        """
        List user's documents
        
        Args:
            page: Page number (default: 1)
            limit: Items per page (default: 20, max: 100)
            tags: Filter by tags
        """
        params = {"page": page, "limit": limit}
        if tags:
            params["tags"] = ",".join(tags)
        
        return self._make_request("GET", "/documents", params=params)
    
    def ask_question(self, file: Union[str, BinaryIO], question: str, 
                    model: str = None) -> APIResponse:
        """
        Ask a question about a document
        
        Args:
            file: File path (string) or file-like object
            question: Question to ask about the document
            model: AI model to use (optional)
        """
        files = {}
        data = {"question": question}
        
        # Handle file input
        if isinstance(file, str):
            files["file"] = open(file, "rb")
        else:
            files["file"] = file
        
        if model:
            data["model"] = model
        
        try:
            return self._make_request("POST", "/ask", files=files, data=data)
        finally:
            # Close file if we opened it
            if isinstance(file, str) and "file" in files:
                files["file"].close()
    
    def generate_questions(self, file: Union[str, BinaryIO], max_questions: int = 10,
                          document_category: str = "general") -> APIResponse:
        """
        Generate questions from document content
        
        Args:
            file: File path (string) or file-like object
            max_questions: Maximum number of questions to generate
            document_category: Document category (general, code, research, documentation)
        """
        files = {}
        data = {
            "max_questions": max_questions,
            "document_category": document_category
        }
        
        # Handle file input
        if isinstance(file, str):
            files["file"] = open(file, "rb")
        else:
            files["file"] = file
        
        try:
            return self._make_request("POST", "/generate-questions", files=files, data=data)
        finally:
            # Close file if we opened it
            if isinstance(file, str) and "file" in files:
                files["file"].close()
    
    def search(self, query: str, document_type: str = None, date_from: str = None,
              date_to: str = None, file_format: str = None, tags: List[str] = None,
              size: int = 20) -> APIResponse:
        """
        Search documents
        
        Args:
            query: Search query
            document_type: Filter by document type
            date_from: Filter by creation date (from)
            date_to: Filter by creation date (to)
            file_format: Filter by file format
            tags: Filter by tags
            size: Number of results (max: 100)
        """
        params = {"q": query, "size": size}
        
        if document_type:
            params["document_type"] = document_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if file_format:
            params["file_format"] = file_format
        if tags:
            params["tags"] = ",".join(tags)
        
        return self._make_request("GET", "/search", params=params)
    
    def advanced_search(self, query: str, search_type: SearchType = SearchType.STANDARD,
                       sort_by: str = "relevance", highlight: bool = True,
                       **filters) -> APIResponse:
        """
        Perform advanced search with multiple strategies
        
        Args:
            query: Search query
            search_type: Search strategy (standard, fuzzy, semantic, code)
            sort_by: Sort results by (relevance, date, title, size)
            highlight: Enable result highlighting
            **filters: Additional filters (document_type, date_from, etc.)
        """
        params = {
            "q": query,
            "search_type": search_type.value,
            "sort_by": sort_by,
            "highlight": highlight
        }
        params.update(filters)
        
        return self._make_request("GET", "/search/advanced", params=params)
    
    def compare_documents(self, document1_id: str, document2_id: str,
                         comparison_type: ComparisonType = ComparisonType.COMPREHENSIVE) -> APIResponse:
        """
        Compare two documents
        
        Args:
            document1_id: First document ID
            document2_id: Second document ID
            comparison_type: Type of comparison to perform
        """
        data = {
            "document1_id": document1_id,
            "document2_id": document2_id,
            "comparison_type": comparison_type.value
        }
        
        return self._make_request("POST", "/documents/compare", data=data)
    
    def batch_compare_documents(self, document_ids: List[str], 
                               comparison_mode: str = "all_pairs") -> APIResponse:
        """
        Compare multiple documents simultaneously
        
        Args:
            document_ids: List of document IDs to compare
            comparison_mode: Comparison mode (all_pairs, clustering, outlier_detection)
        """
        data = {
            "document_ids": ",".join(document_ids),
            "comparison_mode": comparison_mode
        }
        
        return self._make_request("POST", "/documents/batch-compare", data=data)
    
    def find_similar_documents(self, document_id: str, limit: int = 10,
                              min_similarity: float = 0.3) -> APIResponse:
        """
        Find documents similar to the specified document
        
        Args:
            document_id: Target document ID
            limit: Maximum number of similar documents to return
            min_similarity: Minimum similarity threshold
        """
        params = {
            "limit": limit,
            "min_similarity": min_similarity
        }
        
        return self._make_request("GET", f"/documents/{document_id}/find-similar", params=params)
    
    def analyze_relationships(self, document_ids: List[str], 
                             relationship_types: str = "all") -> APIResponse:
        """
        Analyze relationships between documents
        
        Args:
            document_ids: List of document IDs to analyze
            relationship_types: Types of relationships to analyze
        """
        data = {
            "document_ids": ",".join(document_ids),
            "relationship_types": relationship_types
        }
        
        return self._make_request("POST", "/documents/analyze-relationships", data=data)
    
    def create_clusters(self, document_ids: List[str], 
                       clustering_method: ClusteringMethod = ClusteringMethod.TOPIC,
                       max_clusters: int = 10) -> APIResponse:
        """
        Create clusters of related documents
        
        Args:
            document_ids: List of document IDs to cluster
            clustering_method: Clustering method to use
            max_clusters: Maximum number of clusters to create
        """
        data = {
            "document_ids": ",".join(document_ids),
            "clustering_method": clustering_method.value,
            "max_clusters": max_clusters
        }
        
        return self._make_request("POST", "/documents/create-clusters", data=data)
    
    def perform_trend_analysis(self, document_ids: List[str], time_window: int = 30,
                              min_document_count: int = 3) -> APIResponse:
        """
        Perform trend analysis across document collections
        
        Args:
            document_ids: List of document IDs to analyze
            time_window: Time window in days
            min_document_count: Minimum documents required for a trend
        """
        data = {
            "document_ids": ",".join(document_ids),
            "time_window": time_window,
            "min_document_count": min_document_count
        }
        
        return self._make_request("POST", "/documents/trend-analysis", data=data)
    
    def cross_document_search(self, query: str, document_ids: List[str],
                             search_type: str = "comprehensive") -> APIResponse:
        """
        Perform cross-document search with correlation analysis
        
        Args:
            query: Search query
            document_ids: List of document IDs to search within
            search_type: Type of search (comprehensive, entity, topic, temporal)
        """
        data = {
            "query": query,
            "document_ids": ",".join(document_ids),
            "search_type": search_type
        }
        
        return self._make_request("POST", "/documents/cross-search", data=data)
    
    def create_network_map(self, document_ids: List[str], 
                          min_relationship_strength: float = 0.3) -> APIResponse:
        """
        Create a network map of document relationships
        
        Args:
            document_ids: List of document IDs to map
            min_relationship_strength: Minimum relationship strength threshold
        """
        data = {
            "document_ids": ",".join(document_ids),
            "min_relationship_strength": min_relationship_strength
        }
        
        return self._make_request("POST", "/documents/network-map", data=data)
    
    def get_document_influence_score(self, document_id: str, 
                                   context_document_ids: List[str] = None) -> APIResponse:
        """
        Calculate influence score for a document
        
        Args:
            document_id: Target document ID
            context_document_ids: List of context document IDs
        """
        params = {}
        if context_document_ids:
            params["context_document_ids"] = ",".join(context_document_ids)
        
        return self._make_request("GET", f"/documents/{document_id}/influence-score", params=params)

# Convenience functions for quick usage
def quick_search(query: str, api_key: str = None) -> Dict[str, Any]:
    """Quick search function for simple use cases"""
    client = DocumentAIClient(api_key=api_key)
    response = client.search(query)
    return response.data if response.success else {"error": response.error}

def quick_ask(file_path: str, question: str, api_key: str = None) -> Dict[str, Any]:
    """Quick question asking function"""
    client = DocumentAIClient(api_key=api_key)
    response = client.ask_question(file_path, question)
    return response.data if response.success else {"error": response.error}

def quick_compare(doc1_id: str, doc2_id: str, api_key: str = None) -> Dict[str, Any]:
    """Quick document comparison function"""
    client = DocumentAIClient(api_key=api_key)
    response = client.compare_documents(doc1_id, doc2_id)
    return response.data if response.success else {"error": response.error}

# Example usage
if __name__ == "__main__":
    # Example usage of the SDK
    client = DocumentAIClient(api_key="your_api_key_here")
    
    # Check API health
    health = client.health_check()
    print(f"API Health: {health.data}")
    
    # List available models
    models = client.list_models()
    print(f"Available models: {models.data}")
    
    # Search documents
    search_results = client.search("python programming")
    print(f"Search results: {search_results.data}")