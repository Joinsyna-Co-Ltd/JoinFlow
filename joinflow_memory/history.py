"""
User History Storage
====================

Stores user interactions, conversations, and task records
in a vector database for semantic retrieval.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, Sequence
import uuid
import json
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

from joinflow_core.protocols import Embedder
from joinflow_core.validators import validate_vector
from .config import MemoryConfig

logger = logging.getLogger(__name__)


@dataclass
class ConversationEntry:
    """A single conversation entry"""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    session_id: str = ""
    
    # Content
    role: str = "user"  # "user", "assistant", "system"
    content: str = ""
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    agent_type: Optional[str] = None
    task_id: Optional[str] = None
    
    # Additional context
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConversationEntry":
        """Create from dictionary"""
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class TaskRecord:
    """Record of a completed task"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    
    # Task info
    task_description: str = ""
    task_type: str = ""  # "browser", "llm", "os", "rag", "multi"
    
    # Execution details
    status: str = "completed"  # "completed", "failed", "cancelled"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # Results
    result_summary: str = ""
    output_data: Optional[Any] = None
    
    # Agents involved
    agents_used: list[str] = field(default_factory=list)
    actions_count: int = 0
    
    # Cost tracking
    tokens_used: int = 0
    estimated_cost: float = 0.0
    
    # Error info
    error: Optional[str] = None
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "TaskRecord":
        """Create from dictionary"""
        if isinstance(data.get('start_time'), str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if isinstance(data.get('end_time'), str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


class HistoryStore:
    """
    Vector-based storage for user history and task records.
    
    Enables semantic search over past interactions for:
    - Context retrieval
    - Similar task lookup
    - User preference learning
    """
    
    def __init__(
        self,
        embedder: Embedder,
        config: Optional[MemoryConfig] = None,
        client: Optional[QdrantClient] = None
    ):
        self.embedder = embedder
        self.config = config or MemoryConfig()
        
        if client:
            self.client = client
        else:
            self.client = QdrantClient(
                url=self.config.url,
                timeout=self.config.timeout
            )
        
        self._ensure_collections()
    
    def _ensure_collections(self) -> None:
        """Ensure required collections exist"""
        collections = {c.name for c in self.client.get_collections().collections}
        
        # Create history collection
        if self.config.history_collection not in collections:
            self.client.create_collection(
                collection_name=self.config.history_collection,
                vectors_config=VectorParams(
                    size=self.config.vector_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.config.history_collection}")
        
        # Create task collection
        if self.config.task_collection not in collections:
            self.client.create_collection(
                collection_name=self.config.task_collection,
                vectors_config=VectorParams(
                    size=self.config.vector_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.config.task_collection}")
    
    # -------------------------
    # Conversation History
    # -------------------------
    
    def add_conversation(self, entry: ConversationEntry) -> str:
        """
        Add a conversation entry to history.
        
        Args:
            entry: The conversation entry to store
            
        Returns:
            The entry ID
        """
        # Generate embedding from content
        vector = self.embedder.embed(entry.content)
        validate_vector(vector)
        
        # Store in Qdrant
        self.client.upsert(
            collection_name=self.config.history_collection,
            points=[
                PointStruct(
                    id=entry.entry_id,
                    vector=vector,
                    payload=entry.to_dict()
                )
            ]
        )
        
        logger.debug(f"Added conversation entry: {entry.entry_id}")
        return entry.entry_id
    
    def add_message(
        self,
        content: str,
        role: str = "user",
        user_id: str = "default",
        session_id: str = "",
        **metadata
    ) -> str:
        """
        Convenience method to add a message.
        
        Args:
            content: Message content
            role: Role (user/assistant/system)
            user_id: User identifier
            session_id: Session identifier
            **metadata: Additional metadata
            
        Returns:
            Entry ID
        """
        entry = ConversationEntry(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata
        )
        return self.add_conversation(entry)
    
    def search_history(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        role: Optional[str] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None
    ) -> list[tuple[ConversationEntry, float]]:
        """
        Search conversation history semantically.
        
        Args:
            query: Search query
            user_id: Filter by user
            session_id: Filter by session
            role: Filter by role
            top_k: Number of results
            min_score: Minimum similarity score
            
        Returns:
            List of (entry, score) tuples
        """
        top_k = top_k or self.config.default_top_k
        min_score = min_score or self.config.min_similarity_score
        
        # Build filter
        filter_conditions = []
        if user_id:
            filter_conditions.append(
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            )
        if session_id:
            filter_conditions.append(
                FieldCondition(key="session_id", match=MatchValue(value=session_id))
            )
        if role:
            filter_conditions.append(
                FieldCondition(key="role", match=MatchValue(value=role))
            )
        
        query_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        # Embed query
        query_vector = self.embedder.embed(query)
        
        # Search
        results = self._search_collection(
            collection=self.config.history_collection,
            query_vector=query_vector,
            query_filter=query_filter,
            top_k=top_k
        )
        
        # Filter by score and convert
        entries = []
        for hit in results:
            if hit.score >= min_score:
                entry = ConversationEntry.from_dict(hit.payload)
                entries.append((entry, hit.score))
        
        return entries
    
    def get_recent_history(
        self,
        user_id: str = "default",
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> list[ConversationEntry]:
        """
        Get recent conversation history (non-semantic).
        
        Args:
            user_id: User identifier
            session_id: Optional session filter
            limit: Maximum entries to return
            
        Returns:
            List of entries sorted by time (newest first)
        """
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
        if session_id:
            filter_conditions.append(
                FieldCondition(key="session_id", match=MatchValue(value=session_id))
            )
        
        # Scroll through all matching entries
        results, _ = self.client.scroll(
            collection_name=self.config.history_collection,
            scroll_filter=Filter(must=filter_conditions),
            limit=limit,
            with_vectors=False
        )
        
        entries = [ConversationEntry.from_dict(r.payload) for r in results]
        # Sort by timestamp descending
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        
        return entries[:limit]
    
    # -------------------------
    # Task Records
    # -------------------------
    
    def add_task(self, task: TaskRecord) -> str:
        """
        Add a task record.
        
        Args:
            task: The task record to store
            
        Returns:
            Task ID
        """
        # Generate embedding from task description
        vector = self.embedder.embed(task.task_description)
        validate_vector(vector)
        
        self.client.upsert(
            collection_name=self.config.task_collection,
            points=[
                PointStruct(
                    id=task.task_id,
                    vector=vector,
                    payload=task.to_dict()
                )
            ]
        )
        
        logger.debug(f"Added task record: {task.task_id}")
        return task.task_id
    
    def search_similar_tasks(
        self,
        query: str,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        top_k: int = 5
    ) -> list[tuple[TaskRecord, float]]:
        """
        Search for similar past tasks.
        
        Useful for:
        - Finding how similar tasks were handled
        - Learning from past successes/failures
        
        Args:
            query: Task description to search for
            user_id: Filter by user
            task_type: Filter by task type
            status: Filter by status
            top_k: Number of results
            
        Returns:
            List of (task, score) tuples
        """
        filter_conditions = []
        if user_id:
            filter_conditions.append(
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            )
        if task_type:
            filter_conditions.append(
                FieldCondition(key="task_type", match=MatchValue(value=task_type))
            )
        if status:
            filter_conditions.append(
                FieldCondition(key="status", match=MatchValue(value=status))
            )
        
        query_filter = Filter(must=filter_conditions) if filter_conditions else None
        query_vector = self.embedder.embed(query)
        
        results = self._search_collection(
            collection=self.config.task_collection,
            query_vector=query_vector,
            query_filter=query_filter,
            top_k=top_k
        )
        
        tasks = []
        for hit in results:
            task = TaskRecord.from_dict(hit.payload)
            tasks.append((task, hit.score))
        
        return tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[TaskRecord]:
        """Get a specific task by ID"""
        try:
            results = self.client.retrieve(
                collection_name=self.config.task_collection,
                ids=[task_id]
            )
            if results:
                return TaskRecord.from_dict(results[0].payload)
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {e}")
        return None
    
    # -------------------------
    # Context Management
    # -------------------------
    
    def get_relevant_context(
        self,
        query: str,
        user_id: str = "default",
        include_history: bool = True,
        include_tasks: bool = True,
        max_entries: int = 10
    ) -> dict[str, Any]:
        """
        Get relevant context for a new task.
        
        Combines history and past tasks to provide context.
        
        Args:
            query: Current task/question
            user_id: User identifier
            include_history: Include conversation history
            include_tasks: Include past task records
            max_entries: Max entries per category
            
        Returns:
            Dictionary with relevant context
        """
        context = {
            "query": query,
            "user_id": user_id,
            "history": [],
            "similar_tasks": [],
            "recent_messages": []
        }
        
        if include_history:
            # Semantic search in history
            history_results = self.search_history(
                query=query,
                user_id=user_id,
                top_k=max_entries
            )
            context["history"] = [
                {"content": e.content, "role": e.role, "score": s}
                for e, s in history_results
            ]
            
            # Recent messages
            recent = self.get_recent_history(user_id=user_id, limit=5)
            context["recent_messages"] = [
                {"content": e.content, "role": e.role}
                for e in recent
            ]
        
        if include_tasks:
            task_results = self.search_similar_tasks(
                query=query,
                user_id=user_id,
                status="completed",
                top_k=max_entries
            )
            context["similar_tasks"] = [
                {
                    "description": t.task_description,
                    "result": t.result_summary,
                    "agents": t.agents_used,
                    "score": s
                }
                for t, s in task_results
            ]
        
        return context
    
    # -------------------------
    # Internal Methods
    # -------------------------
    
    def _search_collection(
        self,
        collection: str,
        query_vector: Sequence[float],
        query_filter: Optional[Filter],
        top_k: int
    ) -> list:
        """Execute search on a collection with API compatibility"""
        if hasattr(self.client, "query_points"):
            result = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter
            )
            return result.points
        elif hasattr(self.client, "search"):
            return self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter
            )
        else:
            raise RuntimeError("Unsupported qdrant-client version")
    
    # -------------------------
    # Cleanup
    # -------------------------
    
    def clear_user_history(self, user_id: str) -> int:
        """
        Clear all history for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of entries deleted
        """
        # Get all entries for user
        results, _ = self.client.scroll(
            collection_name=self.config.history_collection,
            scroll_filter=Filter(must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            ]),
            limit=10000
        )
        
        if results:
            ids = [r.id for r in results]
            self.client.delete(
                collection_name=self.config.history_collection,
                points_selector=ids
            )
            logger.info(f"Cleared {len(ids)} history entries for user {user_id}")
            return len(ids)
        
        return 0

