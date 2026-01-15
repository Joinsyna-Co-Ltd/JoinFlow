"""
Task Templates System
=====================

Enterprise-grade task template system for reusable workflows.
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


class TemplateCategory(str, Enum):
    """模板分类"""
    RESEARCH = "research"           # 信息检索
    DATA_ANALYSIS = "data_analysis" # 数据分析
    CONTENT = "content"             # 内容创作
    CODE = "code"                   # 代码开发
    DOCUMENT = "document"           # 文档处理
    AUTOMATION = "automation"       # 自动化任务
    CUSTOM = "custom"               # 自定义


@dataclass
class TaskTemplate:
    """任务模板定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: TemplateCategory = TemplateCategory.CUSTOM
    icon: str = "📋"
    
    # 模板内容
    task_prompt: str = ""           # 任务提示词模板
    variables: List[Dict] = field(default_factory=list)  # 变量定义
    default_agents: List[str] = field(default_factory=list)
    default_mode: str = "auto"      # auto 或 step
    
    # 输出配置
    output_formats: List[str] = field(default_factory=lambda: ["markdown"])
    output_template: str = ""       # 输出模板
    
    # 元数据
    is_builtin: bool = False
    is_public: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    use_count: int = 0
    rating: float = 0.0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['category'] = self.category.value
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "TaskTemplate":
        if 'category' in data:
            data['category'] = TemplateCategory(data['category'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    def render(self, variables: Dict[str, Any] = None) -> str:
        """使用变量渲染任务提示词"""
        if variables is None:
            variables = {}
        
        prompt = self.task_prompt
        for var in self.variables:
            var_name = var.get('name', '')
            var_value = variables.get(var_name, var.get('default', ''))
            prompt = prompt.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        return prompt


class TemplateManager:
    """模板管理器"""
    
    def __init__(self, storage_path: str = "./templates"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, TaskTemplate] = {}
        self._load_templates()
        self._ensure_builtin_templates()
    
    def _load_templates(self):
        """从存储加载模板"""
        templates_file = self.storage_path / "templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for tpl_data in data.get('templates', []):
                    tpl = TaskTemplate.from_dict(tpl_data)
                    self.templates[tpl.id] = tpl
                logger.info(f"Loaded {len(self.templates)} templates")
            except Exception as e:
                logger.error(f"Failed to load templates: {e}")
    
    def _save_templates(self):
        """保存模板到存储"""
        templates_file = self.storage_path / "templates.json"
        try:
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'templates': [t.to_dict() for t in self.templates.values()]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
    
    def _ensure_builtin_templates(self):
        """确保内置模板存在"""
        builtin_templates = [
            # 信息检索类
            TaskTemplate(
                id="builtin_web_research",
                name="网络信息研究",
                description="搜索并整理特定主题的网络信息，生成研究报告",
                category=TemplateCategory.RESEARCH,
                icon="🔍",
                task_prompt="请帮我搜索关于「{{topic}}」的最新信息，包括：\n1. 基本概念和定义\n2. 最新发展动态\n3. 主要参与者/公司\n4. 未来趋势预测\n\n请整理成结构化的研究报告。",
                variables=[
                    {"name": "topic", "label": "研究主题", "type": "text", "required": True, "placeholder": "如：人工智能、新能源汽车"}
                ],
                default_agents=["browser", "llm"],
                output_formats=["markdown", "html", "pptx"],
                is_builtin=True,
                tags=["研究", "搜索", "报告"]
            ),
            TaskTemplate(
                id="builtin_competitor_analysis",
                name="竞品分析报告",
                description="分析竞争对手的产品、策略和市场表现",
                category=TemplateCategory.RESEARCH,
                icon="📊",
                task_prompt="请帮我分析「{{company}}」公司的竞品情况：\n1. 公司基本信息\n2. 主要产品/服务\n3. 核心竞争优势\n4. 市场定位和策略\n5. 与{{our_company}}的对比分析\n\n请生成详细的竞品分析报告。",
                variables=[
                    {"name": "company", "label": "竞品公司", "type": "text", "required": True},
                    {"name": "our_company", "label": "我方公司", "type": "text", "default": "我们"}
                ],
                default_agents=["browser", "llm"],
                output_formats=["markdown", "excel", "pptx"],
                is_builtin=True,
                tags=["竞品", "分析", "市场"]
            ),
            
            # 数据分析类
            TaskTemplate(
                id="builtin_data_report",
                name="数据分析报告",
                description="对数据进行分析并生成可视化报告",
                category=TemplateCategory.DATA_ANALYSIS,
                icon="📈",
                task_prompt="请分析以下数据并生成报告：\n\n数据描述：{{data_description}}\n\n分析要求：\n1. 数据概览和基本统计\n2. 关键趋势和模式\n3. 异常值分析\n4. 结论和建议\n\n请生成包含图表的数据分析报告。",
                variables=[
                    {"name": "data_description", "label": "数据描述", "type": "textarea", "required": True, "placeholder": "描述您的数据来源、格式和分析目标"}
                ],
                default_agents=["data", "llm"],
                output_formats=["markdown", "excel", "html"],
                is_builtin=True,
                tags=["数据", "分析", "图表"]
            ),
            
            # 内容创作类
            TaskTemplate(
                id="builtin_article_writing",
                name="文章撰写",
                description="根据主题撰写专业文章",
                category=TemplateCategory.CONTENT,
                icon="✍️",
                task_prompt="请帮我撰写一篇关于「{{title}}」的{{article_type}}：\n\n要求：\n- 字数：{{word_count}}字左右\n- 风格：{{style}}\n- 目标读者：{{audience}}\n\n额外要求：{{requirements}}",
                variables=[
                    {"name": "title", "label": "文章标题", "type": "text", "required": True},
                    {"name": "article_type", "label": "文章类型", "type": "select", "options": ["博客文章", "新闻稿", "技术文档", "产品介绍", "研究报告"], "default": "博客文章"},
                    {"name": "word_count", "label": "字数要求", "type": "number", "default": "1500"},
                    {"name": "style", "label": "写作风格", "type": "select", "options": ["专业严谨", "轻松活泼", "通俗易懂", "学术研究"], "default": "专业严谨"},
                    {"name": "audience", "label": "目标读者", "type": "text", "default": "普通读者"},
                    {"name": "requirements", "label": "额外要求", "type": "textarea", "default": ""}
                ],
                default_agents=["browser", "llm"],
                output_formats=["markdown", "html"],
                is_builtin=True,
                tags=["写作", "内容", "文章"]
            ),
            TaskTemplate(
                id="builtin_social_media",
                name="社交媒体内容",
                description="生成多平台社交媒体内容",
                category=TemplateCategory.CONTENT,
                icon="📱",
                task_prompt="请为「{{topic}}」生成社交媒体内容：\n\n目标平台：{{platforms}}\n内容目的：{{purpose}}\n品牌调性：{{tone}}\n\n请为每个平台生成适合其特点的内容，包括文案和配图建议。",
                variables=[
                    {"name": "topic", "label": "内容主题", "type": "text", "required": True},
                    {"name": "platforms", "label": "目标平台", "type": "multiselect", "options": ["微信公众号", "微博", "小红书", "抖音", "知乎", "LinkedIn"], "default": ["微信公众号", "微博"]},
                    {"name": "purpose", "label": "内容目的", "type": "select", "options": ["品牌宣传", "产品推广", "活动预热", "知识分享", "互动引流"], "default": "品牌宣传"},
                    {"name": "tone", "label": "品牌调性", "type": "text", "default": "专业可信"}
                ],
                default_agents=["llm"],
                output_formats=["markdown"],
                is_builtin=True,
                tags=["社媒", "营销", "内容"]
            ),
            
            # 代码开发类
            TaskTemplate(
                id="builtin_code_review",
                name="代码审查",
                description="审查代码并提供改进建议",
                category=TemplateCategory.CODE,
                icon="🔧",
                task_prompt="请审查以下代码：\n\n语言：{{language}}\n代码功能：{{function_desc}}\n\n```{{language}}\n{{code}}\n```\n\n请检查：\n1. 代码规范和风格\n2. 潜在的bug和安全问题\n3. 性能优化建议\n4. 可读性和可维护性\n\n请提供详细的审查报告和改进建议。",
                variables=[
                    {"name": "language", "label": "编程语言", "type": "select", "options": ["python", "javascript", "java", "go", "rust", "c++"], "default": "python"},
                    {"name": "function_desc", "label": "代码功能", "type": "text", "required": True},
                    {"name": "code", "label": "代码内容", "type": "code", "required": True}
                ],
                default_agents=["code", "llm"],
                output_formats=["markdown"],
                is_builtin=True,
                tags=["代码", "审查", "优化"]
            ),
            
            # 文档处理类
            TaskTemplate(
                id="builtin_meeting_summary",
                name="会议纪要生成",
                description="根据会议内容生成结构化会议纪要",
                category=TemplateCategory.DOCUMENT,
                icon="📝",
                task_prompt="请根据以下会议内容生成会议纪要：\n\n会议主题：{{meeting_title}}\n参会人员：{{participants}}\n会议时间：{{meeting_time}}\n\n会议内容/录音转写：\n{{content}}\n\n请生成包含以下内容的会议纪要：\n1. 会议概要\n2. 主要讨论点\n3. 决策事项\n4. 待办事项（含负责人和截止时间）\n5. 下次会议安排",
                variables=[
                    {"name": "meeting_title", "label": "会议主题", "type": "text", "required": True},
                    {"name": "participants", "label": "参会人员", "type": "text", "required": True},
                    {"name": "meeting_time", "label": "会议时间", "type": "text", "default": ""},
                    {"name": "content", "label": "会议内容", "type": "textarea", "required": True}
                ],
                default_agents=["llm"],
                output_formats=["markdown", "html", "excel"],
                is_builtin=True,
                tags=["会议", "纪要", "文档"]
            ),
            
            # 自动化任务类
            TaskTemplate(
                id="builtin_daily_report",
                name="每日工作汇报",
                description="生成每日工作汇报，支持定时执行",
                category=TemplateCategory.AUTOMATION,
                icon="📅",
                task_prompt="请生成{{date}}的工作汇报：\n\n今日完成：\n{{completed_tasks}}\n\n进行中的工作：\n{{ongoing_tasks}}\n\n明日计划：\n{{tomorrow_plan}}\n\n遇到的问题：\n{{issues}}\n\n请整理成规范的工作汇报格式。",
                variables=[
                    {"name": "date", "label": "日期", "type": "date", "default": "today"},
                    {"name": "completed_tasks", "label": "完成的任务", "type": "textarea", "required": True},
                    {"name": "ongoing_tasks", "label": "进行中的工作", "type": "textarea", "default": ""},
                    {"name": "tomorrow_plan", "label": "明日计划", "type": "textarea", "default": ""},
                    {"name": "issues", "label": "遇到的问题", "type": "textarea", "default": "无"}
                ],
                default_agents=["llm"],
                output_formats=["markdown", "html"],
                is_builtin=True,
                tags=["汇报", "日报", "自动化"]
            ),
            TaskTemplate(
                id="builtin_news_monitor",
                name="新闻监控",
                description="监控特定主题的新闻动态",
                category=TemplateCategory.AUTOMATION,
                icon="📰",
                task_prompt="请搜索并整理「{{keywords}}」相关的最新新闻：\n\n时间范围：{{time_range}}\n来源偏好：{{sources}}\n\n请整理：\n1. 重要新闻标题和摘要\n2. 新闻来源和发布时间\n3. 关键观点总结\n4. 趋势分析",
                variables=[
                    {"name": "keywords", "label": "监控关键词", "type": "text", "required": True, "placeholder": "多个关键词用逗号分隔"},
                    {"name": "time_range", "label": "时间范围", "type": "select", "options": ["最近24小时", "最近3天", "最近一周"], "default": "最近24小时"},
                    {"name": "sources", "label": "来源偏好", "type": "text", "default": "主流媒体"}
                ],
                default_agents=["browser", "llm"],
                output_formats=["markdown", "html", "excel"],
                is_builtin=True,
                tags=["新闻", "监控", "自动化"]
            ),
        ]
        
        # 添加内置模板（不覆盖已存在的）
        for tpl in builtin_templates:
            if tpl.id not in self.templates:
                self.templates[tpl.id] = tpl
        
        self._save_templates()
    
    def get_template(self, template_id: str) -> Optional[TaskTemplate]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def get_all_templates(self, category: TemplateCategory = None) -> List[TaskTemplate]:
        """获取所有模板"""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return sorted(templates, key=lambda t: (-t.use_count, t.name))
    
    def get_templates_by_category(self) -> Dict[str, List[TaskTemplate]]:
        """按分类获取模板"""
        result = {}
        for tpl in self.templates.values():
            cat = tpl.category.value
            if cat not in result:
                result[cat] = []
            result[cat].append(tpl)
        return result
    
    def create_template(self, template: TaskTemplate) -> TaskTemplate:
        """创建新模板"""
        template.is_builtin = False
        self.templates[template.id] = template
        self._save_templates()
        return template
    
    def update_template(self, template_id: str, updates: dict) -> Optional[TaskTemplate]:
        """更新模板"""
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        if template.is_builtin:
            raise ValueError("不能修改内置模板")
        
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self._save_templates()
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        if template.is_builtin:
            raise ValueError("不能删除内置模板")
        
        del self.templates[template_id]
        self._save_templates()
        return True
    
    def increment_use_count(self, template_id: str):
        """增加使用次数"""
        if template_id in self.templates:
            self.templates[template_id].use_count += 1
            self._save_templates()
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """渲染模板"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        self.increment_use_count(template_id)
        return template.render(variables)
    
    def search_templates(self, query: str) -> List[TaskTemplate]:
        """搜索模板"""
        query = query.lower()
        results = []
        for tpl in self.templates.values():
            if (query in tpl.name.lower() or 
                query in tpl.description.lower() or
                any(query in tag.lower() for tag in tpl.tags)):
                results.append(tpl)
        return results

