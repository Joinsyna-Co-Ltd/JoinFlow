"""
Image Processing Module
=======================

Enhanced image processing capabilities:
- Image understanding (GPT-4V, Claude 3 Vision)
- OCR text extraction
- Image editing (crop, resize, annotate)
- Image generation (DALL-E, Stable Diffusion)
"""

import base64
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """支持的图像格式"""
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    BMP = "bmp"


@dataclass
class ImageAnalysisResult:
    """图像分析结果"""
    description: str = ""
    objects: List[str] = field(default_factory=list)
    text_content: Optional[str] = None
    colors: List[str] = field(default_factory=list)
    dimensions: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "objects": self.objects,
            "text_content": self.text_content,
            "colors": self.colors,
            "dimensions": self.dimensions,
            "format": self.format,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class ImageGenerationResult:
    """图像生成结果"""
    image_data: str = ""  # base64
    prompt: str = ""
    model: str = ""
    dimensions: Tuple[int, int] = (1024, 1024)
    format: str = "png"
    
    def save(self, path: str):
        """保存图像到文件"""
        data = base64.b64decode(self.image_data)
        Path(path).write_bytes(data)


class ImageProcessor:
    """
    图像处理器
    
    功能：
    - 图像理解和描述
    - OCR文字提取
    - 图像编辑
    - 图像生成
    """
    
    def __init__(
        self,
        workspace: str = "./workspace",
        default_model: str = "gpt-4o"
    ):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.default_model = default_model
    
    # ========================
    # 图像理解
    # ========================
    
    def analyze(
        self,
        image: Union[str, bytes, Path],
        prompt: str = "请详细描述这张图片的内容",
        model: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        分析图像内容
        
        Args:
            image: 图像路径、base64字符串或字节数据
            prompt: 分析提示词
            model: 使用的模型
            
        Returns:
            ImageAnalysisResult: 分析结果
        """
        image_data, image_format, dimensions = self._prepare_image(image)
        
        try:
            response = self._call_vision_model(
                image_data,
                prompt,
                model or self.default_model
            )
            
            return ImageAnalysisResult(
                description=response,
                dimensions=dimensions,
                format=image_format,
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return ImageAnalysisResult(
                description=f"分析失败: {str(e)}",
                confidence=0.0
            )
    
    def extract_text(
        self,
        image: Union[str, bytes, Path],
        language: str = "auto"
    ) -> str:
        """
        OCR提取图像中的文字
        
        Args:
            image: 图像数据
            language: 语言（auto自动检测）
            
        Returns:
            提取的文字内容
        """
        image_data, _, _ = self._prepare_image(image)
        
        prompt = "请提取并列出这张图片中的所有文字内容。按照图片中的位置顺序排列，保持原有格式。"
        if language != "auto":
            prompt += f" 文字语言为{language}。"
        
        try:
            return self._call_vision_model(image_data, prompt)
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return f"文字提取失败: {str(e)}"
    
    def answer_question(
        self,
        image: Union[str, bytes, Path],
        question: str
    ) -> str:
        """
        回答关于图像的问题
        
        Args:
            image: 图像数据
            question: 问题
            
        Returns:
            回答
        """
        image_data, _, _ = self._prepare_image(image)
        prompt = f"根据这张图片回答问题: {question}"
        
        try:
            return self._call_vision_model(image_data, prompt)
        except Exception as e:
            logger.error(f"Visual QA failed: {e}")
            return f"回答失败: {str(e)}"
    
    def detect_objects(
        self,
        image: Union[str, bytes, Path]
    ) -> List[Dict[str, Any]]:
        """
        检测图像中的物体
        
        Args:
            image: 图像数据
            
        Returns:
            检测到的物体列表
        """
        image_data, _, _ = self._prepare_image(image)
        
        prompt = """请识别并列出这张图片中的所有物体。
对于每个物体，请提供：
1. 物体名称
2. 大致位置（左上/右上/中间/左下/右下等）
3. 置信度（高/中/低）

请以JSON格式返回，例如：
[{"name": "猫", "position": "中间", "confidence": "高"}]
"""
        
        try:
            response = self._call_vision_model(image_data, prompt)
            # 尝试解析JSON
            import json
            import re
            
            # 提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    # ========================
    # 图像编辑
    # ========================
    
    def resize(
        self,
        image: Union[str, bytes, Path],
        width: int,
        height: int,
        keep_aspect: bool = True
    ) -> bytes:
        """
        调整图像大小
        
        Args:
            image: 图像数据
            width: 目标宽度
            height: 目标高度
            keep_aspect: 是否保持宽高比
            
        Returns:
            调整后的图像字节数据
        """
        try:
            from PIL import Image
            
            img = self._load_pil_image(image)
            
            if keep_aspect:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format=img.format or 'PNG')
            return buffer.getvalue()
            
        except ImportError:
            raise RuntimeError("PIL/Pillow is required for image editing")
    
    def crop(
        self,
        image: Union[str, bytes, Path],
        left: int,
        top: int,
        right: int,
        bottom: int
    ) -> bytes:
        """
        裁剪图像
        
        Args:
            image: 图像数据
            left, top, right, bottom: 裁剪区域
            
        Returns:
            裁剪后的图像字节数据
        """
        try:
            from PIL import Image
            
            img = self._load_pil_image(image)
            cropped = img.crop((left, top, right, bottom))
            
            buffer = io.BytesIO()
            cropped.save(buffer, format=img.format or 'PNG')
            return buffer.getvalue()
            
        except ImportError:
            raise RuntimeError("PIL/Pillow is required for image editing")
    
    def add_text(
        self,
        image: Union[str, bytes, Path],
        text: str,
        position: Tuple[int, int] = (10, 10),
        font_size: int = 24,
        color: str = "white"
    ) -> bytes:
        """
        在图像上添加文字
        
        Args:
            image: 图像数据
            text: 要添加的文字
            position: 文字位置 (x, y)
            font_size: 字体大小
            color: 文字颜色
            
        Returns:
            添加文字后的图像字节数据
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = self._load_pil_image(image)
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            draw.text(position, text, fill=color, font=font)
            
            buffer = io.BytesIO()
            img.save(buffer, format=img.format or 'PNG')
            return buffer.getvalue()
            
        except ImportError:
            raise RuntimeError("PIL/Pillow is required for image editing")
    
    def convert_format(
        self,
        image: Union[str, bytes, Path],
        target_format: ImageFormat
    ) -> bytes:
        """
        转换图像格式
        
        Args:
            image: 图像数据
            target_format: 目标格式
            
        Returns:
            转换后的图像字节数据
        """
        try:
            from PIL import Image
            
            img = self._load_pil_image(image)
            
            # 处理透明度
            if target_format == ImageFormat.JPEG and img.mode == 'RGBA':
                img = img.convert('RGB')
            
            buffer = io.BytesIO()
            img.save(buffer, format=target_format.value.upper())
            return buffer.getvalue()
            
        except ImportError:
            raise RuntimeError("PIL/Pillow is required for image conversion")
    
    # ========================
    # 图像生成
    # ========================
    
    def generate(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> ImageGenerationResult:
        """
        生成图像
        
        Args:
            prompt: 图像描述
            model: 生成模型
            size: 图像尺寸
            quality: 图像质量
            
        Returns:
            ImageGenerationResult: 生成结果
        """
        try:
            import litellm
            
            response = litellm.image_generation(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                response_format="b64_json"
            )
            
            image_data = response.data[0].b64_json
            width, height = map(int, size.split('x'))
            
            return ImageGenerationResult(
                image_data=image_data,
                prompt=prompt,
                model=model,
                dimensions=(width, height)
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    # ========================
    # 辅助方法
    # ========================
    
    def _prepare_image(
        self,
        image: Union[str, bytes, Path]
    ) -> Tuple[str, str, Optional[Tuple[int, int]]]:
        """
        准备图像数据
        
        Returns:
            (base64数据, 格式, 尺寸)
        """
        dimensions = None
        image_format = "jpeg"
        
        if isinstance(image, (str, Path)):
            path = Path(image)
            
            # 如果是base64字符串
            if isinstance(image, str) and not path.exists():
                if image.startswith("data:"):
                    # data URL格式
                    parts = image.split(",", 1)
                    return parts[1] if len(parts) > 1 else image, image_format, dimensions
                return image, image_format, dimensions
            
            # 读取文件
            if path.exists():
                image_format = path.suffix[1:].lower()
                data = path.read_bytes()
                
                # 获取尺寸
                try:
                    from PIL import Image
                    img = Image.open(path)
                    dimensions = img.size
                except:
                    pass
                
                return base64.b64encode(data).decode(), image_format, dimensions
            else:
                raise FileNotFoundError(f"Image not found: {image}")
        
        elif isinstance(image, bytes):
            # 尝试获取格式和尺寸
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(image))
                dimensions = img.size
                image_format = img.format.lower() if img.format else "jpeg"
            except:
                pass
            
            return base64.b64encode(image).decode(), image_format, dimensions
        
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
    
    def _load_pil_image(self, image: Union[str, bytes, Path]):
        """加载为PIL Image对象"""
        from PIL import Image
        
        if isinstance(image, bytes):
            return Image.open(io.BytesIO(image))
        elif isinstance(image, (str, Path)):
            path = Path(image)
            if path.exists():
                return Image.open(path)
            else:
                # 尝试作为base64解码
                data = base64.b64decode(image)
                return Image.open(io.BytesIO(data))
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
    
    def _call_vision_model(
        self,
        image_data: str,
        prompt: str,
        model: Optional[str] = None
    ) -> str:
        """调用视觉模型"""
        try:
            import litellm
            
            # 确定媒体类型
            if image_data.startswith("/9j/"):
                media_type = "image/jpeg"
            elif image_data.startswith("iVBOR"):
                media_type = "image/png"
            else:
                media_type = "image/jpeg"
            
            response = litellm.completion(
                model=model or self.default_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Vision model call failed: {e}")
            raise
    
    def save_image(
        self,
        data: Union[str, bytes],
        filename: str
    ) -> Path:
        """
        保存图像到工作区
        
        Args:
            data: 图像数据（base64或字节）
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        if isinstance(data, str):
            data = base64.b64decode(data)
        
        path = self.workspace / filename
        path.write_bytes(data)
        return path

