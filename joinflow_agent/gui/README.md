# JoinFlow GUI Agent

> 类似 [Agent-S](https://github.com/simular-ai/Agent-S) 的 GUI 自动化框架，让 AI 像人一样操作电脑。

## 🎯 功能特性

- **🖥️ 屏幕理解**: 使用多模态 LLM（GPT-4V、Claude 3 等）理解屏幕内容
- **🎯 元素定位 (Grounding)**: 精确定位 UI 元素坐标
- **🖱️ 动作执行**: 支持点击、输入、滚动、快捷键等操作
- **🔄 自动循环**: 截图→分析→操作→重复
- **🤔 反思机制**: 自动评估任务进度，必要时调整策略
- **🌐 跨平台**: 支持 Windows、macOS、Linux

## 📦 安装

```bash
# 安装 GUI Agent 依赖
pip install pyautogui pillow pyperclip litellm psutil

# 或者安装完整的 JoinFlow
pip install -e ".[gui]"
```

## 🚀 快速开始

### 方式一：命令行

```bash
# 执行单个任务
python -m joinflow_agent.gui.cli run "打开记事本"

# 交互式模式
python -m joinflow_agent.gui.cli interactive

# 测试截图
python -m joinflow_agent.gui.cli screenshot

# 检查依赖
python -m joinflow_agent.gui.cli check
```

### 方式二：Python 代码

```python
import os
from joinflow_agent.gui import GUIAgent, GUIAgentConfig

# 创建配置 - 默认使用 OpenRouter
config = GUIAgentConfig(
    model="openrouter/google/gemini-2.0-flash-exp:free",
    api_key="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",
    max_steps=30,
    enable_reflection=True,
)

# 创建 Agent
agent = GUIAgent(config)

# 执行任务
result = agent.run("打开记事本并输入 Hello World")

print(f"状态: {result.status.value}")
print(f"消息: {result.message}")
print(f"步数: {result.steps_taken}")
```

### 方式三：启动脚本

Windows:
```batch
start_gui_agent.bat
```

Linux/macOS:
```bash
./start_gui_agent.sh
```

## ⚙️ 配置选项

```python
config = GUIAgentConfig(
    # LLM 配置 - 默认使用 OpenRouter
    model="openrouter/google/gemini-2.0-flash-exp:free",  # 免费视觉模型
    api_key="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",
    base_url=None,                     # 自定义 API 端点
    temperature=0.1,
    
    # 执行配置
    max_steps=50,                      # 最大执行步数
    max_retries=3,                     # 每步最大重试
    step_delay=0.5,                    # 步骤间延迟
    
    # 反思配置
    enable_reflection=True,            # 启用反思 Agent
    reflection_interval=5,             # 每隔几步反思
    
    # 安全配置
    fail_safe=True,                    # 鼠标移到角落中断
    
    # 截图配置
    max_screenshot_width=1920,
    max_screenshot_height=1080,
)
```

## 🔧 支持的 LLM

通过 [LiteLLM](https://github.com/BerriAI/litellm) 支持多种提供商：

| 提供商 | 模型示例 | 环境变量 |
|--------|----------|----------|
| OpenAI | `gpt-4o`, `gpt-4-vision-preview` | `OPENAI_API_KEY` |
| Azure | `azure/gpt-4o` | `AZURE_API_KEY` |
| Anthropic | `claude-3-opus-20240229` | `ANTHROPIC_API_KEY` |
| Google | `gemini/gemini-pro-vision` | `GOOGLE_API_KEY` |
| Ollama | `ollama/llava` | (本地运行) |

## 🎮 支持的动作

| 动作 | 描述 | 示例 |
|------|------|------|
| `click` | 点击元素 | 点击"开始"按钮 |
| `double_click` | 双击 | 双击文件打开 |
| `right_click` | 右键点击 | 右键打开菜单 |
| `type` | 输入文本 | 在搜索框输入文字 |
| `press` | 按键 | 按 Enter 确认 |
| `hotkey` | 组合键 | Ctrl+C 复制 |
| `scroll` | 滚动 | 向下滚动页面 |
| `wait` | 等待 | 等待加载完成 |
| `done` | 完成 | 任务成功完成 |
| `fail` | 失败 | 无法完成任务 |

## 📊 执行轨迹

每次执行会记录完整轨迹：

```python
result = agent.run("打开计算器")

for step in result.trajectory:
    print(f"步骤 {step.step_number}:")
    print(f"  观察: {step.observation}")
    print(f"  思考: {step.thinking}")
    print(f"  动作: {step.action}")
```

## 🛡️ 安全注意事项

1. **沙盒环境**: 建议在虚拟机中测试
2. **API 费用**: 每步截图+LLM调用会产生费用
3. **权限**: 需要屏幕截图和输入控制权限
4. **Fail-Safe**: 默认启用，鼠标移到屏幕角落可中断

## 🏗️ 架构

```
GUI Agent 架构
┌─────────────────────────────────────────────────────┐
│                    GUIAgent                         │
│  ┌──────────────────────────────────────────────┐  │
│  │              Main Loop                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │  │
│  │  │Screenshot│→│  LLM    │→│Action Execute│  │  │
│  │  │ Parser  │  │ Analysis│  │             │  │  │
│  │  └─────────┘  └────┬────┘  └──────┬──────┘  │  │
│  │                    │              │          │  │
│  │              ┌─────▼─────┐        │          │  │
│  │              │ Grounding │────────┘          │  │
│  │              │   Agent   │                   │  │
│  │              └───────────┘                   │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 📁 模块结构

```
joinflow_agent/gui/
├── __init__.py          # 模块入口
├── gui_agent.py         # 主控制器（核心）
├── screen_parser.py     # 屏幕截图和解析
├── grounding.py         # UI 元素定位
├── action_space.py      # 动作定义和执行
├── planner.py           # 分层任务规划（Agent-S 风格）
├── memory.py            # 经验记忆学习（Agent-S 风格）
├── code_executor.py     # 本地代码执行（Agent-S 风格）
├── prompts.py           # 提示词模板
├── cli.py               # 命令行界面
├── examples.py          # 使用示例
└── README.md            # 本文档
```

## 🔍 与 Agent-S 的对比

| 特性 | Agent-S | JoinFlow GUI Agent |
|------|---------|-------------------|
| 开源 | ✅ Apache-2.0 | ✅ MIT |
| 视觉理解 | ✅ GPT-4V/Claude | ✅ 多模态 LLM |
| Grounding | ✅ UI-TARS | ✅ Vision LLM / 可扩展 |
| 反思机制 | ✅ Reflection Agent | ✅ 可配置 |
| **分层规划** | ✅ Hierarchical Planning | ✅ HierarchicalPlanner |
| **经验学习** | ✅ Experience-augmented | ✅ ExperienceMemory |
| **代码执行** | ✅ Local Code Env | ✅ LocalCodeExecutor |
| 跨平台 | ✅ Win/Mac/Linux | ✅ Win/Mac/Linux |
| 中文支持 | ⚠️ 有限 | ✅ 完善 |
| 集成度 | 独立项目 | JoinFlow 生态 |

### ✅ Agent-S 核心功能对照

| Agent-S 功能 | JoinFlow 实现 | 说明 |
|-------------|--------------|------|
| 屏幕截图 | `ScreenParser` | 跨平台截图 |
| 视觉理解 | 多模态 LLM | GPT-4V, Claude 3, Gemini |
| Grounding | `GroundingAgent` | 支持 Vision LLM 和专用模型 |
| 动作执行 | `ActionExecutor` | pyautogui 驱动 |
| 反思机制 | `_reflect()` | 定期评估进度 |
| 分层规划 | `HierarchicalPlanner` | 任务分解为子任务 |
| 经验学习 | `ExperienceMemory` | 记录和复用成功经验 |
| 代码执行 | `LocalCodeExecutor` | Python/Shell 执行 |

## 📝 任务示例

```python
# 基础任务
agent.run("打开记事本")
agent.run("打开浏览器搜索 Python 教程")
agent.run("截图保存到桌面")

# 复杂任务
agent.run("打开 Excel，创建新工作表，在 A1 输入 Hello")
agent.run("打开 Chrome，登录 GitHub，star 第一个项目")
agent.run("打开命令提示符，执行 dir 命令")
```

## 🐛 常见问题

**Q: pyautogui 无法截图怎么办？**
A: Windows 需要管理员权限，macOS 需要在系统偏好设置中授权屏幕录制。

**Q: 如何使用本地模型？**
A: 使用 Ollama + llava：
```python
config = GUIAgentConfig(
    model="ollama/llava",
    base_url="http://localhost:11434"
)
```

**Q: 执行速度很慢？**
A: 每步需要截图+LLM调用，可以尝试：
1. 使用更快的模型（如 gpt-4o-mini）
2. 减小截图分辨率
3. 减少 step_delay

## 📄 License

MIT License - 可自由使用、修改、商用。

