"""
Memory Configuration
====================
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MemoryConfig:
    """Configuration for memory/history storage"""
    
    # Qdrant connection
    url: str = "http://localhost:6333"
    
    # Collection names
    history_collection: str = "user_history"
    task_collection: str = "task_records"
    context_collection: str = "agent_context"
    
    # Vector dimensions
    vector_dim: int = 384
    
    # Retention settings
    max_history_entries: int = 10000
    max_context_entries: int = 1000
    retention_days: int = 90
    
    # Search settings
    default_top_k: int = 10
    min_similarity_score: float = 0.5
    
    # Timeout
    timeout: float = 5.0

