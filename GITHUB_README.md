<div align="center">

# 🚀 JoinFlow

<img src="https://img.shields.io/badge/JoinFlow-Enterprise%20AI%20Agent-4361EE?style=for-the-badge&logo=robot&logoColor=white" alt="JoinFlow">

### **企业级 AI Agent 自动化平台**

*智能任务执行 · 多Agent协作 · 企业级报告生成*

[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

[🌟 功能特性](#-功能特性) •
[🚀 快速开始](#-快速开始) •
[📖 文档](#-文档) •
[🎯 演示](#-演示) •
[🤝 贡献](#-贡献)

</div>

---

## 🎯 项目简介

**JoinFlow** 是一款功能强大的**企业级 AI Agent 自动化平台**，通过多智能体协作技术实现复杂任务的自动化执行。无论是网络搜索、数据分析、文件操作还是专业报告生成，JoinFlow 都能智能规划并高效完成。

### 💡 核心理念

> **"让 AI 成为你的智能助手，自动完成繁琐任务"**

传统的 AI 助手只能进行对话，而 JoinFlow 可以：
- 🔍 **自主搜索** - 浏览网页、收集信息、分析数据
- 💻 **操作系统** - 打开应用、管理文件、执行命令
- 📊 **生成报告** - 专业 PDF、Excel 表格、PPT 演示文稿
- ⏰ **定时执行** - 7×24 小时无人值守运行

---

## ✨ 功能特性

<table>
<tr>
<td width="50%">

### 🤖 多智能体协作

6种专业Agent智能协作，自动规划执行路径

| Agent | 功能 |
|-------|------|
| 🌐 Browser | 网页浏览、搜索、数据采集 |
| 🧠 LLM | 自然语言处理、内容生成 |
| 💻 OS | 系统操作、文件管理 |
| 📊 Data | 数据分析、可视化 |
| 👁️ Vision | 图像识别、视觉分析 |
| 💻 Code | 代码生成、执行 |

</td>
<td width="50%">

### 📊 企业级导出

支持7种格式，满足不同场景需求

| 格式 | 特点 |
|------|------|
| 📝 Markdown | 轻量级文档 |
| 🌐 HTML | 网页格式 |
| 📊 JSON | 结构化数据 |
| 📕 PDF | 完美中文支持 |
| 📈 Excel | 多工作表+图表 |
| 📽️ PowerPoint | 专业演示模板 |
| 📄 TXT | 纯文本格式 |

</td>
</tr>
<tr>
<td width="50%">

### ⏰ 定时任务

支持多种调度方式，无人值守执行

```yaml
调度类型:
- interval: 固定间隔 (如每30分钟)
- cron: Cron表达式 (如 0 9 * * *)
- daily: 每日定时 (如 09:00)
- weekly: 每周定时
- monthly: 每月定时
```

</td>
<td width="50%">

### 🧠 智能优化

LLM 缓存与 Token 优化

| 指标 | 效果 |
|------|------|
| 缓存命中率 | 35-50% |
| Token 节省 | 30-40% |
| 响应加速 | 90%+ |

*语义相似度匹配，自动缓存热门查询*

</td>
</tr>
</table>

### 更多特性

- 🔄 **工作流模板** - 预定义流程，一键执行
- 📚 **知识库管理** - 文档上传、向量索引、RAG 检索
- 🌍 **多语言界面** - 中文/英文切换
- 🌓 **主题切换** - 深色/浅色模式
- 🔒 **安全可靠** - 沙箱执行、API 密钥管理
- 🏠 **私有部署** - 支持完全本地运行

---

## 🚀 快速开始

### 方式一：一键启动

```bash
# 克隆仓库
git clone https://github.com/JoinSyna/joinflow.git
cd joinflow

# Windows
.\start.bat

# Linux/macOS
chmod +x start.sh && ./start.sh
```

### 方式二：手动安装

```bash
# 安装依赖
pip install -r requirements.txt

# 安装可选依赖（企业功能）
pip install openpyxl python-pptx reportlab

# 配置
cp config.example.json config.json
# 编辑 config.json，填入 API 密钥

# 启动
python -m web.server
```

### 方式三：Docker 部署

```bash
docker-compose up -d
```

### 🌐 访问服务

启动后访问：**http://localhost:8000**

---

## 📖 文档

| 文档 | 描述 |
|------|------|
| [📘 快速开始](docs/QUICKSTART.md) | 5分钟上手指南 |
| [📗 用户手册](docs/USER_GUIDE.md) | 完整使用教程 |
| [📕 API 文档](docs/API.md) | REST API 参考 |
| [📙 部署指南](docs/DEPLOYMENT.md) | 生产环境部署 |
| [📓 开发文档](docs/DEVELOPMENT.md) | 二次开发指南 |
| [📔 架构设计](ARCHITECTURE.md) | 系统架构说明 |

---

## 🎯 使用场景

<table>
<tr>
<td align="center" width="25%">
<img src="https://img.icons8.com/fluency/96/search.png" width="48px"><br>
<b>信息调研</b><br>
<sub>自动搜索、整理、生成报告</sub>
</td>
<td align="center" width="25%">
<img src="https://img.icons8.com/fluency/96/combo-chart.png" width="48px"><br>
<b>数据分析</b><br>
<sub>处理数据、生成图表、Excel报表</sub>
</td>
<td align="center" width="25%">
<img src="https://img.icons8.com/fluency/96/document.png" width="48px"><br>
<b>文档生成</b><br>
<sub>PDF报告、PPT演示、技术文档</sub>
</td>
<td align="center" width="25%">
<img src="https://img.icons8.com/fluency/96/time-machine.png" width="48px"><br>
<b>定时任务</b><br>
<sub>每日汇总、定期报告、自动同步</sub>
</td>
</tr>
</table>

### 💼 典型案例

```
📰 "每天早上9点，搜索科技新闻，生成PDF日报发送邮件"

📊 "分析销售数据，生成Excel报表和PPT汇报材料"

🔍 "调研竞品信息，整理成对比分析文档"

💻 "监控服务器状态，异常时自动告警"
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Interface                           │
│                  (现代化响应式界面)                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Server                            │
│              (REST API + WebSocket + SSE)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐
   │Orchestrator│    │ Scheduler │    │ Exporter  │
   │  智能编排  │    │  任务调度  │    │  导出管理  │
   └─────┬─────┘    └───────────┘    └───────────┘
         │
   ┌─────┴─────┬──────┬──────┬──────┬──────┐
   ▼           ▼      ▼      ▼      ▼      ▼
┌──────┐  ┌──────┐ ┌────┐ ┌────┐ ┌──────┐ ┌────┐
│Browser│  │ LLM  │ │ OS │ │Data│ │Vision│ │Code│
│Agent │  │Agent │ │Agent││Agent││Agent │ │Agent│
└──────┘  └──────┘ └────┘ └────┘ └──────┘ └────┘
```

---

## 📊 性能指标

<table>
<tr>
<td width="50%">

### RAG 性能
*基于 10,000 文档测试*

| 指标 | 结果 |
|------|------|
| 嵌入速度 | 408 docs/s |
| 索引速度 | 1326 docs/s |
| 查询延迟 | **80ms** |
| P95 延迟 | **140ms** |

</td>
<td width="50%">

### LLM 缓存
*语义相似度缓存效果*

| 指标 | 结果 |
|------|------|
| 命中率 | 35-50% |
| Token节省 | 30-40% |
| 响应加速 | 90%+ |
| 成本降低 | 30%+ |

</td>
</tr>
</table>

---

## 🛠️ 技术栈

<table>
<tr>
<td align="center" width="20%">
<img src="https://img.icons8.com/color/48/python.png" width="32px"><br>
<b>Python 3.9+</b>
</td>
<td align="center" width="20%">
<img src="https://img.icons8.com/color/48/api.png" width="32px"><br>
<b>FastAPI</b>
</td>
<td align="center" width="20%">
<img src="https://img.icons8.com/color/48/docker.png" width="32px"><br>
<b>Docker</b>
</td>
<td align="center" width="20%">
<img src="https://img.icons8.com/color/48/chrome.png" width="32px"><br>
<b>Playwright</b>
</td>
<td align="center" width="20%">
<img src="https://img.icons8.com/color/48/database.png" width="32px"><br>
<b>Qdrant</b>
</td>
</tr>
</table>

- **后端**: FastAPI, Uvicorn, Pydantic
- **AI/ML**: OpenAI GPT, SentenceTransformers, Qdrant
- **浏览器**: Playwright (Chromium)
- **导出**: ReportLab (PDF), openpyxl (Excel), python-pptx (PPT)
- **部署**: Docker, Nginx, Kubernetes

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. 🍴 Fork 本仓库
2. 🌿 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 💾 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 📤 推送分支 (`git push origin feature/AmazingFeature`)
5. 🔃 创建 Pull Request

详细指南请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 许可证

本项目采用 **MIT 许可证** - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢以下开源项目的支持：

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [Qdrant](https://qdrant.tech/) - 向量数据库
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [OpenAI](https://openai.com/) - LLM API
- [ReportLab](https://www.reportlab.com/) - PDF 生成
- [python-pptx](https://python-pptx.readthedocs.io/) - PPT 生成
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel 生成

---

## 📞 联系方式

<table>
<tr>
<td align="center">
<b>👨‍💻 作者</b><br>
JoinSyna
</td>
<td align="center">
<b>🐛 问题反馈</b><br>
<a href="https://github.com/JoinSyna/joinflow/issues">GitHub Issues</a>
</td>
<td align="center">
<b>💬 讨论交流</b><br>
<a href="https://github.com/JoinSyna/joinflow/discussions">GitHub Discussions</a>
</td>
</tr>
</table>

---

<div align="center">

### ⭐ 如果这个项目对您有帮助，请给一个 Star！

<img src="https://img.shields.io/github/stars/JoinSyna/joinflow?style=social" alt="GitHub Stars">

---

**Made with ❤️ by [JoinSyna](https://github.com/JoinSyna)**

*打造属于你的 AI 智能助手*

</div>
