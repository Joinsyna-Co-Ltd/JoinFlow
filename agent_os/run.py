"""
Agent OS 启动脚本
"""
import argparse
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description='Agent OS - 智能操作系统代理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动Web界面
  python -m agent_os.run --web
  
  # 命令行交互模式
  python -m agent_os.run -i
  
  # 执行单个命令
  python -m agent_os.run "打开记事本"
        """
    )
    
    parser.add_argument('command', nargs='?', help='要执行的命令')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 启动Web服务
    if args.web:
        from agent_os.ui.server import run_server
        run_server(host=args.host, port=args.port, debug=args.debug)
        return
    
    # 交互模式
    if args.interactive:
        interactive_mode()
        return
    
    # 执行单个命令
    if args.command:
        from agent_os import AgentOS
        agent = AgentOS()
        result = agent.run(args.command)
        print(result.message)
        
        if result.data:
            import json
            print(json.dumps(result.data, indent=2, ensure_ascii=False))
        
        sys.exit(0 if result.success else 1)
    
    # 显示帮助
    parser.print_help()


def interactive_mode():
    """交互模式"""
    from agent_os import AgentOS
    
    agent = AgentOS()
    
    print("")
    print("=" * 60)
    print("  Agent OS v2.0 - Interactive Mode")
    print("=" * 60)
    print("  Type commands to execute, 'exit' to quit, 'help' for help")
    print("=" * 60)
    print("")
    
    while True:
        try:
            command = input('\n🤖 Agent > ').strip()
            
            if not command:
                continue
            
            if command.lower() in ['exit', 'quit', '退出', 'q']:
                print('\nGoodbye! Thank you for using Agent OS\n')
                break
            
            result = agent.run(command)
            
            # 显示结果
            if result.success:
                print(f'\n[SUCCESS] {result.message}')
            else:
                print(f'\n[FAILED] {result.message}')
            
            # 显示数据摘要
            if result.data and isinstance(result.data, dict):
                if 'results' in result.data:
                    items = result.data['results']
                    if items:
                        print(f'\nResults ({len(items)} items):')
                        for item in items[:5]:
                            name = item.get('name', str(item))
                            print(f'   - {name}')
                        if len(items) > 5:
                            print(f'   ... and {len(items) - 5} more')
                            
        except KeyboardInterrupt:
            print('\n\nOperation cancelled')
        except Exception as e:
            print(f'\n[ERROR] {e}')


if __name__ == '__main__':
    main()

