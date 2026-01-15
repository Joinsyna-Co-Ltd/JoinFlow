"""
Webhook System
==============

External event triggers for task execution.
"""

import hashlib
import hmac
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook事件类型"""
    GENERIC = "generic"          # 通用触发
    GITHUB = "github"            # GitHub事件
    GITLAB = "gitlab"            # GitLab事件
    SLACK = "slack"              # Slack事件
    DISCORD = "discord"          # Discord事件
    CUSTOM = "custom"            # 自定义


@dataclass
class WebhookEndpoint:
    """Webhook端点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # 端点配置
    path: str = ""               # 触发路径 /webhook/{path}
    secret: str = ""             # 验证密钥
    event_type: WebhookEventType = WebhookEventType.GENERIC
    
    # 任务配置
    task_description: str = ""   # 要执行的任务
    workflow_id: Optional[str] = None  # 关联工作流
    agents: List[str] = field(default_factory=list)
    
    # 过滤器
    event_filter: Dict[str, Any] = field(default_factory=dict)  # 事件过滤条件
    
    # 状态
    enabled: bool = True
    trigger_count: int = 0
    last_triggered: Optional[datetime] = None
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "default"
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['last_triggered'] = self.last_triggered.isoformat() if self.last_triggered else None
        data['created_at'] = self.created_at.isoformat()
        # 不返回secret
        data['secret'] = "***" if self.secret else ""
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "WebhookEndpoint":
        if 'event_type' in data:
            data['event_type'] = WebhookEventType(data['event_type'])
        if isinstance(data.get('last_triggered'), str):
            data['last_triggered'] = datetime.fromisoformat(data['last_triggered'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class WebhookLog:
    """Webhook调用日志"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    endpoint_id: str = ""
    
    # 请求信息
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    source_ip: str = ""
    
    # 结果
    success: bool = False
    task_id: Optional[str] = None
    error: Optional[str] = None
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class WebhookManager:
    """Webhook管理器"""
    
    def __init__(
        self,
        storage_path: str = "./webhooks",
        executor: Optional[Callable] = None
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.executor = executor
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.logs: List[WebhookLog] = []
        
        self._load_endpoints()
    
    def _load_endpoints(self):
        """加载端点配置"""
        config_file = self.storage_path / "webhooks.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for ep_data in data.get('endpoints', []):
                    ep = WebhookEndpoint.from_dict(ep_data)
                    self.endpoints[ep.id] = ep
                logger.info(f"Loaded {len(self.endpoints)} webhook endpoints")
            except Exception as e:
                logger.error(f"Failed to load webhooks: {e}")
    
    def _save_endpoints(self):
        """保存端点配置"""
        config_file = self.storage_path / "webhooks.json"
        try:
            # 保存时包含完整secret
            endpoints_data = []
            for ep in self.endpoints.values():
                ep_dict = asdict(ep)
                ep_dict['event_type'] = ep.event_type.value
                ep_dict['last_triggered'] = ep.last_triggered.isoformat() if ep.last_triggered else None
                ep_dict['created_at'] = ep.created_at.isoformat()
                endpoints_data.append(ep_dict)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'endpoints': endpoints_data}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save webhooks: {e}")
    
    def create_endpoint(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """创建Webhook端点"""
        # 生成唯一路径
        if not endpoint.path:
            endpoint.path = str(uuid.uuid4())[:8]
        
        # 生成密钥
        if not endpoint.secret:
            endpoint.secret = str(uuid.uuid4())
        
        self.endpoints[endpoint.id] = endpoint
        self._save_endpoints()
        
        logger.info(f"Created webhook endpoint: {endpoint.name} -> /webhook/{endpoint.path}")
        return endpoint
    
    def update_endpoint(self, endpoint_id: str, updates: dict) -> Optional[WebhookEndpoint]:
        """更新端点"""
        if endpoint_id not in self.endpoints:
            return None
        
        endpoint = self.endpoints[endpoint_id]
        for key, value in updates.items():
            if hasattr(endpoint, key) and key not in ('id', 'created_at'):
                setattr(endpoint, key, value)
        
        self._save_endpoints()
        return endpoint
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """删除端点"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            self._save_endpoints()
            return True
        return False
    
    def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        """获取端点"""
        return self.endpoints.get(endpoint_id)
    
    def get_endpoint_by_path(self, path: str) -> Optional[WebhookEndpoint]:
        """通过路径获取端点"""
        for ep in self.endpoints.values():
            if ep.path == path:
                return ep
        return None
    
    def get_all_endpoints(self) -> List[WebhookEndpoint]:
        """获取所有端点"""
        return list(self.endpoints.values())
    
    def verify_signature(
        self,
        endpoint: WebhookEndpoint,
        payload: bytes,
        signature: str
    ) -> bool:
        """验证请求签名"""
        if not endpoint.secret:
            return True
        
        if endpoint.event_type == WebhookEventType.GITHUB:
            # GitHub: sha256=xxx
            expected = 'sha256=' + hmac.new(
                endpoint.secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        
        elif endpoint.event_type == WebhookEventType.GITLAB:
            # GitLab: X-Gitlab-Token header
            return hmac.compare_digest(endpoint.secret, signature)
        
        else:
            # 默认: HMAC-SHA256
            expected = hmac.new(
                endpoint.secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
    
    def process_webhook(
        self,
        path: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        source_ip: str = ""
    ) -> Optional[str]:
        """
        处理Webhook请求
        
        Returns:
            task_id if successful, None otherwise
        """
        endpoint = self.get_endpoint_by_path(path)
        
        if not endpoint:
            logger.warning(f"Webhook endpoint not found: {path}")
            return None
        
        if not endpoint.enabled:
            logger.warning(f"Webhook endpoint disabled: {path}")
            return None
        
        # 记录日志
        log = WebhookLog(
            endpoint_id=endpoint.id,
            headers={k: v for k, v in headers.items() if k.lower() not in ('authorization', 'x-api-key')},
            payload=payload,
            source_ip=source_ip
        )
        
        try:
            # 检查事件过滤器
            if endpoint.event_filter:
                if not self._match_filter(payload, endpoint.event_filter):
                    logger.info(f"Webhook filtered out: {path}")
                    log.error = "Filtered"
                    self.logs.append(log)
                    return None
            
            # 构建任务描述
            task_desc = self._build_task_description(endpoint, payload)
            
            # 执行任务
            if self.executor:
                task_id = self.executor(task_desc, endpoint.workflow_id, endpoint.agents)
                log.success = True
                log.task_id = task_id
                
                # 更新统计
                endpoint.trigger_count += 1
                endpoint.last_triggered = datetime.now()
                self._save_endpoints()
                
                logger.info(f"Webhook triggered task: {task_id}")
                self.logs.append(log)
                return task_id
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            log.error = str(e)
        
        self.logs.append(log)
        return None
    
    def _match_filter(self, payload: Dict, filter_rules: Dict) -> bool:
        """检查payload是否匹配过滤规则"""
        for key, expected in filter_rules.items():
            # 支持嵌套路径: "data.action"
            value = payload
            for part in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return False
            
            if isinstance(expected, list):
                if value not in expected:
                    return False
            elif value != expected:
                return False
        
        return True
    
    def _build_task_description(
        self,
        endpoint: WebhookEndpoint,
        payload: Dict
    ) -> str:
        """构建任务描述"""
        desc = endpoint.task_description
        
        # 支持模板变量 {payload.key}
        import re
        
        def replace_var(match):
            path = match.group(1)
            value = payload
            for part in path.split('.'):
                if isinstance(value, dict):
                    value = value.get(part, '')
                else:
                    return ''
            return str(value)
        
        desc = re.sub(r'\{payload\.([^}]+)\}', replace_var, desc)
        
        return desc
    
    def get_logs(
        self,
        endpoint_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookLog]:
        """获取日志"""
        logs = self.logs
        
        if endpoint_id:
            logs = [l for l in logs if l.endpoint_id == endpoint_id]
        
        return sorted(logs, key=lambda l: l.timestamp, reverse=True)[:limit]

