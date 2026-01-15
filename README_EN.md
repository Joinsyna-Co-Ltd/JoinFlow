# JoinFlow

<div align="center">

**🚀 Enterprise-Grade AI Agent Automation Platform**

*All-in-One Intelligent Task Execution, Multi-Agent Collaboration, and Enterprise Report Generation Solution*

English | [简体中文](./README.MD)

</div>

---

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Core Features](#-core-features)
- [Feature Details](#-feature-details)
- [Quick Start](#-quick-start)
- [User Guide](#-user-guide)
- [API Documentation](#-api-documentation)
- [System Architecture](#-system-architecture)
- [Deployment Guide](#-deployment-guide)
- [Configuration](#-configuration)
- [Version History](#-version-history)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Introduction

**JoinFlow** is a fully-featured **Enterprise-Grade AI Agent Automation Platform** designed to automate complex task execution through multi-agent collaboration. Whether it's web searching, data analysis, file operations, or report generation, JoinFlow can intelligently plan and efficiently complete any task.

### Why Choose JoinFlow?

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-Agent Collaboration** | 6 specialized Agents working together, automatically planning task execution paths |
| 📊 **Enterprise Export** | Supports 7 formats including PDF, Excel, PowerPoint with full Chinese support |
| ⏰ **Unattended Operation** | Cron scheduled tasks, workflow automation, 24/7 operation |
| 🧠 **Intelligent Optimization** | LLM caching, Token optimization, reducing API costs by 30-40% |
| 🌐 **Modern Interface** | Real-time task monitoring, multi-language support, responsive design |
| 🔒 **Secure & Reliable** | Sandbox execution, API key management, private deployment support |

---

## ✨ Core Features

### Feature Overview

| Module | Support | Description |
|--------|:-------:|-------------|
| **Multi-Agent Collaboration** | ✅ | Browser/LLM/OS/Data/Vision/Code - 6 types of Agents |
| **Intelligent Task Planning** | ✅ | Automatic complex task decomposition, intelligent scheduling |
| **Real-time Monitoring** | ✅ | WebSocket/SSE real-time status updates |
| **Multi-format Export** | ✅ | MD/TXT/HTML/JSON/PDF/Excel/PPT - 7 formats |
| **Scheduled Tasks** | ✅ | Cron expressions, interval execution, daily/weekly scheduling |
| **Workflow Templates** | ✅ | Predefined workflows, custom templates, one-click execution |
| **Knowledge Base** | ✅ | Document upload, vector indexing, RAG retrieval enhancement |
| **LLM Caching** | ✅ | Semantic similarity caching, reducing Token consumption |
| **Multi-model Support** | ✅ | OpenAI/Claude/DeepSeek/Local models |
| **Multi-language UI** | ✅ | Chinese/English interface switching |
| **Private Deployment** | ✅ | Docker/K8s/Local fully private operation |
| **Open Source** | ✅ | MIT License, commercially available |

---

## 📖 Feature Details

### 🤖 Multi-Agent System

JoinFlow includes 6 specialized Agents, each with specific responsibilities:

| Agent | Icon | Function | Typical Tasks |
|-------|:----:|----------|---------------|
| **Browser Agent** | 🌐 | Web browsing, searching, data collection | News search, data scraping, web screenshots |
| **LLM Agent** | 🧠 | Natural language processing, content generation | Text generation, translation, summarization, analysis |
| **OS Agent** | 💻 | System operations, file management | Open applications, file operations, execute commands |
| **Data Agent** | 📊 | Data analysis, visualization | Data processing, chart generation, statistical analysis |
| **Vision Agent** | 👁️ | Image recognition, visual analysis | OCR recognition, image analysis, screenshot understanding |
| **Code Agent** | 💻 | Code generation, execution | Script writing, code review, automation |

**Intelligent Orchestrator** automatically:
1. Analyzes task requirements
2. Selects appropriate Agent combinations
3. Plans execution steps
4. Coordinates multi-Agent collaboration
5. Aggregates execution results

### 📊 Multi-format Export System

Supports 7 export formats for different scenarios:

| Format | Extension | Features | Use Cases |
|--------|-----------|----------|-----------|
| **Markdown** | .md | Lightweight markup language | Documentation, notes |
| **Plain Text** | .txt | Maximum compatibility | Simple text archiving |
| **HTML** | .html | Web format | Browser viewing, emails |
| **JSON** | .json | Structured data | Program processing, APIs |
| **PDF** | .pdf | Portable document (Chinese support) | Printing, formal reports |
| **Excel** | .xlsx | Spreadsheet | Data analysis, statistics |
| **PowerPoint** | .pptx | Presentation | Reporting, meetings |

**PDF Export Features**:
- ✅ Full Chinese support (auto-detect system fonts)
- ✅ Beautiful formatting (titles, dividers, tables)
- ✅ Status icon display
- ✅ Metadata information

**Excel Export Features**:
- ✅ Multiple worksheets (Overview, Steps, Results, Statistics)
- ✅ Chart support
- ✅ Style beautification
- ✅ Data filtering

**PowerPoint Export Features**:
- ✅ Professional template design
- ✅ Cover/Content/Ending pages
- ✅ Step card display
- ✅ Brand customization

### ⏰ Scheduled Task System

Supports multiple scheduling methods:

```yaml
# Supported schedule types
- interval: Fixed interval execution (e.g., every 30 minutes)
- cron: Cron expression (e.g., "0 9 * * *" daily at 9 AM)
- daily: Daily schedule (e.g., 09:00)
- weekly: Weekly schedule (e.g., Monday 10:00)
- monthly: Monthly schedule (e.g., 1st of each month)
- once: One-time execution
```

**Typical Use Cases**:
- 📰 Daily news summary
- 📊 Periodic data reports
- 🔄 Automated data synchronization
- 📧 Scheduled email sending

### 🔄 Workflow Templates

Quick start with predefined workflows:

| Template Name | Category | Description |
|---------------|----------|-------------|
| Web Research | Research | Search topic information and generate reports |
| Data Analysis | Data | Analyze data and generate visualizations |
| Code Review | Code | Review code quality and provide suggestions |
| Document Generation | Content | Generate complete documents from outlines |
| Competitive Analysis | Research | Collect and compare competitor information |

Custom workflow support:
- Variable templates (e.g., `{topic}`, `{date}`)
- Multi-step processes
- Conditional branching
- Loop execution

### 🧠 Knowledge Base & RAG

**Knowledge Base Management**:
- Supported formats: PDF, Word, Markdown, TXT, HTML
- Automatic text extraction and chunking
- Vector indexing storage
- Collection classification management

**RAG Retrieval Enhancement**:
- Semantic similarity search
- Context injection
- Relevance ranking
- Citation tracing

### 💾 LLM Cache Optimization

**Intelligent Caching Mechanism**:
- Semantic similarity matching (configurable threshold)
- Automatic caching of popular queries
- Expiration time management
- Cache statistics analysis

**Performance Data**:
| Metric | Value |
|--------|-------|
| Average cache hit rate | 35-50% |
| Token savings | 30-40% |
| Response latency reduction | 90%+ (on hit) |

### 🌐 Web Interface Features

**Main Pages**:
- **Home**: Task creation, quick templates, task list
- **Workspace**: Real-time execution monitoring, step visualization, result preview
- **Settings**: Model configuration, API keys, system parameters

**Interface Features**:
- 🌓 Dark/Light theme switching
- 🌍 Chinese/English language switching
- 📱 Responsive design
- ⌨️ Keyboard shortcuts
- 🔔 Real-time notifications

---

## 🚀 Quick Start

### Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows 10+, Linux, macOS
- **Memory**: 8GB+ recommended
- **Optional**: Docker, CUDA (GPU acceleration)

### Option 1: One-Click Start

```bash
# Windows
.\start.bat

# Linux/macOS
chmod +x start.sh
./start.sh
```

### Option 2: Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/Joinsyna-Co-Ltd/JoinFlow.git
cd joinflow

# 2. Create virtual environment (recommended)
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3. Install base dependencies
pip install -r requirements.txt

# 4. Install optional dependencies (enterprise features)
pip install openpyxl python-pptx reportlab  # Export features
pip install playwright && playwright install chromium  # Browser Agent

# 5. Configure
cp config.example.json config.json
# Edit config.json, add API keys

# 6. Start service
python -m web.server
```

### Option 3: Docker Deployment

```bash
# Development environment
docker-compose up -d

# Production environment
docker-compose -f deploy/docker-compose.full.yml up -d
```

### Access Service

After starting, visit: `http://localhost:8000`

---

## 📖 User Guide

### Web Interface Usage

#### 1. Create Task

Enter task description on the home page, for example:
- "Search today's tech news and compile a report"
- "Analyze this data and generate charts"
- "Open Notepad and write a story"

#### 2. View Execution Process

- View task decomposition steps in real-time
- Monitor each Agent's execution status
- View log output

#### 3. Export Results

Click "Export as..." to select format:
- 📝 Markdown
- 🌐 HTML
- 📊 JSON
- 📕 PDF
- 📈 Excel
- 📽️ PowerPoint

### Programming Interface Usage

```python
from joinflow_agent import Orchestrator, AgentConfig

# Create configuration
config = AgentConfig(
    llm_model="gpt-4o-mini",
    browser_headless=True,
    enable_cache=True
)

# Create orchestrator
orchestrator = Orchestrator(config=config)

# Execute task
result = orchestrator.execute("Search for the latest Python version information")

# Get results
print(result.output)
print(f"Execution steps: {len(result.steps)}")
print(f"Duration: {result.duration}s")
```

### Export Feature Usage

```python
from joinflow_core.advanced_exporter import AdvancedExportManager

exporter = AdvancedExportManager(output_dir="./exports")

# Export to Excel
content, path = exporter.export_task(
    task_id="task_001",
    description="Data Analysis Report",
    result="Analysis results...",
    steps=[...],
    format="excel"
)
print(f"Exported to: {path}")

# Get available formats
formats = exporter.get_available_formats()
for fmt in formats:
    status = "✅" if fmt['available'] else "❌"
    print(f"{status} {fmt['name']} ({fmt['extension']})")
```

### Scheduled Task Usage

```python
from joinflow_core.scheduler import TaskScheduler, ScheduledTask, ScheduleType

scheduler = TaskScheduler()

# Create daily task
task = ScheduledTask(
    name="Daily News Summary",
    description="Automatically collect tech news",
    schedule_type=ScheduleType.DAILY,
    run_at="09:00",
    task_description="Search today's tech news and generate summary report"
)

scheduler.add_task(task)
scheduler.start()
```

---

## 📡 API Documentation

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send chat message |
| `/task/execute` | POST | Execute task |
| `/task/{id}/stream` | GET | Task progress stream (SSE) |
| `/api/export/task/{id}` | POST | Export task results |
| `/api/export/formats` | GET | Get available export formats |
| `/api/export/download/{file}` | GET | Download exported file |
| `/api/workflows` | GET/POST | Workflow management |
| `/api/schedules` | GET/POST | Scheduled task management |
| `/api/knowledge/upload` | POST | Upload knowledge base documents |
| `/api/models` | GET/POST | Model configuration management |

### Export API Example

```bash
# Export to PDF
curl -X POST "http://localhost:8000/api/export/task/task_001" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "pdf",
    "description": "Task description",
    "result": "Task result content",
    "steps": [],
    "metadata": {"status": "completed"}
  }'

# Get available formats
curl "http://localhost:8000/api/export/formats"
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Interface                            │
│                    (HTML + JavaScript + CSS)                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/WebSocket/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Web Server                          │
│                    (REST API + Real-time Communication)          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Orchestrator │      │  Scheduler   │      │   Exporter   │
│  Intelligent │      │    Task      │      │    Export    │
│  Orchestrator│      │  Scheduler   │      │   Manager    │
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
│              (Vector Storage / LLM Cache / Token Optimization)   │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
joinflow/
├── main.py                    # Main entry
├── config.json                # Configuration file
├── start.bat / start.sh       # One-click start scripts
│
├── joinflow_agent/            # Agent System
│   ├── orchestrator.py        # Intelligent Orchestrator
│   ├── browser.py             # Browser Agent
│   ├── llm.py                 # LLM Agent
│   ├── os_agent.py            # System Agent
│   ├── data_agent.py          # Data Analysis Agent
│   ├── vision_agent.py        # Vision Agent
│   └── session.py             # Session Management
│
├── joinflow_core/             # Core Modules
│   ├── qdrant_service.py      # Qdrant Service Management
│   ├── cached_llm.py          # LLM Cache
│   ├── scheduler.py           # Task Scheduling
│   ├── exporter.py            # Basic Export (MD/HTML/JSON/PDF)
│   ├── advanced_exporter.py   # Enterprise Export (Excel/PPT)
│   ├── webhooks.py            # Webhook Notifications
│   └── task_templates.py      # Task Templates
│
├── joinflow_rag/              # RAG Engine
│   ├── engine.py              # RAG Core
│   └── knowledge_base.py      # Knowledge Base Management
│
├── joinflow_memory/           # Memory System
│   └── history.py             # History Storage
│
├── web/                       # Web Service
│   ├── server.py              # FastAPI Server
│   ├── api_extensions.py      # API Extensions
│   ├── subscription.py        # Subscription Management
│   ├── templates/             # HTML Templates
│   └── static/                # Static Resources
│
├── deploy/                    # Deployment Configuration
│   ├── docker-compose.*.yml   # Docker Configuration
│   ├── nginx/                 # Nginx Configuration
│   ├── kubernetes/            # K8s Configuration
│   └── scripts/               # Deployment Scripts
│
└── workspace/                 # Workspace
    ├── exports/               # Export Files
    └── results/               # Result Files
```

---

## 🚢 Deployment Guide

### Docker Deployment

```bash
# Full deployment (includes Qdrant)
docker-compose -f deploy/docker-compose.full.yml up -d

# View logs
docker-compose logs -f joinflow
```

### Kubernetes Deployment

```bash
# Apply configuration
kubectl apply -f deploy/kubernetes/

# Check status
kubectl get pods -n joinflow
```

### Production Environment Configuration

```bash
# Nginx reverse proxy
sudo cp deploy/nginx/joinflow.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/joinflow.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Systemd service
sudo cp deploy/scripts/joinflow.service /etc/systemd/system/
sudo systemctl enable joinflow
sudo systemctl start joinflow
```

---

## ⚙️ Configuration

### config.json Example

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

### Environment Variables

```bash
# LLM Configuration
export OPENAI_API_KEY=your-key
export LLM_MODEL=gpt-4o-mini

# Service Configuration
export JOINFLOW_PORT=8000
export JOINFLOW_HOST=0.0.0.0

# Qdrant Configuration
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
```

---

## 📊 Performance Metrics

### RAG Performance (10,000 documents)

| Metric | Result |
|--------|--------|
| Embedding time | ~24.5s (408 docs/s) |
| Indexing time | ~7.5s (1326 docs/s) |
| Average query latency | **80ms** |
| P95 latency | **140ms** |

### LLM Cache Performance

| Metric | Result |
|--------|--------|
| Average cache hit rate | 35-50% |
| Token savings | 30-40% |
| Response latency reduction | 90%+ (on cache hit) |

---

## 🆕 Version History

### v0.3.0 (2026-01-11) - Enterprise Edition

**New Features:**
- ☁️ Cloud service deployment
- 📊 Advanced export (Excel/PPT/PDF with Chinese support)
- 🧠 Qdrant Service Manager
- 💾 LLM response caching
- 🔔 Webhook/notification system
- 📋 Task template system

**Fixes:**
- Fixed PDF export Chinese character encoding issues
- Fixed PPT export compatibility issues
- Fixed export format selection not working

### v0.2.0 - Agent System

- 🤖 Multi-Agent system
- 🧠 Intelligent Orchestrator
- 💾 User history records

### v0.1.0 - RAG Foundation

- 📚 RAG Engine
- 🔍 Vector storage

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md)

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push branch (`git push origin feature/AmazingFeature`)
5. Create Pull Request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- [Qdrant](https://qdrant.tech/) - Vector Database
- [Playwright](https://playwright.dev/) - Browser Automation
- [FastAPI](https://fastapi.tiangolo.com/) - Web Framework
- [OpenAI](https://openai.com/) - LLM API
- [ReportLab](https://www.reportlab.com/) - PDF Generation
- [python-pptx](https://python-pptx.readthedocs.io/) - PPT Generation
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel Generation

---

## 📞 Contact

- **Author**: Joinsyna Co., Ltd.
- **GitHub**: [https://github.com/Joinsyna-Co-Ltd/JoinFlow](https://github.com/Joinsyna-Co-Ltd/JoinFlow)
- **Issues**: [Submit Issues](https://github.com/Joinsyna-Co-Ltd/JoinFlow/issues)
- **Discussions**: [Join Discussions](https://github.com/Joinsyna-Co-Ltd/JoinFlow/discussions)

---

<div align="center">

**⭐ If this project helps you, please give us a Star!**

Made with ❤️ by Joinsyna Co., Ltd.

</div>
