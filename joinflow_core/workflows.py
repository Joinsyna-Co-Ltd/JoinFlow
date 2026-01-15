"""
Workflow Templates
==================

Save, load, and manage reusable workflow templates.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowCategory(str, Enum):
    RESEARCH = "research"        # 研究调研
    CODE = "code"                # 代码开发
    DATA = "data"                # 数据处理
    FILE = "file"                # 文件操作
    AUTOMATION = "automation"    # 自动化
    CUSTOM = "custom"            # 自定义


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    agent: str = "llm"           # 使用的Agent
    
    # 步骤配置
    prompt_template: str = ""     # 提示模板
    input_mapping: Dict[str, str] = field(default_factory=dict)  # 输入映射
    output_key: str = ""          # 输出键名
    
    # 条件
    condition: str = ""           # 执行条件
    dependencies: List[str] = field(default_factory=list)  # 依赖步骤
    
    # 其他
    timeout: int = 300            # 超时秒数
    retry_count: int = 3          # 重试次数
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowStep":
        # 只提取 WorkflowStep 支持的字段，忽略额外字段
        valid_fields = {
            'id', 'name', 'description', 'agent', 'prompt_template',
            'input_mapping', 'output_mapping', 'output_key', 'condition',
            'dependencies', 'timeout', 'retry_count'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: WorkflowCategory = WorkflowCategory.CUSTOM
    
    # 图标和标签
    icon: str = "fas fa-project-diagram"
    color: str = "#58a6ff"
    tags: List[str] = field(default_factory=list)
    
    # 步骤
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # 输入参数
    input_schema: Dict[str, Any] = field(default_factory=dict)
    
    # 输出配置
    output_template: str = ""     # 输出模板
    
    # 统计
    use_count: int = 0
    last_used: Optional[datetime] = None
    
    # 元数据
    is_system: bool = False       # 是否系统模板
    is_public: bool = True        # 是否公开
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "default"
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['category'] = self.category.value
        data['steps'] = [s.to_dict() if isinstance(s, WorkflowStep) else s for s in self.steps]
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['last_used'] = self.last_used.isoformat() if self.last_used else None
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowTemplate":
        # 创建数据副本避免修改原始数据
        data = dict(data)
        
        if 'category' in data:
            try:
                data['category'] = WorkflowCategory(data['category'])
            except ValueError:
                data['category'] = WorkflowCategory.CUSTOM
        
        if 'steps' in data:
            data['steps'] = [
                WorkflowStep.from_dict(s) if isinstance(s, dict) else s 
                for s in data['steps']
            ]
        
        for field_name in ['created_at', 'updated_at', 'last_used']:
            if isinstance(data.get(field_name), str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except ValueError:
                    del data[field_name]
        
        # 只提取 WorkflowTemplate 支持的字段，忽略额外字段
        valid_fields = {
            'id', 'name', 'description', 'category', 'icon', 'color', 'tags',
            'steps', 'input_schema', 'output_template', 'use_count', 'last_used',
            'is_system', 'is_public', 'created_at', 'updated_at', 'created_by'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)


class WorkflowManager:
    """工作流管理器"""
    
    @staticmethod
    def _get_preset_templates() -> List["WorkflowTemplate"]:
        """获取预设模板（每次调用创建新实例）"""
        return [
            WorkflowTemplate(
                id="tpl_research",
                name="🔍 信息检索与整理",
                description="搜索网络信息，分析整理成结构化报告",
                category=WorkflowCategory.RESEARCH,
                icon="fas fa-search",
                color="#58a6ff",
                tags=["搜索", "研究", "报告"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="search",
                        name="搜索信息",
                        description="使用浏览器搜索相关信息",
                        agent="browser",
                        prompt_template="搜索关于 {topic} 的最新信息"
                    ),
                    WorkflowStep(
                        id="analyze",
                        name="分析整理",
                        description="分析搜索结果并整理成报告",
                        agent="llm",
                        prompt_template="根据搜索结果，整理关于 {topic} 的详细报告",
                        dependencies=["search"]
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "搜索主题（如：人工智能最新进展）"}
                    },
                    "required": ["topic"]
                }
            ),
            WorkflowTemplate(
                id="tpl_code_gen",
                name="💻 代码生成与执行",
                description="根据需求生成Python代码并执行验证",
                category=WorkflowCategory.CODE,
                icon="fas fa-code",
                color="#7c3aed",
                tags=["代码", "开发", "Python"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="generate",
                        name="生成代码",
                        description="根据需求生成代码",
                        agent="llm",
                        prompt_template="根据以下需求生成Python代码：\n{requirement}"
                    ),
                    WorkflowStep(
                        id="execute",
                        name="执行代码",
                        description="在安全沙盒中执行代码",
                        agent="code",
                        prompt_template="执行生成的代码",
                        dependencies=["generate"]
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "requirement": {"type": "string", "description": "代码需求（如：计算斐波那契数列前20项）"}
                    },
                    "required": ["requirement"]
                }
            ),
            WorkflowTemplate(
                id="tpl_data_analysis",
                name="📊 数据分析报告",
                description="分析CSV/Excel数据文件，生成统计报告和图表",
                category=WorkflowCategory.DATA,
                icon="fas fa-chart-bar",
                color="#10b981",
                tags=["数据", "分析", "图表", "Excel"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="load",
                        name="加载数据",
                        description="读取数据文件",
                        agent="data",
                        prompt_template="读取并分析文件：{file_path}"
                    ),
                    WorkflowStep(
                        id="analyze",
                        name="统计分析",
                        description="进行数据统计分析",
                        agent="data",
                        prompt_template="对数据进行统计分析，包括：均值、中位数、标准差等",
                        dependencies=["load"]
                    ),
                    WorkflowStep(
                        id="visualize",
                        name="生成图表",
                        description="生成数据可视化图表",
                        agent="data",
                        prompt_template="生成数据可视化图表",
                        dependencies=["analyze"]
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "数据文件路径（CSV/Excel）"}
                    },
                    "required": ["file_path"]
                }
            ),
            WorkflowTemplate(
                id="tpl_file_batch",
                name="📁 批量文件处理",
                description="批量处理目录中的文件（重命名、转换、整理等）",
                category=WorkflowCategory.FILE,
                icon="fas fa-folder-open",
                color="#f59e0b",
                tags=["文件", "批量", "整理"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="list",
                        name="列出文件",
                        description="获取目录下的文件列表",
                        agent="os",
                        prompt_template="列出目录 {directory} 中的所有文件"
                    ),
                    WorkflowStep(
                        id="process",
                        name="处理文件",
                        description="对文件执行操作",
                        agent="os",
                        prompt_template="对文件执行 {operation} 操作",
                        dependencies=["list"]
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径（如：./documents）"},
                        "operation": {"type": "string", "description": "操作类型（如：按日期重命名）"}
                    },
                    "required": ["directory", "operation"]
                }
            ),
            WorkflowTemplate(
                id="tpl_web_scrape",
                name="🌐 网页内容抓取",
                description="抓取网页内容并提取关键信息",
                category=WorkflowCategory.RESEARCH,
                icon="fas fa-globe",
                color="#06b6d4",
                tags=["网页", "抓取", "提取"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="fetch",
                        name="访问网页",
                        description="访问目标网页",
                        agent="browser",
                        prompt_template="访问网页 {url} 并获取内容"
                    ),
                    WorkflowStep(
                        id="extract",
                        name="提取信息",
                        description="从网页中提取关键信息",
                        agent="llm",
                        prompt_template="从网页内容中提取 {extract_target}",
                        dependencies=["fetch"]
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "网页URL"},
                        "extract_target": {"type": "string", "description": "要提取的信息（如：文章标题和摘要）"}
                    },
                    "required": ["url", "extract_target"]
                }
            ),
            WorkflowTemplate(
                id="tpl_text_process",
                name="📝 文本处理",
                description="对文本进行翻译、摘要、改写等处理",
                category=WorkflowCategory.AUTOMATION,
                icon="fas fa-file-alt",
                color="#ec4899",
                tags=["文本", "翻译", "摘要"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="process",
                        name="处理文本",
                        description="对文本执行处理操作",
                        agent="llm",
                        prompt_template="对以下文本进行{action}：\n\n{text}"
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要处理的文本"},
                        "action": {"type": "string", "description": "处理方式（翻译成英文/生成摘要/改写润色）"}
                    },
                    "required": ["text", "action"]
                }
            ),
            WorkflowTemplate(
                id="tpl_daily_report",
                name="📋 每日报告生成",
                description="收集信息并生成每日工作/新闻报告",
                category=WorkflowCategory.AUTOMATION,
                icon="fas fa-newspaper",
                color="#8b5cf6",
                tags=["报告", "自动化", "每日"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="collect",
                        name="收集信息",
                        description="从多个来源收集信息",
                        agent="browser",
                        prompt_template="搜索 {topic} 的最新动态"
                    ),
                    WorkflowStep(
                        id="summarize",
                        name="整理摘要",
                        description="整理成报告格式",
                        agent="llm",
                        prompt_template="将收集的信息整理成结构化的每日报告",
                        dependencies=["collect"]
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "报告主题（如：AI行业动态）"}
                    },
                    "required": ["topic"]
                }
            ),
            WorkflowTemplate(
                id="tpl_image_analyze",
                name="🖼️ 图片分析",
                description="分析图片内容，提取文字或描述",
                category=WorkflowCategory.DATA,
                icon="fas fa-image",
                color="#f472b6",
                tags=["图片", "OCR", "分析"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="analyze",
                        name="分析图片",
                        description="分析图片内容",
                        agent="vision",
                        prompt_template="分析图片 {image_path}，{task}"
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "image_path": {"type": "string", "description": "图片路径"},
                        "task": {"type": "string", "description": "分析任务（提取文字/描述内容/识别物体）", "default": "描述图片内容"}
                    },
                    "required": ["image_path"]
                }
            ),
            WorkflowTemplate(
                id="tpl_qa_knowledge",
                name="📚 知识库问答",
                description="基于知识库回答问题（RAG）",
                category=WorkflowCategory.RESEARCH,
                icon="fas fa-book-open",
                color="#14b8a6",
                tags=["知识库", "问答", "RAG"],
                is_system=True,
                steps=[
                    WorkflowStep(
                        id="search",
                        name="检索知识",
                        description="从知识库中检索相关内容",
                        agent="rag",
                        prompt_template="在知识库中搜索与 {question} 相关的内容"
                    ),
                    WorkflowStep(
                        id="answer",
                        name="生成答案",
                        description="基于检索结果生成答案",
                        agent="llm",
                        prompt_template="根据检索到的知识，回答问题：{question}",
                        dependencies=["search"]
                    ),
                ],
                input_schema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "要回答的问题"}
                    },
                    "required": ["question"]
                }
            ),
        ]
    
    def __init__(self, storage_path: str = "./workflows"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, WorkflowTemplate] = {}
        
        self._load_templates()
        self._init_preset_templates()
    
    def _load_templates(self):
        """加载模板"""
        config_file = self.storage_path / "workflows.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for tpl_data in data.get('templates', []):
                    tpl = WorkflowTemplate.from_dict(tpl_data)
                    self.templates[tpl.id] = tpl
                logger.info(f"Loaded {len(self.templates)} workflow templates")
            except Exception as e:
                logger.error(f"Failed to load workflow templates: {e}")
    
    def _save_templates(self):
        """保存模板"""
        config_file = self.storage_path / "workflows.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'templates': [t.to_dict() for t in self.templates.values()]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save workflow templates: {e}")
    
    def _init_preset_templates(self):
        """初始化预设模板"""
        presets = self._get_preset_templates()
        added = 0
        for preset in presets:
            if preset.id not in self.templates:
                self.templates[preset.id] = preset
                added += 1
        if added > 0:
            self._save_templates()
            logger.info(f"Added {added} preset workflow templates")
    
    def create_template(self, template: WorkflowTemplate) -> WorkflowTemplate:
        """创建模板"""
        self.templates[template.id] = template
        self._save_templates()
        logger.info(f"Created workflow template: {template.name}")
        return template
    
    def update_template(self, template_id: str, updates: dict) -> Optional[WorkflowTemplate]:
        """更新模板"""
        if template_id not in self.templates:
            return None
        
        tpl = self.templates[template_id]
        
        # 不允许修改系统模板
        if tpl.is_system and not updates.get('_force'):
            logger.warning(f"Cannot modify system template: {template_id}")
            return None
        
        for key, value in updates.items():
            if key.startswith('_'):
                continue
            if hasattr(tpl, key):
                setattr(tpl, key, value)
        
        tpl.updated_at = datetime.now()
        self._save_templates()
        return tpl
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id not in self.templates:
            return False
        
        if self.templates[template_id].is_system:
            logger.warning(f"Cannot delete system template: {template_id}")
            return False
        
        del self.templates[template_id]
        self._save_templates()
        return True
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        category: WorkflowCategory = None,
        tags: List[str] = None,
        include_system: bool = True
    ) -> List[WorkflowTemplate]:
        """列出模板"""
        templates = list(self.templates.values())
        
        if not include_system:
            templates = [t for t in templates if not t.is_system]
        if category:
            templates = [t for t in templates if t.category == category]
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return sorted(templates, key=lambda t: (not t.is_system, -t.use_count))
    
    def duplicate_template(self, template_id: str, new_name: str = None) -> Optional[WorkflowTemplate]:
        """复制模板"""
        original = self.get_template(template_id)
        if not original:
            return None
        
        # 创建副本
        data = original.to_dict()
        data['id'] = str(uuid.uuid4())
        data['name'] = new_name or f"{original.name} (副本)"
        data['is_system'] = False
        data['use_count'] = 0
        data['created_at'] = datetime.now().isoformat()
        
        new_template = WorkflowTemplate.from_dict(data)
        return self.create_template(new_template)
    
    def record_usage(self, template_id: str):
        """记录模板使用"""
        if template_id in self.templates:
            self.templates[template_id].use_count += 1
            self.templates[template_id].last_used = datetime.now()
            self._save_templates()
    
    def export_template(self, template_id: str) -> Optional[str]:
        """导出模板为JSON"""
        tpl = self.get_template(template_id)
        if not tpl:
            return None
        return json.dumps(tpl.to_dict(), indent=2, ensure_ascii=False)
    
    def import_template(self, json_data: str) -> Optional[WorkflowTemplate]:
        """从JSON导入模板"""
        try:
            data = json.loads(json_data)
            # 生成新ID避免冲突
            data['id'] = str(uuid.uuid4())
            data['is_system'] = False
            data['created_at'] = datetime.now().isoformat()
            
            tpl = WorkflowTemplate.from_dict(data)
            return self.create_template(tpl)
        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return None
    
    def build_task_from_template(
        self,
        template_id: str,
        inputs: Dict[str, Any]
    ) -> Optional[str]:
        """
        从模板构建任务描述
        
        Args:
            template_id: 模板ID
            inputs: 输入参数
            
        Returns:
            构建好的任务描述
        """
        tpl = self.get_template(template_id)
        if not tpl:
            return None
        
        # 构建任务描述
        task_parts = [f"执行工作流: {tpl.name}\n"]
        
        for step in tpl.steps:
            # 替换模板变量
            prompt = step.prompt_template
            for key, value in inputs.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))
            task_parts.append(f"- {step.name}: {prompt}")
        
        self.record_usage(template_id)
        
        return "\n".join(task_parts)

