"""
JoinFlow Memory - User History and Memory Management
==================================================

Provides persistent storage for:
- User conversation history
- Task execution records
- Agent learning and context
- Long-term memory and knowledge
"""

# Long-term Memory (SQLite-based, no external dependencies)
from .long_term_memory import (
    LongTermMemoryStore,
    Memory,
    MemoryType,
    MemoryPriority,
    UserPreference,
    get_memory_store
)

from .config import MemoryConfig

# History Store (requires qdrant_client, optional)
try:
    from .history import HistoryStore, ConversationEntry, TaskRecord
    _HAS_HISTORY = True
except ImportError:
    HistoryStore = None
    ConversationEntry = None
    TaskRecord = None
    _HAS_HISTORY = False

__all__ = [
    # Long-term Memory (always available)
    "LongTermMemoryStore",
    "Memory",
    "MemoryType",
    "MemoryPriority",
    "UserPreference",
    "get_memory_store",
    # Config
    "MemoryConfig",
    # History (optional)
    "HistoryStore",
    "ConversationEntry", 
    "TaskRecord",
]

