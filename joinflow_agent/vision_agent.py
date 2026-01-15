"""
Vision Agent
============

Provides multi-modal capabilities:
- Image understanding and analysis
- OCR (text extraction from images)
- Image description generation
- Visual Q&A
"""

import base64
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Dict, List
from pathlib import Path
import logging

from .base import (
    BaseAgent, AgentResult, AgentConfig, AgentType,
    AgentAction, Tool
)

logger = logging.getLogger(__name__)


@dataclass
class ImageAnalysis:
    """Result of image analysis"""
    description: str
    objects: List[str]
    text_content: Optional[str] = None
    colors: Optional[List[str]] = None
    dimensions: Optional[tuple] = None
    format: Optional[str] = None


class VisionAgent(BaseAgent):
    """
    Agent for image understanding and multi-modal tasks.
    
    Capabilities:
    - Analyze images and describe content
    - Extract text from images (OCR)
    - Answer questions about images
    - Process screenshots from other agents
    
    Uses vision-capable LLMs (GPT-4V, Claude 3, etc.)
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self._workspace = Path(config.os_workspace if config else "./workspace")
        self._workspace.mkdir(parents=True, exist_ok=True)
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.LLM
    
    @property
    def name(self) -> str:
        return "Vision Agent"
    
    @property
    def description(self) -> str:
        return """Vision agent capable of:
        - Analyzing images and describing their content
        - Extracting text from images (OCR)
        - Answering questions about images
        - Processing screenshots and diagrams
        """
    
    def can_handle(self, task: str) -> bool:
        """Check if this is a vision task"""
        vision_keywords = [
            "图片", "图像", "照片", "截图", "看", "识别",
            "image", "picture", "photo", "screenshot", "看图",
            "ocr", "文字识别", "describe", "描述图",
            ".jpg", ".png", ".jpeg", ".gif", ".webp"
        ]
        return any(kw in task.lower() for kw in vision_keywords)
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Execute a vision task"""
        result = self._create_result()
        
        try:
            # Extract image from task or context
            image_data, image_path = self._get_image(task, context)
            
            if not image_data:
                result.output = "没有找到图片。请提供图片路径或base64编码的图片数据。"
                result.finalize(success=False, error="No image provided")
                return result
            
            # Parse task type
            if any(kw in task.lower() for kw in ["ocr", "文字", "text", "提取"]):
                output = self._extract_text(image_data, result)
            elif any(kw in task.lower() for kw in ["问", "question", "？", "?"]):
                question = self._extract_question(task)
                output = self._answer_question(image_data, question, result)
            else:
                output = self._describe_image(image_data, result)
            
            result.output = output
            result.data = {
                "image_path": str(image_path) if image_path else None,
                "task_type": "vision"
            }
            result.finalize(success=True)
            
        except Exception as e:
            self._handle_error(result, e)
        
        return result
    
    def _get_image(self, task: str, context: Optional[dict]) -> tuple[Optional[str], Optional[Path]]:
        """Get image data from task or context"""
        import re
        
        # Check context for image data
        if context and context.get("image_base64"):
            return context["image_base64"], None
        
        if context and context.get("image_path"):
            path = Path(context["image_path"])
            if path.exists():
                return self._encode_image(path), path
        
        # Extract path from task
        path_pattern = r'["\']?([^\s"\']+\.(jpg|jpeg|png|gif|webp|bmp))["\']?'
        match = re.search(path_pattern, task, re.IGNORECASE)
        
        if match:
            path = Path(match.group(1))
            if not path.is_absolute():
                path = self._workspace / path
            
            if path.exists():
                return self._encode_image(path), path
        
        return None, None
    
    def _encode_image(self, path: Path) -> str:
        """Encode image file to base64"""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def _extract_question(self, task: str) -> str:
        """Extract question from task"""
        import re
        # Remove image path references
        clean_task = re.sub(r'["\']?[^\s"\']+\.(jpg|jpeg|png|gif|webp)["\']?', '', task, flags=re.IGNORECASE)
        # Remove common prefixes
        for prefix in ["看图", "根据图片", "分析图片", "图片中"]:
            clean_task = clean_task.replace(prefix, "")
        return clean_task.strip()
    
    def _describe_image(self, image_data: str, result: AgentResult) -> str:
        """Describe image content"""
        self._log_action(result, "describe_image", "Analyzing image content")
        
        return self._call_vision_llm(
            image_data,
            "请详细描述这张图片的内容，包括主要物体、场景、颜色、文字等信息。"
        )
    
    def _extract_text(self, image_data: str, result: AgentResult) -> str:
        """Extract text from image (OCR)"""
        self._log_action(result, "ocr", "Extracting text from image")
        
        return self._call_vision_llm(
            image_data,
            "请提取并列出这张图片中的所有文字内容。按照图片中的位置顺序排列。"
        )
    
    def _answer_question(self, image_data: str, question: str, result: AgentResult) -> str:
        """Answer question about image"""
        self._log_action(result, "visual_qa", f"Answering: {question[:50]}...")
        
        return self._call_vision_llm(
            image_data,
            f"根据这张图片回答问题: {question}"
        )
    
    def _call_vision_llm(self, image_data: str, prompt: str) -> str:
        """Call vision-capable LLM"""
        try:
            import litellm
            
            # Determine image format
            if image_data.startswith("/9j/"):
                media_type = "image/jpeg"
            elif image_data.startswith("iVBOR"):
                media_type = "image/png"
            else:
                media_type = "image/jpeg"
            
            response = litellm.completion(
                model=self.config.llm_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Vision LLM error: {e}")
            return f"图片分析失败: {str(e)}"
    
    def analyze_image(self, image_path: str) -> ImageAnalysis:
        """Analyze image and return structured result"""
        result = self._create_result()
        
        path = Path(image_path)
        if not path.is_absolute():
            path = self._workspace / path
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image_data = self._encode_image(path)
        
        # Get description
        description = self._call_vision_llm(
            image_data,
            "描述这张图片的主要内容。"
        )
        
        # Try to get image info
        try:
            from PIL import Image
            img = Image.open(path)
            dimensions = img.size
            img_format = img.format
        except ImportError:
            dimensions = None
            img_format = path.suffix[1:].upper()
        
        return ImageAnalysis(
            description=description,
            objects=[],  # Would need object detection
            text_content=None,
            dimensions=dimensions,
            format=img_format
        )
    
    def get_tools(self) -> List[Tool]:
        """Get tools for LLM function calling"""
        return [
            Tool(
                name="vision_describe",
                description="Describe the content of an image",
                func=lambda path: self.execute(f"描述图片 {path}").output,
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the image file"}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="vision_ocr",
                description="Extract text from an image (OCR)",
                func=lambda path: self.execute(f"OCR提取文字 {path}").output,
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the image file"}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="vision_qa",
                description="Answer a question about an image",
                func=lambda path, question: self.execute(f"{path} {question}").output,
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the image file"},
                        "question": {"type": "string", "description": "Question about the image"}
                    },
                    "required": ["path", "question"]
                }
            ),
        ]

