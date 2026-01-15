# 更新日志 (Changelog)

本文档记录 JoinFlow 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [未发布] - Unreleased

### 计划中
- [ ] 实时协作编辑
- [ ] 插件市场

---

## [0.3.1] - 2026-01-08

### 🌐 全球 LLM 提供商支持

#### 新增 (Added)

##### 🤖 完整 LLM 提供商支持 (`joinflow_core/llm_providers.py`)
- **国际提供商 (9个)**
  - OpenAI (GPT-4o, GPT-4, o1, o3系列)
  - Anthropic (Claude 3.5, Claude 3系列)
  - Google AI (Gemini 2.0, 1.5系列)
  - Mistral AI (Mistral Large, Mixtral系列)
  - Cohere (Command R+, Command R)
  - Groq (超快速推理，LPU加速)
  - Together AI (开源模型云托管)
  - Perplexity AI (实时联网搜索)
  - Fireworks AI (高性能推理)

- **国内提供商 (12个)**
  - DeepSeek 深度求索 (deepseek-chat, R1推理模型)
  - 阿里云通义千问 Qwen (qwen-max, qwen-plus, qwen-turbo, qwen-long)
  - 百度文心一言 ERNIE (ernie-4.0, ernie-3.5系列)
  - 智谱AI GLM (glm-4-plus, glm-4-flash免费模型)
  - 月之暗面 Moonshot/Kimi (moonshot-v1, 超长上下文)
  - 零一万物 Yi (yi-large, yi-medium系列)
  - MiniMax (abab6.5, 擅长多轮对话)
  - 字节跳动豆包 Doubao (doubao-pro, doubao-lite)
  - 讯飞星火 Spark (spark-4.0-ultra, spark-pro)
  - 百川智能 Baichuan (baichuan-4, baichuan-3-turbo)
  - 阶跃星辰 Step (step-2, 万亿参数模型)
  - 商汤日日新 SenseNova (sensechat-5, sensechat-vision)

- **云服务提供商 (2个)**
  - Azure OpenAI (微软企业级服务)
  - AWS Bedrock (亚马逊多模型服务)

- **本地部署 (4个)**
  - Ollama (本地运行开源模型，免费)
  - LM Studio (图形化本地模型运行)
  - vLLM (高性能推理服务器)
  - Xinference (分布式推理框架)

##### 📡 新增 API 端点
- `GET /api/providers` - 获取所有LLM提供商列表
- `GET /api/providers/{id}` - 获取提供商详细信息
- `GET /api/providers/{id}/models` - 获取提供商的所有模型
- `GET /api/models/all` - 获取所有提供商的所有模型
- `GET /api/models/search?query=xxx` - 搜索模型

##### 🔧 功能特性
- 自动检测模型提供商 (根据模型ID智能识别)
- 预配置API端点 (无需手动输入API地址)
- 模型定价信息 (显示每1K tokens成本)
- 上下文长度信息 (显示最大tokens数)
- 视觉能力标记 (标记支持图像的模型)
- 推理能力标记 (标记o1/R1等推理模型)

##### 📋 预配置模型 (`config.json`)
- 31个预配置模型，覆盖主流提供商
- 每个模型包含描述信息
- 支持一键启用/禁用

---

## [0.3.0] - 2026-01-08

### 🎉 企业版发布

这是一个重大版本更新，引入企业级功能。

### 新增 (Added)

#### ☁️ 云服务功能
- **Docker Compose 部署配置**
  - `docker-compose.yml` - 开发环境
  - `docker-compose.prod.yml` - 生产环境
  - `docker-compose.cloud.yml` - 云部署环境
  - `docker-compose.full.yml` - 完整功能环境

- **Kubernetes 部署支持**
  - `kubernetes/joinflow-deployment.yaml` - K8s 部署配置
  - 支持 Deployment、Service、ConfigMap、PVC

- **云平台部署脚本**
  - `deploy/cloud-deploy.sh` - Linux/Mac 部署脚本
  - `deploy/cloud-deploy.ps1` - Windows PowerShell 部署脚本
  - 支持 AWS EC2、Azure VM、阿里云 ECS

- **Nginx 反向代理配置**
  - SSL 终端支持
  - 静态文件缓存
  - WebSocket 代理
  - 负载均衡配置

- **健康检查系统**
  - `deploy/scripts/health-check.sh` - 健康检查脚本
  - Systemd 服务单元和定时器
  - 自动告警 (Slack、邮件)

- **云服务管理界面** (`web/templates/cloud.html`)
  - 服务状态实时监控
  - 一键部署功能
  - 资源使用统计

#### 📊 多格式导出
- **Excel 导出** (`joinflow_core/advanced_exporter.py`)
  - 多工作表报告 (概览、步骤、结果、统计)
  - 样式美化 (表头、边框、颜色)
  - 图表生成 (状态分布图)
  - 数据表格导出功能

- **PowerPoint 导出**
  - 专业演示文稿生成
  - 标题页、概览页、步骤页、结果页、结束页
  - 自定义主题和样式
  - 适合企业汇报使用

- **增强型 HTML 导出**
  - 响应式设计
  - 打印优化
  - 交互式元素

#### 🧠 Qdrant 服务管理器
- **QdrantServiceManager** (`joinflow_core/qdrant_service.py`)
  - 单例模式连接管理
  - 自动重连机制
  - 内存模式降级支持

- **健康检查 API**
  - 服务状态监控
  - 集合信息查询
  - 连接状态追踪

- **集合自动管理**
  - 知识库集合 (`joinflow_knowledge`)
  - 历史记录集合 (`joinflow_history`)
  - 任务集合 (`joinflow_tasks`)
  - LLM 缓存集合 (`joinflow_llm_cache`)

#### 💾 LLM 响应缓存
- **CachedLLM** (`joinflow_core/cached_llm.py`)
  - 语义相似度缓存 (阈值可配置)
  - 自动缓存管理 (TTL 过期)
  - 缓存命中统计

- **Token 使用追踪**
  - 提示词 Token 计数
  - 完成 Token 计数
  - 节省 Token 统计
  - 预估成本计算

- **SmartLLMRouter** 
  - 多模型智能路由
  - 复杂度自动判断
  - 降级策略支持

#### 🔔 通知系统
- **NotificationManager** (`joinflow_core/advanced_exporter.py`)
  - Webhook 通知
  - 邮件通知 (SMTP)
  - Slack 集成 (计划中)

#### 📋 任务模板
- **任务模板系统** (`joinflow_core/task_templates.py`)
  - 预定义工作流模板
  - 输入参数模式
  - 快速任务创建

### 变更 (Changed)

- **Qdrant 作为独立服务**
  - 从嵌入式改为独立服务模式
  - 支持远程 Qdrant 服务器连接
  - 支持 API 密钥认证

- **API 扩展** (`web/api_extensions.py`)
  - 新增导出端点 (`/api/export/*`)
  - 新增云服务端点 (`/api/cloud/*`)
  - 新增 Token 统计端点 (`/api/stats/tokens`)

- **主程序更新** (`main.py`)
  - 集成 Qdrant 服务管理器
  - 添加缓存统计路由
  - 优化启动流程

### 修复 (Fixed)

- 修复向量数据库连接超时问题
- 修复大文件导出内存溢出
- 修复定时任务时区问题

### 安全 (Security)

- 添加 API 密钥验证
- 添加请求频率限制
- 添加输入验证和清理

---

## [0.2.1] - 2026-01-07

### 修复 (Fixed)

- 文本溢出 UI 边界问题
- 工作区页面翻译缺失
- 搜索引擎选择只显示百度

### 变更 (Changed)

- 自动规划模式现在自动启动任务
- 并行多搜索引擎支持
- 完善国际化翻译

---

## [0.2.0] - 2026-01-05

### 🤖 Agent 系统发布

### 新增 (Added)

#### Multi-Agent 系统
- **BrowserAgent** - 浏览器自动化和信息提取
  - 网页搜索
  - 内容提取
  - 表单填写
  - 截图功能

- **LLMAgent** - 文本生成和分析
  - 文本生成
  - 代码生成
  - 任务规划
  - 数据分析

- **OSAgent** - 文件操作和系统管理
  - 文件读写
  - 目录管理
  - 系统信息
  - 命令执行

- **DataAgent** - 数据处理和分析
  - 数据清洗
  - 统计分析
  - 可视化

- **VisionAgent** - 图像识别
  - 图像描述
  - OCR 文字提取
  - 视觉问答

#### 智能编排器
- **Orchestrator** - Agent 协调器
  - 任务自动分解
  - Agent 智能路由
  - 结果聚合
  - 错误处理和重试

#### 用户历史
- **HistoryStore** - 向量存储历史记录
  - 对话历史
  - 任务记录
  - 语义搜索

#### 工具调用
- LLM 函数调用支持
- 工具注册机制

### 变更 (Changed)

- 重构 Web 界面
- 添加实时任务监控
- WebSocket 实时通信

---

## [0.1.0] - 2026-01-01

### 🚀 初始版本

### 新增 (Added)

#### RAG 引擎
- **RAGEngine** - 检索增强生成
  - 查询嵌入
  - 向量检索
  - 上下文组装
  - 答案生成

#### 向量存储
- **QdrantVectorStore** - Qdrant 向量存储
  - 文档索引
  - 相似度搜索
  - Payload 过滤

#### 知识库
- **KnowledgeBaseManager** - 知识库管理
  - 文档上传
  - 文本分块
  - 向量化索引

#### Web 界面
- FastAPI 服务器
- 基础聊天界面
- 任务管理

---

## 版本对比

| 版本 | 主要特性 | 状态 |
|------|----------|------|
| 0.1.0 | RAG 基础 | ✅ 已发布 |
| 0.2.0 | Agent 系统 | ✅ 已发布 |
| 0.2.1 | Bug 修复 | ✅ 已发布 |
| 0.3.0 | 企业功能 | ✅ 已发布 |
| 0.4.0 | 插件系统 | 📋 计划中 |
| 1.0.0 | 稳定版 | 📋 计划中 |

---

## 升级指南

### 从 0.2.x 升级到 0.3.0

1. **安装新依赖**
```bash
pip install openpyxl python-pptx reportlab aiohttp
```

2. **配置 Qdrant 服务**
```bash
# 启动 Qdrant 服务器
docker run -p 6333:6333 qdrant/qdrant
```

3. **更新配置文件**
```json
{
  "qdrant": {
    "url": "http://localhost:6333"
  },
  "cache": {
    "enabled": true,
    "similarity_threshold": 0.95
  }
}
```

4. **数据迁移**
```bash
python -m joinflow_core.migrate --from 0.2 --to 0.3
```

### 从 0.1.x 升级到 0.2.0

1. **安装 Playwright**
```bash
pip install playwright
playwright install chromium
```

2. **更新配置**
```json
{
  "agents": {
    "browser": {
      "headless": true
    }
  }
}
```

---

## 贡献者

感谢所有贡献者！

- @contributor1
- @contributor2
- ...

---

## 链接

- [GitHub 仓库](https://github.com/your-org/joinflow)
- [问题反馈](https://github.com/your-org/joinflow/issues)
- [讨论区](https://github.com/your-org/joinflow/discussions)

