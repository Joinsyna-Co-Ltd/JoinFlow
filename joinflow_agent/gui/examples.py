"""
GUI Agent 使用示例
==================

展示如何使用 GUI Agent 执行各种任务
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from joinflow_agent.gui import (
    GUIAgent, 
    GUIAgentConfig,
    ScreenParser,
    ActionExecutor,
    Action,
    ActionType
)


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_basic_usage():
    """
    示例 1: 基本使用
    
    创建 Agent 并执行简单任务
    """
    print("\n" + "="*50)
    print("示例 1: 基本使用")
    print("="*50)
    
    # 使用 OpenRouter API Key
    api_key = os.getenv("OPENROUTER_API_KEY") or "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"
    
    # 创建配置
    config = GUIAgentConfig(
        model="openrouter/google/gemini-2.0-flash-exp:free",
        api_key=api_key,
        max_steps=20,
        enable_reflection=True,
    )
    
    # 创建 Agent
    agent = GUIAgent(config)
    
    # 设置回调（可选）
    agent.on_step(lambda step: print(f"  完成: {step}"))
    
    # 执行任务
    result = agent.run("打开记事本")
    
    print(f"\n结果: {result.status.value}")
    print(f"消息: {result.message}")
    print(f"步数: {result.steps_taken}")


def example_with_callbacks():
    """
    示例 2: 使用回调监控执行过程
    """
    print("\n" + "="*50)
    print("示例 2: 使用回调监控")
    print("="*50)
    
    api_key = os.getenv("OPENROUTER_API_KEY") or "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"
    
    agent = GUIAgent(GUIAgentConfig(
        model="openrouter/google/gemini-2.0-flash-exp:free",
        api_key=api_key,
    ))
    
    # 截图回调
    def on_screenshot(screen_state):
        print(f"  📷 截图: {screen_state.width}x{screen_state.height}")
    
    # 动作回调
    def on_action(action):
        print(f"  🎯 执行: {action.action_type.value} - {action.target or action.text or ''}")
    
    # 步骤回调
    def on_step(step):
        print(f"  ✅ 步骤 {step.step_number}: {step.action.reason[:50]}")
    
    agent.on_screenshot(on_screenshot)
    agent.on_action(on_action)
    agent.on_step(on_step)
    
    result = agent.run("打开浏览器并搜索 'Python 教程'")
    
    print(f"\n完成: {result.status.value}")


def example_screen_parser():
    """
    示例 3: 单独使用屏幕解析器
    """
    print("\n" + "="*50)
    print("示例 3: 屏幕解析器")
    print("="*50)
    
    parser = ScreenParser()
    
    # 获取屏幕信息
    print(f"屏幕尺寸: {parser.screen_size}")
    print(f"缩放因子: {parser.scale_factor}")
    print(f"鼠标位置: {parser.get_cursor_position()}")
    
    # 截图
    state = parser.capture()
    print(f"截图大小: {len(state.screenshot_bytes) / 1024:.1f} KB")
    
    # 调整大小后截图
    state_resized = parser.capture_and_resize(max_width=1280, max_height=720)
    print(f"调整后大小: {len(state_resized.screenshot_bytes) / 1024:.1f} KB")
    
    # 保存截图
    save_path = Path("./workspace/screenshot_test.png")
    save_path.parent.mkdir(exist_ok=True)
    state.save(str(save_path))
    print(f"截图已保存: {save_path}")


def example_action_executor():
    """
    示例 4: 单独使用动作执行器
    """
    print("\n" + "="*50)
    print("示例 4: 动作执行器")
    print("="*50)
    
    executor = ActionExecutor(fail_safe=True)
    
    print(f"屏幕尺寸: {executor.screen_size}")
    
    # 创建动作（不执行）
    actions = [
        Action(ActionType.WAIT, duration=1, reason="等待"),
        Action(ActionType.CLICK, coordinates=(100, 100), reason="点击示例位置"),
        Action(ActionType.TYPE, text="Hello", reason="输入文本"),
        Action(ActionType.PRESS, key="enter", reason="按回车"),
        Action(ActionType.HOTKEY, keys=["ctrl", "s"], reason="保存"),
    ]
    
    print("\n预定义的动作:")
    for action in actions:
        print(f"  - {action}")
    
    # 只执行等待动作作为演示
    print("\n执行等待动作...")
    result = executor.execute(Action(ActionType.WAIT, duration=0.5, reason="演示"))
    print(f"  结果: {'成功' if result.success else '失败'}")


def example_custom_grounding():
    """
    示例 5: 使用自定义 Grounding 模型
    """
    print("\n" + "="*50)
    print("示例 5: 自定义 Grounding 模型")
    print("="*50)
    
    from joinflow_agent.gui import GroundingAgent, GroundingConfig, GroundingMethod
    
    # 使用 GPT-4V 作为 grounding
    config = GroundingConfig(
        method=GroundingMethod.VISION_LLM,
        vision_model="openrouter/google/gemini-2.0-flash-exp:free",
        vision_api_key=os.getenv("OPENROUTER_API_KEY") or "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",
    )
    
    grounding = GroundingAgent(config)
    
    # 或者使用专用 grounding 模型（如 UI-TARS）
    # grounding.set_grounding_model(
    #     model="ui-tars-7b",
    #     url="http://localhost:8000/v1/chat/completions",
    #     width=1920,
    #     height=1080
    # )
    
    print("Grounding Agent 配置:")
    print(f"  方法: {config.method.value}")
    print(f"  模型: {config.vision_model}")


def example_complex_task():
    """
    示例 6: 执行复杂任务
    """
    print("\n" + "="*50)
    print("示例 6: 复杂任务")
    print("="*50)
    
    api_key = os.getenv("OPENROUTER_API_KEY") or "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"
    
    agent = GUIAgent(GUIAgentConfig(
        model="openrouter/google/gemini-2.0-flash-exp:free",
        api_key=api_key,
        max_steps=30,
        enable_reflection=True,
        reflection_interval=5,
    ))
    
    # 复杂任务示例
    tasks = [
        "打开记事本，输入 'Hello World'，然后保存到桌面",
        "打开 Chrome 浏览器，搜索 'Python 教程'，点击第一个搜索结果",
        "打开计算器，计算 123 + 456",
    ]
    
    print("可执行的复杂任务示例:")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. {task}")
    
    # 这里只打印，不实际执行
    print("\n提示: 取消注释下面的代码来执行任务")
    # result = agent.run(tasks[0])


def example_with_litellm():
    """
    示例 7: 使用不同的 LLM 提供商
    """
    print("\n" + "="*50)
    print("示例 7: 多 LLM 提供商支持")
    print("="*50)
    
    # litellm 支持多种提供商
    providers = [
        {
            "name": "OpenAI",
            "model": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
        },
        {
            "name": "Azure OpenAI",
            "model": "azure/gpt-4o",
            "api_key_env": "AZURE_API_KEY",
            "base_url_env": "AZURE_API_BASE",
        },
        {
            "name": "Anthropic Claude",
            "model": "claude-3-opus-20240229",
            "api_key_env": "ANTHROPIC_API_KEY",
        },
        {
            "name": "Google Gemini",
            "model": "gemini/gemini-pro-vision",
            "api_key_env": "GOOGLE_API_KEY",
        },
        {
            "name": "本地 Ollama",
            "model": "ollama/llava",
            "base_url": "http://localhost:11434",
        },
    ]
    
    print("支持的 LLM 提供商:")
    for p in providers:
        key_status = "✓" if os.getenv(p.get("api_key_env", "")) else "✗"
        print(f"  {key_status} {p['name']}: {p['model']}")
    
    print("\n使用方法:")
    print("""
    # OpenAI
    agent = GUIAgent(GUIAgentConfig(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY")
    ))
    
    # Claude
    agent = GUIAgent(GUIAgentConfig(
        model="claude-3-opus-20240229",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    ))
    
    # 本地 Ollama
    agent = GUIAgent(GUIAgentConfig(
        model="ollama/llava",
        base_url="http://localhost:11434"
    ))
    """)


def run_interactive():
    """
    交互式模式
    """
    print("\n" + "="*50)
    print("GUI Agent 交互式模式")
    print("="*50)
    
    api_key = os.getenv("OPENROUTER_API_KEY") or "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"
    
    agent = GUIAgent(GUIAgentConfig(
        model="openrouter/google/gemini-2.0-flash-exp:free",
        api_key=api_key,
        max_steps=20,
    ))
    
    print("\n输入任务描述，让 AI 帮你操作电脑")
    print("输入 'quit' 退出\n")
    
    while True:
        try:
            task = input("任务> ").strip()
            
            if task.lower() in ('quit', 'exit', 'q'):
                print("再见！")
                break
            
            if not task:
                continue
            
            print(f"\n正在执行: {task}\n")
            result = agent.run(task)
            
            print(f"\n结果: {result.status.value}")
            print(f"消息: {result.message}")
            print(f"步数: {result.steps_taken}")
            print(f"耗时: {result.total_duration_ms/1000:.1f} 秒\n")
            
        except KeyboardInterrupt:
            print("\n\n已取消")
            break


if __name__ == "__main__":
    setup_logging()
    
    print("="*50)
    print("JoinFlow GUI Agent - 使用示例")
    print("="*50)
    
    # 运行示例
    example_screen_parser()
    example_action_executor()
    example_with_litellm()
    
    # 以下示例需要 API 密钥
    # example_basic_usage()
    # example_with_callbacks()
    # example_custom_grounding()
    # example_complex_task()
    
    # 交互式模式
    # run_interactive()

