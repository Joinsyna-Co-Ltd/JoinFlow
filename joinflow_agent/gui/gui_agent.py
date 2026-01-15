"""
GUI Agent - 主控制器
====================

类似 Agent-S 的 GUI 自动化 Agent。
能够像人一样通过视觉理解和操作电脑。

主要功能:
1. 屏幕截图和状态感知
2. 视觉理解（使用多模态 LLM）
3. UI 元素定位（Grounding）
4. 动作规划和执行
5. 任务进度追踪和反思

工作流程:
截图 → LLM 分析 → 生成动作 → Grounding 定位 → 执行动作 → 循环
"""

import json
import re
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Tuple
from datetime import datetime
from enum import Enum

from .screen_parser import ScreenParser, ScreenState
from .grounding import GroundingAgent, GroundingConfig, UIElement
from .action_space import Action, ActionType, ActionExecutor
from .prompts import get_system_prompt, build_user_message, SYSTEM_PROMPTS
from .planner import HierarchicalPlanner, TaskPlan
from .memory import ExperienceMemory, get_experience_memory
from .code_executor import LocalCodeExecutor, CodeExecutorConfig

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GUIAgentConfig:
    """GUI Agent 配置"""
    # LLM 配置 - 默认使用 OpenRouter
    model: str = "openrouter/google/gemini-2.0-flash-exp:free"  # 免费视觉模型
    api_key: Optional[str] = "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"
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2000
    
    # Grounding 配置
    grounding_model: Optional[str] = None      # 专用 grounding 模型
    grounding_url: Optional[str] = None
    grounding_api_key: Optional[str] = None
    
    # 执行配置
    max_steps: int = 50                        # 最大执行步数
    max_retries: int = 3                       # 每步最大重试次数
    step_delay: float = 0.5                    # 步骤间延迟（秒）
    screenshot_delay: float = 0.3             # 截图前延迟
    
    # 反思配置
    enable_reflection: bool = True             # 启用反思 Agent
    reflection_interval: int = 5               # 每隔几步反思一次
    
    # 分层规划配置 (Agent-S 风格)
    enable_planning: bool = True               # 启用分层规划
    
    # 经验记忆配置 (Agent-S 风格)
    enable_memory: bool = True                 # 启用经验记忆
    memory_path: str = "./workspace/experience_memory"
    
    # 代码执行配置 (Agent-S 风格)
    enable_code_execution: bool = False        # 启用本地代码执行（危险！）
    code_execution_timeout: int = 30
    
    # 安全配置
    fail_safe: bool = True                     # pyautogui 安全模式
    confirm_dangerous_actions: bool = True     # 危险操作需确认
    
    # 截图配置
    max_screenshot_width: int = 1920
    max_screenshot_height: int = 1080
    screenshot_quality: int = 85
    
    # 轨迹配置
    max_trajectory_length: int = 10            # 保留的历史步数（用于 LLM 上下文）


@dataclass
class TrajectoryStep:
    """执行轨迹中的一步"""
    step_number: int
    observation: str                           # 屏幕观察
    thinking: str                              # 思考过程
    action: Action                             # 执行的动作
    screenshot_base64: Optional[str] = None    # 截图（可选保存）
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "step": self.step_number,
            "observation": self.observation,
            "thinking": self.thinking,
            "action": self.action.to_dict(),
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        return f"Step {self.step_number}: {self.action.action_type.value} - {self.action.reason[:50]}"


@dataclass
class TaskResult:
    """任务执行结果"""
    task: str
    status: TaskStatus
    message: str
    steps_taken: int
    trajectory: List[TrajectoryStep]
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "status": self.status.value,
            "message": self.message,
            "steps_taken": self.steps_taken,
            "duration_ms": self.total_duration_ms,
            "error": self.error,
            "trajectory": [step.to_dict() for step in self.trajectory],
        }


class GUIAgent:
    """
    GUI Agent 主类
    
    像人一样操作电脑的 AI Agent。
    
    使用示例:
    ```python
    agent = GUIAgent(config=GUIAgentConfig(
        model="openrouter/google/gemini-2.0-flash-exp:free",
        api_key="sk-or-v1-..."  # OpenRouter API Key
    ))
    
    result = agent.run("打开记事本并输入 Hello World")
    print(result.status, result.message)
    ```
    """
    
    def __init__(self, config: Optional[GUIAgentConfig] = None):
        self.config = config or GUIAgentConfig()
        
        # 初始化核心组件
        self.screen_parser = ScreenParser()
        self.grounding_agent = GroundingAgent(self._build_grounding_config())
        self.action_executor = ActionExecutor(
            fail_safe=self.config.fail_safe,
            pause=self.config.step_delay
        )
        
        # LLM 客户端
        self._llm_client = None
        self._init_llm()
        
        # Agent-S 风格组件
        # 1. 分层规划器
        self.planner: Optional[HierarchicalPlanner] = None
        if self.config.enable_planning:
            self.planner = HierarchicalPlanner()
            if self._llm_client:
                self.planner.set_llm_client(self._llm_client, self.config.model)
        
        # 2. 经验记忆
        self.memory: Optional[ExperienceMemory] = None
        if self.config.enable_memory:
            self.memory = ExperienceMemory(self.config.memory_path)
        
        # 3. 代码执行器
        self.code_executor: Optional[LocalCodeExecutor] = None
        if self.config.enable_code_execution:
            self.code_executor = LocalCodeExecutor(CodeExecutorConfig(
                timeout=self.config.code_execution_timeout
            ))
        
        # 状态
        self._current_task: Optional[str] = None
        self._current_plan: Optional[TaskPlan] = None
        self._trajectory: List[TrajectoryStep] = []
        self._is_running: bool = False
        self._should_stop: bool = False
        
        # 回调
        self._on_step: Optional[Callable[[TrajectoryStep], None]] = None
        self._on_screenshot: Optional[Callable[[ScreenState], None]] = None
        self._on_action: Optional[Callable[[Action], None]] = None
        self._on_plan: Optional[Callable[[TaskPlan], None]] = None
        
        logger.info(f"GUIAgent initialized with model: {self.config.model}")
        logger.info(f"  - Planning: {self.config.enable_planning}")
        logger.info(f"  - Memory: {self.config.enable_memory}")
        logger.info(f"  - Code Execution: {self.config.enable_code_execution}")
    
    def _build_grounding_config(self) -> GroundingConfig:
        """构建 Grounding 配置"""
        config = GroundingConfig(
            vision_model=self.config.model,
            vision_api_key=self.config.api_key,
            vision_base_url=self.config.base_url,
        )
        
        if self.config.grounding_model:
            config.grounding_model = self.config.grounding_model
            config.grounding_url = self.config.grounding_url
            config.grounding_api_key = self.config.grounding_api_key
        
        return config
    
    def _init_llm(self) -> None:
        """初始化 LLM 客户端"""
        try:
            import litellm
            self._llm_client = litellm
            logger.info("LLM client initialized")
        except ImportError:
            logger.error("litellm not installed. Run: pip install litellm")
    
    def run(self, task: str, **kwargs) -> TaskResult:
        """
        执行任务
        
        Args:
            task: 任务描述（自然语言）
            **kwargs: 额外参数
            
        Returns:
            TaskResult: 执行结果
        """
        logger.info(f"Starting task: {task}")
        
        self._current_task = task
        self._trajectory = []
        self._is_running = True
        self._should_stop = False
        self._current_plan = None
        
        result = TaskResult(
            task=task,
            status=TaskStatus.RUNNING,
            message="",
            steps_taken=0,
            trajectory=[],
        )
        
        try:
            # === Agent-S 风格: 查找相似经验 ===
            experience_hints = []
            if self.memory:
                similar_experiences = self.memory.find_similar(task, limit=3)
                if similar_experiences:
                    logger.info(f"Found {len(similar_experiences)} similar experiences")
                    experience_hints = self.memory.get_action_hints(task)
            
            # === Agent-S 风格: 分层规划 ===
            if self.planner and self.config.enable_planning:
                screen_state = self.screen_parser.capture_and_resize()
                self._current_plan = self.planner.create_plan(
                    task=task,
                    screen_description="初始屏幕状态",
                    api_key=self.config.api_key,
                    base_url=self.config.base_url
                )
                if self._current_plan and self._on_plan:
                    self._on_plan(self._current_plan)
                    logger.info(f"Created plan with {len(self._current_plan.subtasks)} subtasks")
            
            # 主执行循环
            step_count = 0
            
            while step_count < self.config.max_steps and not self._should_stop:
                step_count += 1
                
                # 获取当前子任务焦点
                current_focus = task
                if self._current_plan and self._current_plan.current_subtask:
                    current_focus = f"{task}\n[当前子任务]: {self._current_plan.current_subtask.description}"
                
                # 执行一步
                step_result = self._execute_step(step_count, current_focus)
                
                if step_result is None:
                    result.status = TaskStatus.FAILED
                    result.message = "步骤执行失败"
                    result.error = "Step execution returned None"
                    break
                
                self._trajectory.append(step_result)
                result.trajectory.append(step_result)
                result.steps_taken = step_count
                
                # 触发回调
                if self._on_step:
                    self._on_step(step_result)
                
                # 检查是否完成
                if step_result.action.action_type == ActionType.DONE:
                    result.status = TaskStatus.SUCCESS
                    result.message = step_result.action.reason
                    
                    # 检查是否还有子任务
                    if self._current_plan and not self._current_plan.is_complete:
                        if self.planner.mark_subtask_complete():
                            continue  # 继续下一个子任务
                    break
                
                # 检查是否失败
                if step_result.action.action_type == ActionType.FAIL:
                    # 尝试重新规划
                    if self.planner and self._current_plan:
                        new_plan = self.planner.replan(
                            error=step_result.action.reason,
                            api_key=self.config.api_key,
                            base_url=self.config.base_url
                        )
                        if new_plan:
                            self._current_plan = new_plan
                            logger.info("Replanned after failure")
                            continue
                    
                    result.status = TaskStatus.FAILED
                    result.message = step_result.action.reason
                    result.error = step_result.action.reason
                    break
                
                # 反思检查（每隔几步）
                if self.config.enable_reflection and step_count % self.config.reflection_interval == 0:
                    should_continue = self._reflect(task, self._trajectory)
                    if not should_continue:
                        result.status = TaskStatus.FAILED
                        result.message = "反思 Agent 建议停止任务"
                        break
                
                # 步骤间延迟
                time.sleep(self.config.step_delay)
            
            # 检查是否超出步数限制
            if step_count >= self.config.max_steps and result.status == TaskStatus.RUNNING:
                result.status = TaskStatus.FAILED
                result.message = f"超出最大步数限制: {self.config.max_steps}"
                result.error = "Max steps exceeded"
            
        except KeyboardInterrupt:
            result.status = TaskStatus.CANCELLED
            result.message = "任务被用户取消"
            logger.info("Task cancelled by user")
        
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.message = f"执行错误: {str(e)}"
            result.error = str(e)
            logger.error(f"Task execution error: {e}", exc_info=True)
        
        finally:
            self._is_running = False
            result.end_time = datetime.now()
            result.total_duration_ms = (result.end_time - result.start_time).total_seconds() * 1000
            
            # === Agent-S 风格: 保存经验到记忆 ===
            if self.memory and result.steps_taken > 0:
                try:
                    actions = [step.action.to_dict() for step in result.trajectory]
                    self.memory.add_experience(
                        task=task,
                        success=(result.status == TaskStatus.SUCCESS),
                        actions=actions,
                        duration_ms=result.total_duration_ms,
                        error=result.error,
                    )
                except Exception as e:
                    logger.warning(f"Failed to save experience: {e}")
        
        logger.info(f"Task completed: {result.status.value} in {result.steps_taken} steps")
        return result
    
    def _execute_step(self, step_number: int, task: str) -> Optional[TrajectoryStep]:
        """
        执行单个步骤
        
        流程: 截图 → LLM 分析 → 生成动作 → 定位 → 执行
        """
        logger.debug(f"Executing step {step_number}")
        
        # 1. 截图
        time.sleep(self.config.screenshot_delay)  # 等待界面稳定
        screen_state = self.screen_parser.capture_and_resize(
            max_width=self.config.max_screenshot_width,
            max_height=self.config.max_screenshot_height,
            quality=self.config.screenshot_quality
        )
        
        if not screen_state.screenshot_bytes:
            logger.error("Failed to capture screenshot")
            return None
        
        if self._on_screenshot:
            self._on_screenshot(screen_state)
        
        # 2. 调用 LLM 分析并生成动作
        llm_response = self._call_llm(task, screen_state)
        
        if not llm_response:
            logger.error("LLM call failed")
            return None
        
        # 3. 解析 LLM 响应
        observation, thinking, action = self._parse_llm_response(llm_response)
        
        # 4. 如果需要坐标，使用 Grounding
        if action.target and action.coordinates is None:
            if action.action_type in (ActionType.CLICK, ActionType.DOUBLE_CLICK, 
                                       ActionType.RIGHT_CLICK, ActionType.TYPE, 
                                       ActionType.HOVER):
                element = self.grounding_agent.locate(
                    target=action.target,
                    screenshot_base64=screen_state.get_base64(),
                    screen_width=screen_state.width,
                    screen_height=screen_state.height
                )
                
                if element:
                    action.coordinates = element.coordinates
                    logger.debug(f"Grounded '{action.target}' to {action.coordinates}")
                else:
                    logger.warning(f"Failed to ground element: {action.target}")
        
        # 5. 执行动作
        if action.action_type not in (ActionType.DONE, ActionType.FAIL, ActionType.THINK):
            if self._on_action:
                self._on_action(action)
            
            action = self.action_executor.execute(action)
            
            if not action.success:
                logger.warning(f"Action failed: {action.error}")
        
        # 6. 创建轨迹步骤
        step = TrajectoryStep(
            step_number=step_number,
            observation=observation,
            thinking=thinking,
            action=action,
        )
        
        logger.info(f"Step {step_number}: {action.action_type.value} - {action.reason[:50]}")
        
        return step
    
    def _call_llm(self, task: str, screen_state: ScreenState) -> Optional[str]:
        """调用 LLM 分析屏幕并生成动作"""
        if not self._llm_client:
            logger.error("LLM client not available")
            return None
        
        # 构建历史记录
        history = []
        for step in self._trajectory[-self.config.max_trajectory_length:]:
            history.append(str(step))
        
        try:
            messages = [
                {"role": "system", "content": get_system_prompt("main")},
                {
                    "role": "user",
                    "content": build_user_message(
                        task=task,
                        screenshot_base64=screen_state.get_base64(),
                        history=history
                    )
                }
            ]
            
            response = self._llm_client.completion(
                model=self.config.model,
                messages=messages,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None
    
    def _parse_llm_response(self, response: str) -> Tuple[str, str, Action]:
        """解析 LLM 响应"""
        observation = ""
        thinking = ""
        action = Action(ActionType.FAIL, reason="Failed to parse LLM response")
        
        try:
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning(f"No JSON in response: {response[:200]}")
                return observation, thinking, action
            
            data = json.loads(json_match.group())
            
            observation = data.get("observation", "")
            thinking = data.get("thinking", "")
            
            action_data = data.get("action", {})
            action_type_str = action_data.get("type", "fail")
            
            # 映射动作类型
            action_type_map = {
                "click": ActionType.CLICK,
                "double_click": ActionType.DOUBLE_CLICK,
                "right_click": ActionType.RIGHT_CLICK,
                "type": ActionType.TYPE,
                "press": ActionType.PRESS,
                "hotkey": ActionType.HOTKEY,
                "scroll": ActionType.SCROLL,
                "hover": ActionType.HOVER,
                "drag": ActionType.DRAG,
                "wait": ActionType.WAIT,
                "done": ActionType.DONE,
                "fail": ActionType.FAIL,
                "think": ActionType.THINK,
            }
            
            action_type = action_type_map.get(action_type_str.lower(), ActionType.FAIL)
            
            action = Action(
                action_type=action_type,
                target=action_data.get("target"),
                text=action_data.get("text"),
                key=action_data.get("key"),
                keys=action_data.get("keys"),
                scroll_amount=action_data.get("amount", 0),
                duration=action_data.get("duration", 0.5),
                reason=action_data.get("reason", ""),
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
        except Exception as e:
            logger.error(f"Response parse error: {e}")
        
        return observation, thinking, action
    
    def _reflect(self, task: str, trajectory: List[TrajectoryStep]) -> bool:
        """反思当前进度，决定是否继续"""
        if not self._llm_client or len(trajectory) == 0:
            return True
        
        try:
            # 构建反思提示
            actions_summary = "\n".join([str(step) for step in trajectory[-5:]])
            
            # 获取最新截图
            screen_state = self.screen_parser.capture_and_resize()
            
            prompt = get_system_prompt(
                "reflection",
                task=task,
                actions=actions_summary,
                screen_description="见截图",
                last_result=str(trajectory[-1].action) if trajectory else "无"
            )
            
            messages = [
                {"role": "system", "content": "你是一个任务反思 Agent，帮助评估任务进度。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{screen_state.get_base64()}"}
                        }
                    ]
                }
            ]
            
            response = self._llm_client.completion(
                model=self.config.model,
                messages=messages,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                temperature=0.1,
                max_tokens=500,
            )
            
            content = response.choices[0].message.content
            
            # 解析反思结果
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                should_continue = data.get("should_continue", True)
                
                logger.info(f"Reflection: progress={data.get('progress', 'unknown')}, continue={should_continue}")
                
                return should_continue
            
        except Exception as e:
            logger.warning(f"Reflection failed: {e}")
        
        return True  # 默认继续
    
    def stop(self) -> None:
        """停止当前任务"""
        self._should_stop = True
        logger.info("Stop requested")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._is_running
    
    def get_trajectory(self) -> List[TrajectoryStep]:
        """获取执行轨迹"""
        return self._trajectory.copy()
    
    # 回调设置
    def on_step(self, callback: Callable[[TrajectoryStep], None]) -> None:
        """设置步骤完成回调"""
        self._on_step = callback
    
    def on_screenshot(self, callback: Callable[[ScreenState], None]) -> None:
        """设置截图回调"""
        self._on_screenshot = callback
    
    def on_action(self, callback: Callable[[Action], None]) -> None:
        """设置动作执行回调"""
        self._on_action = callback
    
    # 便捷方法
    def click(self, target: str) -> TaskResult:
        """点击指定元素"""
        return self.run(f"点击 '{target}'")
    
    def type_text(self, target: str, text: str) -> TaskResult:
        """在指定位置输入文本"""
        return self.run(f"在 '{target}' 中输入 '{text}'")
    
    def open_app(self, app_name: str) -> TaskResult:
        """打开应用程序"""
        return self.run(f"打开 {app_name}")
    
    def search_web(self, query: str) -> TaskResult:
        """网页搜索"""
        return self.run(f"打开浏览器搜索 '{query}'")


# 便捷函数
def create_gui_agent(
    model: str = "openrouter/google/gemini-2.0-flash-exp:free",
    api_key: Optional[str] = "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",
    **kwargs
) -> GUIAgent:
    """
    创建 GUI Agent 实例
    
    Args:
        model: LLM 模型名称
        api_key: API 密钥
        **kwargs: 其他配置参数
        
    Returns:
        GUIAgent 实例
    """
    config = GUIAgentConfig(
        model=model,
        api_key=api_key,
        **kwargs
    )
    return GUIAgent(config)

