"""
Elasticsearch service for document indexing and search functionality
"""

from elasticsearch import Elasticsearch
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

class ElasticsearchService:
    """Service for document indexing and search using Elasticsearch"""
    
    def __init__(self):
        # Elasticsearch configuration
        es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
        es_user = os.getenv("ELASTICSEARCH_USER", "")
        es_password = os.getenv("ELASTICSEARCH_PASSWORD", "")
        
        # Initialize Elasticsearch client
        if es_user and es_password:
            self.es = Elasticsearch(
                [{"host": es_host, "port": es_port}],
                http_auth=(es_user, es_password),
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
        else:
            self.es = Elasticsearch(
                [{"host": es_host, "port": es_port}],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
        
        self.index_name = "documents"
        
        # Test connection and create index if needed
        try:
            if self.es.ping():
                print("✅ Elasticsearch connection established")
                self._create_index_if_not_exists()
            else:
                print("❌ Elasticsearch connection failed")
                self.es = None
        except Exception as e:
            print(f"❌ Elasticsearch connection error: {str(e)}")
            self.es = None
    
    def _create_index_if_not_exists(self):
        """Create the documents index with proper mapping if it doesn't exist"""
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "document_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "filename": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "content_type": {"type": "keyword"},
                        "document_category": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "metadata": {"type": "object"},
                        "tags": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "processing_status": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "programming_languages": {"type": "keyword"},
                        "frameworks": {"type": "keyword"},
                        "complexity_score": {"type": "float"},
                        "technical_score": {"type": "integer"},
                        "conceptual_score": {"type": "integer"},
                        "ocr_confidence": {"type": "float"},
                        "ocr_engine": {"type": "keyword"},
                        "has_text": {"type": "boolean"},
                        "word_count": {"type": "integer"},
                        "line_count": {"type": "integer"},
                        "entities": {"type": "keyword"},
                        "topics": {"type": "keyword"},
                        "sentiment_score": {"type": "float"},
                        "readability_score": {"type": "float"},
                        "search_vector": {"type": "dense_vector", "dims": 384}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "code_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop", "stemmer"]
                            },
                            "content_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop", "stemmer", "synonym"]
                            },
                            "filename_analyzer": {
                                "type": "custom",
                                "tokenizer": "keyword",
                                "filter": ["lowercase"]
                            }
                        },
                        "filter": {
                            "stemmer": {
                                "type": "stemmer",
                                "language": "english"
                            },
                            "synonym": {
                                "type": "synonym",
                                "synonyms": [
                                    "js,javascript",
                                    "py,python",
                                    "ts,typescript",
                                    "cpp,c++",
                                    "md,markdown",
                                    "doc,document",
                                    "api,interface",
                                    "db,database"
                                ]
                            }
                        }
                    }
                }\n            }\n            \n            self.es.indices.create(index=self.index_name, body=mapping)\n            print(f\"✅ Created Elasticsearch index: {self.index_name}\")\n    \n    def index_document(self, document_data: Dict[str, Any]) -> bool:\n        \"\"\"Index a document in Elasticsearch\"\"\"\n        if not self.es:\n            return False\n        \n        try:\n            # Prepare document for indexing\n            doc = {\n                \"document_id\": str(document_data.get(\"id\")),\n                \"user_id\": str(document_data.get(\"user_id\")),\n                \"filename\": document_data.get(\"filename\", \"\"),\n                \"content\": document_data.get(\"extracted_text\", \"\"),\n                \"content_type\": document_data.get(\"content_type\", \"\"),\n                \"document_category\": document_data.get(\"document_category\", \"\"),\n                \"file_size\": document_data.get(\"file_size\", 0),\n                \"metadata\": document_data.get(\"metadata\", {}),\n                \"tags\": document_data.get(\"tags\", []),\n                \"created_at\": document_data.get(\"created_at\", datetime.utcnow()).isoformat(),\n                \"updated_at\": document_data.get(\"updated_at\", datetime.utcnow()).isoformat(),\n                \"processing_status\": document_data.get(\"processing_status\", \"completed\")\n            }\n            \n            # Add computed fields for better search\n            doc.update(self._extract_search_features(doc[\"content\"], doc[\"filename\"]))\n            \n            # Index the document\n            response = self.es.index(\n                index=self.index_name,\n                id=doc[\"document_id\"],\n                body=doc\n            )\n            \n            return response[\"result\"] in [\"created\", \"updated\"]\n            \n        except Exception as e:\n            print(f\"Error indexing document {document_data.get('id')}: {str(e)}\")\n            return False\n    \n    def _extract_search_features(self, content: str, filename: str) -> Dict[str, Any]:\n        \"\"\"Extract search-relevant features from document content\"\"\"\n        features = {\n            \"language\": \"unknown\",\n            \"programming_languages\": [],\n            \"frameworks\": [],\n            \"complexity_score\": 0.0,\n            \"technical_score\": 0,\n            \"conceptual_score\": 0\n        }\n        \n        if not content:\n            return features\n        \n        content_lower = content.lower()\n        \n        # Detect programming languages\n        language_patterns = {\n            \"python\": [\"def \", \"import \", \"from \", \"print(\"],\n            \"javascript\": [\"function \", \"const \", \"let \", \"console.log\"],\n            \"java\": [\"public class\", \"public static void main\", \"System.out.println\"],\n            \"cpp\": [\"#include\", \"std::\", \"int main(\"],\n            \"html\": [\"<html\", \"<div\", \"<script\"],\n            \"css\": [\"{\", \"}\", \"@media\"],\n            \"sql\": [\"SELECT \", \"FROM \", \"WHERE \", \"INSERT INTO\"]\n        }\n        \n        detected_languages = []\n        for lang, patterns in language_patterns.items():\n            if any(pattern in content_lower for pattern in patterns):\n                detected_languages.append(lang)\n        \n        features[\"programming_languages\"] = detected_languages\n        \n        # Detect frameworks\n        framework_patterns = {\n            \"react\": [\"react\", \"usestate\", \"useeffect\", \"jsx\"],\n            \"vue\": [\"vue\", \"v-if\", \"v-for\"],\n            \"angular\": [\"angular\", \"@component\", \"ngoninit\"],\n            \"django\": [\"django\", \"models.model\", \"httpresponse\"],\n            \"flask\": [\"flask\", \"@app.route\", \"render_template\"],\n            \"express\": [\"express\", \"app.get\", \"app.post\"]\n        }\n        \n        detected_frameworks = []\n        for framework, patterns in framework_patterns.items():\n            if any(pattern in content_lower for pattern in patterns):\n                detected_frameworks.append(framework)\n        \n        features[\"frameworks\"] = detected_frameworks\n        \n        # Calculate technical vs conceptual scores\n        technical_keywords = [\n            \"function\", \"class\", \"import\", \"def\", \"var\", \"const\", \"let\", \"public\", \"private\",\n            \"algorithm\", \"data structure\", \"api\", \"database\", \"server\", \"client\", \"framework\"\n        ]\n        \n        conceptual_keywords = [\n            \"analysis\", \"research\", \"study\", \"methodology\", \"conclusion\", \"abstract\",\n            \"theory\", \"concept\", \"principle\", \"approach\", \"strategy\", \"evaluation\"\n        ]\n        \n        technical_score = sum(1 for keyword in technical_keywords if keyword in content_lower)\n        conceptual_score = sum(1 for keyword in conceptual_keywords if keyword in content_lower)\n        \n        features[\"technical_score\"] = technical_score\n        features[\"conceptual_score\"] = conceptual_score\n        \n        # Calculate complexity score\n        lines = content.split('\\n')\n        nested_structures = content.count('    ') + content.count('\\t')\n        function_count = len([line for line in lines if any(pattern in line.lower() for pattern in [\"def \", \"function \", \"class \"])])\n        \n        complexity_score = (nested_structures * 0.1) + (function_count * 2) + (len(detected_languages) * 1.5)\n        features[\"complexity_score\"] = round(complexity_score, 2)\n        \n        # Determine primary language\n        if detected_languages:\n            features[\"language\"] = detected_languages[0]\n        elif filename:\n            ext = filename.split('.')[-1].lower() if '.' in filename else \"\"\n            ext_to_lang = {\n                \"py\": \"python\", \"js\": \"javascript\", \"ts\": \"typescript\",\n                \"java\": \"java\", \"cpp\": \"cpp\", \"c\": \"c\", \"html\": \"html\",\n                \"css\": \"css\", \"md\": \"markdown\", \"txt\": \"text\"\n            }\n            features[\"language\"] = ext_to_lang.get(ext, \"unknown\")\n        \n        return features\n    \n    def search_documents(self, user_id: str, query: str, filters: Optional[Dict[str, Any]] = None, \n                        size: int = 20, from_: int = 0) -> Dict[str, Any]:\n        \"\"\"Search documents with optional filters\"\"\"\n        if not self.es:\n            return {\"hits\": [], \"total\": 0}\n        \n        try:\n            # Build search query\n            search_body = {\n                \"query\": {\n                    \"bool\": {\n                        \"must\": [\n                            {\"term\": {\"user_id\": user_id}}\n                        ],\n                        \"should\": [\n                            {\"match\": {\"content\": {\"query\": query, \"boost\": 2}}},\n                            {\"match\": {\"filename\": {\"query\": query, \"boost\": 1.5}}},\n                            {\"match\": {\"metadata\": query}}\n                        ],\n                        \"minimum_should_match\": 1\n                    }\n                },\n                \"highlight\": {\n                    \"fields\": {\n                        \"content\": {\"fragment_size\": 150, \"number_of_fragments\": 3},\n                        \"filename\": {}\n                    }\n                },\n                \"size\": size,\n                \"from\": from_,\n                \"sort\": [{\"_score\": {\"order\": \"desc\"}}]\n            }\n            \n            # Apply filters\n            if filters:\n                filter_clauses = []\n                \n                if filters.get(\"document_category\"):\n                    filter_clauses.append({\"term\": {\"document_category\": filters[\"document_category\"]}})\n                \n                if filters.get(\"content_type\"):\n                    filter_clauses.append({\"term\": {\"content_type\": filters[\"content_type\"]}})\n                \n                if filters.get(\"programming_languages\"):\n                    filter_clauses.append({\"terms\": {\"programming_languages\": filters[\"programming_languages\"]}})\n                \n                if filters.get(\"date_range\"):\n                    date_filter = {\"range\": {\"created_at\": {}}}\n                    if filters[\"date_range\"].get(\"gte\"):\n                        date_filter[\"range\"][\"created_at\"][\"gte\"] = filters[\"date_range\"][\"gte\"]\n                    if filters[\"date_range\"].get(\"lte\"):\n                        date_filter[\"range\"][\"created_at\"][\"lte\"] = filters[\"date_range\"][\"lte\"]\n                    filter_clauses.append(date_filter)\n                \n                if filter_clauses:\n                    search_body[\"query\"][\"bool\"][\"filter\"] = filter_clauses\n            \n            # Execute search\n            response = self.es.search(index=self.index_name, body=search_body)\n            \n            # Process results\n            hits = []\n            for hit in response[\"hits\"][\"hits\"]:\n                result = {\n                    \"document_id\": hit[\"_source\"][\"document_id\"],\n                    \"filename\": hit[\"_source\"][\"filename\"],\n                    \"content_type\": hit[\"_source\"][\"content_type\"],\n                    \"document_category\": hit[\"_source\"][\"document_category\"],\n                    \"score\": hit[\"_score\"],\n                    \"created_at\": hit[\"_source\"][\"created_at\"],\n                    \"highlights\": hit.get(\"highlight\", {})\n                }\n                hits.append(result)\n            \n            return {\n                \"hits\": hits,\n                \"total\": response[\"hits\"][\"total\"][\"value\"],\n                \"max_score\": response[\"hits\"][\"max_score\"]\n            }\n            \n        except Exception as e:\n            print(f\"Error searching documents: {str(e)}\")\n            return {\"hits\": [], \"total\": 0}\n    \n    def get_similar_documents(self, document_id: str, user_id: str, size: int = 5) -> List[Dict[str, Any]]:\n        \"\"\"Find similar documents using More Like This query\"\"\"\n        if not self.es:\n            return []\n        \n        try:\n            search_body = {\n                \"query\": {\n                    \"bool\": {\n                        \"must\": [\n                            {\"term\": {\"user_id\": user_id}},\n                            {\n                                \"more_like_this\": {\n                                    \"fields\": [\"content\", \"filename\"],\n                                    \"like\": [\n                                        {\n                                            \"_index\": self.index_name,\n                                            \"_id\": document_id\n                                        }\n                                    ],\n                                    \"min_term_freq\": 2,\n                                    \"max_query_terms\": 12\n                                }\n                            }\n                        ]\n                    }\n                },\n                \"size\": size\n            }\n            \n            response = self.es.search(index=self.index_name, body=search_body)\n            \n            similar_docs = []\n            for hit in response[\"hits\"][\"hits\"]:\n                similar_docs.append({\n                    \"document_id\": hit[\"_source\"][\"document_id\"],\n                    \"filename\": hit[\"_source\"][\"filename\"],\n                    \"score\": hit[\"_score\"],\n                    \"document_category\": hit[\"_source\"][\"document_category\"]\n                })\n            \n            return similar_docs\n            \n        except Exception as e:\n            print(f\"Error finding similar documents: {str(e)}\")\n            return []\n    \n    def delete_document(self, document_id: str) -> bool:\n        \"\"\"Delete a document from the index\"\"\"\n        if not self.es:\n            return False\n        \n        try:\n            response = self.es.delete(index=self.index_name, id=document_id)\n            return response[\"result\"] == \"deleted\"\n        except Exception as e:\n            print(f\"Error deleting document {document_id}: {str(e)}\")\n            return False\n    \n    def get_search_suggestions(self, user_id: str, partial_query: str, size: int = 5) -> List[str]:\n        \"\"\"Get search suggestions based on partial query\"\"\"\n        if not self.es or len(partial_query) < 2:\n            return []\n        \n        try:\n            search_body = {\n                \"suggest\": {\n                    \"filename_suggest\": {\n                        \"prefix\": partial_query,\n                        \"completion\": {\n                            \"field\": \"filename.keyword\",\n                            \"size\": size,\n                            \"contexts\": {\n                                \"user_id\": [user_id]\n                            }\n                        }\n                    }\n                }\n            }\n            \n            response = self.es.search(index=self.index_name, body=search_body)\n            suggestions = []\n            \n            for suggestion in response[\"suggest\"][\"filename_suggest\"][0][\"options\"]:\n                suggestions.append(suggestion[\"text\"])\n            \n            return suggestions\n            \n        except Exception as e:\n            print(f\"Error getting search suggestions: {str(e)}\")\n            return []\n    \n    def get_index_stats(self) -> Dict[str, Any]:\n        \"\"\"Get index statistics\"\"\"\n        if not self.es:\n            return {\"status\": \"disabled\"}\n        \n        try:\n            stats = self.es.indices.stats(index=self.index_name)\n            return {\n                \"status\": \"active\",\n                \"document_count\": stats[\"indices\"][self.index_name][\"total\"][\"docs\"][\"count\"],\n                \"index_size\": stats[\"indices\"][self.index_name][\"total\"][\"store\"][\"size_in_bytes\"]\n            }\n        except Exception as e:\n            return {\"status\": \"error\", \"error\": str(e)}\n\n# Global Elasticsearch service instance\nelasticsearch_service = ElasticsearchService()"    de
f _extract_advanced_features(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract advanced features for better indexing and search"""
        features = {
            "ocr_confidence": 0.0,
            "ocr_engine": "none",
            "has_text": bool(content.strip()),
            "word_count": len(content.split()) if content else 0,
            "line_count": len(content.split('\n')) if content else 0,
            "entities": [],
            "topics": [],
            "sentiment_score": 0.0,
            "readability_score": 0.0
        }
        
        # Extract OCR-related metadata
        if metadata.get("ocr_confidence"):
            features["ocr_confidence"] = float(metadata["ocr_confidence"])
        if metadata.get("ocr_engine"):
            features["ocr_engine"] = metadata["ocr_engine"]
        
        if not content:
            return features
        
        # Extract entities (simple approach - capitalized words)
        import re
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        # Filter common words
        common_words = {"The", "This", "That", "These", "Those", "And", "But", "Or", "For", "In", "On", "At", "To", "From"}
        features["entities"] = list(set([entity for entity in entities if entity not in common_words]))[:20]
        
        # Extract topics using keyword frequency
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3 and word not in ['this', 'that', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'each', 'which', 'their']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        features["topics"] = [word for word, freq in sorted_words[:10] if freq > 1]
        
        # Simple sentiment analysis (count positive/negative words)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect', 'best', 'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'success', 'successful', 'effective', 'efficient', 'useful', 'helpful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike', 'angry', 'frustrated', 'disappointed', 'failed', 'failure', 'problem', 'issue', 'error', 'bug', 'broken', 'difficult', 'hard', 'challenging']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            features["sentiment_score"] = (positive_count - negative_count) / total_sentiment_words
        
        # Simple readability score (based on sentence and word length)
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / len(sentences)
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            
            # Simple readability formula (lower is more readable)
            features["readability_score"] = (avg_sentence_length * 0.39) + (avg_word_length * 11.8) - 15.59
        
        return features
    
    def advanced_search(self, user_id: str, query: str, search_type: str = "hybrid", 
                       filters: Optional[Dict[str, Any]] = None, size: int = 20, from_: int = 0) -> Dict[str, Any]:
        """Advanced search with multiple search strategies"""
        if not self.es:
            return {"hits": [], "total": 0}
        
        try:
            if search_type == "semantic":
                return self._semantic_search(user_id, query, filters, size, from_)
            elif search_type == "fuzzy":
                return self._fuzzy_search(user_id, query, filters, size, from_)
            elif search_type == "hybrid":
                return self._hybrid_search(user_id, query, filters, size, from_)
            else:
                return self.search_documents(user_id, query, filters, size, from_)
                
        except Exception as e:
            print(f"Error in advanced search: {str(e)}")
            return {"hits": [], "total": 0}
    
    def _hybrid_search(self, user_id: str, query: str, filters: Optional[Dict[str, Any]] = None, 
                      size: int = 20, from_: int = 0) -> Dict[str, Any]:
        """Hybrid search combining multiple strategies"""
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}}
                    ],
                    "should": [
                        # Exact phrase matching (highest boost)
                        {"match_phrase": {"content": {"query": query, "boost": 3.0}}},
                        {"match_phrase": {"filename": {"query": query, "boost": 2.5}}},
                        
                        # Standard matching
                        {"match": {"content": {"query": query, "boost": 2.0, "analyzer": "content_analyzer"}}},
                        {"match": {"filename": {"query": query, "boost": 1.8, "analyzer": "filename_analyzer"}}},
                        
                        # Fuzzy matching for typos
                        {"fuzzy": {"content": {"value": query, "boost": 0.5, "fuzziness": "AUTO"}}},
                        
                        # Entity and topic matching
                        {"terms": {"entities": query.split(), "boost": 1.2}},
                        {"terms": {"topics": query.split(), "boost": 1.0}},
                        
                        # Programming language specific
                        {"terms": {"programming_languages": query.split(), "boost": 1.5}},
                        {"terms": {"frameworks": query.split(), "boost": 1.3}},
                        
                        # Metadata matching
                        {"nested": {
                            "path": "metadata",
                            "query": {"match": {"metadata": query}},
                            "boost": 0.8
                        }}
                    ],
                    "minimum_should_match": 1
                }
            },
            "highlight": {
                "fields": {
                    "content": {
                        "fragment_size": 150,
                        "number_of_fragments": 3,
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"]
                    },
                    "filename": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"]
                    }
                }
            },
            "size": size,
            "from": from_,
            "sort": [
                {"_score": {"order": "desc"}},
                {"created_at": {"order": "desc"}}
            ]
        }
        
        # Apply filters
        if filters:
            filter_clauses = []
            
            if filters.get("document_category"):
                filter_clauses.append({"term": {"document_category": filters["document_category"]}})
            
            if filters.get("content_type"):
                filter_clauses.append({"term": {"content_type": filters["content_type"]}})
            
            if filters.get("programming_languages"):
                filter_clauses.append({"terms": {"programming_languages": filters["programming_languages"]}})
            
            if filters.get("has_text") is not None:
                filter_clauses.append({"term": {"has_text": filters["has_text"]}})
            
            if filters.get("ocr_confidence_min"):
                filter_clauses.append({"range": {"ocr_confidence": {"gte": filters["ocr_confidence_min"]}}})
            
            if filters.get("complexity_range"):
                complexity_filter = {"range": {"complexity_score": {}}}
                if filters["complexity_range"].get("min"):
                    complexity_filter["range"]["complexity_score"]["gte"] = filters["complexity_range"]["min"]
                if filters["complexity_range"].get("max"):
                    complexity_filter["range"]["complexity_score"]["lte"] = filters["complexity_range"]["max"]
                filter_clauses.append(complexity_filter)
            
            if filters.get("date_range"):
                date_filter = {"range": {"created_at": {}}}
                if filters["date_range"].get("gte"):
                    date_filter["range"]["created_at"]["gte"] = filters["date_range"]["gte"]
                if filters["date_range"].get("lte"):
                    date_filter["range"]["created_at"]["lte"] = filters["date_range"]["lte"]
                filter_clauses.append(date_filter)
            
            if filter_clauses:
                search_body["query"]["bool"]["filter"] = filter_clauses
        
        # Execute search
        response = self.es.search(index=self.index_name, body=search_body)
        
        # Process results with enhanced metadata
        hits = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            result = {
                "document_id": source["document_id"],
                "filename": source["filename"],
                "content_type": source["content_type"],
                "document_category": source["document_category"],
                "score": hit["_score"],
                "created_at": source["created_at"],
                "highlights": hit.get("highlight", {}),
                "metadata": {
                    "word_count": source.get("word_count", 0),
                    "complexity_score": source.get("complexity_score", 0),
                    "programming_languages": source.get("programming_languages", []),
                    "frameworks": source.get("frameworks", []),
                    "ocr_confidence": source.get("ocr_confidence", 0),
                    "has_text": source.get("has_text", True),
                    "entities": source.get("entities", [])[:5],  # Top 5 entities
                    "topics": source.get("topics", [])[:5]  # Top 5 topics
                }
            }
            hits.append(result)
        
        return {
            "hits": hits,
            "total": response["hits"]["total"]["value"],
            "max_score": response["hits"]["max_score"],
            "search_type": "hybrid"
        }
    
    def _fuzzy_search(self, user_id: str, query: str, filters: Optional[Dict[str, Any]] = None, 
                     size: int = 20, from_: int = 0) -> Dict[str, Any]:
        """Fuzzy search for handling typos and variations"""
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}}
                    ],
                    "should": [
                        {"fuzzy": {"content": {"value": query, "boost": 2.0, "fuzziness": "AUTO"}}},
                        {"fuzzy": {"filename": {"value": query, "boost": 1.5, "fuzziness": "AUTO"}}},
                        {"wildcard": {"content": {"value": f"*{query}*", "boost": 1.0}}},
                        {"wildcard": {"filename": {"value": f"*{query}*", "boost": 0.8}}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": size,
            "from": from_
        }
        
        response = self.es.search(index=self.index_name, body=search_body)
        
        hits = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            hits.append({
                "document_id": source["document_id"],
                "filename": source["filename"],
                "content_type": source["content_type"],
                "document_category": source["document_category"],
                "score": hit["_score"],
                "created_at": source["created_at"]
            })
        
        return {
            "hits": hits,
            "total": response["hits"]["total"]["value"],
            "max_score": response["hits"]["max_score"],
            "search_type": "fuzzy"
        }
    
    def get_search_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get search analytics and insights"""
        if not self.es:
            return {"status": "disabled"}
        
        try:
            # Get document distribution by category
            category_agg = self.es.search(
                index=self.index_name,
                body={
                    "query": {"term": {"user_id": user_id}},
                    "size": 0,
                    "aggs": {
                        "categories": {
                            "terms": {"field": "document_category", "size": 10}
                        },
                        "languages": {
                            "terms": {"field": "programming_languages", "size": 10}
                        },
                        "avg_complexity": {
                            "avg": {"field": "complexity_score"}
                        },
                        "total_words": {
                            "sum": {"field": "word_count"}
                        }
                    }
                }
            )
            
            return {
                "total_documents": category_agg["hits"]["total"]["value"],
                "categories": [
                    {"name": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in category_agg["aggregations"]["categories"]["buckets"]
                ],
                "programming_languages": [
                    {"name": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in category_agg["aggregations"]["languages"]["buckets"]
                ],
                "avg_complexity": round(category_agg["aggregations"]["avg_complexity"]["value"] or 0, 2),
                "total_words": int(category_agg["aggregations"]["total_words"]["value"] or 0)
            }
            
        except Exception as e:
            print(f"Error getting search analytics: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def bulk_reindex(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk reindex multiple documents for better performance"""
        if not self.es:
            return {"success": False, "error": "Elasticsearch not available"}
        
        try:
            from elasticsearch.helpers import bulk
            
            actions = []
            for doc_data in documents:
                # Prepare document
                doc = {
                    "document_id": str(doc_data.get("id")),
                    "user_id": str(doc_data.get("user_id")),
                    "filename": doc_data.get("filename", ""),
                    "content": doc_data.get("extracted_text", ""),
                    "content_type": doc_data.get("content_type", ""),
                    "document_category": doc_data.get("document_category", ""),
                    "file_size": doc_data.get("file_size", 0),
                    "metadata": doc_data.get("metadata", {}),
                    "tags": doc_data.get("tags", []),
                    "created_at": doc_data.get("created_at", datetime.utcnow()).isoformat(),
                    "updated_at": doc_data.get("updated_at", datetime.utcnow()).isoformat(),
                    "processing_status": doc_data.get("processing_status", "completed")
                }
                
                # Add computed fields
                search_features = self._extract_search_features(doc["content"], doc["filename"])
                doc.update(search_features)
                
                advanced_features = self._extract_advanced_features(doc["content"], doc_data.get("metadata", {}))
                doc.update(advanced_features)
                
                # Prepare for bulk indexing
                action = {
                    "_index": self.index_name,
                    "_id": doc["document_id"],
                    "_source": doc
                }
                actions.append(action)
            
            # Execute bulk indexing
            success_count, failed_items = bulk(self.es, actions)
            
            return {
                "success": True,
                "indexed": success_count,
                "failed": len(failed_items),
                "errors": failed_items if failed_items else []
            }
            
        except Exception as e:
            print(f"Error in bulk reindexing: {str(e)}")
            return {"success": False, "error": str(e)}