"""
Enhanced Elasticsearch service for advanced document search and indexing
"""

from typing import Dict, List, Any, Optional, Tuple
import os
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

@dataclass
class SearchFilter:
    """Search filter configuration"""
    field: str
    value: Any
    operator: str = "term"  # term, range, match, wildcard, exists

@dataclass
class SearchResult:
    """Search result item"""
    document_id: str
    title: str
    content: str
    score: float
    highlights: List[str]
    metadata: Dict[str, Any]

@dataclass
class SearchResponse:
    """Complete search response"""
    results: List[SearchResult]
    total_hits: int
    max_score: float
    took_ms: int
    aggregations: Dict[str, Any]
    suggestions: List[str]

class ElasticsearchService:
    """Enhanced Elasticsearch service for document search and indexing"""
    
    def __init__(self):
        """Initialize Elasticsearch service"""
        self.es = None
        self.index_name = "documents"
        self.search_history = []  # In-memory search history for demo
        self.saved_searches = {}  # In-memory saved searches for demo
        print("⚠️  Elasticsearch not available - using enhanced mock implementation")
    
    def index_document(self, document_data: Dict[str, Any]) -> bool:
        """Index a document for search"""
        try:
            # In a real implementation, this would index to Elasticsearch
            print(f"📝 Indexing document: {document_data.get('filename', 'unknown')}")
            return True
        except Exception as e:
            print(f"❌ Failed to index document: {str(e)}")
            return False
    
    def search_documents(self, user_id: str, query: str, 
                        filters: Optional[List[SearchFilter]] = None,
                        size: int = 20, from_: int = 0) -> SearchResponse:
        """Enhanced document search with filtering"""
        
        # Record search in history
        self._record_search(user_id, query, filters)
        
        # Mock search results for demonstration
        mock_results = self._generate_mock_search_results(query, filters, size)
        
        return SearchResponse(
            results=mock_results,
            total_hits=len(mock_results),
            max_score=1.0 if mock_results else 0.0,
            took_ms=45,
            aggregations=self._generate_aggregations(),
            suggestions=self._generate_suggestions(query)
        )
    
    def advanced_search(self, user_id: str, query: str, search_type: str = "standard",
                       filters: Optional[List[SearchFilter]] = None,
                       size: int = 20, from_: int = 0,
                       highlight: bool = True,
                       sort_by: str = "relevance") -> SearchResponse:
        """Advanced search with multiple strategies and options"""
        
        # Parse advanced search operators
        parsed_query = self._parse_advanced_query(query)
        
        # Apply search type specific logic
        if search_type == "fuzzy":
            # Fuzzy search for typos and variations
            results = self._fuzzy_search(user_id, parsed_query, filters, size, from_)
        elif search_type == "semantic":
            # Semantic search using embeddings
            results = self._semantic_search(user_id, parsed_query, filters, size, from_)
        elif search_type == "code":
            # Code-specific search with syntax awareness
            results = self._code_search(user_id, parsed_query, filters, size, from_)
        else:
            # Standard search
            results = self.search_documents(user_id, query, filters, size, from_)
        
        # Apply sorting
        if sort_by != "relevance":
            results.results = self._sort_results(results.results, sort_by)
        
        return results
    
    def get_search_suggestions(self, user_id: str, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query"""
        suggestions = []
        
        # Add suggestions based on search history
        for search in self.search_history:
            if search["user_id"] == user_id and partial_query.lower() in search["query"].lower():
                suggestions.append(search["query"])
        
        # Add common search patterns
        common_patterns = [
            f"{partial_query} functions",
            f"{partial_query} documentation",
            f"{partial_query} examples",
            f"{partial_query} tutorial",
            f"{partial_query} API",
            f"how to {partial_query}",
            f"{partial_query} best practices"
        ]
        
        suggestions.extend(common_patterns)
        
        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:limit]
    
    def save_search(self, user_id: str, name: str, query: str, 
                   filters: Optional[List[SearchFilter]] = None) -> bool:
        """Save a search query for later use"""
        try:
            search_id = f"{user_id}_{name}"
            self.saved_searches[search_id] = {
                "name": name,
                "query": query,
                "filters": [f.__dict__ for f in filters] if filters else [],
                "created_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            return True
        except Exception as e:
            print(f"❌ Failed to save search: {str(e)}")
            return False
    
    def get_saved_searches(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's saved searches"""
        user_searches = []
        for search_id, search_data in self.saved_searches.items():
            if search_data["user_id"] == user_id:
                user_searches.append(search_data)
        return user_searches
    
    def get_search_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's search history"""
        user_history = [
            search for search in self.search_history 
            if search["user_id"] == user_id
        ]
        return user_history[-limit:]  # Return most recent searches
    
    def get_search_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get search analytics for user"""
        user_searches = [s for s in self.search_history if s["user_id"] == user_id]
        
        # Calculate analytics
        total_searches = len(user_searches)
        recent_searches = [s for s in user_searches if 
                          datetime.fromisoformat(s["timestamp"]) > datetime.utcnow() - timedelta(days=7)]
        
        # Popular queries
        query_counts = {}
        for search in user_searches:
            query = search["query"].lower()
            query_counts[query] = query_counts.get(query, 0) + 1
        
        popular_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_searches": total_searches,
            "searches_this_week": len(recent_searches),
            "popular_queries": [{"query": q, "count": c} for q, c in popular_queries],
            "search_trends": self._calculate_search_trends(user_searches),
            "average_results_per_search": 8.5,  # Mock data
            "most_active_day": "Tuesday"  # Mock data
        }
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from search index"""
        try:
            print(f"🗑️  Deleting document from index: {document_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete document: {str(e)}")
            return False
    
    def get_similar_documents(self, document_id: str, user_id: str, limit: int = 5) -> List[SearchResult]:
        """Find documents similar to the given document"""
        # Mock similar documents
        similar_docs = []
        for i in range(min(limit, 3)):
            similar_docs.append(SearchResult(
                document_id=f"doc_{i+1}",
                title=f"Similar Document {i+1}",
                content=f"This document is similar to {document_id}...",
                score=0.8 - (i * 0.1),
                highlights=[f"Similar content found in document {i+1}"],
                metadata={"similarity_score": 0.8 - (i * 0.1)}
            ))
        
        return similar_docs
    
    def bulk_reindex(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk reindex multiple documents"""
        try:
            indexed_count = 0
            failed_count = 0
            
            for doc in documents:
                if self.index_document(doc):
                    indexed_count += 1
                else:
                    failed_count += 1
            
            return {
                "indexed": indexed_count,
                "failed": failed_count,
                "success": failed_count == 0,
                "total": len(documents)
            }
        except Exception as e:
            return {
                "indexed": 0,
                "failed": len(documents),
                "success": False,
                "error": str(e)
            }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get search index statistics"""
        return {
            "status": "mock_active",
            "document_count": 150,  # Mock data
            "index_size": "2.5MB",  # Mock data
            "search_requests_today": 45,
            "average_response_time": "45ms",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    # Private helper methods
    
    def _record_search(self, user_id: str, query: str, filters: Optional[List[SearchFilter]]):
        """Record search in history"""
        self.search_history.append({
            "user_id": user_id,
            "query": query,
            "filters": [f.__dict__ for f in filters] if filters else [],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 1000 searches
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-1000:]
    
    def _generate_mock_search_results(self, query: str, filters: Optional[List[SearchFilter]], 
                                    size: int) -> List[SearchResult]:
        """Generate mock search results for demonstration"""
        results = []
        
        # Generate results based on query
        result_count = min(size, 8)  # Mock: return up to 8 results
        
        for i in range(result_count):
            results.append(SearchResult(
                document_id=f"doc_{i+1}",
                title=f"Document {i+1} - {query.title()} Related",
                content=f"This document contains information about {query}. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                score=1.0 - (i * 0.1),
                highlights=[f"<mark>{query}</mark> appears in this document"],
                metadata={
                    "document_type": "text",
                    "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "file_size": f"{(i+1)*100}KB"
                }
            ))
        
        return results
    
    def _generate_aggregations(self) -> Dict[str, Any]:
        """Generate search result aggregations"""
        return {
            "document_types": {
                "text": 45,
                "code": 32,
                "pdf": 18,
                "markdown": 25
            },
            "date_ranges": {
                "last_week": 15,
                "last_month": 35,
                "last_year": 70
            },
            "file_sizes": {
                "small": 40,
                "medium": 50,
                "large": 30
            }
        }
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions"""
        base_suggestions = [
            f"{query} tutorial",
            f"{query} examples",
            f"{query} documentation",
            f"how to {query}",
            f"{query} best practices"
        ]
        return base_suggestions[:3]
    
    def _parse_advanced_query(self, query: str) -> Dict[str, Any]:
        """Parse advanced search operators"""
        parsed = {
            "terms": [],
            "phrases": [],
            "exclude": [],
            "wildcards": [],
            "fields": {}
        }
        
        # Extract quoted phrases
        phrases = re.findall(r'"([^"]*)"', query)
        parsed["phrases"] = phrases
        
        # Remove phrases from query for further processing
        query_without_phrases = re.sub(r'"[^"]*"', '', query)
        
        # Extract field searches (field:value)
        field_searches = re.findall(r'(\w+):(\w+)', query_without_phrases)
        for field, value in field_searches:
            parsed["fields"][field] = value
        
        # Extract exclusions (-term)
        exclusions = re.findall(r'-(\w+)', query_without_phrases)
        parsed["exclude"] = exclusions
        
        # Extract wildcards (*term or term*)
        wildcards = re.findall(r'\*\w+|\w+\*', query_without_phrases)
        parsed["wildcards"] = wildcards
        
        # Remaining terms
        remaining_query = re.sub(r'(\w+):(\w+)|-(\w+)|\*\w+|\w+\*', '', query_without_phrases)
        terms = [term.strip() for term in remaining_query.split() if term.strip()]
        parsed["terms"] = terms
        
        return parsed
    
    def _fuzzy_search(self, user_id: str, parsed_query: Dict[str, Any], 
                     filters: Optional[List[SearchFilter]], size: int, from_: int) -> SearchResponse:
        """Perform fuzzy search"""
        # Mock fuzzy search implementation
        return self.search_documents(user_id, " ".join(parsed_query["terms"]), filters, size, from_)
    
    def _semantic_search(self, user_id: str, parsed_query: Dict[str, Any], 
                        filters: Optional[List[SearchFilter]], size: int, from_: int) -> SearchResponse:
        """Perform semantic search using embeddings"""
        # Mock semantic search implementation
        return self.search_documents(user_id, " ".join(parsed_query["terms"]), filters, size, from_)
    
    def _code_search(self, user_id: str, parsed_query: Dict[str, Any], 
                    filters: Optional[List[SearchFilter]], size: int, from_: int) -> SearchResponse:
        """Perform code-specific search"""
        # Mock code search implementation
        return self.search_documents(user_id, " ".join(parsed_query["terms"]), filters, size, from_)
    
    def _sort_results(self, results: List[SearchResult], sort_by: str) -> List[SearchResult]:
        """Sort search results"""
        if sort_by == "date":
            return sorted(results, key=lambda x: x.metadata.get("created_at", ""), reverse=True)
        elif sort_by == "title":
            return sorted(results, key=lambda x: x.title)
        elif sort_by == "size":
            return sorted(results, key=lambda x: x.metadata.get("file_size", "0"), reverse=True)
        else:
            return results  # Keep relevance order
    
    def _calculate_search_trends(self, searches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate search trends over time"""
        # Mock trend calculation
        return {
            "daily_searches": [5, 8, 12, 6, 9, 15, 11],
            "trending_terms": ["python", "api", "documentation", "tutorial"],
            "peak_hours": [9, 14, 16]
        }

# Global Elasticsearch service instance
elasticsearch_service = ElasticsearchService()