"""
Screen Parser - 屏幕解析模块
============================

负责截取和解析屏幕内容，提取 UI 元素信息。
"""

import io
import base64
import logging
import platform
import tempfile
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScreenState:
    """
    屏幕状态快照
    
    包含截图和相关元数据
    """
    # 截图数据
    screenshot_bytes: Optional[bytes] = None
    screenshot_base64: Optional[str] = None
    screenshot_path: Optional[str] = None
    
    # 屏幕信息
    width: int = 1920
    height: int = 1080
    scale_factor: float = 1.0
    
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 可选：OCR 识别的文本
    ocr_text: Optional[str] = None
    
    # 可选：UI 元素列表
    ui_elements: List[Any] = field(default_factory=list)
    
    def get_base64(self) -> str:
        """获取 base64 编码的截图"""
        if self.screenshot_base64:
            return self.screenshot_base64
        if self.screenshot_bytes:
            self.screenshot_base64 = base64.b64encode(self.screenshot_bytes).decode()
            return self.screenshot_base64
        return ""
    
    def get_bytes(self) -> bytes:
        """获取截图字节数据"""
        if self.screenshot_bytes:
            return self.screenshot_bytes
        if self.screenshot_base64:
            self.screenshot_bytes = base64.b64decode(self.screenshot_base64)
            return self.screenshot_bytes
        return b""
    
    def save(self, path: str) -> str:
        """保存截图到文件"""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(self.get_bytes())
        
        self.screenshot_path = str(file_path)
        return self.screenshot_path
    
    def to_dict(self) -> dict:
        """转换为字典（不含图片数据）"""
        return {
            "width": self.width,
            "height": self.height,
            "scale_factor": self.scale_factor,
            "timestamp": self.timestamp.isoformat(),
            "has_screenshot": self.screenshot_bytes is not None,
            "screenshot_path": self.screenshot_path,
            "ocr_text": self.ocr_text,
            "ui_elements_count": len(self.ui_elements),
        }


class ScreenParser:
    """
    屏幕解析器
    
    功能：
    - 截取全屏或指定区域
    - 获取屏幕尺寸和缩放因子
    - 可选的 OCR 文本提取
    - 可选的 UI 元素识别
    """
    
    def __init__(self):
        self._pyautogui = None
        self._pillow = None
        self._platform = platform.system()
        
        self._init_dependencies()
    
    def _init_dependencies(self) -> None:
        """初始化依赖"""
        try:
            import pyautogui
            self._pyautogui = pyautogui
        except ImportError:
            logger.warning("pyautogui not available")
        
        try:
            from PIL import Image
            self._pillow = Image
        except ImportError:
            logger.warning("Pillow not available")
    
    @property
    def screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        if self._pyautogui:
            return self._pyautogui.size()
        return (1920, 1080)
    
    @property
    def scale_factor(self) -> float:
        """获取屏幕缩放因子"""
        try:
            if self._platform == "Windows":
                import ctypes
                try:
                    # Windows 8.1+
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except:
                    pass
                return ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
            elif self._platform == "Darwin":
                # macOS - 通常是 2x Retina
                return 2.0
        except:
            pass
        return 1.0
    
    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> ScreenState:
        """
        截取屏幕
        
        Args:
            region: 截取区域 (left, top, width, height)，None 表示全屏
            
        Returns:
            ScreenState 包含截图数据
        """
        state = ScreenState()
        width, height = self.screen_size
        state.width = width
        state.height = height
        state.scale_factor = self.scale_factor
        
        try:
            if self._pyautogui and self._pillow:
                # 使用 pyautogui 截图
                screenshot = self._pyautogui.screenshot(region=region)
                
                # 转换为 bytes
                buffer = io.BytesIO()
                screenshot.save(buffer, format='PNG')
                state.screenshot_bytes = buffer.getvalue()
                
                logger.debug(f"Captured screenshot: {width}x{height}")
                
            else:
                # 使用原生方法
                state = self._capture_native(region)
                
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
        
        return state
    
    def _capture_native(self, region: Optional[Tuple[int, int, int, int]] = None) -> ScreenState:
        """使用原生方法截图"""
        state = ScreenState()
        
        try:
            if self._platform == "Windows":
                state = self._capture_windows(region)
            elif self._platform == "Darwin":
                state = self._capture_macos(region)
            elif self._platform == "Linux":
                state = self._capture_linux(region)
        except Exception as e:
            logger.error(f"Native screenshot failed: {e}")
        
        return state
    
    def _capture_windows(self, region=None) -> ScreenState:
        """Windows 原生截图"""
        import subprocess
        
        state = ScreenState()
        temp_path = Path(tempfile.gettempdir()) / f"screenshot_{int(time.time())}.png"
        
        # 使用 PowerShell 截图
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size)
        $bitmap.Save("{temp_path}")
        '''
        
        subprocess.run(["powershell", "-Command", ps_script], 
                      capture_output=True, check=True)
        
        if temp_path.exists():
            state.screenshot_bytes = temp_path.read_bytes()
            state.screenshot_path = str(temp_path)
            state.width, state.height = self._get_image_size(state.screenshot_bytes)
        
        return state
    
    def _capture_macos(self, region=None) -> ScreenState:
        """macOS 原生截图"""
        import subprocess
        
        state = ScreenState()
        temp_path = Path(tempfile.gettempdir()) / f"screenshot_{int(time.time())}.png"
        
        subprocess.run(["screencapture", "-x", str(temp_path)], check=True)
        
        if temp_path.exists():
            state.screenshot_bytes = temp_path.read_bytes()
            state.screenshot_path = str(temp_path)
            state.width, state.height = self._get_image_size(state.screenshot_bytes)
        
        return state
    
    def _capture_linux(self, region=None) -> ScreenState:
        """Linux 原生截图"""
        import subprocess
        
        state = ScreenState()
        temp_path = Path(tempfile.gettempdir()) / f"screenshot_{int(time.time())}.png"
        
        try:
            # 尝试 scrot
            subprocess.run(["scrot", str(temp_path)], check=True)
        except:
            try:
                # 尝试 gnome-screenshot
                subprocess.run(["gnome-screenshot", "-f", str(temp_path)], check=True)
            except:
                # 尝试 import (ImageMagick)
                subprocess.run(["import", "-window", "root", str(temp_path)], check=True)
        
        if temp_path.exists():
            state.screenshot_bytes = temp_path.read_bytes()
            state.screenshot_path = str(temp_path)
            state.width, state.height = self._get_image_size(state.screenshot_bytes)
        
        return state
    
    def _get_image_size(self, image_bytes: bytes) -> Tuple[int, int]:
        """从图片数据获取尺寸"""
        if self._pillow:
            img = self._pillow.open(io.BytesIO(image_bytes))
            return img.size
        return (1920, 1080)
    
    def capture_and_resize(
        self, 
        max_width: int = 1920, 
        max_height: int = 1080,
        quality: int = 85
    ) -> ScreenState:
        """
        截图并调整大小（用于发送给 LLM）
        
        Args:
            max_width: 最大宽度
            max_height: 最大高度
            quality: JPEG 质量 (1-100)
        """
        state = self.capture()
        
        if not state.screenshot_bytes or not self._pillow:
            return state
        
        try:
            img = self._pillow.open(io.BytesIO(state.screenshot_bytes))
            
            # 计算缩放比例
            ratio = min(max_width / img.width, max_height / img.height, 1.0)
            
            if ratio < 1.0:
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, self._pillow.LANCZOS)
                
                # 转换为 JPEG（更小的文件）
                buffer = io.BytesIO()
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(buffer, format='JPEG', quality=quality)
                state.screenshot_bytes = buffer.getvalue()
                state.screenshot_base64 = None  # 清除缓存
                state.width, state.height = new_size
                
                logger.debug(f"Resized screenshot to {new_size}")
        
        except Exception as e:
            logger.error(f"Failed to resize screenshot: {e}")
        
        return state
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> ScreenState:
        """截取指定区域"""
        return self.capture(region=(x, y, width, height))
    
    def capture_window(self, window_title: str) -> ScreenState:
        """截取指定窗口（跨平台支持）"""
        # 这个功能需要额外的库支持，暂时使用全屏截图
        logger.warning(f"Window capture not fully implemented, using full screen")
        return self.capture()
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        if self._pyautogui:
            return self._pyautogui.position()
        return (0, 0)
    
    def get_active_window_info(self) -> dict:
        """获取当前活动窗口信息"""
        info = {"title": "", "rect": None}
        
        try:
            if self._platform == "Windows":
                import ctypes
                from ctypes import wintypes
                
                user32 = ctypes.windll.user32
                hwnd = user32.GetForegroundWindow()
                
                length = user32.GetWindowTextLengthW(hwnd)
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                info["title"] = buffer.value
                
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                info["rect"] = (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
                
        except Exception as e:
            logger.debug(f"Could not get active window info: {e}")
        
        return info

