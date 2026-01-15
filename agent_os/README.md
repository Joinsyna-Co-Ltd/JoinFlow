# 🤖 Agent OS - 智能操作系统代理

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

**Agent OS** 是一个基于AI的智能操作系统代理，让您通过自然语言控制电脑的一切操作。

## ✨ 核心特性

- 🗣️ **自然语言交互** - 用日常语言描述任务，Agent OS理解并执行
- 📁 **全面文件管理** - 创建、读取、搜索、复制、移动文件
- 🚀 **应用程序控制** - 打开、关闭、管理应用程序
- 🔍 **智能搜索** - 本地文件搜索和网页搜索
- 💻 **系统监控** - CPU、内存、磁盘等系统信息
- 🎨 **现代化UI** - 美观的Web界面，支持暗色主题
- 🔗 **LLM集成** - 支持OpenAI、Anthropic、DeepSeek等

## 🚀 快速开始

### 安装依赖

```bash
pip install flask flask-cors psutil pyperclip
```

### 启动Web界面

```bash
python -m agent_os --web
```

然后访问 http://localhost:8080

### 命令行模式

```bash
# 交互模式
python -m agent_os -i

# 执行单个命令
python -m agent_os "打开记事本"
python -m agent_os "查找PDF文件"
```

## 📖 使用示例

### 文件操作

```
创建文件 test.txt
读取 config.json
在桌面创建项目文件夹
复制 file.txt 到 backup 文件夹
查找所有PDF文件
```

### 应用管理

```
打开记事本
启动Chrome浏览器
打开VSCode
关闭微信
```

### 网页搜索

```
搜索Python教程
百度一下天气预报
打开github.com
谷歌搜索机器学习
```

### 系统操作

```
系统信息
截图保存到桌面
获取剪贴板内容
执行 dir 命令
```

## 🏗️ 架构

```
agent_os/
├── core/               # 核心模块
│   ├── agent.py       # 主代理类
│   ├── config.py      # 配置管理
│   ├── session.py     # 会话管理
│   └── runtime.py     # 运行时环境
├── intent/            # 意图理解
│   ├── parser.py      # 意图解析器
│   └── types.py       # 意图类型
├── planner/           # 任务规划
│   ├── planner.py     # 任务规划器
│   └── task.py        # 任务定义
├── executors/         # 执行器
│   ├── file_executor.py    # 文件操作
│   ├── app_executor.py     # 应用管理
│   ├── search_executor.py  # 搜索功能
│   ├── system_executor.py  # 系统操作
│   ├── browser_executor.py # 浏览器操作
│   └── compose_executor.py # 内容生成
├── llm/               # LLM集成
│   └── client.py      # LLM客户端
└── ui/                # Web界面
    ├── server.py      # Flask服务器
    ├── static/        # 静态资源
    └── templates/     # HTML模板
```

## ⚙️ 配置

### 环境变量

```bash
# OpenAI API
export OPENAI_API_KEY="your-api-key"

# DeepSeek API
export DEEPSEEK_API_KEY="your-api-key"
```

### 配置文件

创建 `config.json`:

```json
{
    "name": "Agent OS",
    "security_level": "USER",
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "theme": "dark"
}
```

## 🔐 安全级别

| 级别 | 描述 |
|------|------|
| SANDBOX | 仅工作目录 |
| USER | 用户目录（默认） |
| SYSTEM | 全系统访问 |

## 🤝 API参考

### Python API

```python
from agent_os import AgentOS

agent = AgentOS()

# 执行命令
result = agent.run("打开记事本")
print(result.success, result.message)

# 搜索文件
result = agent.search_files("*.pdf", "~/Documents")

# 网页搜索
result = agent.search_web("Python教程", engine="google")

# 系统信息
result = agent.get_system_info()
```

### HTTP API

```bash
# 执行命令
POST /api/execute
{"command": "打开记事本"}

# 系统信息
GET /api/system/info

# 搜索文件
POST /api/search
{"query": "*.pdf", "path": "~/Documents"}
```

## 🛠️ 扩展开发

### 添加自定义执行器

```python
from agent_os.executors.base import BaseExecutor
from agent_os.core.runtime import ActionResult

class MyExecutor(BaseExecutor):
    name = "my"
    
    def execute(self, action, command, params):
        # 实现你的逻辑
        return ActionResult(
            success=True,
            action=action,
            message="操作完成"
        )
```

## 📝 许可证

MIT License

---

<p align="center">
  <b>Agent OS</b> - 让AI成为您的操作系统助手 🚀
</p>

