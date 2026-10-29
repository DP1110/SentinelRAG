import datetime
import json
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Float,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")


class Group(Base):
    __tablename__ = "groups"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    source = Column(String(64), default="local")
    source_id = Column(String(255), nullable=True)

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(64), ForeignKey("groups.id"), nullable=False)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="group_memberships")
    group = relationship("Group", back_populates="members")


class Connector(Base):
    __tablename__ = "connectors"

    id = Column(String(64), primary_key=True)
    type = Column(String(64), nullable=False)  # 'gdrive', 'github', 'slack'
    name = Column(String(255), nullable=False)
    config = Column(JSON, default=dict)
    status = Column(String(32), default="active")
    last_sync_at = Column(DateTime, nullable=True)

    documents = relationship("Document", back_populates="connector", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True)
    connector_id = Column(String(64), ForeignKey("connectors.id"), nullable=False)
    source_id = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=True)
    path = Column(String(1024), nullable=True)
    version = Column(String(32), default="1.0")
    content_hash = Column(String(64), nullable=False)
    sensitivity = Column(String(32), default="internal")  # 'public', 'internal', 'confidential', 'restricted'
    is_active = Column(Boolean, default=True, index=True)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)

    connector = relationship("Connector", back_populates="documents")
    acls = relationship("DocumentACL", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class DocumentACL(Base):
    __tablename__ = "document_acl"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    principal_type = Column(String(32), nullable=False)  # 'user', 'group', 'domain', 'public'
    principal_id = Column(String(255), nullable=False, index=True)
    role = Column(String(32), default="reader")  # 'reader', 'writer', 'owner'

    document = relationship("Document", back_populates="acls")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    ordinal = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # JSON-serialized list of floats (384-d)
    tsv = Column(Text, nullable=True)  # Normalized text for full-text search
    metadata_json = Column(JSON, default=dict)
    allowed_principals = Column(JSON, default=list, nullable=False)  # e.g. ["user:alice", "group:eng", "public"]
    risk_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True, index=True)
    index_version = Column(String(32), default="v1.0")

    document = relationship("Document", back_populates="chunks")


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connector_id = Column(String(64), ForeignKey("connectors.id"), nullable=False)
    event_type = Column(String(32), nullable=False)  # 'create', 'update', 'delete', 'acl_change'
    document_id = Column(String(64), nullable=True)
    status = Column(String(32), default="success")  # 'success', 'failed'
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    query = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=True)
    retrieved_ids = Column(JSON, default=list)  # list of chunk IDs
    removed_ids = Column(JSON, default=list)  # list of chunk IDs removed by answer-time check
    model = Column(String(64), nullable=False)
    latency_ms = Column(Float, default=0.0)
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(String(64), primary_key=True)
    config_json = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    summary_json = Column(JSON, default=dict)
