# JoinFlow

<div align="center">

**🚀 企业级 AI Agent 自动化平台**

*一站式智能任务执行、多Agent协作、企业级报告生成解决方案*

[English](./README_EN.md) | 简体中文

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [核心功能](#-核心功能)
- [功能特性详解](#-功能特性详解)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [API 文档](#-api-文档)
- [系统架构](#-系统架构)
- [部署指南](#-部署指南)
- [配置说明](#-配置说明)
- [版本历史](#-版本历史)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 项目简介

**JoinFlow** 是一个功能完整的 **企业级 AI Agent 自动化平台**，旨在通过多智能体协作实现复杂任务的自动化执行。无论是网络搜索、数据分析、文件操作还是报告生成，JoinFlow 都能智能规划并高效完成。

### 为什么选择 JoinFlow？

| 特性 | 描述 |
|------|------|
| 🤖 **多智能体协作** | 6种专业Agent协同工作，自动规划任务执行路径 |
| 📊 **企业级导出** | 支持 PDF、Excel、PowerPoint 等7种格式，完美支持中文 |
| ⏰ **无人值守** | Cron定时任务、工作流自动化，7×24小时运行 |
| 🧠 **智能优化** | LLM缓存、Token优化，降低30-40%的API成本 |
| 🌐 **现代化界面** | 实时任务监控、多语言支持、响应式设计 |
| 🔒 **安全可靠** | 沙箱执行、API密钥管理、支持私有化部署 |

---

## ✨ 核心功能

### 功能总览

| 功能模块 | 支持 | 说明 |
|----------|:----:|------|
| **多 Agent 协作** | ✅ | Browser/LLM/OS/Data/Vision/Code 6种Agent |
| **智能任务规划** | ✅ | 自动分解复杂任务，智能调度执行 |
| **实时执行监控** | ✅ | WebSocket/SSE 实时状态推送 |
| **多格式导出** | ✅ | MD/TXT/HTML/JSON/PDF/Excel/PPT 7种格式 |
| **定时任务** | ✅ | Cron表达式、间隔执行、每日/每周定时 |
| **工作流模板** | ✅ | 预定义工作流、自定义模板、一键执行 |
| **知识库管理** | ✅ | 文档上传、向量索引、RAG检索增强 |
| **LLM 缓存** | ✅ | 语义相似度缓存，减少Token消耗 |
| **多模型支持** | ✅ | OpenAI/Claude/DeepSeek/本地模型 |
| **多语言界面** | ✅ | 中文/英文界面切换 |
| **私有化部署** | ✅ | Docker/K8s/本地完全私有运行 |
| **开源免费** | ✅ | MIT许可证，商业可用 |

---

## 📖 功能特性详解

### 🤖 多智能体系统

JoinFlow 内置6种专业Agent，各司其职：

| Agent | 图标 | 功能 | 典型任务 |
|-------|:----:|------|----------|
| **Browser Agent** | 🌐 | 网页浏览、搜索、数据采集 | 搜索新闻、爬取数据、网页截图 |
| **LLM Agent** | 🧠 | 自然语言处理、内容生成 | 文本生成、翻译、摘要、分析 |
| **OS Agent** | 💻 | 系统操作、文件管理 | 打开应用、文件操作、执行命令 |
| **Data Agent** | 📊 | 数据分析、可视化 | 数据处理、图表生成、统计分析 |
| **Vision Agent** | 👁️ | 图像识别、视觉分析 | OCR识别、图像分析、截图理解 |
| **Code Agent** | 💻 | 代码生成、执行 | 编写脚本、代码审查、自动化 |

**智能编排器 (Orchestrator)** 会根据任务描述自动：
1. 分析任务需求
2. 选择合适的Agent组合
3. 规划执行步骤
4. 协调多Agent协作
5. 汇总执行结果

### 📊 多格式导出系统

支持7种导出格式，满足不同场景需求：

| 格式 | 扩展名 | 特点 | 适用场景 |
|------|--------|------|----------|
| **Markdown** | .md | 轻量级标记语言 | 文档记录、笔记 |
| **纯文本** | .txt | 最大兼容性 | 简单文本存档 |
| **HTML** | .html | 网页格式 | 浏览器查看、邮件 |
| **JSON** | .json | 结构化数据 | 程序处理、API |
| **PDF** | .pdf | 便携文档（支持中文） | 打印、正式报告 |
| **Excel** | .xlsx | 电子表格 | 数据分析、统计 |
| **PowerPoint** | .pptx | 演示文稿 | 汇报展示、会议 |

**PDF 导出特性**：
- ✅ 完整中文支持（自动检测系统字体）
- ✅ 精美排版（标题、分隔线、表格）
- ✅ 状态图标显示
- ✅ 元数据信息

**Excel 导出特性**：
- ✅ 多工作表（概览、步骤、结果、统计）
- ✅ 图表支持
- ✅ 样式美化
- ✅ 数据筛选

**PowerPoint 导出特性**：
- ✅ 专业模板设计
- ✅ 封面页/内容页/结束页
- ✅ 步骤卡片展示
- ✅ 品牌定制

### ⏰ 定时任务系统

支持多种定时执行方式：

```yaml
# 支持的调度类型
- interval: 固定间隔执行（如每30分钟）
- cron: Cron表达式（如 "0 9 * * *" 每天9点）
- daily: 每日定时（如 09:00）
- weekly: 每周定时（如周一 10:00）
- monthly: 每月定时（如每月1号）
- once: 一次性执行
```

**典型应用场景**：
- 📰 每日新闻汇总
- 📊 定期数据报告
- 🔄 自动化数据同步
- 📧 定时邮件发送

### 🔄 工作流模板

预定义工作流快速启动：

| 模板名称 | 类别 | 描述 |
|----------|------|------|
| 网络调研 | 研究 | 搜索指定主题信息并生成报告 |
| 数据分析 | 数据 | 分析数据并生成可视化图表 |
| 代码审查 | 代码 | 审查代码质量并提供建议 |
| 文档生成 | 内容 | 根据大纲生成完整文档 |
| 竞品分析 | 研究 | 收集并对比竞品信息 |

自定义工作流支持：
- 变量模板（如 `{topic}`, `{date}`）
- 多步骤流程
- 条件分支
- 循环执行

### 🧠 知识库与 RAG

**知识库管理**：
- 支持文档格式：PDF、Word、Markdown、TXT、HTML
- 自动文本提取与分块
- 向量化索引存储
- 集合分类管理

**RAG 检索增强**：
- 语义相似度搜索
- 上下文注入
- 相关度排序
- 引用溯源

### 💾 LLM 缓存优化

**智能缓存机制**：
- 语义相似度匹配（可配置阈值）
- 自动缓存热门查询
- 过期时间管理
- 缓存统计分析

**效果数据**：
| 指标 | 数值 |
|------|------|
| 平均缓存命中率 | 35-50% |
| Token 节省 | 30-40% |
| 响应延迟降低 | 90%+（命中时） |

### 🌐 Web 界面功能

**主要页面**：
- **首页**：任务创建、快捷模板、任务列表
- **工作区**：实时执行监控、步骤可视化、结果预览
- **设置**：模型配置、API密钥、系统参数

**界面特性**：
- 🌓 深色/浅色主题切换
- 🌍 中文/英文语言切换
- 📱 响应式设计
- ⌨️ 快捷键支持
- 🔔 实时通知

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows 10+, Linux, macOS
- **内存**: 建议 8GB+
- **可选**: Docker, CUDA（GPU加速）

### 方式一：一键启动

```bash
# Windows
.\start.bat

# Linux/macOS
chmod +x start.sh
./start.sh
```

### 方式二：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/JoinSyna/joinflow.git
cd joinflow

# 2. 创建虚拟环境（推荐）
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3. 安装基础依赖
pip install -r requirements.txt

# 4. 安装可选依赖（企业功能）
pip install openpyxl python-pptx reportlab  # 导出功能
pip install playwright && playwright install chromium  # 浏览器Agent

# 5. 配置
cp config.example.json config.json
# 编辑 config.json，填入 API 密钥

# 6. 启动服务
python -m web.server
```

### 方式三：Docker 部署

```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f deploy/docker-compose.full.yml up -d
```

### 访问服务

启动后访问：`http://localhost:8000`

---

## 📖 使用指南

### Web 界面使用

#### 1. 创建任务

在首页输入任务描述，例如：
- "搜索今天的科技新闻，汇总成报告"
- "分析这份数据，生成图表"
- "打开记事本，写一段故事"

#### 2. 查看执行过程

- 实时查看任务分解步骤
- 监控每个Agent的执行状态
- 查看日志输出

#### 3. 导出结果

点击"导出为..."选择格式：
- 📝 Markdown
- 🌐 HTML
- 📊 JSON
- 📕 PDF
- 📈 Excel
- 📽️ PowerPoint

### 编程接口使用

```python
from joinflow_agent import Orchestrator, AgentConfig

# 创建配置
config = AgentConfig(
    llm_model="gpt-4o-mini",
    browser_headless=True,
    enable_cache=True
)

# 创建编排器
orchestrator = Orchestrator(config=config)

# 执行任务
result = orchestrator.execute("搜索Python最新版本信息")

# 获取结果
print(result.output)
print(f"执行步骤: {len(result.steps)}")
print(f"耗时: {result.duration}s")
```

### 导出功能使用

```python
from joinflow_core.advanced_exporter import AdvancedExportManager

exporter = AdvancedExportManager(output_dir="./exports")

# 导出为Excel
content, path = exporter.export_task(
    task_id="task_001",
    description="数据分析报告",
    result="分析结果...",
    steps=[...],
    format="excel"
)
print(f"已导出到: {path}")

# 获取可用格式
formats = exporter.get_available_formats()
for fmt in formats:
    status = "✅" if fmt['available'] else "❌"
    print(f"{status} {fmt['name']} ({fmt['extension']})")
```

### 定时任务使用

```python
from joinflow_core.scheduler import TaskScheduler, ScheduledTask, ScheduleType

scheduler = TaskScheduler()

# 创建每日任务
task = ScheduledTask(
    name="每日新闻汇总",
    description="自动收集科技新闻",
    schedule_type=ScheduleType.DAILY,
    run_at="09:00",
    task_description="搜索今天的科技新闻并生成汇总报告"
)

scheduler.add_task(task)
scheduler.start()
```

---

## 📡 API 文档

### 主要端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/chat` | POST | 发送聊天消息 |
| `/task/execute` | POST | 执行任务 |
| `/task/{id}/stream` | GET | 任务进度流(SSE) |
| `/api/export/task/{id}` | POST | 导出任务结果 |
| `/api/export/formats` | GET | 获取可用导出格式 |
| `/api/export/download/{file}` | GET | 下载导出文件 |
| `/api/workflows` | GET/POST | 工作流管理 |
| `/api/schedules` | GET/POST | 定时任务管理 |
| `/api/knowledge/upload` | POST | 上传知识库文档 |
| `/api/models` | GET/POST | 模型配置管理 |

### 导出 API 示例

```bash
# 导出为PDF
curl -X POST "http://localhost:8000/api/export/task/task_001" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "pdf",
    "description": "任务描述",
    "result": "任务结果内容",
    "steps": [],
    "metadata": {"status": "completed"}
  }'

# 获取可用格式
curl "http://localhost:8000/api/export/formats"
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Interface                            │
│                    (HTML + JavaScript + CSS)                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/WebSocket/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Web Server                          │
│                    (REST API + 实时通信)                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Orchestrator │      │  Scheduler   │      │   Exporter   │
│   智能编排器  │      │  任务调度器   │      │  导出管理器   │
└──────┬───────┘      └──────────────┘      └──────────────┘
       │
       ├──────┬──────┬──────┬──────┬──────┐
       │      │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼      ▼
   ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
   │Browser││ LLM ││  OS  ││ Data ││Vision││ Code │
   │Agent ││Agent ││Agent ││Agent ││Agent ││Agent │
   └──────┘└──────┘└──────┘└──────┘└──────┘└──────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Qdrant Service Manager                        │
│              (向量存储 / LLM缓存 / Token优化)                     │
└─────────────────────────────────────────────────────────────────┘
```

### 目录结构

```
joinflow/
├── main.py                    # 主入口
├── config.json                # 配置文件
├── start.bat / start.sh       # 一键启动脚本
│
├── joinflow_agent/            # Agent 系统
│   ├── orchestrator.py        # 智能编排器
│   ├── browser.py             # 浏览器 Agent
│   ├── llm.py                 # LLM Agent
│   ├── os_agent.py            # 系统 Agent
│   ├── data_agent.py          # 数据分析 Agent
│   ├── vision_agent.py        # 视觉 Agent
│   └── session.py             # 会话管理
│
├── joinflow_core/             # 核心模块
│   ├── qdrant_service.py      # Qdrant 服务管理
│   ├── cached_llm.py          # LLM 缓存
│   ├── scheduler.py           # 任务调度
│   ├── exporter.py            # 基础导出 (MD/HTML/JSON/PDF)
│   ├── advanced_exporter.py   # 企业导出 (Excel/PPT)
│   ├── webhooks.py            # Webhook 通知
│   └── task_templates.py      # 任务模板
│
├── joinflow_rag/              # RAG 引擎
│   ├── engine.py              # RAG 核心
│   └── knowledge_base.py      # 知识库管理
│
├── joinflow_memory/           # 记忆系统
│   └── history.py             # 历史存储
│
├── web/                       # Web 服务
│   ├── server.py              # FastAPI 服务器
│   ├── api_extensions.py      # API 扩展
│   ├── subscription.py        # 订阅管理
│   ├── templates/             # HTML 模板
│   └── static/                # 静态资源
│
├── deploy/                    # 部署配置
│   ├── docker-compose.*.yml   # Docker 配置
│   ├── nginx/                 # Nginx 配置
│   ├── kubernetes/            # K8s 配置
│   └── scripts/               # 部署脚本
│
└── workspace/                 # 工作空间
    ├── exports/               # 导出文件
    └── results/               # 结果文件
```

---

## 🚢 部署指南

### Docker 部署

```bash
# 完整部署（包含 Qdrant）
docker-compose -f deploy/docker-compose.full.yml up -d

# 查看日志
docker-compose logs -f joinflow
```

### Kubernetes 部署

```bash
# 应用配置
kubectl apply -f deploy/kubernetes/

# 查看状态
kubectl get pods -n joinflow
```

### 生产环境配置

```bash
# Nginx 反向代理
sudo cp deploy/nginx/joinflow.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/joinflow.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Systemd 服务
sudo cp deploy/scripts/joinflow.service /etc/systemd/system/
sudo systemctl enable joinflow
sudo systemctl start joinflow
```

---

## ⚙️ 配置说明

### config.json 示例

```json
{
  "llm": {
    "default_model": "gpt-4o-mini",
    "api_key": "your-api-key",
    "api_base": "https://api.openai.com/v1",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "models": [
    {
      "id": "gpt-4o-mini",
      "name": "GPT-4o Mini",
      "provider": "openai",
      "api_key": "sk-xxx",
      "is_default": true
    }
  ],
  "qdrant": {
    "host": "localhost",
    "port": 6333,
    "use_memory": true
  },
  "cache": {
    "enabled": true,
    "similarity_threshold": 0.92,
    "ttl_hours": 24
  },
  "export": {
    "default_format": "markdown",
    "output_dir": "./workspace/exports"
  }
}
```

### 环境变量

```bash
# LLM 配置
export OPENAI_API_KEY=your-key
export LLM_MODEL=gpt-4o-mini

# 服务配置
export JOINFLOW_PORT=8000
export JOINFLOW_HOST=0.0.0.0

# Qdrant 配置
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
```

---

## 📊 性能指标

### RAG 性能 (10,000 文档)

| 指标 | 结果 |
|------|------|
| 嵌入时间 | ~24.5s (408 docs/s) |
| 索引时间 | ~7.5s (1326 docs/s) |
| 平均查询延迟 | **80ms** |
| P95 延迟 | **140ms** |

### LLM 缓存效果

| 指标 | 结果 |
|------|------|
| 平均缓存命中率 | 35-50% |
| Token 节省 | 30-40% |
| 响应延迟降低 | 90%+ (缓存命中时) |

---

## 🆕 版本历史

### v0.3.0 (2026-01-11) - 企业版

**新增功能:**
- ☁️ 云服务部署功能
- 📊 高级导出功能（Excel/PPT/PDF中文支持）
- 🧠 Qdrant 服务管理器
- 💾 LLM 响应缓存
- 🔔 Webhook/通知系统
- 📋 任务模板系统

**修复:**
- 修复 PDF 导出中文乱码问题
- 修复 PPT 导出兼容性问题
- 修复导出格式选择无效问题

### v0.2.0 - Agent 系统

- 🤖 多 Agent 系统
- 🧠 智能编排器
- 💾 用户历史记录

### v0.1.0 - RAG 基础

- 📚 RAG 引擎
- 🔍 向量存储

---

## 🤝 贡献指南

欢迎贡献代码！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [Qdrant](https://qdrant.tech/) - 向量数据库
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [OpenAI](https://openai.com/) - LLM API
- [ReportLab](https://www.reportlab.com/) - PDF 生成
- [python-pptx](https://python-pptx.readthedocs.io/) - PPT 生成
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel 生成

---

## 📞 联系方式

- **作者**: JoinSyna
- **GitHub**: [https://github.com/JoinSyna/joinflow](https://github.com/JoinSyna/joinflow)
- **Issues**: [提交问题](https://github.com/JoinSyna/joinflow/issues)
- **Discussions**: [参与讨论](https://github.com/JoinSyna/joinflow/discussions)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个 Star！**

Made with ❤️ by JoinSyna

</div>
