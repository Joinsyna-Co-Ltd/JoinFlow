"""
Smart Suggestion System
=======================

Provides intelligent suggestions based on:
- User context and history
- Task patterns
- Current activity
- Error recovery
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum
import hashlib
import re

logger = logging.getLogger(__name__)


class SuggestionType(str, Enum):
    """建议类型"""
    TASK = "task"               # 任务建议
    OPERATION = "operation"     # 操作建议
    OPTIMIZATION = "opt"        # 优化建议
    FIX = "fix"                # 修复建议
    SHORTCUT = "shortcut"      # 快捷操作
    FOLLOWUP = "followup"      # 后续建议
    LEARNING = "learning"      # 学习建议


class SuggestionTrigger(str, Enum):
    """建议触发时机"""
    IDLE = "idle"              # 空闲时
    INPUT = "input"            # 输入时
    EXECUTING = "executing"    # 执行中
    ERROR = "error"            # 出错时
    COMPLETED = "completed"    # 完成后
    STARTUP = "startup"        # 启动时


class SuggestionPriority(str, Enum):
    """建议优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Suggestion:
    """建议"""
    id: str = ""
    type: SuggestionType = SuggestionType.TASK
    trigger: SuggestionTrigger = SuggestionTrigger.IDLE
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    
    # 内容
    title: str = ""
    description: str = ""
    action: str = ""           # 执行动作/命令
    action_params: Dict[str, Any] = field(default_factory=dict)
    
    # 评分
    confidence: float = 0.5    # 置信度 0-1
    relevance: float = 0.5     # 相关度 0-1
    
    # 上下文
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # 元数据
    source: str = ""           # 建议来源
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # 统计
    shown_count: int = 0
    accepted_count: int = 0
    dismissed_count: int = 0
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['type'] = self.type.value
        data['trigger'] = self.trigger.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Suggestion":
        if isinstance(data.get('type'), str):
            data['type'] = SuggestionType(data['type'])
        if isinstance(data.get('trigger'), str):
            data['trigger'] = SuggestionTrigger(data['trigger'])
        if isinstance(data.get('priority'), str):
            data['priority'] = SuggestionPriority(data['priority'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('expires_at'), str) and data['expires_at']:
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)
    
    @property
    def score(self) -> float:
        """计算综合评分"""
        priority_weights = {
            SuggestionPriority.LOW: 0.5,
            SuggestionPriority.MEDIUM: 1.0,
            SuggestionPriority.HIGH: 1.5,
            SuggestionPriority.CRITICAL: 2.0
        }
        
        base_score = (self.confidence + self.relevance) / 2
        priority_weight = priority_weights.get(self.priority, 1.0)
        
        # 考虑历史表现
        if self.shown_count > 0:
            acceptance_rate = self.accepted_count / self.shown_count
            base_score = base_score * 0.7 + acceptance_rate * 0.3
        
        return base_score * priority_weight


@dataclass
class SuggestionRule:
    """建议规则"""
    id: str
    name: str
    description: str = ""
    
    # 触发条件
    trigger: SuggestionTrigger = SuggestionTrigger.IDLE
    pattern: str = ""          # 正则匹配模式
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # 建议模板
    suggestion_type: SuggestionType = SuggestionType.TASK
    title_template: str = ""
    description_template: str = ""
    action_template: str = ""
    
    # 配置
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    confidence: float = 0.7
    enabled: bool = True
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """检查是否匹配"""
        if not self.enabled:
            return False
        
        # 检查触发时机
        if context.get('trigger') != self.trigger.value:
            return False
        
        # 检查正则模式
        if self.pattern:
            text = context.get('input', '') or context.get('task', '')
            if not re.search(self.pattern, text, re.IGNORECASE):
                return False
        
        # 检查条件
        for key, expected in self.conditions.items():
            actual = context.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        
        return True
    
    def generate_suggestion(self, context: Dict[str, Any]) -> Suggestion:
        """生成建议"""
        # 模板变量替换
        def replace_vars(template: str) -> str:
            result = template
            for key, value in context.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result
        
        return Suggestion(
            id=hashlib.md5(f"{self.id}:{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            type=self.suggestion_type,
            trigger=self.trigger,
            priority=self.priority,
            title=replace_vars(self.title_template),
            description=replace_vars(self.description_template),
            action=replace_vars(self.action_template),
            confidence=self.confidence,
            relevance=0.8,
            context=context,
            source=f"rule:{self.id}"
        )


class SuggestionEngine:
    """
    智能建议引擎
    
    功能：
    - 分析用户上下文
    - 生成智能建议
    - 基于历史学习
    - 个性化推荐
    """
    
    def __init__(self, storage_path: str = "./workspace/suggestions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.rules: List[SuggestionRule] = []
        self.suggestion_cache: Dict[str, Suggestion] = {}
        self.user_preferences: Dict[str, Any] = {}
        
        self._init_default_rules()
        self._load_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        default_rules = [
            # 搜索建议
            SuggestionRule(
                id="search_suggestion",
                name="搜索建议",
                trigger=SuggestionTrigger.INPUT,
                pattern=r"(搜索|查找|找|search|find)",
                suggestion_type=SuggestionType.OPERATION,
                title_template="搜索: {input}",
                description_template="使用浏览器Agent搜索相关信息",
                action_template="browser_search",
                priority=SuggestionPriority.MEDIUM,
                confidence=0.8
            ),
            
            # 文件操作建议
            SuggestionRule(
                id="file_operation",
                name="文件操作建议",
                trigger=SuggestionTrigger.INPUT,
                pattern=r"(打开|保存|创建|删除|文件|file)",
                suggestion_type=SuggestionType.OPERATION,
                title_template="文件操作",
                description_template="使用系统Agent进行文件操作",
                action_template="os_file_operation",
                priority=SuggestionPriority.MEDIUM,
                confidence=0.75
            ),
            
            # 写作建议
            SuggestionRule(
                id="writing_suggestion",
                name="写作建议",
                trigger=SuggestionTrigger.INPUT,
                pattern=r"(写|生成|创作|write|generate|create)",
                suggestion_type=SuggestionType.OPERATION,
                title_template="内容生成",
                description_template="使用大模型Agent生成内容",
                action_template="llm_generate",
                priority=SuggestionPriority.MEDIUM,
                confidence=0.8
            ),
            
            # 错误修复建议
            SuggestionRule(
                id="error_retry",
                name="错误重试建议",
                trigger=SuggestionTrigger.ERROR,
                suggestion_type=SuggestionType.FIX,
                title_template="重试任务",
                description_template="上次任务执行失败，是否重试？",
                action_template="retry_task",
                priority=SuggestionPriority.HIGH,
                confidence=0.9
            ),
            
            # API错误修复
            SuggestionRule(
                id="api_error_fix",
                name="API错误修复",
                trigger=SuggestionTrigger.ERROR,
                pattern=r"(api|API|认证|auth|key)",
                suggestion_type=SuggestionType.FIX,
                title_template="检查API配置",
                description_template="API调用失败，请检查API密钥配置",
                action_template="check_api_config",
                priority=SuggestionPriority.CRITICAL,
                confidence=0.85
            ),
            
            # 任务完成后续建议
            SuggestionRule(
                id="export_suggestion",
                name="导出建议",
                trigger=SuggestionTrigger.COMPLETED,
                suggestion_type=SuggestionType.FOLLOWUP,
                title_template="导出结果",
                description_template="任务已完成，是否导出结果？",
                action_template="export_result",
                priority=SuggestionPriority.MEDIUM,
                confidence=0.7
            ),
            
            # 空闲时建议
            SuggestionRule(
                id="idle_suggestion",
                name="空闲时建议",
                trigger=SuggestionTrigger.IDLE,
                suggestion_type=SuggestionType.TASK,
                title_template="继续未完成的任务",
                description_template="您有未完成的任务，是否继续？",
                action_template="resume_task",
                priority=SuggestionPriority.LOW,
                confidence=0.6
            ),
            
            # 启动建议
            SuggestionRule(
                id="startup_welcome",
                name="启动欢迎",
                trigger=SuggestionTrigger.STARTUP,
                suggestion_type=SuggestionType.TASK,
                title_template="开始新任务",
                description_template="欢迎回来！您可以开始一个新任务",
                action_template="new_task",
                priority=SuggestionPriority.LOW,
                confidence=0.5
            ),
        ]
        
        self.rules.extend(default_rules)
    
    def _load_rules(self):
        """加载自定义规则"""
        rules_file = self.storage_path / "custom_rules.json"
        if rules_file.exists():
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for rule_data in data.get('rules', []):
                    rule = SuggestionRule(**rule_data)
                    self.rules.append(rule)
                    
            except Exception as e:
                logger.error(f"Failed to load custom rules: {e}")
    
    def _save_rules(self):
        """保存自定义规则"""
        rules_file = self.storage_path / "custom_rules.json"
        try:
            custom_rules = [r for r in self.rules if not r.id.startswith(('search_', 'file_', 'writing_', 'error_', 'api_', 'export_', 'idle_', 'startup_'))]
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'rules': [asdict(r) for r in custom_rules]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")
    
    # ========================
    # 建议生成
    # ========================
    
    def get_suggestions(
        self,
        context: Dict[str, Any],
        max_suggestions: int = 5
    ) -> List[Suggestion]:
        """
        获取建议
        
        Args:
            context: 上下文信息
            max_suggestions: 最大建议数
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 基于规则生成建议
        for rule in self.rules:
            if rule.matches(context):
                suggestion = rule.generate_suggestion(context)
                suggestions.append(suggestion)
        
        # 基于历史生成建议
        history_suggestions = self._generate_from_history(context)
        suggestions.extend(history_suggestions)
        
        # 基于用户偏好调整
        suggestions = self._apply_preferences(suggestions, context.get('user_id', 'default'))
        
        # 排序和去重
        suggestions = self._rank_and_dedupe(suggestions)
        
        return suggestions[:max_suggestions]
    
    def get_input_suggestions(
        self,
        input_text: str,
        user_id: str = "default"
    ) -> List[Suggestion]:
        """
        获取输入建议（实时补全）
        
        Args:
            input_text: 用户输入
            user_id: 用户ID
            
        Returns:
            建议列表
        """
        context = {
            'trigger': SuggestionTrigger.INPUT.value,
            'input': input_text,
            'user_id': user_id
        }
        
        return self.get_suggestions(context, max_suggestions=3)
    
    def get_error_suggestions(
        self,
        error: str,
        task_context: Dict[str, Any]
    ) -> List[Suggestion]:
        """
        获取错误修复建议
        
        Args:
            error: 错误信息
            task_context: 任务上下文
            
        Returns:
            修复建议列表
        """
        context = {
            'trigger': SuggestionTrigger.ERROR.value,
            'error': error,
            **task_context
        }
        
        return self.get_suggestions(context, max_suggestions=3)
    
    def get_followup_suggestions(
        self,
        task_result: Dict[str, Any]
    ) -> List[Suggestion]:
        """
        获取后续建议
        
        Args:
            task_result: 任务结果
            
        Returns:
            后续建议列表
        """
        context = {
            'trigger': SuggestionTrigger.COMPLETED.value,
            **task_result
        }
        
        return self.get_suggestions(context, max_suggestions=3)
    
    def get_idle_suggestions(
        self,
        user_id: str = "default"
    ) -> List[Suggestion]:
        """
        获取空闲时建议
        
        Args:
            user_id: 用户ID
            
        Returns:
            建议列表
        """
        context = {
            'trigger': SuggestionTrigger.IDLE.value,
            'user_id': user_id
        }
        
        # 检查是否有未完成的任务
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager
            manager = get_checkpoint_manager()
            resumable = manager.get_resumable(user_id)
            
            if resumable:
                context['has_resumable_tasks'] = True
                context['resumable_count'] = len(resumable)
        except:
            pass
        
        return self.get_suggestions(context, max_suggestions=3)
    
    # ========================
    # 内部方法
    # ========================
    
    def _generate_from_history(self, context: Dict[str, Any]) -> List[Suggestion]:
        """基于历史生成建议"""
        suggestions = []
        
        try:
            from joinflow_memory.long_term_memory import get_memory_store, MemoryType
            
            memory_store = get_memory_store()
            user_id = context.get('user_id', 'default')
            
            # 查找相似的历史任务
            if 'input' in context:
                similar_tasks = memory_store.recall(
                    query=context['input'],
                    user_id=user_id,
                    memory_type=MemoryType.TASK_PATTERN,
                    limit=3
                )
                
                for memory, score in similar_tasks:
                    if score > 0.7:  # 高相似度
                        suggestions.append(Suggestion(
                            id=f"history_{memory.id}",
                            type=SuggestionType.TASK,
                            trigger=SuggestionTrigger(context.get('trigger', 'idle')),
                            priority=SuggestionPriority.MEDIUM,
                            title=f"类似任务: {memory.summary[:30]}",
                            description=f"您之前执行过类似的任务",
                            action="execute_similar",
                            action_params={"memory_id": memory.id},
                            confidence=score,
                            relevance=score,
                            source="history"
                        ))
                        
        except Exception as e:
            logger.debug(f"History suggestion generation failed: {e}")
        
        return suggestions
    
    def _apply_preferences(
        self,
        suggestions: List[Suggestion],
        user_id: str
    ) -> List[Suggestion]:
        """应用用户偏好"""
        # 获取用户偏好
        prefs = self.user_preferences.get(user_id, {})
        
        # 过滤掉用户不喜欢的类型
        disabled_types = prefs.get('disabled_types', [])
        suggestions = [s for s in suggestions if s.type.value not in disabled_types]
        
        # 调整优先级
        preferred_types = prefs.get('preferred_types', [])
        for s in suggestions:
            if s.type.value in preferred_types:
                s.confidence *= 1.2
        
        return suggestions
    
    def _rank_and_dedupe(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """排序和去重"""
        # 去重（基于action）
        seen_actions = set()
        unique = []
        for s in suggestions:
            if s.action not in seen_actions:
                seen_actions.add(s.action)
                unique.append(s)
        
        # 按评分排序
        unique.sort(key=lambda s: s.score, reverse=True)
        
        return unique
    
    # ========================
    # 反馈学习
    # ========================
    
    def record_feedback(
        self,
        suggestion_id: str,
        accepted: bool,
        user_id: str = "default"
    ):
        """
        记录用户反馈
        
        Args:
            suggestion_id: 建议ID
            accepted: 是否接受
            user_id: 用户ID
        """
        suggestion = self.suggestion_cache.get(suggestion_id)
        if suggestion:
            suggestion.shown_count += 1
            if accepted:
                suggestion.accepted_count += 1
            else:
                suggestion.dismissed_count += 1
        
        # 更新用户偏好
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'preferred_types': [],
                'disabled_types': [],
                'feedback_history': []
            }
        
        self.user_preferences[user_id]['feedback_history'].append({
            'suggestion_id': suggestion_id,
            'accepted': accepted,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保存偏好
        self._save_preferences()
    
    def _save_preferences(self):
        """保存用户偏好"""
        prefs_file = self.storage_path / "preferences.json"
        try:
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def _load_preferences(self):
        """加载用户偏好"""
        prefs_file = self.storage_path / "preferences.json"
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
    
    # ========================
    # 规则管理
    # ========================
    
    def add_rule(self, rule: SuggestionRule):
        """添加规则"""
        self.rules.append(rule)
        self._save_rules()
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        original_len = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        
        if len(self.rules) < original_len:
            self._save_rules()
            return True
        return False
    
    def list_rules(self) -> List[SuggestionRule]:
        """列出所有规则"""
        return self.rules.copy()


# 全局实例
_suggestion_engine: Optional[SuggestionEngine] = None


def get_suggestion_engine() -> SuggestionEngine:
    """获取全局建议引擎实例"""
    global _suggestion_engine
    if _suggestion_engine is None:
        _suggestion_engine = SuggestionEngine()
    return _suggestion_engine

