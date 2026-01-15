"""
基本使用示例
"""
from joinflow_os_assistant import OSAssistant


def main():
    """基本使用示例"""
    
    # 创建助手
    assistant = OSAssistant()
    
    print("=" * 50)
    print("JoinFlow 智能操作系统助手")
    print("=" * 50)
    
    # 示例1: 打开应用
    print("\n--- 示例1: 打开记事本 ---")
    result = assistant.execute("打开记事本")
    print(f"结果: {result.message}")
    
    # 示例2: 获取系统信息
    print("\n--- 示例2: 获取系统信息 ---")
    result = assistant.get_system_info()
    if result.success:
        info = result.data
        print(f"系统: {info['platform']['system']}")
        print(f"CPU核心: {info['cpu']['cores_logical']}")
        print(f"内存: {info['memory']['total_gb']}GB")
    
    # 示例3: 搜索文件
    print("\n--- 示例3: 搜索文件 ---")
    result = assistant.execute("在桌面查找所有txt文件")
    if result.success and result.data:
        files = result.data.get("results", [])
        print(f"找到 {len(files)} 个文件")
        for f in files[:5]:
            print(f"  - {f['name']}")
    
    # 示例4: 浏览器搜索
    print("\n--- 示例4: 浏览器搜索 ---")
    result = assistant.search_web("Python教程", engine="baidu")
    print(f"结果: {result.message}")
    
    # 示例5: 创建文件
    print("\n--- 示例5: 创建文件 ---")
    result = assistant.create_file(
        "test_assistant.txt",
        "这是由JoinFlow助手创建的测试文件"
    )
    print(f"结果: {result.message}")
    
    # 示例6: 复杂任务
    print("\n--- 示例6: 复杂任务 ---")
    result = assistant.execute(
        "在当前目录创建一个名为'项目'的文件夹，然后在里面创建README.md文件"
    )
    print(f"结果: {result.message}")
    
    # 查看帮助
    print("\n--- 查看帮助 ---")
    result = assistant.execute("帮助")
    print(result.message)


def interactive_mode():
    """交互式模式"""
    assistant = OSAssistant()
    
    print("=" * 50)
    print("JoinFlow 智能操作系统助手 - 交互模式")
    print("输入 'exit' 退出，输入 'help' 查看帮助")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['exit', 'quit', '退出']:
                print("再见！")
                break
            
            result = assistant.execute(command)
            
            print(f"\n{result.message}")
            
            if result.data and isinstance(result.data, dict):
                # 显示部分数据
                if "results" in result.data:
                    results = result.data["results"]
                    if results:
                        print(f"\n找到 {len(results)} 个结果:")
                        for item in results[:5]:
                            if isinstance(item, dict):
                                print(f"  - {item.get('name', item.get('path', str(item)))}")
                            else:
                                print(f"  - {item}")
                elif "content" in result.data:
                    content = result.data["content"]
                    if len(content) > 500:
                        print(f"\n内容预览:\n{content[:500]}...")
                    else:
                        print(f"\n{content}")
                        
        except KeyboardInterrupt:
            print("\n\n操作已取消")
        except Exception as e:
            print(f"\n错误: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '-i':
        interactive_mode()
    else:
        main()

