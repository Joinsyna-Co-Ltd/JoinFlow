#!/usr/bin/env python3
"""
JoinFlow - Multi-Agent RAG System
==============================================

A complete AI agent system with:
- Browser automation
- Code execution in sandbox
- Data processing
- Image understanding
- Knowledge base (RAG)
- User history storage

Usage:
    python main.py                     # Interactive chat mode
    python main.py --task "your task"  # Execute a single task
    python main.py --api               # Start API server
    python main.py --demo              # Run demo
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Setup environment variables and dependencies"""
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        api_key = os.environ.get("LLM_API_KEY")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            logger.warning(
                "No OPENAI_API_KEY found. Set it with:\n"
                "  export OPENAI_API_KEY=your-key\n"
                "Or use a local LLM with LiteLLM."
            )


def create_system(
    with_memory: bool = True,
    with_rag: bool = True,
    collection: str = "joinflow_knowledge"
):
    """
    Create and configure the complete agent system.
    
    Returns:
        Tuple of (orchestrator, session_manager, task_queue)
    """
    from joinflow_agent import (
        Orchestrator, AgentConfig, 
        SessionManager, TaskQueue
    )
    
    # Create config
    config = AgentConfig(
        llm_model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        llm_api_key=os.environ.get("OPENAI_API_KEY"),
        browser_headless=True,
        os_workspace="./workspace",
        verbose=True
    )
    
    # Create orchestrator
    orchestrator = Orchestrator(config=config)
    
    # Create session manager
    session_manager = SessionManager(
        storage_path="./sessions",
        session_timeout_hours=24
    )
    
    # Create task queue
    task_queue = TaskQueue(max_workers=4)
    
    # Setup Qdrant service (centralized management)
    qdrant_service = None
    try:
        from joinflow_core.qdrant_service import get_qdrant_service, QdrantConfig
        
        # Use environment variable for Qdrant URL
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        qdrant_config = QdrantConfig(
            url=qdrant_url,
            knowledge_collection=collection,
            cache_enabled=True  # Enable LLM response caching
        )
        
        qdrant_service = get_qdrant_service(qdrant_config)
        
        if qdrant_service.is_connected:
            logger.info(f"✅ Qdrant connected at {qdrant_url}")
        elif qdrant_service.is_available:
            logger.info("⚠️ Qdrant using in-memory mode (data not persistent)")
        
    except ImportError as e:
        logger.warning(f"Qdrant service not available: {e}")
    except Exception as e:
        logger.warning(f"Failed to initialize Qdrant service: {e}")
    
    # Setup RAG if enabled
    if with_rag and qdrant_service and qdrant_service.is_available:
        try:
            from joinflow_index.qdrant_store import QdrantVectorStore
            from joinflow_index.config import QdrantConfig as IndexConfig
            from joinflow_rag.engine import RAGEngine
            from joinflow_core.cached_llm import CachedLLM
            
            # Use Qdrant service client and embedder
            store = QdrantVectorStore(
                IndexConfig(
                    collection=collection,
                    vector_dim=qdrant_service.config.vector_dim,
                    url=qdrant_service.config.url
                ),
                client=qdrant_service.client
            )
            
            embedder = qdrant_service.get_embedder()
            
            # Create cached LLM wrapper to reduce token consumption
            def llm_func(prompt):
                return orchestrator._llm_agent.execute(prompt).output
            
            cached_llm = CachedLLM(
                llm_func,
                model_name=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                cache_enabled=True,
                similarity_threshold=0.92
            )
            
            rag_engine = RAGEngine(
                embedder=embedder,
                store=store,
                llm=cached_llm.query  # Use cached LLM
            )
            
            orchestrator.set_rag_engine(rag_engine)
            logger.info("✅ RAG engine initialized with caching")
            
        except ImportError as e:
            logger.warning(f"RAG dependencies not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize RAG: {e}")
    
    # Setup memory if enabled
    if with_memory and qdrant_service and qdrant_service.is_available:
        try:
            from joinflow_memory import HistoryStore, MemoryConfig
            
            embedder = qdrant_service.get_embedder()
            
            memory_config = MemoryConfig(
                url=qdrant_service.config.url,
                history_collection=qdrant_service.config.history_collection,
                task_collection=qdrant_service.config.tasks_collection,
                vector_dim=qdrant_service.config.vector_dim
            )
            
            memory_store = HistoryStore(
                embedder=embedder,
                config=memory_config,
                client=qdrant_service.client
            )
            
            orchestrator.set_memory_store(memory_store)
            logger.info("✅ Memory store initialized")
            
        except ImportError as e:
            logger.warning(f"Memory dependencies not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize memory: {e}")
    
    return orchestrator, session_manager, task_queue


def interactive_chat(orchestrator, session_manager=None):
    """Run interactive chat session"""
    print("\n" + "="*60)
    print("🤖 JoinFlow - Agent System")
    print("="*60)
    print("\n可用的 Agent:")
    print("  🌐 Browser - 网页浏览和搜索")
    print("  🤖 LLM     - 文本生成和推理")
    print("  💻 OS      - 文件和系统操作")
    print("  📝 Code    - 代码执行")
    print("  📊 Data    - 数据处理分析")
    print("  👁️  Vision  - 图片理解")
    print("  📚 RAG     - 知识库检索")
    print("\n命令:")
    print("  /quit, /exit - 退出")
    print("  /clear       - 清除历史")
    print("  /history     - 查看执行历史")
    print("  /agents      - 查看可用 Agent")
    print("  /help        - 显示帮助")
    print("="*60 + "\n")
    
    session = None
    if session_manager:
        session = session_manager.create_session(system_prompt="你是一个强大的AI助手")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["/quit", "/exit", "exit", "quit"]:
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == "/clear":
                orchestrator.clear_history()
                if session:
                    session.messages = []
                print("✅ 历史已清除\n")
                continue
            
            if user_input.lower() == "/history":
                history = orchestrator.get_execution_history()
                if not history:
                    print("暂无执行历史\n")
                else:
                    for i, plan in enumerate(history[-5:], 1):
                        print(f"{i}. {plan.original_task[:50]}...")
                        for step in plan.steps:
                            status = "✅" if step.status == "completed" else "❌"
                            print(f"   {status} [{step.agent_type.value}] {step.description[:40]}...")
                print()
                continue
            
            if user_input.lower() == "/agents":
                agents = orchestrator.get_agents()
                print("可用的 Agent:")
                for name, agent in agents.items():
                    print(f"  - {name}: {agent.name}")
                print()
                continue
            
            if user_input.lower() == "/help":
                print("命令: /quit, /clear, /history, /agents, /help")
                print("\n示例任务:")
                print("  - 搜索今天的科技新闻")
                print("  - 执行 Python 代码: print('hello')")
                print("  - 分析 data.csv 文件")
                print("  - 描述这张图片 image.jpg")
                print()
                continue
            
            # Execute task
            print("\n🤔 思考中...\n")
            
            # Add to session
            if session:
                session.add_message("user", user_input)
            
            result = orchestrator.execute(user_input)
            
            print(f"🤖 Assistant: {result.output}\n")
            
            # Add response to session
            if session:
                session.add_message("assistant", result.output)
                session.total_tokens += result.tokens_used
            
            # Show execution info
            if result.data and result.data.get("steps"):
                print(f"   📊 执行了 {len(result.data['steps'])} 个步骤")
                for step in result.data['steps']:
                    status = "✅" if step.get('success', True) else "❌"
                    print(f"      {status} {step['description'][:50]}...")
            if result.tokens_used:
                print(f"   🔢 Tokens: {result.tokens_used}")
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            logger.exception("Error in chat")


def run_api_server(orchestrator, session_manager, task_queue, host="0.0.0.0", port=8000, with_ui=True):
    """Run the API server with optional Web UI"""
    try:
        if with_ui:
            # Run with beautiful Web UI
            from web.server import run_server
            run_server(host=host, port=port)
        else:
            # Run API only
            from joinflow_agent import run_api
            
            print(f"\n🚀 Starting JoinFlow API server on http://{host}:{port}")
            print(f"   Documentation: http://localhost:{port}/docs")
            print("   Press Ctrl+C to stop\n")
            
            run_api(orchestrator, session_manager, task_queue, host=host, port=port)
        
    except ImportError as e:
        print(f"❌ Required packages not installed: {e}")
        print("   Install with: pip install fastapi uvicorn jinja2")
        sys.exit(1)


def run_demo():
    """Run a demo showcasing all capabilities"""
    print("\n" + "="*60)
    print("🎬 JoinFlow 功能演示")
    print("="*60 + "\n")
    
    orchestrator, _, _ = create_system(with_memory=True, with_rag=True)
    
    demos = [
        ("💬 对话", "你好，请介绍一下你能做什么？"),
        ("🔍 搜索", "搜索 Python 3.12 的新特性"),
        ("📁 文件", "列出当前目录的文件"),
        ("📊 分析", "分析一下人工智能的发展趋势"),
    ]
    
    for name, task in demos:
        print(f"\n{'='*40}")
        print(f"{name}: {task}")
        print('='*40)
        
        try:
            result = orchestrator.execute(task)
            output = result.output[:500]
            if len(result.output) > 500:
                output += "..."
            print(f"\n结果:\n{output}")
            
            if result.data and result.data.get("steps"):
                print(f"\n执行了 {len(result.data['steps'])} 个步骤")
        except Exception as e:
            print(f"Error: {e}")
        
        print()
    
    print("="*60)
    print("演示完成!")
    print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="JoinFlow - Multi-Agent RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # 交互式聊天
  python main.py --task "搜索新闻"  # 执行单个任务
  python main.py --api              # 启动 API 服务器
  python main.py --api --port 9000  # 指定端口
  python main.py --demo             # 运行演示
        """
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        help="Execute a single task"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start API server"
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Start Web UI server (includes API)"
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Start API server without Web UI"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="API server host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo"
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable user history storage"
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG knowledge base"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model to use"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup
    setup_environment()
    os.environ["LLM_MODEL"] = args.model
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.demo:
        run_demo()
    elif args.ui or args.api:
        orchestrator, session_manager, task_queue = create_system(
            with_memory=not args.no_memory,
            with_rag=not args.no_rag
        )
        with_ui = args.ui or (args.api and not args.api_only)
        run_api_server(orchestrator, session_manager, task_queue, args.host, args.port, with_ui=with_ui)
    elif args.task:
        orchestrator, _, _ = create_system(
            with_memory=not args.no_memory,
            with_rag=not args.no_rag
        )
        result = orchestrator.execute(args.task)
        print(result.output)
    else:
        orchestrator, session_manager, _ = create_system(
            with_memory=not args.no_memory,
            with_rag=not args.no_rag
        )
        interactive_chat(orchestrator, session_manager)


if __name__ == "__main__":
    main()
