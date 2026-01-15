"""
命令行接口
"""
import argparse
import sys
from .core.assistant import OSAssistant
from .core.config import AssistantConfig


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="JoinFlow 智能操作系统助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行单个命令
  python -m joinflow_os_assistant "打开记事本"
  
  # 交互模式
  python -m joinflow_os_assistant -i
  
  # 启动API服务
  python -m joinflow_os_assistant --server --port 5000
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        help="要执行的命令"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="交互模式"
    )
    
    parser.add_argument(
        "--server",
        action="store_true",
        help="启动API服务器"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="服务器端口 (默认: 5000)"
    )
    
    parser.add_argument(
        "--auto-confirm",
        action="store_true",
        help="自动确认危险操作"
    )
    
    args = parser.parse_args()
    
    # 启动服务器
    if args.server:
        from .api.server import run_server
        print(f"启动API服务器: http://{args.host}:{args.port}")
        run_server(host=args.host, port=args.port)
        return
    
    # 交互模式
    if args.interactive:
        interactive_mode()
        return
    
    # 执行单个命令
    if args.command:
        assistant = OSAssistant()
        result = assistant.execute(args.command, auto_confirm=args.auto_confirm)
        print(result.message)
        
        if result.data:
            if isinstance(result.data, dict):
                if "results" in result.data:
                    results = result.data["results"]
                    if results:
                        print(f"\n找到 {len(results)} 个结果:")
                        for item in results[:10]:
                            if isinstance(item, dict):
                                print(f"  - {item.get('name', item.get('path', str(item)))}")
                elif "content" in result.data:
                    content = result.data["content"]
                    if len(content) > 500:
                        print(f"\n{content[:500]}...")
                    else:
                        print(f"\n{content}")
        
        sys.exit(0 if result.success else 1)
    
    # 没有命令，显示帮助
    parser.print_help()


def interactive_mode():
    """交互模式"""
    assistant = OSAssistant()
    
    print("=" * 50)
    print("JoinFlow 智能操作系统助手")
    print("输入命令执行，输入 'exit' 退出，'help' 查看帮助")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n🤖 > ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['exit', 'quit', '退出', 'q']:
                print("再见！👋")
                break
            
            result = assistant.execute(command)
            
            # 显示结果
            if result.success:
                print(f"✓ {result.message}")
            else:
                print(f"✗ {result.message}")
            
            # 显示数据
            if result.data and isinstance(result.data, dict):
                if "results" in result.data:
                    results = result.data["results"]
                    if results:
                        print(f"\n📋 找到 {len(results)} 个结果:")
                        for item in results[:5]:
                            if isinstance(item, dict):
                                name = item.get('name', item.get('path', str(item)))
                                print(f"   📄 {name}")
                elif "content" in result.data:
                    content = result.data["content"]
                    print(f"\n📝 内容:")
                    if len(content) > 300:
                        print(f"   {content[:300]}...")
                    else:
                        print(f"   {content}")
                        
        except KeyboardInterrupt:
            print("\n\n⚠️ 操作已取消")
        except Exception as e:
            print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()

