# JoinFlow 系统架构

本文档详细描述 JoinFlow 的内部架构设计。

---

## 🎯 设计目标

JoinFlow 设计为**企业级 AI Agent 平台**，核心目标：

1. **确定性**: 相同输入产生可预测的输出
2. **可扩展性**: 支持水平扩展和高可用部署
3. **可观测性**: 完整的监控、日志和追踪
4. **安全性**: 沙箱执行、权限控制、数据加密

---

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户层 (User Layer)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Web UI        │  REST API        │  WebSocket/SSE     │  CLI              │
│  (浏览器)       │  (程序集成)        │  (实时通信)          │  (命令行)          │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────────────┐
│                            应用层 (Application Layer)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI Server                               │   │
│  │  - 路由管理    - 请求验证    - 响应序列化    - 错误处理                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │   会话管理     │  │   任务调度     │  │   导出服务     │  │  通知服务    │  │
│  │  (Session)    │  │  (Scheduler)  │  │  (Exporter)   │  │ (Notifier)  │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  └─────────────┘  │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────────────┐
│                            核心层 (Core Layer)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Orchestrator (智能编排器)                      │   │
│  │  - 任务分析    - 计划生成    - Agent 路由    - 结果聚合                    │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│  ┌────────────┬──────────┬────────┴─────┬──────────────┬──────────────┐    │
│  │            │          │              │              │              │    │
│  ▼            ▼          ▼              ▼              ▼              ▼    │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Browser│  │ LLM  │  │  OS  │  │   Data   │  │  Vision  │  │ Custom   │  │
│  │ Agent │  │Agent │  │Agent │  │  Agent   │  │  Agent   │  │  Agent   │  │
│  └──────┘  └──────┘  └──────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Cached LLM (缓存 LLM)                         │   │
│  │  - 语义相似度缓存    - Token 追踪    - 智能路由                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────────────┐
│                            数据层 (Data Layer)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Qdrant Service Manager                            │   │
│  │  - 连接管理    - 健康检查    - 集合管理    - 查询缓存                      │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│  ┌────────────┬──────────────┬────┴───────┬─────────────────────────────┐  │
│  │            │              │            │                             │  │
│  ▼            ▼              ▼            ▼                             │  │
│  ┌──────────┐  ┌────────────┐  ┌────────┐  ┌─────────────┐              │  │
│  │ Knowledge │  │  History   │  │  Tasks │  │  LLM Cache  │              │  │
│  │ Collection│  │ Collection │  │Collection│ │ Collection  │              │  │
│  │  (知识库)  │  │  (历史记录) │  │ (任务)  │  │  (LLM缓存)  │              │  │
│  └──────────┘  └────────────┘  └────────┘  └─────────────┘              │  │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴─────────────────────────────────────────┐
│                          基础设施层 (Infrastructure)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Qdrant    │  │   Redis     │  │  File Store │  │   Nginx     │        │
│  │  (向量DB)   │  │  (缓存/队列) │  │  (文件存储)  │  │  (反向代理)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 模块详解

### joinflow_core - 核心模块

**职责:**
- 定义公共契约和协议
- 提供共享类型和错误处理
- 强制执行不变量

**关键组件:**

| 文件 | 功能 |
|------|------|
| `protocols.py` | 接口定义和协议 |
| `types.py` | 共享数据类型 |
| `validators.py` | 输入验证器 |
| `errors.py` | 错误类型定义 |
| `qdrant_service.py` | Qdrant 服务管理 |
| `cached_llm.py` | LLM 响应缓存 |
| `scheduler.py` | Cron 任务调度 |
| `exporter.py` | 基础导出功能 |
| `advanced_exporter.py` | 企业级导出 |
| `webhooks.py` | Webhook 通知 |
| `task_templates.py` | 任务模板 |

### joinflow_agent - Agent 系统

**职责:**
- 实现各类专业 Agent
- 提供 Agent 编排能力
- 管理 Agent 生命周期

**Agent 类型:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator (编排器)                       │
│  - 任务理解与分解                                                 │
│  - Agent 选择与调度                                               │
│  - 结果聚合与优化                                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Browser    │         │    LLM      │         │     OS      │
│   Agent     │         │   Agent     │         │   Agent     │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ • 网页搜索   │         │ • 文本生成   │         │ • 文件操作   │
│ • 内容提取   │         │ • 代码生成   │         │ • 系统命令   │
│ • 表单填写   │         │ • 任务规划   │         │ • 进程管理   │
│ • 截图      │         │ • 数据分析   │         │ • 环境配置   │
└─────────────┘         └─────────────┘         └─────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    Data     │         │   Vision    │         │   Custom    │
│   Agent     │         │   Agent     │         │   Agent     │
├─────────────┤         ├─────────────┤         ├─────────────┤
│ • 数据处理   │         │ • 图像识别   │         │ • 用户自定义 │
│ • 统计分析   │         │ • OCR 提取   │         │ • 插件扩展   │
│ • 可视化    │         │ • 视觉问答   │         │ • API 集成   │
└─────────────┘         └─────────────┘         └─────────────┘
```

### joinflow_index - 向量索引

**职责:**
- 向量存储实现
- ANN (近似最近邻) 搜索
- Payload 过滤

**当前后端: Qdrant (Rust HNSW)**

```python
# 配置示例
from joinflow_index.config import QdrantConfig

config = QdrantConfig(
    collection="documents",
    vector_dim=384,
    distance="Cosine"
)
```

### joinflow_rag - RAG 引擎

**职责:**
- 查询嵌入
- 检索执行
- 上下文组装
- 提示构建
- 可回答性检查

**工作流:**

```
Query → Embedding → Retrieval → Ranking → Assembly → Generation
  │         │           │          │          │          │
  │         ▼           ▼          ▼          ▼          ▼
  │    ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
  └───▶│ Embed  │─▶│ Search │─▶│ Rerank │─▶│Assembly│─▶│  LLM   │
       └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

### joinflow_memory - 记忆系统

**职责:**
- 对话历史存储
- 任务记录管理
- 语义搜索历史
- 上下文检索

---

## 🔄 数据流

### 任务执行流程

```
用户请求
    │
    ▼
┌─────────────────┐
│  FastAPI Server │ ←── 验证请求
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Session      │ ←── 创建/恢复会话
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │ ←── 任务分析与规划
└────────┬────────┘
         │
    ┌────┴────┐
    │ 检查缓存 │
    └────┬────┘
         │
    Yes ─┴─ No
    │       │
    ▼       ▼
┌───────┐ ┌─────────────┐
│ 返回  │ │  Agent 执行  │
│ 缓存  │ └──────┬──────┘
└───────┘        │
                 ▼
         ┌─────────────┐
         │  缓存结果   │
         └──────┬──────┘
                │
                ▼
         ┌─────────────┐
         │  返回响应   │
         └─────────────┘
```

### LLM 缓存流程

```
LLM 调用请求
    │
    ▼
┌──────────────────┐
│  生成查询嵌入    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 搜索相似查询缓存  │ ←── Qdrant cache_collection
└────────┬─────────┘
         │
    ┌────┴────┐
    │相似度检查│ ←── threshold: 0.95
    └────┬────┘
         │
   ≥0.95─┴─<0.95
    │       │
    ▼       ▼
┌───────┐ ┌────────────┐
│ Cache │ │  调用 LLM  │
│  Hit  │ └─────┬──────┘
└───┬───┘       │
    │           ▼
    │    ┌────────────┐
    │    │  缓存响应   │ ←── 存入 Qdrant
    │    └─────┬──────┘
    │          │
    └────┬─────┘
         │
         ▼
┌──────────────────┐
│  更新 Token 统计  │
└──────────────────┘
```

---

## 🗃️ 数据模型

### Qdrant Collections

```yaml
joinflow_knowledge:
  description: 知识库文档
  vector_dim: 384
  fields:
    - content: text
    - source: string
    - metadata: json
    - created_at: datetime

joinflow_history:
  description: 对话和任务历史
  vector_dim: 384
  fields:
    - content: text
    - role: string (user/assistant/system)
    - session_id: string
    - task_id: string
    - created_at: datetime

joinflow_tasks:
  description: 任务记录
  vector_dim: 384
  fields:
    - description: text
    - result: text
    - status: string
    - steps: json
    - created_at: datetime

joinflow_llm_cache:
  description: LLM 响应缓存
  vector_dim: 384
  fields:
    - query_hash: string
    - query_text: text
    - response_text: text
    - model: string
    - prompt_tokens: int
    - completion_tokens: int
    - created_at: datetime
    - expires_at: datetime
    - hit_count: int
```

### 任务数据结构

```python
@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus  # pending/running/completed/failed
    mode: str  # auto/manual
    steps: List[Step]
    result: str
    metadata: Dict
    created_at: datetime
    updated_at: datetime

@dataclass
class Step:
    id: str
    description: str
    agent: str
    status: StepStatus
    input: Dict
    output: str
    started_at: datetime
    completed_at: datetime
```

---

## 🔐 安全设计

### 沙箱执行

```
┌─────────────────────────────────────────────────────┐
│                   Host System                        │
│  ┌───────────────────────────────────────────────┐  │
│  │              Docker Container                  │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │          Application Sandbox             │  │  │
│  │  │  • 受限文件系统访问                        │  │  │
│  │  │  • 网络隔离                               │  │  │
│  │  │  • 资源限制 (CPU/Memory)                  │  │  │
│  │  │  • 命令白名单                             │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### API 安全

- **认证**: API Key / JWT Token
- **授权**: 基于角色的访问控制
- **加密**: HTTPS/TLS 传输加密
- **验证**: 输入验证和清理
- **限流**: 请求频率限制

---

## 📈 可扩展性

### 水平扩展

```
                    ┌─────────────┐
                    │   Nginx     │
                    │ Load Balancer│
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ JoinFlow │    │ JoinFlow │    │ JoinFlow │
    │ Instance │    │ Instance │    │ Instance │
    │    #1    │    │    #2    │    │    #3    │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       ┌──────────┐          ┌──────────┐
       │  Qdrant  │          │  Redis   │
       │ Cluster  │          │ Cluster  │
       └──────────┘          └──────────┘
```

### 插件系统

```python
# 自定义 Agent 示例
from joinflow_agent.base import BaseAgent, AgentResult

class CustomAgent(BaseAgent):
    """自定义 Agent"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "custom"
        self.capabilities = ["custom_task"]
    
    def execute(self, task: str) -> AgentResult:
        # 实现自定义逻辑
        result = self._process(task)
        return AgentResult(
            success=True,
            output=result
        )

# 注册到编排器
orchestrator.register_agent(CustomAgent(config))
```

---

## 🔧 配置管理

### 配置层次

```
默认配置 (代码内置)
    │
    ▼
环境变量 (JOINFLOW_*)
    │
    ▼
配置文件 (config.json)
    │
    ▼
运行时参数 (命令行/API)
```

### 配置示例

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "${OPENAI_API_KEY}",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "qdrant": {
    "url": "http://localhost:6333",
    "api_key": null,
    "collections": {
      "knowledge": "joinflow_knowledge",
      "history": "joinflow_history",
      "cache": "joinflow_llm_cache"
    }
  },
  "cache": {
    "enabled": true,
    "similarity_threshold": 0.95,
    "ttl_hours": 168
  },
  "agents": {
    "browser": {
      "headless": true,
      "timeout": 30000
    },
    "os": {
      "workspace": "./workspace",
      "allowed_commands": ["ls", "cat", "mkdir"]
    }
  }
}
```

---

## 📊 监控与可观测性

### 指标收集

```yaml
# Prometheus 指标
joinflow_requests_total:
  type: counter
  labels: [endpoint, method, status]

joinflow_request_duration_seconds:
  type: histogram
  labels: [endpoint]

joinflow_agent_executions_total:
  type: counter
  labels: [agent, status]

joinflow_llm_tokens_total:
  type: counter
  labels: [model, type]

joinflow_cache_hits_total:
  type: counter

joinflow_qdrant_queries_total:
  type: counter
  labels: [collection]
```

### 日志结构

```json
{
  "timestamp": "2026-01-08T12:00:00Z",
  "level": "INFO",
  "logger": "joinflow_agent.orchestrator",
  "message": "Task completed",
  "context": {
    "task_id": "abc123",
    "duration_ms": 1234,
    "agents_used": ["browser", "llm"],
    "cache_hits": 2
  }
}
```

---

## 🎯 设计原则

1. **显式优于隐式**: 没有隐藏的 prompt，没有自动魔法上下文注入
2. **契约神圣不可侵犯**: 任何模块不得违反 `joinflow_core` 契约
3. **确定性优于灵活性**: 相同输入产生可预测结果
4. **单一职责**: 每个模块只做一件事
5. **依赖倒置**: 高层模块不依赖低层模块细节

---

## 📚 参考文档

- [API 文档](./docs/api.md)
- [部署指南](./deploy/README.md)
- [开发指南](./CONTRIBUTING.md)
- [更新日志](./CHANGELOG.md)
