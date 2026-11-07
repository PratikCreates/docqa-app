"""
Document Comparison Engine for Advanced Document Intelligence Platform
Implements document similarity detection, side-by-side comparison, and batch analysis
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import difflib
from collections import Counter
import hashlib

@dataclass
class DocumentSimilarity:
    """Document similarity result"""
    document1_id: str
    document2_id: str
    similarity_score: float
    similarity_type: str  # content, structure, semantic, code
    common_elements: List[str]
    differences: List[str]
    metadata: Dict[str, Any]

@dataclass
class ComparisonResult:
    """Complete document comparison result"""
    document1: Dict[str, Any]
    document2: Dict[str, Any]
    overall_similarity: float
    content_similarity: float
    structure_similarity: float
    semantic_similarity: float
    differences: List[Dict[str, Any]]
    common_sections: List[Dict[str, Any]]
    recommendations: List[str]
    comparison_metadata: Dict[str, Any]

@dataclass
class BatchComparisonResult:
    """Batch document comparison result"""
    total_documents: int
    comparisons_performed: int
    similarity_matrix: Dict[str, Dict[str, float]]
    clusters: List[List[str]]
    outliers: List[str]
    summary_stats: Dict[str, Any]

class DocumentComparisonEngine:
    """Advanced document comparison and similarity detection engine"""
    
    def __init__(self):
        """Initialize the document comparison engine"""
        self.similarity_threshold = 0.7
        self.semantic_cache = {}  # Cache for semantic similarity calculations
        print("[COMPARISON] Document Comparison Engine initialized")
    
    def compare_documents(self, doc1: Dict[str, Any], doc2: Dict[str, Any], 
                         comparison_type: str = "comprehensive") -> ComparisonResult:
        """
        Compare two documents comprehensively
        
        Args:
            doc1: First document data
            doc2: Second document data
            comparison_type: Type of comparison (comprehensive, content, structure, semantic)
        """
        
        # Extract content and metadata
        content1 = doc1.get('content', '')
        content2 = doc2.get('content', '')
        
        # Perform different types of similarity analysis
        content_sim = self._calculate_content_similarity(content1, content2)
        structure_sim = self._calculate_structure_similarity(doc1, doc2)
        semantic_sim = self._calculate_semantic_similarity(content1, content2)
        
        # Calculate overall similarity
        overall_sim = (content_sim * 0.4 + structure_sim * 0.3 + semantic_sim * 0.3)
        
        # Find differences and common sections
        differences = self._find_differences(content1, content2)
        common_sections = self._find_common_sections(content1, content2)
        
        # Generate recommendations
        recommendations = self._generate_comparison_recommendations(
            overall_sim, content_sim, structure_sim, semantic_sim, doc1, doc2
        )
        
        return ComparisonResult(
            document1=doc1,
            document2=doc2,
            overall_similarity=overall_sim,
            content_similarity=content_sim,
            structure_similarity=structure_sim,
            semantic_similarity=semantic_sim,
            differences=differences,
            common_sections=common_sections,
            recommendations=recommendations,
            comparison_metadata={
                "comparison_type": comparison_type,
                "timestamp": datetime.utcnow().isoformat(),
                "algorithm_version": "1.0",
                "processing_time_ms": 150  # Mock processing time
            }
        )
    
    def find_similar_documents(self, target_doc: Dict[str, Any], 
                              document_pool: List[Dict[str, Any]], 
                              limit: int = 10,
                              min_similarity: float = 0.3) -> List[DocumentSimilarity]:
        """
        Find documents similar to the target document
        
        Args:
            target_doc: Document to find similarities for
            document_pool: Pool of documents to search in
            limit: Maximum number of similar documents to return
            min_similarity: Minimum similarity threshold
        """
        
        similarities = []
        target_content = target_doc.get('content', '')
        
        for doc in document_pool:
            if doc.get('id') == target_doc.get('id'):
                continue  # Skip self-comparison
            
            doc_content = doc.get('content', '')
            
            # Calculate similarity
            content_sim = self._calculate_content_similarity(target_content, doc_content)
            structure_sim = self._calculate_structure_similarity(target_doc, doc)
            overall_sim = (content_sim * 0.6 + structure_sim * 0.4)
            
            if overall_sim >= min_similarity:
                # Find common elements and differences
                common_elements = self._extract_common_elements(target_content, doc_content)
                differences = self._extract_key_differences(target_content, doc_content)
                
                similarity = DocumentSimilarity(
                    document1_id=target_doc.get('id', 'unknown'),
                    document2_id=doc.get('id', 'unknown'),
                    similarity_score=overall_sim,
                    similarity_type=self._determine_similarity_type(target_doc, doc),
                    common_elements=common_elements,
                    differences=differences,
                    metadata={
                        "content_similarity": content_sim,
                        "structure_similarity": structure_sim,
                        "document_types": [target_doc.get('type'), doc.get('type')]
                    }
                )
                similarities.append(similarity)
        
        # Sort by similarity score and return top results
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:limit]
    
    def batch_compare_documents(self, documents: List[Dict[str, Any]], 
                               comparison_mode: str = "all_pairs") -> BatchComparisonResult:
        """
        Perform batch comparison of multiple documents
        
        Args:
            documents: List of documents to compare
            comparison_mode: Mode of comparison (all_pairs, clustering, outlier_detection)
        """
        
        total_docs = len(documents)
        comparisons_performed = 0
        similarity_matrix = {}
        
        # Initialize similarity matrix
        for doc in documents:
            doc_id = doc.get('id', f'doc_{documents.index(doc)}')
            similarity_matrix[doc_id] = {}
        
        # Perform pairwise comparisons
        for i, doc1 in enumerate(documents):
            doc1_id = doc1.get('id', f'doc_{i}')
            
            for j, doc2 in enumerate(documents):
                if i >= j:  # Skip duplicate comparisons and self-comparison
                    continue
                
                doc2_id = doc2.get('id', f'doc_{j}')
                
                # Calculate similarity
                content_sim = self._calculate_content_similarity(
                    doc1.get('content', ''), doc2.get('content', '')
                )
                structure_sim = self._calculate_structure_similarity(doc1, doc2)
                overall_sim = (content_sim * 0.6 + structure_sim * 0.4)
                
                # Store in similarity matrix
                similarity_matrix[doc1_id][doc2_id] = overall_sim
                similarity_matrix[doc2_id][doc1_id] = overall_sim
                comparisons_performed += 1
        
        # Perform clustering
        clusters = self._cluster_documents(documents, similarity_matrix)
        
        # Identify outliers
        outliers = self._identify_outliers(documents, similarity_matrix)
        
        # Calculate summary statistics
        summary_stats = self._calculate_batch_summary_stats(similarity_matrix, clusters, outliers)
        
        return BatchComparisonResult(
            total_documents=total_docs,
            comparisons_performed=comparisons_performed,
            similarity_matrix=similarity_matrix,
            clusters=clusters,
            outliers=outliers,
            summary_stats=summary_stats
        )
    
    def get_document_fingerprint(self, document: Dict[str, Any]) -> str:
        """
        Generate a unique fingerprint for a document based on its content and structure
        """
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        # Create fingerprint components
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        structure_elements = [
            str(len(content)),
            str(len(content.split())),
            str(len(content.split('\n'))),
            document.get('type', 'unknown'),
            str(metadata.get('file_size', 0))
        ]
        structure_hash = hashlib.md5('|'.join(structure_elements).encode()).hexdigest()[:16]
        
        return f"{content_hash}-{structure_hash}"
    
    # Private helper methods
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate content-based similarity using multiple algorithms"""
        if not content1 or not content2:
            return 0.0
        
        # Tokenize content
        tokens1 = set(re.findall(r'\w+', content1.lower()))
        tokens2 = set(re.findall(r'\w+', content2.lower()))
        
        # Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        jaccard_sim = intersection / union if union > 0 else 0.0
        
        # Sequence similarity using difflib
        sequence_sim = difflib.SequenceMatcher(None, content1, content2).ratio()
        
        # Combined similarity
        return (jaccard_sim * 0.6 + sequence_sim * 0.4)
    
    def _calculate_structure_similarity(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> float:
        """Calculate structural similarity between documents"""
        
        # Extract structural features
        features1 = self._extract_structural_features(doc1)
        features2 = self._extract_structural_features(doc2)
        
        # Compare features
        similarity_scores = []
        
        for feature in features1:
            if feature in features2:
                # Calculate feature similarity
                val1 = features1[feature]
                val2 = features2[feature]
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Numerical similarity
                    max_val = max(val1, val2)
                    if max_val > 0:
                        similarity_scores.append(1 - abs(val1 - val2) / max_val)
                    else:
                        similarity_scores.append(1.0)
                else:
                    # String similarity
                    similarity_scores.append(1.0 if val1 == val2 else 0.0)
        
        return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
    
    def _calculate_semantic_similarity(self, content1: str, content2: str) -> float:
        """Calculate semantic similarity (mock implementation)"""
        # In a real implementation, this would use embeddings or NLP models
        
        # Simple keyword-based semantic similarity
        keywords1 = self._extract_keywords(content1)
        keywords2 = self._extract_keywords(content2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        common_keywords = set(keywords1).intersection(set(keywords2))
        total_keywords = set(keywords1).union(set(keywords2))
        
        return len(common_keywords) / len(total_keywords) if total_keywords else 0.0
    
    def _extract_structural_features(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structural features from a document"""
        content = doc.get('content', '')
        
        return {
            'word_count': len(content.split()),
            'line_count': len(content.split('\n')),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'avg_sentence_length': self._calculate_avg_sentence_length(content),
            'document_type': doc.get('type', 'unknown'),
            'has_code_blocks': '```' in content or '    ' in content,
            'has_headers': any(line.startswith('#') for line in content.split('\n')),
            'has_lists': any(line.strip().startswith(('-', '*', '1.')) for line in content.split('\n'))
        }
    
    def _calculate_avg_sentence_length(self, content: str) -> float:
        """Calculate average sentence length"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        total_words = sum(len(sentence.split()) for sentence in sentences)
        return total_words / len(sentences)
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content (simple implementation)"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        words = re.findall(r'\w+', content.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Return most frequent keywords
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(20)]
    
    def _find_differences(self, content1: str, content2: str) -> List[Dict[str, Any]]:
        """Find differences between two documents"""
        differ = difflib.unified_diff(
            content1.splitlines(keepends=True),
            content2.splitlines(keepends=True),
            fromfile='document1',
            tofile='document2',
            lineterm=''
        )
        
        differences = []
        for line in differ:
            if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
                continue
            
            if line.startswith('+'):
                differences.append({
                    'type': 'addition',
                    'content': line[1:].strip(),
                    'line_type': 'added'
                })
            elif line.startswith('-'):
                differences.append({
                    'type': 'deletion',
                    'content': line[1:].strip(),
                    'line_type': 'removed'
                })
        
        return differences[:50]  # Limit to first 50 differences
    
    def _find_common_sections(self, content1: str, content2: str) -> List[Dict[str, Any]]:
        """Find common sections between documents"""
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        common_sections = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal' and i2 - i1 > 2:  # Only include substantial common sections
                common_sections.append({
                    'content': '\n'.join(lines1[i1:i2]),
                    'start_line_doc1': i1,
                    'end_line_doc1': i2,
                    'start_line_doc2': j1,
                    'end_line_doc2': j2,
                    'length': i2 - i1
                })
        
        return common_sections
    
    def _extract_common_elements(self, content1: str, content2: str) -> List[str]:
        """Extract common elements between documents"""
        keywords1 = set(self._extract_keywords(content1))
        keywords2 = set(self._extract_keywords(content2))
        
        common_keywords = keywords1.intersection(keywords2)
        return list(common_keywords)[:10]  # Return top 10 common elements
    
    def _extract_key_differences(self, content1: str, content2: str) -> List[str]:
        """Extract key differences between documents"""
        keywords1 = set(self._extract_keywords(content1))
        keywords2 = set(self._extract_keywords(content2))
        
        unique_to_doc1 = keywords1 - keywords2
        unique_to_doc2 = keywords2 - keywords1
        
        differences = []
        differences.extend([f"Only in doc1: {word}" for word in list(unique_to_doc1)[:5]])
        differences.extend([f"Only in doc2: {word}" for word in list(unique_to_doc2)[:5]])
        
        return differences
    
    def _determine_similarity_type(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> str:
        """Determine the type of similarity between documents"""
        type1 = doc1.get('type', 'unknown')
        type2 = doc2.get('type', 'unknown')
        
        if type1 == type2:
            if type1 in ['py', 'js', 'java', 'cpp']:
                return 'code'
            elif type1 in ['md', 'txt', 'html']:
                return 'content'
            else:
                return 'structure'
        else:
            return 'semantic'
    
    def _generate_comparison_recommendations(self, overall_sim: float, content_sim: float, 
                                           structure_sim: float, semantic_sim: float,
                                           doc1: Dict[str, Any], doc2: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison results"""
        recommendations = []
        
        if overall_sim > 0.8:
            recommendations.append("Documents are highly similar - consider consolidating or cross-referencing")
        elif overall_sim > 0.6:
            recommendations.append("Documents share significant content - review for potential duplication")
        elif overall_sim < 0.3:
            recommendations.append("Documents are quite different - may serve complementary purposes")
        
        if content_sim > structure_sim:
            recommendations.append("Content similarity is higher than structural - focus on content alignment")
        elif structure_sim > content_sim:
            recommendations.append("Structural similarity is higher than content - consider content harmonization")
        
        if semantic_sim > 0.7:
            recommendations.append("Strong semantic similarity detected - documents likely cover related topics")
        
        return recommendations
    
    def _cluster_documents(self, documents: List[Dict[str, Any]], 
                          similarity_matrix: Dict[str, Dict[str, float]]) -> List[List[str]]:
        """Cluster documents based on similarity"""
        # Simple clustering algorithm
        clusters = []
        processed = set()
        
        for doc in documents:
            doc_id = doc.get('id', f'doc_{documents.index(doc)}')
            
            if doc_id in processed:
                continue
            
            # Start new cluster
            cluster = [doc_id]
            processed.add(doc_id)
            
            # Find similar documents
            for other_doc in documents:
                other_id = other_doc.get('id', f'doc_{documents.index(other_doc)}')
                
                if other_id in processed or other_id == doc_id:
                    continue
                
                # Check similarity
                similarity = similarity_matrix.get(doc_id, {}).get(other_id, 0.0)
                if similarity > self.similarity_threshold:
                    cluster.append(other_id)
                    processed.add(other_id)
            
            if len(cluster) > 1:  # Only include clusters with multiple documents
                clusters.append(cluster)
        
        return clusters
    
    def _identify_outliers(self, documents: List[Dict[str, Any]], 
                          similarity_matrix: Dict[str, Dict[str, float]]) -> List[str]:
        """Identify outlier documents with low similarity to others"""
        outliers = []
        
        for doc in documents:
            doc_id = doc.get('id', f'doc_{documents.index(doc)}')
            
            # Calculate average similarity to other documents
            similarities = []
            for other_doc in documents:
                other_id = other_doc.get('id', f'doc_{documents.index(other_doc)}')
                if other_id != doc_id:
                    similarity = similarity_matrix.get(doc_id, {}).get(other_id, 0.0)
                    similarities.append(similarity)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            
            # Consider as outlier if average similarity is very low
            if avg_similarity < 0.2:
                outliers.append(doc_id)
        
        return outliers
    
    def _calculate_batch_summary_stats(self, similarity_matrix: Dict[str, Dict[str, float]], 
                                     clusters: List[List[str]], outliers: List[str]) -> Dict[str, Any]:
        """Calculate summary statistics for batch comparison"""
        all_similarities = []
        
        for doc_id in similarity_matrix:
            for other_id, similarity in similarity_matrix[doc_id].items():
                all_similarities.append(similarity)
        
        if not all_similarities:
            return {}
        
        return {
            'average_similarity': sum(all_similarities) / len(all_similarities),
            'max_similarity': max(all_similarities),
            'min_similarity': min(all_similarities),
            'total_clusters': len(clusters),
            'largest_cluster_size': max(len(cluster) for cluster in clusters) if clusters else 0,
            'total_outliers': len(outliers),
            'similarity_distribution': {
                'high_similarity_pairs': len([s for s in all_similarities if s > 0.7]),
                'medium_similarity_pairs': len([s for s in all_similarities if 0.3 <= s <= 0.7]),
                'low_similarity_pairs': len([s for s in all_similarities if s < 0.3])
            }
        }

# Global document comparison engine instance
document_comparison_engine = DocumentComparisonEngine()