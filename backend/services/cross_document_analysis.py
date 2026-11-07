"""
Cross-Document Analysis Service for Advanced Document Intelligence Platform
Implements cross-document search, relationship mapping, trend analysis, and clustering
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re
import json
from enum import Enum

class RelationshipType(Enum):
    """Types of relationships between documents"""
    SIMILAR_CONTENT = "similar_content"
    SHARED_ENTITIES = "shared_entities"
    TEMPORAL_SEQUENCE = "temporal_sequence"
    TOPIC_RELATED = "topic_related"
    AUTHOR_RELATED = "author_related"
    REFERENCE_LINK = "reference_link"
    DEPENDENCY = "dependency"

@dataclass
class DocumentRelationship:
    """Represents a relationship between two documents"""
    source_doc_id: str
    target_doc_id: str
    relationship_type: RelationshipType
    strength: float  # 0.0 to 1.0
    evidence: List[str]
    metadata: Dict[str, Any]

@dataclass
class DocumentCluster:
    """Represents a cluster of related documents"""
    cluster_id: str
    cluster_name: str
    document_ids: List[str]
    cluster_type: str  # topic, temporal, author, etc.
    centroid_features: Dict[str, Any]
    coherence_score: float
    created_at: datetime

@dataclass
class TrendAnalysis:
    """Represents trend analysis across document collections"""
    trend_id: str
    trend_name: str
    time_period: Tuple[datetime, datetime]
    document_count: int
    key_topics: List[str]
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float
    supporting_documents: List[str]

@dataclass
class CrossDocumentSearchResult:
    """Results from cross-document search and correlation"""
    query: str
    total_documents: int
    matching_documents: List[str]
    correlations: List[DocumentRelationship]
    entity_mentions: Dict[str, List[str]]  # entity -> document_ids
    topic_distribution: Dict[str, int]
    temporal_patterns: Dict[str, Any]

class CrossDocumentAnalysisService:
    """Advanced cross-document analysis and correlation service"""
    
    def __init__(self):
        """Initialize the cross-document analysis service"""
        self.document_cache = {}  # Cache for document data
        self.relationship_cache = {}  # Cache for computed relationships
        self.entity_index = defaultdict(set)  # entity -> set of document_ids
        self.topic_index = defaultdict(set)  # topic -> set of document_ids
        print("[ANALYSIS] Cross-Document Analysis Service initialized")
    
    def analyze_document_relationships(self, documents: List[Dict[str, Any]], 
                                     relationship_types: Optional[List[RelationshipType]] = None) -> List[DocumentRelationship]:
        """
        Analyze relationships between a collection of documents
        
        Args:
            documents: List of document data
            relationship_types: Types of relationships to analyze (None for all)
        """
        if relationship_types is None:
            relationship_types = list(RelationshipType)
        
        relationships = []
        
        # Build indices for efficient analysis
        self._build_document_indices(documents)
        
        # Analyze each type of relationship
        for rel_type in relationship_types:
            if rel_type == RelationshipType.SIMILAR_CONTENT:
                relationships.extend(self._find_content_relationships(documents))
            elif rel_type == RelationshipType.SHARED_ENTITIES:
                relationships.extend(self._find_entity_relationships(documents))
            elif rel_type == RelationshipType.TEMPORAL_SEQUENCE:
                relationships.extend(self._find_temporal_relationships(documents))
            elif rel_type == RelationshipType.TOPIC_RELATED:
                relationships.extend(self._find_topic_relationships(documents))
            elif rel_type == RelationshipType.AUTHOR_RELATED:
                relationships.extend(self._find_author_relationships(documents))
            elif rel_type == RelationshipType.REFERENCE_LINK:
                relationships.extend(self._find_reference_relationships(documents))
            elif rel_type == RelationshipType.DEPENDENCY:
                relationships.extend(self._find_dependency_relationships(documents))
        
        # Sort by relationship strength
        relationships.sort(key=lambda x: x.strength, reverse=True)
        
        return relationships
    
    def create_document_clusters(self, documents: List[Dict[str, Any]], 
                               clustering_method: str = "topic",
                               max_clusters: int = 10) -> List[DocumentCluster]:
        """
        Create clusters of related documents
        
        Args:
            documents: List of document data
            clustering_method: Method for clustering (topic, temporal, author, similarity)
            max_clusters: Maximum number of clusters to create
        """
        clusters = []
        
        if clustering_method == "topic":
            clusters = self._cluster_by_topic(documents, max_clusters)
        elif clustering_method == "temporal":
            clusters = self._cluster_by_time(documents, max_clusters)
        elif clustering_method == "author":
            clusters = self._cluster_by_author(documents, max_clusters)
        elif clustering_method == "similarity":
            clusters = self._cluster_by_similarity(documents, max_clusters)
        else:
            # Default to topic clustering
            clusters = self._cluster_by_topic(documents, max_clusters)
        
        return clusters
    
    def perform_trend_analysis(self, documents: List[Dict[str, Any]], 
                             time_window: int = 30,  # days
                             min_document_count: int = 3) -> List[TrendAnalysis]:
        """
        Perform trend analysis across document collections
        
        Args:
            documents: List of document data
            time_window: Time window for trend analysis in days
            min_document_count: Minimum documents required for a trend
        """
        trends = []
        
        # Group documents by time periods
        time_groups = self._group_documents_by_time(documents, time_window)
        
        # Analyze trends for each topic
        topic_trends = self._analyze_topic_trends(time_groups, min_document_count)
        trends.extend(topic_trends)
        
        # Analyze volume trends
        volume_trends = self._analyze_volume_trends(time_groups, min_document_count)
        trends.extend(volume_trends)
        
        # Analyze entity trends
        entity_trends = self._analyze_entity_trends(time_groups, min_document_count)
        trends.extend(entity_trends)
        
        return trends
    
    def cross_document_search(self, query: str, documents: List[Dict[str, Any]], 
                            search_type: str = "comprehensive") -> CrossDocumentSearchResult:
        """
        Perform cross-document search with correlation analysis
        
        Args:
            query: Search query
            documents: List of document data to search
            search_type: Type of search (comprehensive, entity, topic, temporal)
        """
        # Find matching documents
        matching_docs = self._find_matching_documents(query, documents)
        
        # Find correlations between matching documents
        correlations = []
        if len(matching_docs) > 1:
            correlations = self.analyze_document_relationships(matching_docs)
        
        # Extract entity mentions
        entity_mentions = self._extract_entity_mentions(query, matching_docs)
        
        # Analyze topic distribution
        topic_distribution = self._analyze_topic_distribution(matching_docs)
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(matching_docs)
        
        return CrossDocumentSearchResult(
            query=query,
            total_documents=len(documents),
            matching_documents=[doc["id"] for doc in matching_docs],
            correlations=correlations[:20],  # Limit to top 20 correlations
            entity_mentions=entity_mentions,
            topic_distribution=topic_distribution,
            temporal_patterns=temporal_patterns
        )
    
    def map_document_network(self, documents: List[Dict[str, Any]], 
                           min_relationship_strength: float = 0.3) -> Dict[str, Any]:
        """
        Create a network map of document relationships
        
        Args:
            documents: List of document data
            min_relationship_strength: Minimum strength for including relationships
        """
        # Analyze all relationships
        relationships = self.analyze_document_relationships(documents)
        
        # Filter by minimum strength
        strong_relationships = [
            rel for rel in relationships 
            if rel.strength >= min_relationship_strength
        ]
        
        # Build network structure
        nodes = []
        edges = []
        
        # Create nodes for each document
        for doc in documents:
            nodes.append({
                "id": doc["id"],
                "title": doc.get("title", f"Document {doc['id']}"),
                "type": doc.get("type", "unknown"),
                "size": len(doc.get("content", "")),
                "created_at": doc.get("created_at"),
                "metadata": doc.get("metadata", {})
            })
        
        # Create edges for relationships
        for rel in strong_relationships:
            edges.append({
                "source": rel.source_doc_id,
                "target": rel.target_doc_id,
                "type": rel.relationship_type.value,
                "strength": rel.strength,
                "evidence": rel.evidence[:3],  # Top 3 evidence items
                "metadata": rel.metadata
            })
        
        # Calculate network statistics
        network_stats = self._calculate_network_statistics(nodes, edges)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": network_stats,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_document_influence_score(self, document_id: str, 
                                   relationships: List[DocumentRelationship]) -> float:
        """
        Calculate influence score for a document based on its relationships
        """
        incoming_strength = sum(
            rel.strength for rel in relationships 
            if rel.target_doc_id == document_id
        )
        outgoing_strength = sum(
            rel.strength for rel in relationships 
            if rel.source_doc_id == document_id
        )
        
        # Weighted combination (incoming relationships weighted more heavily)
        influence_score = (incoming_strength * 0.7) + (outgoing_strength * 0.3)
        
        return min(influence_score, 1.0)  # Cap at 1.0
    
    # Private helper methods
    
    def _build_document_indices(self, documents: List[Dict[str, Any]]):
        """Build indices for efficient document analysis"""
        self.entity_index.clear()
        self.topic_index.clear()
        
        for doc in documents:
            doc_id = doc["id"]
            content = doc.get("content", "")
            
            # Extract and index entities
            entities = self._extract_entities(content)
            for entity in entities:
                self.entity_index[entity.lower()].add(doc_id)
            
            # Extract and index topics
            topics = self._extract_topics(content)
            for topic in topics:
                self.topic_index[topic.lower()].add(doc_id)
    
    def _find_content_relationships(self, documents: List[Dict[str, Any]]) -> List[DocumentRelationship]:
        """Find relationships based on content similarity"""
        relationships = []
        
        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents[i+1:], i+1):
                similarity = self._calculate_content_similarity(
                    doc1.get("content", ""), 
                    doc2.get("content", "")
                )
                
                if similarity > 0.5:  # Threshold for content similarity
                    evidence = self._find_similar_content_evidence(doc1, doc2)
                    
                    relationships.append(DocumentRelationship(
                        source_doc_id=doc1["id"],
                        target_doc_id=doc2["id"],
                        relationship_type=RelationshipType.SIMILAR_CONTENT,
                        strength=similarity,
                        evidence=evidence,
                        metadata={"similarity_score": similarity}
                    ))
        
        return relationships
    
    def _find_entity_relationships(self, documents: List[Dict[str, Any]]) -> List[DocumentRelationship]:
        """Find relationships based on shared entities"""
        relationships = []
        
        for i, doc1 in enumerate(documents):
            entities1 = set(self._extract_entities(doc1.get("content", "")))
            
            for j, doc2 in enumerate(documents[i+1:], i+1):
                entities2 = set(self._extract_entities(doc2.get("content", "")))
                
                shared_entities = entities1.intersection(entities2)
                if shared_entities:
                    strength = len(shared_entities) / len(entities1.union(entities2))
                    
                    relationships.append(DocumentRelationship(
                        source_doc_id=doc1["id"],
                        target_doc_id=doc2["id"],
                        relationship_type=RelationshipType.SHARED_ENTITIES,
                        strength=strength,
                        evidence=list(shared_entities)[:5],
                        metadata={"shared_entity_count": len(shared_entities)}
                    ))
        
        return relationships
    
    def _find_temporal_relationships(self, documents: List[Dict[str, Any]]) -> List[DocumentRelationship]:
        """Find relationships based on temporal proximity"""
        relationships = []
        
        # Sort documents by creation time
        sorted_docs = sorted(
            documents, 
            key=lambda x: x.get("created_at", "1970-01-01T00:00:00Z")
        )
        
        for i, doc1 in enumerate(sorted_docs[:-1]):
            doc2 = sorted_docs[i + 1]
            
            # Calculate temporal proximity (closer in time = stronger relationship)
            time1 = datetime.fromisoformat(doc1.get("created_at", "1970-01-01T00:00:00Z").replace('Z', '+00:00'))
            time2 = datetime.fromisoformat(doc2.get("created_at", "1970-01-01T00:00:00Z").replace('Z', '+00:00'))
            
            time_diff = abs((time2 - time1).total_seconds())
            max_time_diff = 7 * 24 * 3600  # 7 days in seconds
            
            if time_diff < max_time_diff:
                strength = 1.0 - (time_diff / max_time_diff)
                
                relationships.append(DocumentRelationship(
                    source_doc_id=doc1["id"],
                    target_doc_id=doc2["id"],
                    relationship_type=RelationshipType.TEMPORAL_SEQUENCE,
                    strength=strength,
                    evidence=[f"Created {time_diff/3600:.1f} hours apart"],
                    metadata={"time_difference_hours": time_diff/3600}
                ))
        
        return relationships
    
    def _find_topic_relationships(self, documents: List[Dict[str, Any]]) -> List[DocumentRelationship]:
        """Find relationships based on shared topics"""
        relationships = []
        
        for i, doc1 in enumerate(documents):
            topics1 = set(self._extract_topics(doc1.get("content", "")))
            
            for j, doc2 in enumerate(documents[i+1:], i+1):
                topics2 = set(self._extract_topics(doc2.get("content", "")))
                
                shared_topics = topics1.intersection(topics2)
                if shared_topics:
                    strength = len(shared_topics) / len(topics1.union(topics2))
                    
                    relationships.append(DocumentRelationship(
                        source_doc_id=doc1["id"],
                        target_doc_id=doc2["id"],
                        relationship_type=RelationshipType.TOPIC_RELATED,
                        strength=strength,
                        evidence=list(shared_topics)[:5],
                        metadata={"shared_topic_count": len(shared_topics)}
                    ))
        
        return relationships
    
    def _find_author_relationships(self, documents: List[Dict[str, Any]]) -> List[DocumentRelationship]:
        """Find relationships based on shared authors"""
        relationships = []
        
        for i, doc1 in enumerate(documents):
            author1 = doc1.get("metadata", {}).get("author", "").lower()
            if not author1:
                continue
                
            for j, doc2 in enumerate(documents[i+1:], i+1):
                author2 = doc2.get("metadata", {}).get("author", "").lower()
                
                if author1 == author2:
                    relationships.append(DocumentRelationship(
                        source_doc_id=doc1["id"],
                        target_doc_id=doc2["id"],
                        relationship_type=RelationshipType.AUTHOR_RELATED,
                        strength=1.0,
                        evidence=[f"Same author: {author1}"],
                        metadata={"author": author1}
                    ))
        
        return relationships
    
    def _find_reference_relationships(self, documents: List[Dict[str, Any]]) -> List[DocumentRelationship]:
        """Find relationships based on document references"""
        relationships = []
        
        for doc1 in documents:
            content1 = doc1.get("content", "")
            
            # Look for references to other documents
            for doc2 in documents:
                if doc1["id"] == doc2["id"]:
                    continue
                
                doc2_title = doc2.get("title", "")
                doc2_id = doc2["id"]
                
                # Check if doc1 references doc2
                if (doc2_title and doc2_title.lower() in content1.lower()) or \
                   (doc2_id in content1):
                    
                    relationships.append(DocumentRelationship(
                        source_doc_id=doc1["id"],
                        target_doc_id=doc2["id"],
                        relationship_type=RelationshipType.REFERENCE_LINK,
                        strength=0.8,
                        evidence=[f"References '{doc2_title or doc2_id}'"],
                        metadata={"reference_type": "explicit"}
                    ))
        
        return relationships
    
    def _find_dependency_relationships(self, documents: List[Dict[str, Any]]) -> List[DocumentRelationship]:
        """Find dependency relationships (e.g., code imports, document prerequisites)"""
        relationships = []
        
        for doc1 in documents:
            content1 = doc1.get("content", "")
            
            # Look for import statements or dependencies
            import_patterns = [
                r'import\s+(\w+)',
                r'from\s+(\w+)\s+import',
                r'require\([\'"]([^\'"]+)[\'"]\)',
                r'#include\s*[<"]([^>"]+)[>"]'
            ]
            
            dependencies = set()
            for pattern in import_patterns:
                matches = re.findall(pattern, content1, re.IGNORECASE)
                dependencies.update(matches)
            
            # Check if any other document matches these dependencies
            for doc2 in documents:
                if doc1["id"] == doc2["id"]:
                    continue
                
                doc2_name = doc2.get("title", "").lower()
                doc2_filename = doc2.get("filename", "").lower()
                
                for dep in dependencies:
                    if dep.lower() in doc2_name or dep.lower() in doc2_filename:
                        relationships.append(DocumentRelationship(
                            source_doc_id=doc1["id"],
                            target_doc_id=doc2["id"],
                            relationship_type=RelationshipType.DEPENDENCY,
                            strength=0.9,
                            evidence=[f"Depends on '{dep}'"],
                            metadata={"dependency": dep}
                        ))
        
        return relationships
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract named entities from content (simplified implementation)"""
        # Simple entity extraction - in production, use NLP libraries
        entities = []
        
        # Extract capitalized words (potential proper nouns)
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        entities.extend(words)
        
        # Extract common entity patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        entities.extend(emails)
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, content)
        entities.extend(urls)
        
        # Remove duplicates and return
        return list(set(entities))
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content (simplified implementation)"""
        # Simple topic extraction based on keywords
        topic_keywords = {
            'programming': ['code', 'function', 'class', 'variable', 'algorithm', 'programming'],
            'data_science': ['data', 'analysis', 'machine learning', 'statistics', 'model'],
            'web_development': ['html', 'css', 'javascript', 'web', 'frontend', 'backend'],
            'database': ['sql', 'database', 'query', 'table', 'index'],
            'security': ['security', 'encryption', 'authentication', 'vulnerability'],
            'api': ['api', 'endpoint', 'rest', 'json', 'http'],
            'documentation': ['documentation', 'guide', 'tutorial', 'manual', 'readme']
        }
        
        content_lower = content.lower()
        topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings"""
        if not content1 or not content2:
            return 0.0
        
        # Simple Jaccard similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _find_similar_content_evidence(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> List[str]:
        """Find evidence of content similarity between documents"""
        content1 = doc1.get("content", "")
        content2 = doc2.get("content", "")
        
        # Find common phrases
        words1 = content1.lower().split()
        words2 = content2.lower().split()
        
        common_phrases = []
        for i in range(len(words1) - 2):
            phrase = " ".join(words1[i:i+3])
            if phrase in content2.lower():
                common_phrases.append(phrase)
        
        return common_phrases[:5]  # Return top 5 common phrases
    
    def _cluster_by_topic(self, documents: List[Dict[str, Any]], max_clusters: int) -> List[DocumentCluster]:
        """Cluster documents by topic"""
        # Group documents by their primary topics
        topic_groups = defaultdict(list)
        
        for doc in documents:
            topics = self._extract_topics(doc.get("content", ""))
            primary_topic = topics[0] if topics else "uncategorized"
            topic_groups[primary_topic].append(doc["id"])
        
        clusters = []
        for i, (topic, doc_ids) in enumerate(topic_groups.items()):
            if i >= max_clusters:
                break
                
            if len(doc_ids) >= 2:  # Only create clusters with multiple documents
                clusters.append(DocumentCluster(
                    cluster_id=f"topic_cluster_{i+1}",
                    cluster_name=f"Topic: {topic.title()}",
                    document_ids=doc_ids,
                    cluster_type="topic",
                    centroid_features={"primary_topic": topic},
                    coherence_score=0.8,  # Mock coherence score
                    created_at=datetime.utcnow()
                ))
        
        return clusters
    
    def _cluster_by_time(self, documents: List[Dict[str, Any]], max_clusters: int) -> List[DocumentCluster]:
        """Cluster documents by temporal proximity"""
        # Sort documents by creation time
        sorted_docs = sorted(
            documents, 
            key=lambda x: x.get("created_at", "1970-01-01T00:00:00Z")
        )
        
        clusters = []
        current_cluster = []
        cluster_count = 0
        
        for i, doc in enumerate(sorted_docs):
            if not current_cluster:
                current_cluster = [doc["id"]]
                continue
            
            # Check if document is within time window of cluster
            prev_doc = next(d for d in sorted_docs if d["id"] == current_cluster[-1])
            time_diff = self._calculate_time_difference(
                prev_doc.get("created_at", "1970-01-01T00:00:00Z"),
                doc.get("created_at", "1970-01-01T00:00:00Z")
            )
            
            if time_diff <= 7:  # 7 days window
                current_cluster.append(doc["id"])
            else:
                # Create cluster from current group
                if len(current_cluster) >= 2 and cluster_count < max_clusters:
                    clusters.append(DocumentCluster(
                        cluster_id=f"temporal_cluster_{cluster_count+1}",
                        cluster_name=f"Time Period {cluster_count+1}",
                        document_ids=current_cluster,
                        cluster_type="temporal",
                        centroid_features={"time_window": f"{time_diff} days"},
                        coherence_score=0.7,
                        created_at=datetime.utcnow()
                    ))
                    cluster_count += 1
                
                current_cluster = [doc["id"]]
        
        # Handle last cluster
        if len(current_cluster) >= 2 and cluster_count < max_clusters:
            clusters.append(DocumentCluster(
                cluster_id=f"temporal_cluster_{cluster_count+1}",
                cluster_name=f"Time Period {cluster_count+1}",
                document_ids=current_cluster,
                cluster_type="temporal",
                centroid_features={"time_window": "recent"},
                coherence_score=0.7,
                created_at=datetime.utcnow()
            ))
        
        return clusters
    
    def _cluster_by_author(self, documents: List[Dict[str, Any]], max_clusters: int) -> List[DocumentCluster]:
        """Cluster documents by author"""
        author_groups = defaultdict(list)
        
        for doc in documents:
            author = doc.get("metadata", {}).get("author", "unknown")
            author_groups[author].append(doc["id"])
        
        clusters = []
        for i, (author, doc_ids) in enumerate(author_groups.items()):
            if i >= max_clusters:
                break
                
            if len(doc_ids) >= 2:
                clusters.append(DocumentCluster(
                    cluster_id=f"author_cluster_{i+1}",
                    cluster_name=f"Author: {author}",
                    document_ids=doc_ids,
                    cluster_type="author",
                    centroid_features={"author": author},
                    coherence_score=1.0,  # Perfect coherence for same author
                    created_at=datetime.utcnow()
                ))
        
        return clusters
    
    def _cluster_by_similarity(self, documents: List[Dict[str, Any]], max_clusters: int) -> List[DocumentCluster]:
        """Cluster documents by content similarity"""
        # Simple similarity-based clustering
        clusters = []
        processed = set()
        
        for i, doc1 in enumerate(documents):
            if doc1["id"] in processed:
                continue
            
            cluster_docs = [doc1["id"]]
            processed.add(doc1["id"])
            
            # Find similar documents
            for doc2 in documents[i+1:]:
                if doc2["id"] in processed:
                    continue
                
                similarity = self._calculate_content_similarity(
                    doc1.get("content", ""), 
                    doc2.get("content", "")
                )
                
                if similarity > 0.6:  # Similarity threshold
                    cluster_docs.append(doc2["id"])
                    processed.add(doc2["id"])
            
            if len(cluster_docs) >= 2 and len(clusters) < max_clusters:
                clusters.append(DocumentCluster(
                    cluster_id=f"similarity_cluster_{len(clusters)+1}",
                    cluster_name=f"Similar Content Group {len(clusters)+1}",
                    document_ids=cluster_docs,
                    cluster_type="similarity",
                    centroid_features={"similarity_threshold": 0.6},
                    coherence_score=0.75,
                    created_at=datetime.utcnow()
                ))
        
        return clusters
    
    def _group_documents_by_time(self, documents: List[Dict[str, Any]], window_days: int) -> Dict[str, List[Dict[str, Any]]]:
        """Group documents by time windows"""
        time_groups = defaultdict(list)
        
        for doc in documents:
            created_at = doc.get("created_at", "1970-01-01T00:00:00Z")
            try:
                doc_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                # Group by week
                week_start = doc_date - timedelta(days=doc_date.weekday())
                week_key = week_start.strftime("%Y-W%U")
                time_groups[week_key].append(doc)
            except:
                time_groups["unknown"].append(doc)
        
        return dict(time_groups)
    
    def _analyze_topic_trends(self, time_groups: Dict[str, List[Dict[str, Any]]], min_docs: int) -> List[TrendAnalysis]:
        """Analyze trends in topics over time"""
        trends = []
        
        # Track topic frequency over time
        topic_timeline = defaultdict(lambda: defaultdict(int))
        
        for time_period, docs in time_groups.items():
            for doc in docs:
                topics = self._extract_topics(doc.get("content", ""))
                for topic in topics:
                    topic_timeline[topic][time_period] += 1
        
        # Analyze trends for each topic
        for topic, timeline in topic_timeline.items():
            if sum(timeline.values()) >= min_docs:
                # Simple trend analysis
                periods = sorted(timeline.keys())
                if len(periods) >= 2:
                    early_count = sum(timeline[p] for p in periods[:len(periods)//2])
                    late_count = sum(timeline[p] for p in periods[len(periods)//2:])
                    
                    if late_count > early_count * 1.2:
                        direction = "increasing"
                        strength = (late_count - early_count) / early_count if early_count > 0 else 1.0
                    elif early_count > late_count * 1.2:
                        direction = "decreasing"
                        strength = (early_count - late_count) / early_count
                    else:
                        direction = "stable"
                        strength = 0.1
                    
                    trends.append(TrendAnalysis(
                        trend_id=f"topic_trend_{topic}",
                        trend_name=f"Topic: {topic.title()}",
                        time_period=(
                            datetime.utcnow() - timedelta(days=30),
                            datetime.utcnow()
                        ),
                        document_count=sum(timeline.values()),
                        key_topics=[topic],
                        trend_direction=direction,
                        trend_strength=min(strength, 1.0),
                        supporting_documents=[]  # Would be populated with actual doc IDs
                    ))
        
        return trends
    
    def _analyze_volume_trends(self, time_groups: Dict[str, List[Dict[str, Any]]], min_docs: int) -> List[TrendAnalysis]:
        """Analyze document volume trends over time"""
        trends = []
        
        periods = sorted(time_groups.keys())
        if len(periods) >= 2:
            volumes = [len(time_groups[period]) for period in periods]
            
            # Calculate trend
            early_avg = sum(volumes[:len(volumes)//2]) / (len(volumes)//2)
            late_avg = sum(volumes[len(volumes)//2:]) / (len(volumes) - len(volumes)//2)
            
            if late_avg > early_avg * 1.2:
                direction = "increasing"
                strength = (late_avg - early_avg) / early_avg
            elif early_avg > late_avg * 1.2:
                direction = "decreasing"
                strength = (early_avg - late_avg) / early_avg
            else:
                direction = "stable"
                strength = 0.1
            
            trends.append(TrendAnalysis(
                trend_id="volume_trend",
                trend_name="Document Volume",
                time_period=(
                    datetime.utcnow() - timedelta(days=30),
                    datetime.utcnow()
                ),
                document_count=sum(volumes),
                key_topics=["volume"],
                trend_direction=direction,
                trend_strength=min(strength, 1.0),
                supporting_documents=[]
            ))
        
        return trends
    
    def _analyze_entity_trends(self, time_groups: Dict[str, List[Dict[str, Any]]], min_docs: int) -> List[TrendAnalysis]:
        """Analyze entity mention trends over time"""
        trends = []
        
        # Track entity frequency over time
        entity_timeline = defaultdict(lambda: defaultdict(int))
        
        for time_period, docs in time_groups.items():
            for doc in docs:
                entities = self._extract_entities(doc.get("content", ""))
                for entity in entities:
                    entity_timeline[entity][time_period] += 1
        
        # Analyze trends for top entities
        top_entities = sorted(
            entity_timeline.items(),
            key=lambda x: sum(x[1].values()),
            reverse=True
        )[:10]  # Top 10 entities
        
        for entity, timeline in top_entities:
            if sum(timeline.values()) >= min_docs:
                periods = sorted(timeline.keys())
                if len(periods) >= 2:
                    early_count = sum(timeline[p] for p in periods[:len(periods)//2])
                    late_count = sum(timeline[p] for p in periods[len(periods)//2:])
                    
                    if late_count > early_count * 1.2:
                        direction = "increasing"
                        strength = (late_count - early_count) / early_count if early_count > 0 else 1.0
                    elif early_count > late_count * 1.2:
                        direction = "decreasing"
                        strength = (early_count - late_count) / early_count
                    else:
                        direction = "stable"
                        strength = 0.1
                    
                    trends.append(TrendAnalysis(
                        trend_id=f"entity_trend_{entity}",
                        trend_name=f"Entity: {entity}",
                        time_period=(
                            datetime.utcnow() - timedelta(days=30),
                            datetime.utcnow()
                        ),
                        document_count=sum(timeline.values()),
                        key_topics=[entity],
                        trend_direction=direction,
                        trend_strength=min(strength, 1.0),
                        supporting_documents=[]
                    ))
        
        return trends
    
    def _find_matching_documents(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find documents matching the search query"""
        matching_docs = []
        query_lower = query.lower()
        
        for doc in documents:
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()
            
            if query_lower in content or query_lower in title:
                matching_docs.append(doc)
        
        return matching_docs
    
    def _extract_entity_mentions(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract entity mentions from matching documents"""
        entity_mentions = defaultdict(list)
        
        for doc in documents:
            entities = self._extract_entities(doc.get("content", ""))
            for entity in entities:
                if entity.lower() not in entity_mentions[entity]:
                    entity_mentions[entity].append(doc["id"])
        
        return dict(entity_mentions)
    
    def _analyze_topic_distribution(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze topic distribution in matching documents"""
        topic_counts = Counter()
        
        for doc in documents:
            topics = self._extract_topics(doc.get("content", ""))
            for topic in topics:
                topic_counts[topic] += 1
        
        return dict(topic_counts)
    
    def _analyze_temporal_patterns(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in matching documents"""
        if not documents:
            return {}
        
        dates = []
        for doc in documents:
            created_at = doc.get("created_at")
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    dates.append(date)
                except:
                    continue
        
        if not dates:
            return {}
        
        dates.sort()
        
        return {
            "earliest_document": dates[0].isoformat(),
            "latest_document": dates[-1].isoformat(),
            "time_span_days": (dates[-1] - dates[0]).days,
            "document_frequency": len(dates) / max((dates[-1] - dates[0]).days, 1)
        }
    
    def _calculate_network_statistics(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate network statistics"""
        node_count = len(nodes)
        edge_count = len(edges)
        
        # Calculate degree distribution
        degree_counts = defaultdict(int)
        for edge in edges:
            degree_counts[edge["source"]] += 1
            degree_counts[edge["target"]] += 1
        
        avg_degree = sum(degree_counts.values()) / len(degree_counts) if degree_counts else 0
        max_degree = max(degree_counts.values()) if degree_counts else 0
        
        # Calculate density
        max_possible_edges = node_count * (node_count - 1) / 2
        density = edge_count / max_possible_edges if max_possible_edges > 0 else 0
        
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": density,
            "average_degree": avg_degree,
            "max_degree": max_degree,
            "connected_components": 1  # Simplified - would need graph analysis
        }
    
    def _calculate_time_difference(self, time1: str, time2: str) -> float:
        """Calculate time difference in days"""
        try:
            dt1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
            return abs((dt2 - dt1).days)
        except:
            return 0.0

# Global cross-document analysis service instance
cross_document_analysis_service = CrossDocumentAnalysisService()