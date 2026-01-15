"""
意图解析器 - 结合规则和LLM的意图理解
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .types import Intent, IntentType, Entity, EntityType, DANGEROUS_INTENTS
from .patterns import PatternMatcher

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """解析结果"""
    intent: Intent
    source: str  # "pattern" 或 "llm"
    alternatives: List[Intent]  # 备选意图
    raw_llm_response: Optional[str] = None


class IntentParser:
    """
    意图解析器
    
    两阶段解析策略：
    1. 首先使用规则匹配快速识别简单意图
    2. 对于复杂意图或低置信度结果，使用LLM进行深度理解
    """
    
    # LLM 意图解析提示词
    INTENT_PARSE_PROMPT = """你是一个智能操作系统助手的意图理解模块。分析用户的输入，识别他们想要执行的操作。

用户输入: "{user_input}"

请分析并返回JSON格式的结果：
{{
    "intent_type": "意图类型（见下方列表）",
    "confidence": 0.0-1.0的置信度,
    "entities": [
        {{"type": "实体类型", "value": "实体值", "text": "原文"}}
    ],
    "description": "意图的自然语言描述",
    "is_compound": false,  // 是否是复合意图
    "sub_intents": [],  // 如果是复合意图，列出子意图
    "requires_confirmation": false  // 是否需要确认
}}

可用的意图类型：
- FILE_CREATE: 创建文件
- FILE_READ: 读取/查看文件
- FILE_WRITE: 写入/编辑文件
- FILE_DELETE: 删除文件
- FILE_COPY: 复制文件
- FILE_MOVE: 移动/重命名文件
- FILE_OPEN: 打开文件（用默认程序）
- DIR_CREATE: 创建目录/文件夹
- DIR_LIST: 列出目录内容
- DIR_DELETE: 删除目录
- DIR_NAVIGATE: 进入/切换目录
- SEARCH_FILE: 搜索文件
- SEARCH_CONTENT: 搜索文件内容
- APP_OPEN: 打开应用程序
- APP_CLOSE: 关闭应用程序
- APP_LIST: 列出运行的程序
- BROWSER_OPEN: 打开浏览器
- BROWSER_SEARCH: 浏览器搜索
- BROWSER_NAVIGATE: 访问网址
- SYSTEM_INFO: 获取系统信息
- SYSTEM_CLIPBOARD_GET: 获取剪贴板
- SYSTEM_CLIPBOARD_SET: 设置剪贴板
- SYSTEM_SCREENSHOT: 截屏
- SYSTEM_NOTIFY: 发送通知
- EXECUTE_COMMAND: 执行命令
- EXECUTE_SCRIPT: 执行脚本
- COMPOSE_TEXT: 编写文本
- COMPOSE_CODE: 编写代码
- HELP: 帮助/说明
- CANCEL: 取消
- CONFIRM: 确认
- UNKNOWN: 无法识别

实体类型：
- FILE_PATH: 文件路径
- DIR_PATH: 目录路径
- FILE_NAME: 文件名
- FILE_TYPE: 文件类型
- APP_NAME: 应用名称
- URL: 网址
- SEARCH_QUERY: 搜索关键词
- TEXT_CONTENT: 文本内容
- COMMAND: 命令

只返回JSON，不要其他内容。"""

    def __init__(self, llm_client=None):
        """
        初始化解析器
        
        Args:
            llm_client: LLM客户端（可选），如果不提供则只使用规则匹配
        """
        self.llm_client = llm_client
        self.pattern_matcher = PatternMatcher()
        
        # 历史记录（用于学习）
        self.parse_history: List[ParseResult] = []
    
    def parse(self, user_input: str, use_llm: bool = True) -> ParseResult:
        """
        解析用户输入
        
        Args:
            user_input: 用户输入的自然语言
            use_llm: 是否使用LLM（默认True）
        
        Returns:
            ParseResult: 解析结果
        """
        user_input = user_input.strip()
        
        if not user_input:
            return ParseResult(
                intent=Intent(type=IntentType.UNKNOWN, raw_input=user_input),
                source="none",
                alternatives=[],
            )
        
        # 第一阶段：规则匹配
        pattern_intent = self.pattern_matcher.match(user_input)
        
        # 如果规则匹配置信度高，直接返回
        if pattern_intent and pattern_intent.confidence >= 0.8:
            result = ParseResult(
                intent=pattern_intent,
                source="pattern",
                alternatives=[],
            )
            self._record_history(result)
            return result
        
        # 检查是否是复合意图
        is_compound = self.pattern_matcher.is_compound_intent(user_input)
        
        # 第二阶段：LLM 理解（如果可用且需要）
        if use_llm and self.llm_client and (
            pattern_intent is None or 
            pattern_intent.confidence < 0.8 or 
            is_compound
        ):
            llm_intent = self._parse_with_llm(user_input)
            if llm_intent:
                result = ParseResult(
                    intent=llm_intent,
                    source="llm",
                    alternatives=[pattern_intent] if pattern_intent else [],
                )
                self._record_history(result)
                return result
        
        # 返回规则匹配结果（即使置信度低）
        if pattern_intent:
            result = ParseResult(
                intent=pattern_intent,
                source="pattern",
                alternatives=[],
            )
            self._record_history(result)
            return result
        
        # 无法识别
        unknown_intent = Intent(
            type=IntentType.UNKNOWN,
            confidence=0.0,
            raw_input=user_input,
            description="无法识别的意图",
        )
        
        return ParseResult(
            intent=unknown_intent,
            source="none",
            alternatives=[],
        )
    
    def _parse_with_llm(self, user_input: str) -> Optional[Intent]:
        """使用LLM解析意图"""
        try:
            prompt = self.INTENT_PARSE_PROMPT.format(user_input=user_input)
            
            response = self.llm_client.chat(prompt)
            
            # 解析JSON响应
            result = self._parse_llm_response(response, user_input)
            return result
            
        except Exception as e:
            logger.error(f"LLM意图解析失败: {e}")
            return None
    
    def _parse_llm_response(self, response: str, user_input: str) -> Optional[Intent]:
        """解析LLM响应"""
        try:
            # 提取JSON
            json_str = response.strip()
            if json_str.startswith("```"):
                # 去除markdown代码块
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])
            
            data = json.loads(json_str)
            
            # 解析意图类型
            intent_type_str = data.get("intent_type", "UNKNOWN")
            try:
                intent_type = IntentType[intent_type_str]
            except KeyError:
                intent_type = IntentType.UNKNOWN
            
            # 创建意图对象
            intent = Intent(
                type=intent_type,
                confidence=float(data.get("confidence", 0.5)),
                raw_input=user_input,
                description=data.get("description", ""),
                requires_confirmation=data.get("requires_confirmation", False) or intent_type in DANGEROUS_INTENTS,
            )
            
            # 解析实体
            for entity_data in data.get("entities", []):
                try:
                    entity_type = EntityType[entity_data.get("type", "UNKNOWN")]
                except KeyError:
                    entity_type = EntityType.UNKNOWN
                
                entity = Entity(
                    type=entity_type,
                    value=entity_data.get("value", ""),
                    text=entity_data.get("text", ""),
                )
                intent.add_entity(entity)
            
            # 解析子意图（复合意图）
            if data.get("is_compound") and data.get("sub_intents"):
                for sub_data in data["sub_intents"]:
                    sub_intent = self._parse_sub_intent(sub_data, user_input)
                    if sub_intent:
                        intent.sub_intents.append(sub_intent)
                intent.type = IntentType.COMPOUND
            
            return intent
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            return None
    
    def _parse_sub_intent(self, data: Dict, user_input: str) -> Optional[Intent]:
        """解析子意图"""
        try:
            intent_type_str = data.get("intent_type", "UNKNOWN")
            try:
                intent_type = IntentType[intent_type_str]
            except KeyError:
                intent_type = IntentType.UNKNOWN
            
            intent = Intent(
                type=intent_type,
                confidence=float(data.get("confidence", 0.5)),
                raw_input=user_input,
                description=data.get("description", ""),
            )
            
            for entity_data in data.get("entities", []):
                try:
                    entity_type = EntityType[entity_data.get("type", "UNKNOWN")]
                except KeyError:
                    entity_type = EntityType.UNKNOWN
                
                entity = Entity(
                    type=entity_type,
                    value=entity_data.get("value", ""),
                    text=entity_data.get("text", ""),
                )
                intent.add_entity(entity)
            
            return intent
        except Exception:
            return None
    
    def _record_history(self, result: ParseResult) -> None:
        """记录解析历史"""
        self.parse_history.append(result)
        
        # 限制历史长度
        if len(self.parse_history) > 1000:
            self.parse_history = self.parse_history[-500:]
    
    def set_llm_client(self, llm_client) -> None:
        """设置LLM客户端"""
        self.llm_client = llm_client
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取解析统计"""
        if not self.parse_history:
            return {"total": 0}
        
        total = len(self.parse_history)
        pattern_count = sum(1 for r in self.parse_history if r.source == "pattern")
        llm_count = sum(1 for r in self.parse_history if r.source == "llm")
        
        # 意图类型分布
        intent_dist = {}
        for r in self.parse_history:
            intent_name = r.intent.type.name
            intent_dist[intent_name] = intent_dist.get(intent_name, 0) + 1
        
        return {
            "total": total,
            "pattern_matches": pattern_count,
            "llm_matches": llm_count,
            "pattern_ratio": pattern_count / total if total > 0 else 0,
            "intent_distribution": intent_dist,
        }


class QuickIntentParser:
    """
    快速意图解析器
    
    仅使用规则匹配，不依赖LLM，用于性能敏感场景
    """
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
    
    def parse(self, user_input: str) -> Intent:
        """快速解析"""
        intent = self.pattern_matcher.match(user_input)
        
        if intent:
            return intent
        
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.0,
            raw_input=user_input,
        )
    
    def is_file_operation(self, user_input: str) -> bool:
        """判断是否是文件操作"""
        intent = self.parse(user_input)
        file_intents = {
            IntentType.FILE_CREATE, IntentType.FILE_READ, IntentType.FILE_WRITE,
            IntentType.FILE_DELETE, IntentType.FILE_COPY, IntentType.FILE_MOVE,
            IntentType.FILE_OPEN
        }
        return intent.type in file_intents
    
    def is_app_operation(self, user_input: str) -> bool:
        """判断是否是应用操作"""
        intent = self.parse(user_input)
        app_intents = {IntentType.APP_OPEN, IntentType.APP_CLOSE, IntentType.APP_LIST}
        return intent.type in app_intents
    
    def is_search_operation(self, user_input: str) -> bool:
        """判断是否是搜索操作"""
        intent = self.parse(user_input)
        search_intents = {
            IntentType.SEARCH_FILE, IntentType.SEARCH_CONTENT,
            IntentType.BROWSER_SEARCH
        }
        return intent.type in search_intents

