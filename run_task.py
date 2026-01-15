"""
GUI Agent 任务执行脚本
直接执行一个任务并显示结果
"""
import sys
import os
import io

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 设置 API Key
os.environ['OPENROUTER_API_KEY'] = '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'

from joinflow_agent.gui import GUIAgent, GUIAgentConfig

def run_task(task: str):
    print("=" * 60)
    print("  JoinFlow GUI Agent")
    print("=" * 60)
    print(f"\nTask: {task}")
    print("-" * 60)
    
    # 尝试多个模型
    models = [
        "openrouter/meta-llama/llama-3.2-90b-vision-instruct",  # 付费但便宜
        "openrouter/google/gemini-2.0-flash-exp:free",
        "openrouter/qwen/qwen-2-vl-72b-instruct",
    ]
    
    # 创建配置
    config = GUIAgentConfig(
        model=models[0],  # 使用第一个模型
        max_steps=10,
        step_delay=0.5,
        enable_planning=False,  # 先禁用规划简化测试
        enable_memory=True,
        enable_reflection=False,  # 简化测试
        fail_safe=True,
    )
    
    # 创建 Agent
    agent = GUIAgent(config)
    
    # 设置回调
    def on_step(step):
        action = step.action
        print(f"  Step {step.step_number}: {action.action_type.value}")
        if action.reason:
            print(f"    Reason: {action.reason[:80]}")
    
    agent.on_step(on_step)
    
    print("\nExecuting...\n")
    
    # 执行任务
    result = agent.run(task)
    
    print("\n" + "-" * 60)
    print(f"Status: {result.status.value}")
    print(f"Steps: {result.steps_taken}")
    print(f"Duration: {result.total_duration_ms/1000:.1f}s")
    print(f"Message: {result.message}")
    
    if result.error:
        print(f"Error: {result.error}")
    
    return result


if __name__ == "__main__":
    # 从命令行参数获取任务，或使用默认任务
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = "open notepad"  # 默认任务：打开记事本
    
    run_task(task)

