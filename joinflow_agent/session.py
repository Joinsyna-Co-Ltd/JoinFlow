"""
Session Manager
===============

Manages user sessions and conversation context:
- Session creation and management
- Multi-user support
- Conversation history per session
- Session persistence
"""

import uuid
import json
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in a conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class Session:
    """User session with conversation history"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Conversation
    messages: List[Message] = field(default_factory=list)
    system_prompt: Optional[str] = None
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    total_tokens: int = 0
    message_count: int = 0
    
    def add_message(self, role: str, content: str, **metadata) -> Message:
        """Add a message to the session"""
        msg = Message(role=role, content=content, metadata=metadata)
        self.messages.append(msg)
        self.message_count += 1
        self.updated_at = datetime.now()
        return msg
    
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get messages, optionally limited"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_context_messages(self, max_messages: int = 20) -> List[dict]:
        """Get messages formatted for LLM context"""
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        for msg in self.messages[-max_messages:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        return messages
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a session variable"""
        self.variables[key] = value
        self.updated_at = datetime.now()
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a session variable"""
        return self.variables.get(key, default)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "messages": [m.to_dict() for m in self.messages],
            "system_prompt": self.system_prompt,
            "context": self.context,
            "variables": self.variables,
            "metadata": self.metadata,
            "total_tokens": self.total_tokens,
            "message_count": self.message_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        messages = [Message.from_dict(m) for m in data.pop("messages", [])]
        
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("expires_at") and isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        
        session = cls(**data)
        session.messages = messages
        return session


class SessionManager:
    """
    Manages multiple user sessions.
    
    Features:
    - Create, get, delete sessions
    - Session expiration
    - Persistence to disk
    - Thread-safe operations
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        session_timeout_hours: int = 24,
        max_sessions_per_user: int = 10
    ):
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self._lock = threading.RLock()
        
        self._storage_path = Path(storage_path) if storage_path else None
        self._session_timeout = timedelta(hours=session_timeout_hours)
        self._max_sessions_per_user = max_sessions_per_user
        
        if self._storage_path:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            self._load_sessions()
    
    def create_session(
        self,
        user_id: str = "default",
        system_prompt: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Session:
        """Create a new session"""
        with self._lock:
            # Check user session limit
            user_sessions = self._user_sessions.get(user_id, [])
            if len(user_sessions) >= self._max_sessions_per_user:
                # Remove oldest session
                oldest_id = user_sessions[0]
                self.delete_session(oldest_id)
            
            session = Session(
                user_id=user_id,
                system_prompt=system_prompt,
                expires_at=datetime.now() + self._session_timeout,
                metadata=metadata or {}
            )
            
            self._sessions[session.id] = session
            
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(session.id)
            
            self._save_session(session)
            
            logger.info(f"Created session {session.id} for user {user_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        with self._lock:
            session = self._sessions.get(session_id)
            
            if session and session.is_expired():
                self.delete_session(session_id)
                return None
            
            return session
    
    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: str = "default",
        **kwargs
    ) -> Session:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session(user_id=user_id, **kwargs)
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user"""
        with self._lock:
            session_ids = self._user_sessions.get(user_id, [])
            sessions = []
            
            for sid in session_ids:
                session = self.get_session(sid)
                if session:
                    sessions.append(session)
            
            return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        with self._lock:
            session = self._sessions.pop(session_id, None)
            
            if session:
                user_id = session.user_id
                if user_id in self._user_sessions:
                    self._user_sessions[user_id] = [
                        sid for sid in self._user_sessions[user_id]
                        if sid != session_id
                    ]
                
                # Remove from storage
                if self._storage_path:
                    session_file = self._storage_path / f"{session_id}.json"
                    if session_file.exists():
                        session_file.unlink()
                
                logger.info(f"Deleted session {session_id}")
                return True
            
            return False
    
    def update_session(self, session: Session) -> None:
        """Update and persist session"""
        with self._lock:
            session.updated_at = datetime.now()
            self._sessions[session.id] = session
            self._save_session(session)
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        with self._lock:
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if session.is_expired()
            ]
            
            for sid in expired_ids:
                self.delete_session(sid)
            
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
            return len(expired_ids)
    
    def _save_session(self, session: Session) -> None:
        """Save session to disk"""
        if not self._storage_path:
            return
        
        try:
            session_file = self._storage_path / f"{session.id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session {session.id}: {e}")
    
    def _load_sessions(self) -> None:
        """Load sessions from disk"""
        if not self._storage_path:
            return
        
        try:
            for session_file in self._storage_path.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    session = Session.from_dict(data)
                    
                    if not session.is_expired():
                        self._sessions[session.id] = session
                        
                        if session.user_id not in self._user_sessions:
                            self._user_sessions[session.user_id] = []
                        self._user_sessions[session.user_id].append(session.id)
                    else:
                        session_file.unlink()
                        
                except Exception as e:
                    logger.error(f"Failed to load session from {session_file}: {e}")
            
            logger.info(f"Loaded {len(self._sessions)} sessions from disk")
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    def get_stats(self) -> dict:
        """Get session statistics"""
        with self._lock:
            return {
                "total_sessions": len(self._sessions),
                "total_users": len(self._user_sessions),
                "sessions_by_user": {
                    uid: len(sids) for uid, sids in self._user_sessions.items()
                }
            }

