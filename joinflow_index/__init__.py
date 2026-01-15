"""
joinflow-index

Vector indexing layer for JoinFlow.

This module provides production-grade vector search
backed by Qdrant (Rust HNSW), exposed through stable
JoinFlow contracts.
"""

from .qdrant_store import QdrantVectorStore
from .config import QdrantConfig

__all__ = [
    "QdrantVectorStore",
    "QdrantConfig",
]
