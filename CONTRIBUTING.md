# 贡献指南 (Contributing Guide)

感谢您对 JoinFlow 的关注！我们欢迎所有形式的贡献。

---

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境](#开发环境)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [版本规则](#版本规则)

---

## 🤝 行为准则

### 设计哲学

JoinFlow 优先考虑 **正确性、清晰性和稳定性**，而非功能数量。

核心原则：
1. **检索是基础设施**: 检索质量决定生成质量
2. **契约神圣不可侵犯**: 接口定义后不轻易改变
3. **没有隐藏行为**: 代码行为应该是显式和可预测的
4. **确定性优于灵活性**: 相同输入产生相同输出

### 社区准则

- 尊重所有贡献者
- 保持建设性的讨论
- 接受建设性批评
- 专注于社区最佳利益

---

## 💡 如何贡献

### 欢迎的贡献类型

| 类型 | 说明 | 优先级 |
|------|------|:------:|
| 🐛 Bug 修复 | 修复现有问题 | 高 |
| 📖 文档 | 改进文档和注释 | 高 |
| ⚡ 性能优化 | 提升执行效率 | 中 |
| 🧪 测试 | 增加测试覆盖 | 中 |
| 🔧 工具改进 | 开发工具增强 | 中 |
| ✨ 新功能 | 路线图中的功能 | 中 |
| 🌐 国际化 | 新语言翻译 | 低 |

### 可能被拒绝的贡献

- ❌ 破坏核心契约的改动
- ❌ 引入隐式状态或行为
- ❌ 过度复杂的抽象
- ❌ 未经讨论的大型重构
- ❌ 与项目方向不符的功能

---

## 🛠️ 开发环境

### 前置要求

- Python 3.9+
- Git
- Docker (可选，用于测试)
- Node.js (可选，用于前端工具)

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/your-org/joinflow.git
cd joinflow

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install

# 安装浏览器驱动 (如果需要)
playwright install chromium
```

### 目录结构

```
joinflow/
├── joinflow_agent/    # Agent 系统
├── joinflow_core/     # 核心模块
├── joinflow_index/    # 向量索引
├── joinflow_rag/      # RAG 引擎
├── joinflow_memory/   # 记忆系统
├── web/               # Web 服务
├── deploy/            # 部署配置
├── tests/             # 测试文件
├── docs/              # 文档
└── examples/          # 示例代码
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_agent.py -v

# 生成覆盖率报告
pytest --cov=joinflow_core --cov-report=html
```

### 启动开发服务器

```bash
# 开发模式
python main.py --dev

# 或使用 uvicorn 热重载
uvicorn web.server:app --reload --port 8080
```

---

## 📝 代码规范

### Python 风格

我们遵循 PEP 8，但有以下补充：

```python
# ✅ 好的写法

# 显式导入
from joinflow_core.types import Task, Step
from joinflow_agent.base import BaseAgent

# 类型注解
def process_task(task: Task, timeout: int = 30) -> AgentResult:
    """
    处理任务。
    
    Args:
        task: 要处理的任务
        timeout: 超时时间（秒）
        
    Returns:
        执行结果
        
    Raises:
        TaskError: 任务执行失败时
    """
    ...

# 明确的错误处理
try:
    result = agent.execute(task)
except AgentError as e:
    logger.error(f"Agent execution failed: {e}")
    raise TaskError(f"Failed to process task: {e}") from e


# ❌ 避免的写法

# 隐式导入
from joinflow_core import *

# 无类型注解
def process_task(task, timeout=30):
    ...

# 吞掉异常
try:
    result = agent.execute(task)
except:
    pass
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | snake_case | `task_scheduler.py` |
| 类 | PascalCase | `TaskScheduler` |
| 函数/方法 | snake_case | `execute_task()` |
| 常量 | UPPER_SNAKE | `MAX_RETRIES` |
| 私有成员 | _前缀 | `_internal_state` |

### 文档字符串

```python
def search_knowledge(
    query: str,
    top_k: int = 10,
    filters: Optional[Dict] = None
) -> List[SearchResult]:
    """
    在知识库中搜索相关文档。
    
    使用向量相似度搜索找到与查询最相关的文档。
    支持通过 filters 参数进行元数据过滤。
    
    Args:
        query: 搜索查询文本
        top_k: 返回结果数量，默认 10
        filters: 可选的元数据过滤条件
            - source: 来源过滤
            - date_range: 日期范围
            
    Returns:
        SearchResult 列表，按相关度降序排列
        
    Raises:
        ConnectionError: 无法连接向量数据库
        ValidationError: 查询参数无效
        
    Example:
        >>> results = search_knowledge("Python 教程", top_k=5)
        >>> for r in results:
        ...     print(f"{r.score:.2f}: {r.content[:50]}")
    """
    ...
```

### 前端规范

```javascript
// ✅ 好的写法

// 使用 const/let
const config = getConfig();
let currentTask = null;

// 异步处理
async function loadTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to load task:', error);
        showError('加载任务失败');
    }
}

// 事件处理
element.addEventListener('click', handleClick);


// ❌ 避免的写法

// 使用 var
var config = getConfig();

// 回调地狱
fetch(url).then(r => r.json()).then(data => {
    fetch(url2).then(r2 => r2.json()).then(data2 => {
        // ...
    });
});
```

---

## 📦 提交规范

### Commit 消息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构（不增加功能/修复bug） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具变动 |

### Scope 范围

- `agent`: Agent 系统
- `core`: 核心模块
- `rag`: RAG 引擎
- `web`: Web 服务
- `deploy`: 部署相关
- `docs`: 文档

### 示例

```bash
# 新功能
feat(agent): add VisionAgent for image recognition

# Bug 修复
fix(core): resolve memory leak in LLM cache

# 文档
docs(readme): update installation instructions

# 性能
perf(rag): optimize vector search with batch queries
```

---

## 🔄 Pull Request 流程

### 1. 创建 Issue (可选但推荐)

对于大型改动，先创建 Issue 讨论：
- 描述问题或功能需求
- 讨论实现方案
- 获得维护者反馈

### 2. Fork 和 Branch

```bash
# Fork 仓库到你的账号
# 然后克隆

git clone https://github.com/YOUR_USERNAME/joinflow.git
cd joinflow
git remote add upstream https://github.com/your-org/joinflow.git

# 创建功能分支
git checkout -b feature/your-feature-name
```

### 3. 开发和测试

```bash
# 开发代码...

# 运行测试
pytest tests/

# 检查代码风格
flake8 joinflow_core/ joinflow_agent/
black --check joinflow_core/ joinflow_agent/

# 运行类型检查
mypy joinflow_core/
```

### 4. 提交更改

```bash
# 添加更改
git add .

# 提交（遵循提交规范）
git commit -m "feat(agent): add new capability"

# 推送到 fork
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

在 GitHub 上创建 PR，包含：
- 清晰的标题和描述
- 关联的 Issue（如有）
- 测试说明
- 截图（如有 UI 更改）

### 6. 代码审查

- 响应审查意见
- 进行必要的修改
- 保持讨论的建设性

### 7. 合并

通过审查后，维护者会合并 PR。

---

## 🏷️ 版本规则

我们使用 [语义化版本](https://semver.org/lang/zh-CN/)：

```
MAJOR.MINOR.PATCH
```

| 类型 | 何时增加 | 示例 |
|------|----------|------|
| MAJOR | 不兼容的 API 更改 | 1.0.0 → 2.0.0 |
| MINOR | 向后兼容的功能添加 | 1.0.0 → 1.1.0 |
| PATCH | 向后兼容的 bug 修复 | 1.0.0 → 1.0.1 |

### 版本发布流程

1. 更新 `CHANGELOG.md`
2. 更新版本号
3. 创建 Git Tag
4. 发布 Release

---

## ❓ 常见问题

### Q: 我的 PR 被拒绝了怎么办？

A: 别气馁！请：
1. 仔细阅读拒绝原因
2. 如有疑问，在 PR 中讨论
3. 根据反馈修改后重新提交

### Q: 如何报告安全漏洞？

A: 请**不要**在公开 Issue 中报告安全问题。
发送邮件到 security@example.com

### Q: 可以添加新依赖吗？

A: 可以，但需要：
1. 说明为什么需要
2. 确保许可证兼容
3. 考虑是否可以设为可选依赖

---

## 📞 联系方式

- **GitHub Issues**: 问题和功能请求
- **GitHub Discussions**: 一般讨论
- **邮件**: joinflow@example.com

---

## 🙏 致谢

感谢所有贡献者的付出！

每一个贡献，无论大小，都对项目有价值。

---

<div align="center">

**Happy Coding! 🚀**

</div>
