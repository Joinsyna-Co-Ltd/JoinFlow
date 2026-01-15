"""
使用LLM的示例
"""
import os
from joinflow_os_assistant import OSAssistant
from joinflow_os_assistant.llm.client import create_llm_client


def main():
    """使用LLM的示例"""
    
    # 方式1: 使用OpenAI
    # llm = create_llm_client(
    #     provider="openai",
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     model="gpt-4"
    # )
    
    # 方式2: 使用本地Ollama
    # llm = create_llm_client(
    #     provider="ollama",
    #     base_url="http://localhost:11434",
    #     model="llama2"
    # )
    
    # 方式3: 使用LM Studio
    # llm = create_llm_client(
    #     provider="lmstudio",
    #     base_url="http://localhost:1234",
    #     model="local-model"
    # )
    
    # 这里使用Mock客户端演示
    from joinflow_os_assistant.llm.client import MockLLMClient
    llm = MockLLMClient()
    
    # 创建助手
    assistant = OSAssistant(llm_client=llm)
    
    print("=" * 50)
    print("JoinFlow 智能助手 (带LLM)")
    print("=" * 50)
    
    # 执行复杂任务
    print("\n执行: 整理我的下载文件夹，按类型分类")
    result = assistant.execute("整理我的下载文件夹，按类型分类")
    print(f"结果: {result.message}")
    
    # 智能搜索
    print("\n执行: 帮我找到最近修改的Python文件")
    result = assistant.execute("帮我找到最近修改的Python文件")
    print(f"结果: {result.message}")


if __name__ == "__main__":
    main()

