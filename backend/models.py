from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, index=True, nullable=False)
    file_type = Column(String(10), nullable=False)  # 'image' or 'text'
    original_filename = Column(String(255), nullable=False)
    cloudinary_url = Column(Text, nullable=False)
    groq_response = Column(Text, nullable=False)
    audit_result = Column(JSON, nullable=True)  # Store audit results
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AuditPolicy(Base):
    __tablename__ = "audit_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)  # 'required_field', 'amount_limit', 'date_range', 'format_check', 'content_warning'
    field_name = Column(String(100), nullable=False)  # 'invoice_number', 'amount', 'date', 'vendor_name', 'content'
    condition = Column(String(50), nullable=False)  # 'exists', 'max_value', 'min_value', 'format_match', 'contains_keywords'
    expected_value = Column(String(500), nullable=True)  # Expected value or pattern
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'warning'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditRule(Base):
    __tablename__ = "audit_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    max_limit = Column(Float, nullable=False)
    is_restricted = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())