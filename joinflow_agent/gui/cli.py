"""
GUI Agent CLI - 命令行界面
==========================

提供命令行方式使用 GUI Agent
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def run_task(args):
    """执行单个任务"""
    from joinflow_agent.gui import GUIAgent, GUIAgentConfig
    
    # 获取 API 密钥 - 默认使用 OpenRouter
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "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"
    
    if not api_key:
        print("[X] 错误: 请设置 API 密钥")
        print("   方法1: 设置环境变量 OPENAI_API_KEY")
        print("   方法2: 使用 --api-key 参数")
        return 1
    
    # 创建配置
    config = GUIAgentConfig(
        model=args.model or "openrouter/google/gemini-2.0-flash-exp:free",
        api_key=api_key,
        base_url=args.base_url,
        max_steps=args.max_steps,
        enable_reflection=args.reflection,
        step_delay=args.delay,
    )
    
    # 创建 Agent
    agent = GUIAgent(config)
    
    # 设置回调
    if not args.quiet:
        def on_step(step):
            print(f"  [{step.step_number}] {step.action.action_type.value}: {step.action.reason[:60]}")
        agent.on_step(on_step)
    
    # 执行任务
    print(f"\n[>] 开始执行: {args.task}\n")
    
    try:
        result = agent.run(args.task)
        
        print(f"\n{'='*50}")
        print(f"状态: {'[OK] 成功' if result.status.value == 'success' else '[X] 失败'}")
        print(f"消息: {result.message}")
        print(f"步数: {result.steps_taken}")
        print(f"耗时: {result.total_duration_ms/1000:.1f} 秒")
        
        # 保存轨迹
        if args.save_trajectory:
            trajectory_path = Path(args.save_trajectory)
            trajectory_path.parent.mkdir(parents=True, exist_ok=True)
            with open(trajectory_path, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"轨迹已保存: {trajectory_path}")
        
        return 0 if result.status.value == 'success' else 1
        
    except KeyboardInterrupt:
        print("\n\n[!] 任务被取消")
        return 130


def run_interactive(args):
    """交互式模式"""
    from joinflow_agent.gui import GUIAgent, GUIAgentConfig
    
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "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"
    
    if not api_key:
        print("[X] 请设置 OPENAI_API_KEY 环境变量")
        return 1
    
    config = GUIAgentConfig(
        model=args.model or "openrouter/google/gemini-2.0-flash-exp:free",
        api_key=api_key,
        base_url=args.base_url,
        max_steps=args.max_steps,
        enable_reflection=args.reflection,
    )
    
    agent = GUIAgent(config)
    
    print("\n" + "="*50)
    print("[*] JoinFlow GUI Agent - 交互式模式")
    print("="*50)
    print(f"模型: {args.model}")
    print("输入任务描述，让 AI 帮你操作电脑")
    print("命令: 'quit' 退出, 'help' 帮助")
    print("="*50 + "\n")
    
    while True:
        try:
            task = input("[任务]> ").strip()
            
            if not task:
                continue
            
            if task.lower() in ('quit', 'exit', 'q'):
                print("[*] 再见！")
                break
            
            if task.lower() == 'help':
                print_help()
                continue
            
            print(f"\n[...] 正在执行...\n")
            
            result = agent.run(task)
            
            print(f"\n{'='*40}")
            print(f"{'[OK] 成功' if result.status.value == 'success' else '[X] 失败'}: {result.message}")
            print(f"步数: {result.steps_taken} | 耗时: {result.total_duration_ms/1000:.1f}s")
            print(f"{'='*40}\n")
            
        except KeyboardInterrupt:
            print("\n")
            continue


def print_help():
    """打印帮助信息"""
    print("""
GUI Agent 帮助
================

任务示例:
  - 打开记事本
  - 打开浏览器搜索 Python 教程
  - 在桌面创建一个新文件夹叫 test
  - 打开计算器计算 123 + 456
  - 复制选中的文本

提示:
  - 任务描述越具体越好
  - 复杂任务会自动分解为多步执行
  - 遇到问题时 Agent 会尝试恢复

命令:
  quit/exit/q  - 退出程序
  help         - 显示此帮助
""")


def screenshot_test(args):
    """测试截图功能"""
    from joinflow_agent.gui import ScreenParser
    
    parser = ScreenParser()
    
    print(f"屏幕尺寸: {parser.screen_size}")
    print(f"鼠标位置: {parser.get_cursor_position()}")
    
    # 截图
    state = parser.capture_and_resize()
    
    if state.screenshot_bytes:
        save_path = Path(args.output or f"./screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        state.save(str(save_path))
        print(f"[OK] 截图已保存: {save_path}")
        print(f"   大小: {len(state.screenshot_bytes) / 1024:.1f} KB")
    else:
        print("[X] 截图失败")
        return 1
    
    return 0


def check_dependencies():
    """检查依赖"""
    print("[*] 检查依赖...\n")
    
    deps = {
        "pyautogui": "GUI 控制 (鼠标/键盘)",
        "PIL": "图像处理 (截图)",  # Pillow 的导入名是 PIL
        "pyperclip": "剪贴板操作",
        "litellm": "LLM 调用",
        "psutil": "系统信息",
    }
    
    all_ok = True
    
    for module, desc in deps.items():
        try:
            __import__(module)
            print(f"  [OK] {module}: {desc}")
        except ImportError:
            print(f"  [X] {module}: {desc} (未安装)")
            all_ok = False
    
    print()
    
    if all_ok:
        print("[OK] 所有依赖已安装")
    else:
        print("[!] 部分依赖未安装，请运行:")
        print("   pip install pyautogui pillow pyperclip litellm psutil")
    
    # 检查 API 密钥
    print("\n[*] 检查 API 密钥...")
    
    if os.getenv("OPENAI_API_KEY"):
        print("  [OK] OPENAI_API_KEY 已设置")
    else:
        print("  [!] OPENAI_API_KEY 未设置")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        print("  [OK] ANTHROPIC_API_KEY 已设置")
    
    return 0 if all_ok else 1


def main():
    parser = argparse.ArgumentParser(
        description="JoinFlow GUI Agent - 像人一样操作电脑的 AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行单个任务
  python -m joinflow_agent.gui.cli run "打开记事本"
  
  # 交互式模式
  python -m joinflow_agent.gui.cli interactive
  
  # 测试截图
  python -m joinflow_agent.gui.cli screenshot
  
  # 检查依赖
  python -m joinflow_agent.gui.cli check
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # run 命令
    run_parser = subparsers.add_parser('run', help='执行任务')
    run_parser.add_argument('task', help='任务描述')
    run_parser.add_argument('--model', default='gpt-4o', help='LLM 模型 (默认: gpt-4o)')
    run_parser.add_argument('--api-key', help='API 密钥')
    run_parser.add_argument('--base-url', help='API Base URL')
    run_parser.add_argument('--max-steps', type=int, default=30, help='最大步数 (默认: 30)')
    run_parser.add_argument('--delay', type=float, default=0.5, help='步骤延迟秒数 (默认: 0.5)')
    run_parser.add_argument('--no-reflection', dest='reflection', action='store_false', help='禁用反思')
    run_parser.add_argument('--save-trajectory', help='保存执行轨迹到文件')
    run_parser.add_argument('-q', '--quiet', action='store_true', help='静默模式')
    
    # interactive 命令
    int_parser = subparsers.add_parser('interactive', aliases=['i'], help='交互式模式')
    int_parser.add_argument('--model', default='gpt-4o', help='LLM 模型')
    int_parser.add_argument('--api-key', help='API 密钥')
    int_parser.add_argument('--base-url', help='API Base URL')
    int_parser.add_argument('--max-steps', type=int, default=30, help='最大步数')
    int_parser.add_argument('--no-reflection', dest='reflection', action='store_false', help='禁用反思')
    
    # screenshot 命令
    ss_parser = subparsers.add_parser('screenshot', aliases=['ss'], help='测试截图')
    ss_parser.add_argument('-o', '--output', help='输出文件路径')
    
    # check 命令
    subparsers.add_parser('check', help='检查依赖')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if args.command == 'run':
        return run_task(args)
    elif args.command in ('interactive', 'i'):
        return run_interactive(args)
    elif args.command in ('screenshot', 'ss'):
        return screenshot_test(args)
    elif args.command == 'check':
        return check_dependencies()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

