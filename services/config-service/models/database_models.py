"""
SQLAlchemy ORM models for database tables.

Maps to tables created in 02-config-schema.sql.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Create base class for all models using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    pass


class ConfigurationDB(Base):
    """SQLAlchemy model for configurations table."""
    __tablename__ = "configurations"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Configuration data
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    environment = Column(String(50), nullable=False)
    service_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    history = relationship("ConfigurationHistoryDB", back_populates="configuration", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        {"mysql_charset": "utf8mb4"} if hasattr(Base, '__table_args__') else ()
    )
    
    def __repr__(self):
        return f"<ConfigurationDB(id={self.id}, key={self.key}, environment={self.environment})>"


class FeatureFlagDB(Base):
    """SQLAlchemy model for feature_flags table."""
    __tablename__ = "feature_flags"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Feature flag data
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Numeric(5, 2), default=0.00)
    target_users = Column(ARRAY(String), nullable=True)
    environment = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FeatureFlagDB(id={self.id}, name={self.name}, is_enabled={self.is_enabled})>"


class ServiceRegistryDB(Base):
    """SQLAlchemy model for service_registry table."""
    __tablename__ = "service_registry"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Service data
    service_name = Column(String(100), unique=True, nullable=False)
    service_url = Column(String(255), nullable=False)
    health_check_url = Column(String(255), nullable=True)
    status = Column(String(20), default='unknown')
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    service_metadata = Column('metadata', JSONB, nullable=True)
    
    # Timestamps
    registered_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ServiceRegistryDB(id={self.id}, service_name={self.service_name}, status={self.status})>"


class ConfigurationHistoryDB(Base):
    """SQLAlchemy model for configuration_history table."""
    __tablename__ = "configuration_history"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    configuration_id = Column(Integer, ForeignKey("configurations.id", ondelete="CASCADE"), nullable=False)
    
    # History data
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String(100), nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    configuration = relationship("ConfigurationDB", back_populates="history")
    
    def __repr__(self):
        return f"<ConfigurationHistoryDB(id={self.id}, configuration_id={self.configuration_id}, changed_at={self.changed_at})>"

