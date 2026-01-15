"""
User Authentication System
==========================

Multi-user support with authentication and permission management.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    ADMIN = "admin"          # 管理员
    USER = "user"            # 普通用户
    READONLY = "readonly"    # 只读用户
    API = "api"              # API用户


class Permission(str, Enum):
    # 任务权限
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_DELETE = "task:delete"
    TASK_CANCEL = "task:cancel"
    
    # 知识库权限
    KB_READ = "kb:read"
    KB_WRITE = "kb:write"
    KB_DELETE = "kb:delete"
    
    # 工作流权限
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_DELETE = "workflow:delete"
    
    # 系统权限
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"
    USERS_MANAGE = "users:manage"
    PLUGINS_MANAGE = "plugins:manage"
    
    # 统计权限
    STATS_READ = "stats:read"
    STATS_EXPORT = "stats:export"


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.ADMIN: set(Permission),  # 所有权限
    UserRole.USER: {
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.TASK_DELETE,
        Permission.TASK_CANCEL,
        Permission.KB_READ,
        Permission.KB_WRITE,
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_READ,
        Permission.SETTINGS_READ,
        Permission.STATS_READ,
    },
    UserRole.READONLY: {
        Permission.TASK_READ,
        Permission.KB_READ,
        Permission.WORKFLOW_READ,
        Permission.SETTINGS_READ,
        Permission.STATS_READ,
    },
    UserRole.API: {
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.KB_READ,
        Permission.WORKFLOW_READ,
    },
}


@dataclass
class User:
    """用户"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    
    # 认证
    password_hash: str = ""
    salt: str = ""
    
    # 角色和权限
    role: UserRole = UserRole.USER
    extra_permissions: List[str] = field(default_factory=list)
    
    # 状态
    is_active: bool = True
    is_verified: bool = False
    
    # API访问
    api_key: str = ""
    api_key_created_at: Optional[datetime] = None
    
    # 配额
    daily_task_limit: int = 100
    daily_token_limit: int = 1000000
    
    # 统计
    task_count: int = 0
    token_count: int = 0
    last_task_at: Optional[datetime] = None
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login_at: Optional[datetime] = None
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = asdict(self)
        data['role'] = self.role.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['last_login_at'] = self.last_login_at.isoformat() if self.last_login_at else None
        data['last_task_at'] = self.last_task_at.isoformat() if self.last_task_at else None
        data['api_key_created_at'] = self.api_key_created_at.isoformat() if self.api_key_created_at else None
        
        if not include_sensitive:
            data.pop('password_hash', None)
            data.pop('salt', None)
            if data.get('api_key'):
                data['api_key'] = data['api_key'][:8] + '...' if len(data['api_key']) > 8 else '***'
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        if 'role' in data:
            data['role'] = UserRole(data['role'])
        for field_name in ['created_at', 'updated_at', 'last_login_at', 'last_task_at', 'api_key_created_at']:
            if isinstance(data.get(field_name), str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        return cls(**data)
    
    def get_permissions(self) -> Set[Permission]:
        """获取用户所有权限"""
        perms = ROLE_PERMISSIONS.get(self.role, set()).copy()
        for perm_str in self.extra_permissions:
            try:
                perms.add(Permission(perm_str))
            except ValueError:
                pass
        return perms
    
    def has_permission(self, permission: Permission) -> bool:
        """检查用户是否有权限"""
        return permission in self.get_permissions()


@dataclass
class Session:
    """会话"""
    id: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    user_id: str = ""
    
    # 会话信息
    ip_address: str = ""
    user_agent: str = ""
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    last_activity: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
        }


class PasswordHasher:
    """密码哈希器"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """
        哈希密码
        
        Returns:
            (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            iterations=100000
        ).hex()
        
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """验证密码"""
        computed_hash, _ = PasswordHasher.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)


class AuthManager:
    """认证管理器"""
    
    def __init__(self, storage_path: str = "./auth"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> user_id
        
        self._load_data()
        self._ensure_admin()
    
    def _load_data(self):
        """加载数据"""
        users_file = self.storage_path / "users.json"
        if users_file.exists():
            try:
                with open(users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for user_data in data.get('users', []):
                    user = User.from_dict(user_data)
                    self.users[user.id] = user
                    if user.api_key:
                        self.api_keys[user.api_key] = user.id
                logger.info(f"Loaded {len(self.users)} users")
            except Exception as e:
                logger.error(f"Failed to load users: {e}")
    
    def _save_data(self):
        """保存数据"""
        users_file = self.storage_path / "users.json"
        try:
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'users': [u.to_dict(include_sensitive=True) for u in self.users.values()]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def _ensure_admin(self):
        """确保有管理员账户"""
        for user in self.users.values():
            if user.role == UserRole.ADMIN:
                return
        
        # 创建默认管理员
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        self.create_user(
            username="admin",
            email="admin@localhost",
            password=admin_password,
            role=UserRole.ADMIN
        )
        logger.info("Created default admin user (username: admin)")
    
    # ========== 用户管理 ==========
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER
    ) -> User:
        """创建用户"""
        # 检查用户名是否存在
        for user in self.users.values():
            if user.username == username:
                raise ValueError(f"Username already exists: {username}")
            if user.email == email:
                raise ValueError(f"Email already exists: {email}")
        
        password_hash, salt = PasswordHasher.hash_password(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            salt=salt,
            role=role,
            is_verified=role == UserRole.ADMIN
        )
        
        self.users[user.id] = user
        self._save_data()
        
        logger.info(f"Created user: {username} ({role.value})")
        return user
    
    def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        """更新用户"""
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        
        # 处理密码更新
        if 'password' in updates:
            password_hash, salt = PasswordHasher.hash_password(updates.pop('password'))
            user.password_hash = password_hash
            user.salt = salt
        
        # 处理角色更新
        if 'role' in updates:
            user.role = UserRole(updates.pop('role'))
        
        # 更新其他字段
        for key, value in updates.items():
            if hasattr(user, key) and key not in ('id', 'created_at', 'password_hash', 'salt'):
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        self._save_data()
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        
        # 清理API key
        if user.api_key and user.api_key in self.api_keys:
            del self.api_keys[user.api_key]
        
        # 清理会话
        sessions_to_delete = [s.id for s in self.sessions.values() if s.user_id == user_id]
        for session_id in sessions_to_delete:
            del self.sessions[session_id]
        
        del self.users[user_id]
        self._save_data()
        
        return True
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def list_users(self, include_inactive: bool = False) -> List[User]:
        """列出用户"""
        users = list(self.users.values())
        if not include_inactive:
            users = [u for u in users if u.is_active]
        return sorted(users, key=lambda u: u.created_at, reverse=True)
    
    # ========== 认证 ==========
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """验证用户名密码"""
        user = self.get_user_by_username(username)
        if not user:
            user = self.get_user_by_email(username)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not PasswordHasher.verify_password(password, user.password_hash, user.salt):
            return None
        
        return user
    
    def login(
        self,
        username: str,
        password: str,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Optional[Session]:
        """登录"""
        user = self.authenticate(username, password)
        if not user:
            return None
        
        # 创建会话
        session = Session(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session.id] = session
        
        # 更新用户登录时间
        user.last_login_at = datetime.now()
        self._save_data()
        
        logger.info(f"User logged in: {user.username}")
        return session
    
    def logout(self, session_id: str) -> bool:
        """登出"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """验证会话"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        if session.is_expired():
            del self.sessions[session_id]
            return None
        
        # 更新最后活动时间
        session.last_activity = datetime.now()
        
        return self.get_user(session.user_id)
    
    # ========== API Key ==========
    
    def generate_api_key(self, user_id: str) -> Optional[str]:
        """生成API Key"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        # 删除旧的API key
        if user.api_key and user.api_key in self.api_keys:
            del self.api_keys[user.api_key]
        
        # 生成新的API key
        api_key = f"jf_{secrets.token_urlsafe(32)}"
        
        user.api_key = api_key
        user.api_key_created_at = datetime.now()
        self.api_keys[api_key] = user_id
        
        self._save_data()
        
        return api_key
    
    def revoke_api_key(self, user_id: str) -> bool:
        """撤销API Key"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        if user.api_key and user.api_key in self.api_keys:
            del self.api_keys[user.api_key]
        
        user.api_key = ""
        user.api_key_created_at = None
        self._save_data()
        
        return True
    
    def validate_api_key(self, api_key: str) -> Optional[User]:
        """验证API Key"""
        user_id = self.api_keys.get(api_key)
        if not user_id:
            return None
        
        user = self.get_user(user_id)
        if not user or not user.is_active:
            return None
        
        return user
    
    # ========== 权限检查 ==========
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """检查权限"""
        user = self.get_user(user_id)
        if not user:
            return False
        return user.has_permission(permission)
    
    def require_permission(self, user_id: str, permission: Permission) -> None:
        """要求权限，否则抛出异常"""
        if not self.check_permission(user_id, permission):
            raise PermissionError(f"Permission denied: {permission.value}")
    
    # ========== 配额管理 ==========
    
    def check_quota(self, user_id: str, tokens: int = 0) -> bool:
        """检查配额"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        # 管理员无限制
        if user.role == UserRole.ADMIN:
            return True
        
        # 检查任务数配额
        today = datetime.now().date()
        if user.last_task_at and user.last_task_at.date() == today:
            if user.task_count >= user.daily_task_limit:
                return False
            if user.token_count + tokens > user.daily_token_limit:
                return False
        
        return True
    
    def record_usage(self, user_id: str, tokens: int = 0):
        """记录使用"""
        user = self.get_user(user_id)
        if not user:
            return
        
        today = datetime.now().date()
        
        # 重置每日计数
        if not user.last_task_at or user.last_task_at.date() != today:
            user.task_count = 0
            user.token_count = 0
        
        user.task_count += 1
        user.token_count += tokens
        user.last_task_at = datetime.now()
        
        self._save_data()
    
    # ========== 清理 ==========
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        expired = [s.id for s in self.sessions.values() if s.is_expired()]
        for session_id in expired:
            del self.sessions[session_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

