"""
Smart Assistant - 智能命令助手
==============================

理解自然语言意图 → 生成命令 → 执行并返回结果
"""
import sys
import os
import io
import subprocess
import platform

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ['OPENROUTER_API_KEY'] = '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'

import litellm

# 意图理解提示词
INTENT_PROMPT = """你是一个智能操作系统助手。用户会用自然语言告诉你他们想做什么，你需要：
1. 理解用户意图
2. 生成相应的系统命令（Windows PowerShell 或 CMD）
3. 返回 JSON 格式的结果

当前系统: {system}
当前目录: {cwd}

用户说: "{query}"

请分析用户意图并返回 JSON（只返回JSON，不要其他内容）:
```json
{{
    "intent": "用户意图的简短描述",
    "commands": ["要执行的命令1", "要执行的命令2"],
    "explanation": "为什么执行这些命令",
    "dangerous": false
}}
```

常见意图映射：
- 查看电脑配置/系统信息 → systeminfo, wmic cpu get name, wmic memorychip get capacity
- 查看磁盘空间 → wmic logicaldisk get size,freespace,caption
- 查看进程 → tasklist
- 查看网络 → ipconfig /all
- 打开应用 → start <app>
- 查看文件 → dir, type
- 搜索文件 → dir /s /b *keyword*

只返回 JSON，不要额外的解释。
"""


def understand_intent(query: str) -> dict:
    """理解用户意图"""
    prompt = INTENT_PROMPT.format(
        system=platform.system() + " " + platform.release(),
        cwd=os.getcwd(),
        query=query
    )
    
    try:
        response = litellm.completion(
            model="openrouter/mistralai/mistral-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.environ['OPENROUTER_API_KEY'],
            max_tokens=500,
            temperature=0.1,
        )
        
        content = response.choices[0].message.content.strip()
        
        # 提取 JSON
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        
        return {"error": "无法解析响应", "raw": content}
        
    except Exception as e:
        return {"error": str(e)}


def execute_commands(commands: list) -> list:
    """执行命令列表"""
    results = []
    
    for cmd in commands:
        print(f"\n  > 执行: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
            
            output = result.stdout or result.stderr
            results.append({
                "command": cmd,
                "success": result.returncode == 0,
                "output": output[:2000] if output else "(无输出)"
            })
            
        except subprocess.TimeoutExpired:
            results.append({
                "command": cmd,
                "success": False,
                "output": "命令执行超时"
            })
        except Exception as e:
            results.append({
                "command": cmd,
                "success": False,
                "output": str(e)
            })
    
    return results


def main():
    print("=" * 60)
    print("  Smart Assistant - 智能命令助手")
    print("  输入自然语言，我来理解并执行")
    print("  输入 'exit' 退出")
    print("=" * 60)
    
    while True:
        try:
            query = input("\n你: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ('exit', 'quit', 'q'):
                print("再见!")
                break
            
            print("\n[思考中...] 理解你的意图")
            
            # 1. 理解意图
            intent = understand_intent(query)
            
            if "error" in intent:
                print(f"\n[错误] {intent['error']}")
                continue
            
            print(f"\n[理解] {intent.get('intent', '未知')}")
            print(f"[说明] {intent.get('explanation', '')}")
            
            commands = intent.get('commands', [])
            if not commands:
                print("[提示] 没有需要执行的命令")
                continue
            
            # 2. 确认危险操作
            if intent.get('dangerous'):
                confirm = input("\n[警告] 这是危险操作，确认执行? (y/n): ")
                if confirm.lower() != 'y':
                    print("[取消] 操作已取消")
                    continue
            
            # 3. 执行命令
            print("\n[执行中...]")
            results = execute_commands(commands)
            
            # 4. 显示结果
            print("\n" + "=" * 60)
            print("[结果]")
            print("=" * 60)
            
            for r in results:
                status = "✓" if r['success'] else "✗"
                print(f"\n{status} {r['command']}")
                print("-" * 40)
                print(r['output'])
            
        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except Exception as e:
            print(f"\n[错误] {e}")


# 单次执行模式
def run_once(query: str):
    """单次执行一个查询"""
    print("=" * 60)
    print(f"  查询: {query}")
    print("=" * 60)
    
    print("\n[1/3] 理解意图...")
    intent = understand_intent(query)
    
    if "error" in intent:
        print(f"[错误] {intent['error']}")
        return
    
    print(f"  意图: {intent.get('intent', '未知')}")
    print(f"  说明: {intent.get('explanation', '')}")
    
    commands = intent.get('commands', [])
    if not commands:
        print("\n[提示] 没有需要执行的命令")
        return
    
    print(f"\n[2/3] 执行 {len(commands)} 个命令...")
    results = execute_commands(commands)
    
    print("\n[3/3] 结果:")
    print("=" * 60)
    
    for r in results:
        status = "SUCCESS" if r['success'] else "FAILED"
        print(f"\n[{status}] {r['command']}")
        print("-" * 40)
        print(r['output'])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行模式
        query = " ".join(sys.argv[1:])
        run_once(query)
    else:
        # 交互模式
        main()

