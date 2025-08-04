"""
Database models and schema definitions for the Advanced Document Intelligence Platform
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Integer, Float, ForeignKey, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import os

Base = declarative_base()

class User(Base):
    """User model for authentication and document ownership"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    preferences = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    libraries = relationship("DocumentLibrary", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    """Document model for storing uploaded files and metadata"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(BIGINT, nullable=False)
    extracted_text = Column(Text)
    metadata = Column(JSONB, default={})
    document_category = Column(String(50))  # code, documentation, research, etc.
    file_path = Column(String(500))  # Path to stored file
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    processing_history = relationship("ProcessingHistory", back_populates="document", cascade="all, delete-orphan")
    library_documents = relationship("LibraryDocument", back_populates="document", cascade="all, delete-orphan")

class DocumentLibrary(Base):
    """Document library model for organizing documents into collections"""
    __tablename__ = "document_libraries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_shared = Column(Boolean, default=False)
    tags = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="libraries")
    library_documents = relationship("LibraryDocument", back_populates="library", cascade="all, delete-orphan")

class LibraryDocument(Base):
    """Junction table for many-to-many relationship between libraries and documents"""
    __tablename__ = "library_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    library_id = Column(UUID(as_uuid=True), ForeignKey("document_libraries.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    library = relationship("DocumentLibrary", back_populates="library_documents")
    document = relationship("Document", back_populates="library_documents")

class ProcessingHistory(Base):
    """Processing history model for storing Q&A interactions"""
    __tablename__ = "processing_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    ai_model_used = Column(String(100))
    confidence_score = Column(Float)
    processing_time_ms = Column(Integer)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="processing_history")

class ModelPerformance(Base):
    """Model performance tracking for smart recommendations"""
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(String(100), nullable=False)
    document_category = Column(String(50))
    success_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    avg_processing_time_ms = Column(Float)
    avg_confidence_score = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/document_intelligence")

# Create engine and session
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")