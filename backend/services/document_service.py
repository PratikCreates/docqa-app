"""
Clean Document service for managing document lifecycle and operations
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from models.database import Document, DocumentLibrary, LibraryDocument, ProcessingHistory
import uuid
import os

class DocumentService:
    """Service for managing document operations"""
    
    def upload_document(self, db: Session, user_id: str, filename: str, 
                       file_content: bytes, content_type: str = None) -> Optional[Document]:
        """Upload and process a document"""
        try:
            # Simple text extraction for now
            extracted_text = ""
            if content_type and "text" in content_type:
                extracted_text = file_content.decode('utf-8', errors='ignore')
            elif filename.endswith('.txt'):
                extracted_text = file_content.decode('utf-8', errors='ignore')
            else:
                extracted_text = f"[Binary file: {filename}]"
            
            # Determine document category
            document_category = self._categorize_document(filename, extracted_text)
            
            # Create document record
            document = Document(
                user_id=uuid.UUID(user_id),
                filename=filename,
                content_type=content_type or "application/octet-stream",
                file_size=len(file_content),
                extracted_text=extracted_text,
                doc_metadata={
                    "file_hash": str(hash(file_content)),
                    "original_size": len(file_content)
                },
                document_category=document_category,
                file_path=f"uploads/{user_id}/{filename}",
                processing_status="completed"
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            return document
            
        except Exception as e:
            db.rollback()
            print(f"Error uploading document: {str(e)}")
            return None
    
    def get_document(self, db: Session, document_id: str, user_id: str) -> Optional[Document]:
        """Get a document by ID for a specific user"""
        return db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
    
    def get_user_documents(self, db: Session, user_id: str, 
                          skip: int = 0, limit: int = 50,
                          category_filter: str = None) -> List[Document]:
        """Get all documents for a user with optional filtering"""
        query = db.query(Document).filter(Document.user_id == user_id)
        
        if category_filter:
            query = query.filter(Document.document_category == category_filter)
        
        return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    def delete_document(self, db: Session, document_id: str, user_id: str) -> bool:
        """Delete a document and all associated data"""
        try:
            document = self.get_document(db, document_id, user_id)
            if not document:
                return False
            
            # Delete from database (cascades to related records)
            db.delete(document)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def create_library(self, db: Session, user_id: str, name: str, 
                      description: str = None, tags: List[str] = None) -> Optional[DocumentLibrary]:
        """Create a new document library"""
        try:
            library = DocumentLibrary(
                user_id=uuid.UUID(user_id),
                name=name,
                description=description,
                tags=tags or []
            )
            
            db.add(library)
            db.commit()
            db.refresh(library)
            
            return library
            
        except Exception as e:
            db.rollback()
            print(f"Error creating library: {str(e)}")
            return None
    
    def get_user_libraries(self, db: Session, user_id: str) -> List[DocumentLibrary]:
        """Get all libraries for a user"""
        return db.query(DocumentLibrary).filter(
            DocumentLibrary.user_id == user_id
        ).order_by(DocumentLibrary.created_at.desc()).all()
    
    def add_document_to_library(self, db: Session, library_id: str, 
                               document_id: str, user_id: str) -> bool:
        """Add a document to a library"""
        try:
            # Verify library belongs to user
            library = db.query(DocumentLibrary).filter(
                DocumentLibrary.id == library_id,
                DocumentLibrary.user_id == user_id
            ).first()
            
            if not library:
                return False
            
            # Verify document belongs to user
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                return False
            
            # Check if already in library
            existing = db.query(LibraryDocument).filter(
                LibraryDocument.library_id == library_id,
                LibraryDocument.document_id == document_id
            ).first()
            
            if existing:
                return True  # Already in library
            
            # Add to library
            library_doc = LibraryDocument(
                library_id=uuid.UUID(library_id),
                document_id=uuid.UUID(document_id)
            )
            
            db.add(library_doc)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error adding document to library: {str(e)}")
            return False
    
    def get_library_documents(self, db: Session, library_id: str, user_id: str) -> List[Document]:
        """Get all documents in a library"""
        # Verify library belongs to user
        library = db.query(DocumentLibrary).filter(
            DocumentLibrary.id == library_id,
            DocumentLibrary.user_id == user_id
        ).first()
        
        if not library:
            return []
        
        # Get documents in library
        documents = db.query(Document).join(
            LibraryDocument, Document.id == LibraryDocument.document_id
        ).filter(
            LibraryDocument.library_id == library_id
        ).order_by(LibraryDocument.added_at.desc()).all()
        
        return documents
    
    def record_processing_history(self, db: Session, document_id: str, 
                                 question: str, answer: str, ai_model: str,
                                 confidence_score: float = None, 
                                 processing_time_ms: int = None) -> Optional[ProcessingHistory]:
        """Record a Q&A interaction in processing history"""
        try:
            history = ProcessingHistory(
                document_id=uuid.UUID(document_id),
                question=question,
                answer=answer,
                ai_model_used=ai_model,
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms,
                processing_metadata={}
            )
            
            db.add(history)
            db.commit()
            db.refresh(history)
            
            return history
            
        except Exception as e:
            db.rollback()
            print(f"Error recording processing history: {str(e)}")
            return None
    
    def get_document_stats(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get document statistics for a user"""
        try:
            total_docs = db.query(Document).filter(Document.user_id == user_id).count()
            
            # Count by category
            category_counts = db.query(
                Document.document_category,
                db.func.count(Document.id)
            ).filter(
                Document.user_id == user_id
            ).group_by(Document.document_category).all()
            
            # Total file size
            total_size = db.query(
                db.func.sum(Document.file_size)
            ).filter(Document.user_id == user_id).scalar() or 0
            
            return {
                "total_documents": total_docs,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "categories": {category: count for category, count in category_counts}
            }
            
        except Exception as e:
            print(f"Error getting document stats: {str(e)}")
            return {}
    
    def search_documents(self, user_id: str, query: str, 
                        filters: Optional[Dict[str, Any]] = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Simple search implementation (placeholder for Elasticsearch)"""
        return {
            "hits": [],
            "total": 0,
            "max_score": 0
        }
    
    def get_similar_documents(self, document_id: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar documents (placeholder)"""
        return []
    
    def _categorize_document(self, filename: str, content: str) -> str:
        """Categorize document based on filename and content"""
        if not filename:
            return "general"
        
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Code files
        code_extensions = ['py', 'js', 'ts', 'java', 'cpp', 'c', 'sh', 'go', 'rs', 'php']
        if file_ext in code_extensions:
            return "code"
        
        # Web files
        web_extensions = ['html', 'css', 'jsx', 'tsx', 'vue', 'svelte']
        if file_ext in web_extensions:
            return "web"
        
        # Data files
        data_extensions = ['json', 'xml', 'csv', 'yaml', 'yml']
        if file_ext in data_extensions:
            return "data"
        
        # Documentation
        doc_extensions = ['md', 'txt', 'rst']
        if file_ext in doc_extensions:
            return "documentation"
        
        # Research/academic
        research_extensions = ['pdf', 'docx', 'tex']
        if file_ext in research_extensions:
            return "research"
        
        # Notebook
        if file_ext == 'ipynb':
            return "notebook"
        
        return "general"

# Global document service instance
document_service = DocumentService()