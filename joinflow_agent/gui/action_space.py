"""
Action Space - 动作空间定义
===========================

定义 GUI Agent 可执行的所有动作类型。
参考 Agent-S 的 Agent-Computer Interface (ACI) 设计。
"""

import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """动作类型枚举"""
    # 鼠标操作
    CLICK = "click"                    # 单击
    DOUBLE_CLICK = "double_click"      # 双击
    RIGHT_CLICK = "right_click"        # 右键点击
    DRAG = "drag"                      # 拖拽
    SCROLL = "scroll"                  # 滚动
    HOVER = "hover"                    # 悬停
    
    # 键盘操作
    TYPE = "type"                      # 输入文本
    PRESS = "press"                    # 按键
    HOTKEY = "hotkey"                  # 组合键
    
    # 系统操作
    SCREENSHOT = "screenshot"          # 截图
    WAIT = "wait"                      # 等待
    OPEN_APP = "open_app"              # 打开应用
    OPEN_URL = "open_url"              # 打开URL
    
    # 控制操作
    DONE = "done"                      # 任务完成
    FAIL = "fail"                      # 任务失败
    THINK = "think"                    # 思考（不执行动作）


@dataclass
class Action:
    """
    表示一个可执行的动作
    
    Attributes:
        action_type: 动作类型
        target: 目标元素描述（用于 grounding）
        coordinates: 屏幕坐标 (x, y)
        text: 输入的文本（用于 type 动作）
        key: 按键名称（用于 press/hotkey）
        duration: 动作持续时间
        reason: 执行此动作的原因
    """
    action_type: ActionType
    target: Optional[str] = None           # 目标元素描述
    coordinates: Optional[Tuple[int, int]] = None  # (x, y) 坐标
    text: Optional[str] = None             # 输入文本
    key: Optional[str] = None              # 按键
    keys: Optional[List[str]] = None       # 组合键列表
    scroll_amount: int = 0                 # 滚动量
    duration: float = 0.5                  # 持续时间
    reason: str = ""                       # 执行原因
    
    # 执行结果
    executed: bool = False
    success: bool = False
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "action_type": self.action_type.value,
            "target": self.target,
            "coordinates": self.coordinates,
            "text": self.text,
            "key": self.key,
            "keys": self.keys,
            "scroll_amount": self.scroll_amount,
            "reason": self.reason,
            "executed": self.executed,
            "success": self.success,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Action":
        """从字典创建"""
        return cls(
            action_type=ActionType(data.get("action_type", "click")),
            target=data.get("target"),
            coordinates=tuple(data["coordinates"]) if data.get("coordinates") else None,
            text=data.get("text"),
            key=data.get("key"),
            keys=data.get("keys"),
            scroll_amount=data.get("scroll_amount", 0),
            reason=data.get("reason", ""),
        )
    
    def __str__(self) -> str:
        parts = [f"Action({self.action_type.value}"]
        if self.target:
            parts.append(f", target='{self.target}'")
        if self.coordinates:
            parts.append(f", pos={self.coordinates}")
        if self.text:
            parts.append(f", text='{self.text[:20]}...'")
        if self.key:
            parts.append(f", key='{self.key}'")
        parts.append(")")
        return "".join(parts)


class ActionExecutor:
    """
    动作执行器
    
    负责将 Action 转换为实际的系统操作（使用 pyautogui）
    """
    
    def __init__(self, fail_safe: bool = True, pause: float = 0.1):
        """
        初始化执行器
        
        Args:
            fail_safe: 启用 pyautogui 安全模式（鼠标移到角落会中断）
            pause: 每个动作之间的暂停时间
        """
        self.fail_safe = fail_safe
        self.pause = pause
        self._initialized = False
        self._pyautogui = None
        
        self._init_pyautogui()
    
    def _init_pyautogui(self) -> bool:
        """初始化 pyautogui"""
        try:
            import pyautogui
            pyautogui.FAILSAFE = self.fail_safe
            pyautogui.PAUSE = self.pause
            self._pyautogui = pyautogui
            self._initialized = True
            logger.info("ActionExecutor initialized with pyautogui")
            return True
        except ImportError:
            logger.warning("pyautogui not installed. Run: pip install pyautogui")
            return False
    
    @property
    def screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        if self._pyautogui:
            return self._pyautogui.size()
        return (1920, 1080)  # 默认值
    
    def execute(self, action: Action) -> Action:
        """
        执行动作
        
        Args:
            action: 要执行的动作
            
        Returns:
            更新后的 Action（包含执行结果）
        """
        if not self._initialized:
            action.error = "pyautogui not initialized"
            action.success = False
            action.executed = True
            return action
        
        try:
            logger.info(f"Executing: {action}")
            
            # 根据动作类型执行
            if action.action_type == ActionType.CLICK:
                self._execute_click(action)
            
            elif action.action_type == ActionType.DOUBLE_CLICK:
                self._execute_double_click(action)
            
            elif action.action_type == ActionType.RIGHT_CLICK:
                self._execute_right_click(action)
            
            elif action.action_type == ActionType.TYPE:
                self._execute_type(action)
            
            elif action.action_type == ActionType.PRESS:
                self._execute_press(action)
            
            elif action.action_type == ActionType.HOTKEY:
                self._execute_hotkey(action)
            
            elif action.action_type == ActionType.SCROLL:
                self._execute_scroll(action)
            
            elif action.action_type == ActionType.HOVER:
                self._execute_hover(action)
            
            elif action.action_type == ActionType.DRAG:
                self._execute_drag(action)
            
            elif action.action_type == ActionType.WAIT:
                self._execute_wait(action)
            
            elif action.action_type == ActionType.OPEN_APP:
                self._execute_open_app(action)
            
            elif action.action_type == ActionType.OPEN_URL:
                self._execute_open_url(action)
            
            elif action.action_type in (ActionType.DONE, ActionType.FAIL, ActionType.THINK):
                # 这些是控制动作，不需要执行
                pass
            
            else:
                action.error = f"Unknown action type: {action.action_type}"
                action.success = False
                action.executed = True
                return action
            
            action.success = True
            action.executed = True
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            action.error = str(e)
            action.success = False
            action.executed = True
        
        return action
    
    def _execute_click(self, action: Action) -> None:
        """执行点击"""
        if action.coordinates:
            x, y = action.coordinates
            self._pyautogui.click(x, y)
        else:
            self._pyautogui.click()
    
    def _execute_double_click(self, action: Action) -> None:
        """执行双击"""
        if action.coordinates:
            x, y = action.coordinates
            self._pyautogui.doubleClick(x, y)
        else:
            self._pyautogui.doubleClick()
    
    def _execute_right_click(self, action: Action) -> None:
        """执行右键点击"""
        if action.coordinates:
            x, y = action.coordinates
            self._pyautogui.rightClick(x, y)
        else:
            self._pyautogui.rightClick()
    
    def _execute_type(self, action: Action) -> None:
        """执行文本输入"""
        if action.text:
            # 如果有坐标，先点击
            if action.coordinates:
                x, y = action.coordinates
                self._pyautogui.click(x, y)
                time.sleep(0.1)
            
            # 对于中文和特殊字符，使用剪贴板
            try:
                import pyperclip
                pyperclip.copy(action.text)
                # Ctrl+V 粘贴
                self._pyautogui.hotkey('ctrl', 'v')
            except ImportError:
                # 回退到 typewrite（仅支持英文）
                self._pyautogui.typewrite(action.text, interval=0.05)
    
    def _execute_press(self, action: Action) -> None:
        """执行按键"""
        if action.key:
            self._pyautogui.press(action.key)
    
    def _execute_hotkey(self, action: Action) -> None:
        """执行组合键"""
        if action.keys:
            self._pyautogui.hotkey(*action.keys)
        elif action.key:
            # 解析 "ctrl+c" 格式
            keys = action.key.split('+')
            self._pyautogui.hotkey(*keys)
    
    def _execute_scroll(self, action: Action) -> None:
        """执行滚动"""
        if action.coordinates:
            x, y = action.coordinates
            self._pyautogui.moveTo(x, y)
        self._pyautogui.scroll(action.scroll_amount)
    
    def _execute_hover(self, action: Action) -> None:
        """执行悬停"""
        if action.coordinates:
            x, y = action.coordinates
            self._pyautogui.moveTo(x, y, duration=action.duration)
    
    def _execute_drag(self, action: Action) -> None:
        """执行拖拽"""
        # 需要起点和终点坐标
        # coordinates 是起点，需要从其他字段获取终点
        if action.coordinates:
            x, y = action.coordinates
            self._pyautogui.moveTo(x, y)
            # 拖拽到相对位置（由 scroll_amount 临时复用）
            self._pyautogui.drag(action.scroll_amount, 0, duration=action.duration)
    
    def _execute_wait(self, action: Action) -> None:
        """执行等待"""
        time.sleep(action.duration)
    
    def _execute_open_app(self, action: Action) -> None:
        """打开应用程序"""
        import platform
        import subprocess
        
        app_name = action.text or action.target
        if not app_name:
            raise ValueError("No app name specified")
        
        system = platform.system()
        
        if system == "Windows":
            subprocess.Popen(f'start "" "{app_name}"', shell=True)
        elif system == "Darwin":  # macOS
            subprocess.Popen(['open', '-a', app_name])
        else:  # Linux
            subprocess.Popen([app_name], start_new_session=True)
    
    def _execute_open_url(self, action: Action) -> None:
        """打开 URL"""
        import webbrowser
        url = action.text or action.target
        if url:
            webbrowser.open(url)


# 预定义动作工厂函数
def click(target: str = None, x: int = None, y: int = None, reason: str = "") -> Action:
    """创建点击动作"""
    coords = (x, y) if x is not None and y is not None else None
    return Action(ActionType.CLICK, target=target, coordinates=coords, reason=reason)


def double_click(target: str = None, x: int = None, y: int = None, reason: str = "") -> Action:
    """创建双击动作"""
    coords = (x, y) if x is not None and y is not None else None
    return Action(ActionType.DOUBLE_CLICK, target=target, coordinates=coords, reason=reason)


def type_text(text: str, target: str = None, x: int = None, y: int = None, reason: str = "") -> Action:
    """创建输入文本动作"""
    coords = (x, y) if x is not None and y is not None else None
    return Action(ActionType.TYPE, target=target, coordinates=coords, text=text, reason=reason)


def press_key(key: str, reason: str = "") -> Action:
    """创建按键动作"""
    return Action(ActionType.PRESS, key=key, reason=reason)


def hotkey(*keys, reason: str = "") -> Action:
    """创建组合键动作"""
    return Action(ActionType.HOTKEY, keys=list(keys), reason=reason)


def scroll(amount: int, x: int = None, y: int = None, reason: str = "") -> Action:
    """创建滚动动作"""
    coords = (x, y) if x is not None and y is not None else None
    return Action(ActionType.SCROLL, coordinates=coords, scroll_amount=amount, reason=reason)


def wait(seconds: float, reason: str = "") -> Action:
    """创建等待动作"""
    return Action(ActionType.WAIT, duration=seconds, reason=reason)


def done(reason: str = "Task completed successfully") -> Action:
    """创建完成动作"""
    return Action(ActionType.DONE, reason=reason)


def fail(reason: str = "Task failed") -> Action:
    """创建失败动作"""
    return Action(ActionType.FAIL, reason=reason)


def think(reason: str = "") -> Action:
    """创建思考动作（不执行实际操作）"""
    return Action(ActionType.THINK, reason=reason)

