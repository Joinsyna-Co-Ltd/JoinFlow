# JoinFlow 智能操作系统助手

一个基于大模型的智能操作系统助手，能够理解自然语言指令并自动执行各种系统操作。

## 特性

- 🧠 **智能理解** - 使用LLM理解自然语言指令
- 📁 **文件操作** - 创建、读取、写入、删除、复制、移动、搜索文件
- 🚀 **应用管理** - 打开、关闭、列出运行中的应用程序
- 🔍 **智能搜索** - 按名称、内容、大小、时间搜索文件
- 🌐 **浏览器控制** - 打开网页、搜索引擎搜索
- ⚙️ **系统操作** - 获取系统信息、截图、剪贴板、执行命令
- ✏️ **内容创作** - 使用LLM生成文本、代码、文档
- 📝 **任务规划** - 自动分解复杂任务为可执行步骤
- 💾 **记忆系统** - 记住用户偏好和常用操作

## 安装

```bash
# 安装依赖
pip install psutil pyautogui pyperclip pillow

# 可选：安装LLM支持
pip install openai

# 可选：安装Web API支持
pip install flask flask-cors
```

## 快速开始

### 基本使用

```python
from joinflow_os_assistant import OSAssistant

# 创建助手
assistant = OSAssistant()

# 执行自然语言命令
result = assistant.execute("打开记事本")
print(result.message)

# 搜索文件
result = assistant.execute("在桌面查找所有PDF文件")

# 创建文件
result = assistant.create_file("test.txt", "Hello World")

# 获取系统信息
result = assistant.get_system_info()
print(result.data)

# 浏览器搜索
result = assistant.search_web("Python教程", engine="baidu")
```

### 使用LLM增强

```python
from joinflow_os_assistant import OSAssistant
from joinflow_os_assistant.llm.client import create_llm_client

# 创建LLM客户端
llm = create_llm_client(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4"
)

# 创建带LLM的助手
assistant = OSAssistant(llm_client=llm)

# 执行复杂任务
result = assistant.execute("整理下载文件夹，按文件类型分类")
```

### 启动API服务

```python
from joinflow_os_assistant.api.server import run_server

# 启动服务
run_server(host="0.0.0.0", port=5000)
```

## 支持的操作

### 文件操作
- `file.create` - 创建文件
- `file.read` - 读取文件
- `file.write` - 写入文件
- `file.delete` - 删除文件
- `file.copy` - 复制文件
- `file.move` - 移动/重命名文件
- `file.open` - 用默认程序打开

### 目录操作
- `dir.create` - 创建目录
- `dir.list` - 列出目录内容
- `dir.delete` - 删除目录
- `dir.navigate` - 切换目录

### 搜索操作
- `search.file` - 搜索文件
- `search.content` - 搜索文件内容
- `search.recent` - 搜索最近文件
- `search.large` - 搜索大文件

### 应用操作
- `app.open` - 打开应用
- `app.close` - 关闭应用
- `app.list` - 列出运行中的应用

### 浏览器操作
- `browser.open` - 打开浏览器
- `browser.search` - 搜索（支持Google、百度、Bing等）
- `browser.navigate` - 访问URL

### 系统操作
- `system.info` - 获取系统信息
- `system.screenshot` - 截图
- `system.notify` - 发送通知
- `clipboard.get` - 获取剪贴板
- `clipboard.set` - 设置剪贴板
- `command.execute` - 执行命令

### 内容创作
- `compose.text` - 生成文本
- `compose.code` - 生成代码
- `compose.document` - 生成文档
- `compose.summary` - 生成摘要

## 自然语言示例

```
"打开记事本"
"在桌面创建一个名为项目的文件夹"
"查找最近修改的PDF文件"
"搜索Python教程"
"复制桌面上的报告.docx到文档文件夹"
"截一张屏幕截图保存到桌面"
"获取系统信息"
"帮我写一段Python代码来读取CSV文件"
```

## API接口

### POST /api/execute
执行自然语言命令

```json
{
    "command": "打开记事本",
    "auto_confirm": false
}
```

### GET /api/system/info
获取系统信息

### POST /api/file/read
读取文件

```json
{
    "path": "test.txt"
}
```

### POST /api/browser/search
浏览器搜索

```json
{
    "query": "Python教程",
    "engine": "google"
}
```

## 架构

```
joinflow_os_assistant/
├── core/           # 核心模块
│   ├── assistant.py    # 主助手类
│   ├── config.py       # 配置管理
│   ├── context.py      # 执行上下文
│   └── memory.py       # 记忆系统
├── intent/         # 意图理解
│   ├── parser.py       # 意图解析器
│   ├── patterns.py     # 模式匹配
│   └── types.py        # 类型定义
├── planner/        # 任务规划
│   ├── task_planner.py # 任务规划器
│   ├── task.py         # 任务定义
│   └── strategies.py   # 执行策略
├── executors/      # 执行器
│   ├── file_executor.py    # 文件操作
│   ├── app_executor.py     # 应用管理
│   ├── search_executor.py  # 搜索
│   ├── system_executor.py  # 系统操作
│   ├── browser_executor.py # 浏览器
│   └── compose_executor.py # 内容创作
├── llm/            # LLM集成
│   ├── client.py       # LLM客户端
│   └── prompts.py      # 提示词模板
├── api/            # API接口
│   ├── server.py       # Flask服务
│   └── routes.py       # 路由定义
└── examples/       # 示例代码
```

## 安全性

- 危险命令自动阻止（如 `rm -rf /`）
- 敏感路径保护
- 可配置权限级别
- 危险操作需要确认
- 操作日志记录

## 许可证

MIT License

