"""
Qdrant Service Manager
======================

Centralized management for Qdrant vector database service.
Handles connection, health checks, query caching, and token optimization.
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status enum"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    INITIALIZING = "initializing"


@dataclass
class QdrantConfig:
    """Qdrant connection configuration"""
    url: str = field(default_factory=lambda: os.environ.get("QDRANT_URL", "http://localhost:6333"))
    api_key: Optional[str] = field(default_factory=lambda: os.environ.get("QDRANT_API_KEY"))
    timeout: float = 5.0
    prefer_grpc: bool = False
    
    # Collection names
    knowledge_collection: str = "joinflow_knowledge"
    history_collection: str = "joinflow_history"
    tasks_collection: str = "joinflow_tasks"
    cache_collection: str = "joinflow_llm_cache"
    
    # Vector dimensions
    vector_dim: int = 384  # all-MiniLM-L6-v2 default
    
    # Cache settings
    cache_enabled: bool = True
    cache_similarity_threshold: float = 0.95  # High threshold for cache hits
    cache_ttl_hours: int = 24 * 7  # 7 days default


@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_queries: int = 0
    cache_hits: int = 0
    tokens_saved: int = 0
    estimated_cost: float = 0.0
    
    def add(self, prompt: int, completion: int, from_cache: bool = False):
        """Add token usage"""
        if from_cache:
            self.cache_hits += 1
            self.tokens_saved += prompt + completion
        else:
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.total_tokens += prompt + completion
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CachedResponse:
    """Cached LLM response"""
    query_hash: str
    query_text: str
    response_text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "CachedResponse":
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('expires_at'), str) and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class QdrantServiceManager:
    """
    Centralized Qdrant service manager.
    
    Features:
    - Connection management with automatic reconnection
    - Health monitoring
    - LLM query caching to reduce token consumption
    - Token usage tracking and statistics
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config: QdrantConfig = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: QdrantConfig = None):
        if self._initialized:
            return
        
        self.config = config or QdrantConfig()
        self._client = None
        self._embedder = None
        self._status = ServiceStatus.INITIALIZING
        self._last_health_check = None
        self._health_check_interval = 30  # seconds
        
        # Token tracking
        self._token_usage = TokenUsage()
        self._session_start = datetime.now()
        
        # Initialize connection
        self._connect()
        self._initialized = True
    
    # ==========================================
    # Connection Management
    # ==========================================
    
    def _connect(self) -> bool:
        """Establish connection to Qdrant server"""
        try:
            from qdrant_client import QdrantClient
            
            logger.info(f"Connecting to Qdrant at {self.config.url}...")
            
            self._client = QdrantClient(
                url=self.config.url,
                api_key=self.config.api_key,
                timeout=self.config.timeout,
                prefer_grpc=self.config.prefer_grpc
            )
            
            # Test connection
            self._client.get_collections()
            
            self._status = ServiceStatus.CONNECTED
            self._ensure_collections()
            
            logger.info("✅ Qdrant connection established")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Qdrant connection failed: {e}")
            self._status = ServiceStatus.DISCONNECTED
            
            # Fall back to in-memory mode
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(":memory:")
                self._status = ServiceStatus.DEGRADED
                self._ensure_collections()
                logger.info("Using in-memory Qdrant (data not persistent)")
                return True
            except Exception:
                return False
    
    def _ensure_collections(self):
        """Ensure all required collections exist"""
        if not self._client:
            return
        
        from qdrant_client.models import VectorParams, Distance
        
        existing = {c.name for c in self._client.get_collections().collections}
        
        collections = [
            self.config.knowledge_collection,
            self.config.history_collection,
            self.config.tasks_collection,
            self.config.cache_collection,
        ]
        
        for collection in collections:
            if collection not in existing:
                self._client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=self.config.vector_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {collection}")
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to Qdrant"""
        self._status = ServiceStatus.INITIALIZING
        return self._connect()
    
    @property
    def client(self):
        """Get Qdrant client"""
        if not self._client or self._status == ServiceStatus.DISCONNECTED:
            self._connect()
        return self._client
    
    @property
    def status(self) -> ServiceStatus:
        """Get current service status"""
        return self._status
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Qdrant server (not in-memory)"""
        return self._status == ServiceStatus.CONNECTED
    
    @property
    def is_available(self) -> bool:
        """Check if Qdrant is available (including in-memory)"""
        return self._status in [ServiceStatus.CONNECTED, ServiceStatus.DEGRADED]
    
    # ==========================================
    # Health Check
    # ==========================================
    
    def health_check(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform health check on Qdrant service.
        
        Args:
            force: Force check even if recent check exists
            
        Returns:
            Health status dictionary
        """
        now = datetime.now()
        
        # Use cached result if recent
        if not force and self._last_health_check:
            elapsed = (now - self._last_health_check).total_seconds()
            if elapsed < self._health_check_interval:
                return self._get_health_response()
        
        self._last_health_check = now
        
        try:
            if not self._client:
                self._connect()
            
            # Get collections info
            collections = self._client.get_collections().collections
            collection_info = {}
            
            for col in collections:
                try:
                    info = self._client.get_collection(col.name)
                    collection_info[col.name] = {
                        "vectors_count": info.vectors_count,
                        "points_count": info.points_count,
                        "status": info.status.value if hasattr(info.status, 'value') else str(info.status)
                    }
                except Exception:
                    collection_info[col.name] = {"status": "unknown"}
            
            # Update status
            if self._status == ServiceStatus.DEGRADED:
                pass  # Keep degraded status
            else:
                self._status = ServiceStatus.CONNECTED
            
            return self._get_health_response(collection_info)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._status = ServiceStatus.DISCONNECTED
            return self._get_health_response(error=str(e))
    
    def _get_health_response(self, collections: Dict = None, error: str = None) -> Dict:
        """Build health response"""
        return {
            "status": self._status.value,
            "url": self.config.url,
            "connected": self.is_connected,
            "available": self.is_available,
            "in_memory_mode": self._status == ServiceStatus.DEGRADED,
            "collections": collections or {},
            "error": error,
            "last_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "token_usage": self._token_usage.to_dict()
        }
    
    # ==========================================
    # Embedder Management
    # ==========================================
    
    def set_embedder(self, embedder):
        """Set the embedder for vector operations"""
        self._embedder = embedder
    
    def get_embedder(self):
        """Get or create embedder"""
        if not self._embedder:
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer("all-MiniLM-L6-v2")
                
                class Embedder:
                    def __init__(self, model):
                        self._model = model
                    
                    def embed(self, text: str) -> List[float]:
                        return self._model.encode(text).tolist()
                    
                    def embed_batch(self, texts: List[str]) -> List[List[float]]:
                        return self._model.encode(texts).tolist()
                
                self._embedder = Embedder(model)
                logger.info("Created default embedder (all-MiniLM-L6-v2)")
            except ImportError:
                logger.warning("sentence-transformers not installed")
                return None
        
        return self._embedder
    
    # ==========================================
    # LLM Query Cache (Token Optimization)
    # ==========================================
    
    def _hash_query(self, query: str, model: str = "") -> str:
        """Generate hash for query"""
        content = f"{model}:{query}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()[:16]
    
    def get_cached_response(
        self,
        query: str,
        model: str = "",
        similarity_threshold: float = None
    ) -> Optional[Tuple[str, int]]:
        """
        Check if a similar query exists in cache.
        
        This is the KEY feature for reducing token consumption.
        If a very similar query was asked before, return the cached response
        instead of calling the LLM again.
        
        Args:
            query: The query text
            model: Model identifier
            similarity_threshold: Minimum similarity for cache hit
            
        Returns:
            Tuple of (cached_response, tokens_saved) or None
        """
        if not self.config.cache_enabled or not self.is_available:
            return None
        
        embedder = self.get_embedder()
        if not embedder:
            return None
        
        threshold = similarity_threshold or self.config.cache_similarity_threshold
        
        try:
            # Embed the query
            query_vector = embedder.embed(query)
            
            # Search for similar queries
            results = self._search_collection(
                collection=self.config.cache_collection,
                query_vector=query_vector,
                top_k=1
            )
            
            if not results:
                return None
            
            hit = results[0]
            similarity = hit.score
            
            # Check if similarity is above threshold
            if similarity >= threshold:
                payload = hit.payload
                
                # Check expiration
                if payload.get('expires_at'):
                    expires = datetime.fromisoformat(payload['expires_at'])
                    if datetime.now() > expires:
                        return None
                
                # Update hit count
                self._update_cache_hit_count(hit.id)
                
                tokens_saved = payload.get('prompt_tokens', 0) + payload.get('completion_tokens', 0)
                
                logger.info(f"🎯 Cache hit! Similarity: {similarity:.3f}, Tokens saved: {tokens_saved}")
                self._token_usage.add(
                    payload.get('prompt_tokens', 0),
                    payload.get('completion_tokens', 0),
                    from_cache=True
                )
                
                return (payload.get('response_text', ''), tokens_saved)
            
            return None
            
        except Exception as e:
            logger.debug(f"Cache lookup error: {e}")
            return None
    
    def cache_response(
        self,
        query: str,
        response: str,
        model: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        ttl_hours: int = None
    ) -> bool:
        """
        Cache an LLM response for future similar queries.
        
        Args:
            query: Original query
            response: LLM response
            model: Model identifier
            prompt_tokens: Tokens used in prompt
            completion_tokens: Tokens in completion
            ttl_hours: Time to live in hours
            
        Returns:
            Success status
        """
        if not self.config.cache_enabled or not self.is_available:
            return False
        
        embedder = self.get_embedder()
        if not embedder:
            return False
        
        try:
            query_hash = self._hash_query(query, model)
            query_vector = embedder.embed(query)
            
            ttl = ttl_hours or self.config.cache_ttl_hours
            expires_at = datetime.now() + timedelta(hours=ttl)
            
            cached = CachedResponse(
                query_hash=query_hash,
                query_text=query[:1000],  # Truncate long queries
                response_text=response,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                expires_at=expires_at
            )
            
            from qdrant_client.models import PointStruct
            
            self._client.upsert(
                collection_name=self.config.cache_collection,
                points=[
                    PointStruct(
                        id=query_hash,
                        vector=query_vector,
                        payload=cached.to_dict()
                    )
                ]
            )
            
            # Track token usage
            self._token_usage.add(prompt_tokens, completion_tokens, from_cache=False)
            self._token_usage.cached_queries += 1
            
            logger.debug(f"Cached response for query: {query[:50]}...")
            return True
            
        except Exception as e:
            logger.debug(f"Cache store error: {e}")
            return False
    
    def _update_cache_hit_count(self, point_id: str):
        """Update hit count for cached response"""
        try:
            # Retrieve current payload
            results = self._client.retrieve(
                collection_name=self.config.cache_collection,
                ids=[point_id],
                with_vectors=True
            )
            
            if results:
                point = results[0]
                payload = point.payload
                payload['hit_count'] = payload.get('hit_count', 0) + 1
                
                from qdrant_client.models import PointStruct
                
                self._client.upsert(
                    collection_name=self.config.cache_collection,
                    points=[
                        PointStruct(
                            id=point_id,
                            vector=point.vector,
                            payload=payload
                        )
                    ]
                )
        except Exception:
            pass
    
    def clear_cache(self, older_than_days: int = None) -> int:
        """
        Clear expired or old cache entries.
        
        Args:
            older_than_days: Clear entries older than this many days
            
        Returns:
            Number of entries cleared
        """
        if not self.is_available:
            return 0
        
        try:
            # Get all cache entries
            results, _ = self._client.scroll(
                collection_name=self.config.cache_collection,
                limit=10000,
                with_vectors=False
            )
            
            now = datetime.now()
            ids_to_delete = []
            
            for point in results:
                should_delete = False
                payload = point.payload
                
                # Check expiration
                if payload.get('expires_at'):
                    expires = datetime.fromisoformat(payload['expires_at'])
                    if now > expires:
                        should_delete = True
                
                # Check age
                if older_than_days and payload.get('created_at'):
                    created = datetime.fromisoformat(payload['created_at'])
                    age = (now - created).days
                    if age > older_than_days:
                        should_delete = True
                
                if should_delete:
                    ids_to_delete.append(point.id)
            
            if ids_to_delete:
                self._client.delete(
                    collection_name=self.config.cache_collection,
                    points_selector=ids_to_delete
                )
                logger.info(f"Cleared {len(ids_to_delete)} cache entries")
            
            return len(ids_to_delete)
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    # ==========================================
    # Token Usage Statistics
    # ==========================================
    
    def get_token_stats(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        usage = self._token_usage
        
        # Calculate savings
        total_with_cache = usage.total_tokens + usage.tokens_saved
        savings_percent = (usage.tokens_saved / total_with_cache * 100) if total_with_cache > 0 else 0
        
        # Estimate cost (GPT-4 pricing as reference)
        prompt_cost = usage.prompt_tokens * 0.00003  # $0.03 per 1K
        completion_cost = usage.completion_tokens * 0.00006  # $0.06 per 1K
        usage.estimated_cost = prompt_cost + completion_cost
        
        return {
            "session_start": self._session_start.isoformat(),
            "duration_minutes": (datetime.now() - self._session_start).total_seconds() / 60,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cached_queries": usage.cached_queries,
            "cache_hits": usage.cache_hits,
            "cache_hit_rate": f"{(usage.cache_hits / (usage.cached_queries + usage.cache_hits) * 100):.1f}%" if (usage.cached_queries + usage.cache_hits) > 0 else "0%",
            "tokens_saved": usage.tokens_saved,
            "savings_percent": f"{savings_percent:.1f}%",
            "estimated_cost_usd": f"${usage.estimated_cost:.4f}",
            "estimated_savings_usd": f"${usage.tokens_saved * 0.00004:.4f}"
        }
    
    def reset_token_stats(self):
        """Reset token usage statistics"""
        self._token_usage = TokenUsage()
        self._session_start = datetime.now()
    
    # ==========================================
    # Internal Helpers
    # ==========================================
    
    def _search_collection(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filters = None
    ) -> List:
        """Execute search on a collection"""
        if not self._client:
            return []
        
        try:
            if hasattr(self._client, "query_points"):
                result = self._client.query_points(
                    collection_name=collection,
                    query=query_vector,
                    limit=top_k,
                    query_filter=filters
                )
                return result.points
            elif hasattr(self._client, "search"):
                return self._client.search(
                    collection_name=collection,
                    query_vector=query_vector,
                    limit=top_k,
                    query_filter=filters
                )
            else:
                return []
        except Exception as e:
            logger.debug(f"Search error: {e}")
            return []


# Global instance getter
def get_qdrant_service(config: QdrantConfig = None) -> QdrantServiceManager:
    """Get the global Qdrant service manager instance"""
    return QdrantServiceManager(config)

