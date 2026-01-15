"""
JoinFlow GUI Agent 启动脚本
===========================

使用 OpenRouter API 运行 GUI Agent
"""
import os
import sys

# 设置 API Key
os.environ['OPENROUTER_API_KEY'] = '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'

from joinflow_agent.gui import GUIAgent, GUIAgentConfig

def main():
    print("=" * 60)
    print("  JoinFlow GUI Agent")
    print("  Type a task in natural language, or 'quit' to exit")
    print("=" * 60)
    
    # 创建配置
    config = GUIAgentConfig(
        # 使用 OpenRouter 的免费视觉模型
        model="openrouter/google/gemini-2.0-flash-exp:free",
        api_key=os.environ['OPENROUTER_API_KEY'],
        
        # 执行配置
        max_steps=10,           # 最多10步
        step_delay=0.5,         # 每步间隔0.5秒
        
        # Agent-S 风格功能
        enable_planning=True,   # 启用分层规划
        enable_memory=True,     # 启用经验记忆
        enable_reflection=True, # 启用反思
        
        # 安全配置
        fail_safe=True,         # 鼠标移到角落可紧急停止
        confirm_dangerous_actions=False,  # 不需要确认
    )
    
    # 创建 Agent
    agent = GUIAgent(config)
    print("\nGUI Agent ready!")
    print("Tip: Move mouse to corner to emergency stop\n")
    
    while True:
        try:
            task = input("\nTask > ").strip()
            
            if not task:
                continue
            
            if task.lower() in ('quit', 'exit', 'q'):
                print("Goodbye!")
                break
            
            print(f"\nExecuting: {task}")
            print("-" * 40)
            
            result = agent.run(task)
            
            print("-" * 40)
            print(f"Status: {result.status.value}")
            print(f"Steps: {result.steps_taken}")
            print(f"Message: {result.message}")
            
            if result.error:
                print(f"Error: {result.error}")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

