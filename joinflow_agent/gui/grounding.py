"""
Grounding Agent - UI 元素定位模块
==================================

负责在屏幕截图中定位 UI 元素的坐标。
支持多种定位策略：
1. LLM 视觉定位（使用 GPT-4V、Claude 等）
2. 专用 Grounding 模型（如 UI-TARS）
3. OCR + 规则匹配
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class GroundingMethod(Enum):
    """定位方法"""
    VISION_LLM = "vision_llm"      # 使用视觉 LLM
    GROUNDING_MODEL = "grounding"  # 专用 grounding 模型
    OCR_MATCH = "ocr_match"        # OCR + 文本匹配
    TEMPLATE_MATCH = "template"    # 模板匹配


@dataclass
class UIElement:
    """
    UI 元素
    
    表示屏幕上的一个可交互元素
    """
    # 元素信息
    name: str                                   # 元素名称/描述
    element_type: str = "unknown"               # 类型: button, input, link, text, icon, etc.
    
    # 位置信息
    center: Optional[Tuple[int, int]] = None    # 中心坐标 (x, y)
    bbox: Optional[Tuple[int, int, int, int]] = None  # 边界框 (x1, y1, x2, y2)
    
    # 置信度
    confidence: float = 1.0
    
    # 额外属性
    text: Optional[str] = None                  # 元素文本
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def x(self) -> int:
        """获取 x 坐标"""
        if self.center:
            return self.center[0]
        if self.bbox:
            return (self.bbox[0] + self.bbox[2]) // 2
        return 0
    
    @property
    def y(self) -> int:
        """获取 y 坐标"""
        if self.center:
            return self.center[1]
        if self.bbox:
            return (self.bbox[1] + self.bbox[3]) // 2
        return 0
    
    @property
    def coordinates(self) -> Tuple[int, int]:
        """获取坐标元组"""
        return (self.x, self.y)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.element_type,
            "center": self.center,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "text": self.text,
        }
    
    def __str__(self) -> str:
        return f"UIElement('{self.name}', pos={self.coordinates}, conf={self.confidence:.2f})"


@dataclass
class GroundingConfig:
    """Grounding 配置"""
    # 定位方法
    method: GroundingMethod = GroundingMethod.VISION_LLM
    
    # 视觉 LLM 配置 - 默认使用 OpenRouter
    vision_model: str = "openrouter/google/gemini-2.0-flash-exp:free"
    vision_api_key: Optional[str] = "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"
    vision_base_url: Optional[str] = None
    
    # Grounding 模型配置（如 UI-TARS）
    grounding_model: Optional[str] = None
    grounding_url: Optional[str] = None
    grounding_api_key: Optional[str] = None
    grounding_width: int = 1920   # 输出坐标的分辨率
    grounding_height: int = 1080
    
    # 通用配置
    max_retries: int = 3
    timeout: int = 30


class GroundingAgent:
    """
    Grounding Agent - 元素定位代理
    
    负责根据元素描述在屏幕上定位元素坐标。
    这是 Agent-S 的核心组件之一。
    """
    
    # 定位提示模板
    GROUNDING_PROMPT = """你是一个 UI 元素定位专家。根据屏幕截图，找到用户描述的元素并返回其坐标。

用户描述的目标元素: "{target}"

请分析截图，找到该元素的位置，并以 JSON 格式返回：
{{
    "found": true/false,
    "element": {{
        "name": "元素名称",
        "type": "button/input/link/text/icon/menu/other",
        "x": 像素x坐标,
        "y": 像素y坐标,
        "confidence": 置信度0-1
    }},
    "reason": "定位理由"
}}

屏幕分辨率: {width} x {height}
坐标是相对于屏幕左上角(0,0)的绝对像素位置。

只返回 JSON，不要其他内容。"""

    MULTI_ELEMENT_PROMPT = """你是一个 UI 元素定位专家。分析屏幕截图，列出所有可交互的 UI 元素。

请以 JSON 格式返回所有可见的可交互元素：
{{
    "elements": [
        {{
            "name": "元素描述",
            "type": "button/input/link/text/icon/menu",
            "x": x坐标,
            "y": y坐标,
            "text": "元素文本(如有)"
        }}
    ]
}}

屏幕分辨率: {width} x {height}
只返回 JSON。"""
    
    def __init__(self, config: Optional[GroundingConfig] = None):
        self.config = config or GroundingConfig()
        self._llm_client = None
        self._grounding_client = None
        
        self._init_clients()
    
    def _init_clients(self) -> None:
        """初始化 LLM 客户端"""
        try:
            import litellm
            self._llm_client = litellm
            logger.info("Grounding agent initialized with litellm")
        except ImportError:
            logger.warning("litellm not available, grounding functionality limited")
    
    def locate(
        self, 
        target: str, 
        screenshot_base64: str,
        screen_width: int = 1920,
        screen_height: int = 1080
    ) -> Optional[UIElement]:
        """
        定位单个元素
        
        Args:
            target: 目标元素描述（如 "搜索按钮"、"关闭图标"）
            screenshot_base64: base64 编码的截图
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            
        Returns:
            UIElement 如果找到，否则 None
        """
        if self.config.method == GroundingMethod.VISION_LLM:
            return self._locate_with_vision_llm(
                target, screenshot_base64, screen_width, screen_height
            )
        elif self.config.method == GroundingMethod.GROUNDING_MODEL:
            return self._locate_with_grounding_model(
                target, screenshot_base64, screen_width, screen_height
            )
        else:
            logger.warning(f"Unsupported grounding method: {self.config.method}")
            return None
    
    def _locate_with_vision_llm(
        self,
        target: str,
        screenshot_base64: str,
        screen_width: int,
        screen_height: int
    ) -> Optional[UIElement]:
        """使用视觉 LLM 定位元素"""
        if not self._llm_client:
            logger.error("LLM client not available")
            return None
        
        prompt = self.GROUNDING_PROMPT.format(
            target=target,
            width=screen_width,
            height=screen_height
        )
        
        try:
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # 调用 LLM
            response = self._llm_client.completion(
                model=self.config.vision_model,
                messages=messages,
                api_key=self.config.vision_api_key,
                base_url=self.config.vision_base_url,
                max_tokens=500,
                temperature=0.1,
            )
            
            # 解析响应
            content = response.choices[0].message.content
            return self._parse_grounding_response(content, target)
            
        except Exception as e:
            logger.error(f"Vision LLM grounding failed: {e}")
            return None
    
    def _locate_with_grounding_model(
        self,
        target: str,
        screenshot_base64: str,
        screen_width: int,
        screen_height: int
    ) -> Optional[UIElement]:
        """
        使用专用 Grounding 模型定位元素
        
        支持 UI-TARS 等模型
        """
        if not self.config.grounding_url:
            logger.error("Grounding model URL not configured")
            return None
        
        try:
            import httpx
            
            # UI-TARS 风格的请求
            prompt = f"<|user|>\n<image>\n在图片中找到 '{target}' 的位置\n<|end|>\n<|assistant|>\n"
            
            response = httpx.post(
                self.config.grounding_url,
                json={
                    "model": self.config.grounding_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"找到 '{target}' 的坐标"},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 100,
                },
                headers={"Authorization": f"Bearer {self.config.grounding_api_key}"} if self.config.grounding_api_key else {},
                timeout=self.config.timeout,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 解析 grounding 模型的输出
            # 不同模型输出格式可能不同，这里假设返回 (x, y) 坐标
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return self._parse_grounding_model_output(content, target, screen_width, screen_height)
            
        except Exception as e:
            logger.error(f"Grounding model call failed: {e}")
            return None
    
    def _parse_grounding_response(self, response: str, target: str) -> Optional[UIElement]:
        """解析 LLM 返回的定位结果"""
        try:
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning(f"No JSON found in response: {response[:200]}")
                return None
            
            data = json.loads(json_match.group())
            
            if not data.get("found", False):
                logger.info(f"Element not found: {target}")
                return None
            
            element_data = data.get("element", {})
            
            x = element_data.get("x", 0)
            y = element_data.get("y", 0)
            
            if x == 0 and y == 0:
                logger.warning(f"Invalid coordinates for: {target}")
                return None
            
            return UIElement(
                name=element_data.get("name", target),
                element_type=element_data.get("type", "unknown"),
                center=(int(x), int(y)),
                confidence=float(element_data.get("confidence", 0.8)),
                text=element_data.get("text"),
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def _parse_grounding_model_output(
        self, 
        output: str, 
        target: str,
        screen_width: int,
        screen_height: int
    ) -> Optional[UIElement]:
        """解析 Grounding 模型的输出"""
        try:
            # UI-TARS 等模型通常返回类似 "<point x=500 y=300>" 或 "(500, 300)" 的格式
            
            # 尝试匹配 (x, y) 格式
            coord_match = re.search(r'\((\d+),\s*(\d+)\)', output)
            if coord_match:
                x, y = int(coord_match.group(1)), int(coord_match.group(2))
            else:
                # 尝试匹配 x=... y=... 格式
                x_match = re.search(r'x[=:]\s*(\d+)', output, re.IGNORECASE)
                y_match = re.search(r'y[=:]\s*(\d+)', output, re.IGNORECASE)
                if x_match and y_match:
                    x, y = int(x_match.group(1)), int(y_match.group(1))
                else:
                    logger.warning(f"Could not parse coordinates from: {output}")
                    return None
            
            # 根据 grounding 模型的输出分辨率缩放坐标
            if self.config.grounding_width != screen_width:
                x = int(x * screen_width / self.config.grounding_width)
            if self.config.grounding_height != screen_height:
                y = int(y * screen_height / self.config.grounding_height)
            
            return UIElement(
                name=target,
                center=(x, y),
                confidence=0.9,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse grounding model output: {e}")
            return None
    
    def locate_all(
        self,
        screenshot_base64: str,
        screen_width: int = 1920,
        screen_height: int = 1080
    ) -> List[UIElement]:
        """
        定位所有可交互元素
        
        返回屏幕上所有检测到的 UI 元素
        """
        if not self._llm_client:
            return []
        
        prompt = self.MULTI_ELEMENT_PROMPT.format(
            width=screen_width,
            height=screen_height
        )
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ]
            
            response = self._llm_client.completion(
                model=self.config.vision_model,
                messages=messages,
                api_key=self.config.vision_api_key,
                base_url=self.config.vision_base_url,
                max_tokens=2000,
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            return self._parse_multi_element_response(content)
            
        except Exception as e:
            logger.error(f"Failed to locate all elements: {e}")
            return []
    
    def _parse_multi_element_response(self, response: str) -> List[UIElement]:
        """解析多元素定位结果"""
        elements = []
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return elements
            
            data = json.loads(json_match.group())
            
            for elem_data in data.get("elements", []):
                elements.append(UIElement(
                    name=elem_data.get("name", ""),
                    element_type=elem_data.get("type", "unknown"),
                    center=(elem_data.get("x", 0), elem_data.get("y", 0)),
                    text=elem_data.get("text"),
                ))
        
        except Exception as e:
            logger.error(f"Failed to parse multi-element response: {e}")
        
        return elements
    
    def set_vision_model(
        self, 
        model: str, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> None:
        """设置视觉模型"""
        self.config.vision_model = model
        if api_key:
            self.config.vision_api_key = api_key
        if base_url:
            self.config.vision_base_url = base_url
    
    def set_grounding_model(
        self,
        model: str,
        url: str,
        api_key: Optional[str] = None,
        width: int = 1920,
        height: int = 1080
    ) -> None:
        """设置专用 Grounding 模型"""
        self.config.method = GroundingMethod.GROUNDING_MODEL
        self.config.grounding_model = model
        self.config.grounding_url = url
        self.config.grounding_api_key = api_key
        self.config.grounding_width = width
        self.config.grounding_height = height

