"""
Plugin System
=============

Extensible plugin architecture for custom agents and tools.
"""

import importlib
import importlib.util
import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
from abc import ABC, abstractmethod
import sys

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """插件元数据"""
    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""
    
    # 依赖
    dependencies: List[str] = field(default_factory=list)
    python_requires: str = ">=3.9"
    
    # 能力
    provides_agents: List[str] = field(default_factory=list)
    provides_tools: List[str] = field(default_factory=list)
    
    # 状态
    enabled: bool = True
    installed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.installed_at:
            data['installed_at'] = self.installed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "PluginMetadata":
        if isinstance(data.get('installed_at'), str):
            data['installed_at'] = datetime.fromisoformat(data['installed_at'])
        return cls(**data)


class PluginBase(ABC):
    """插件基类"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """返回插件元数据"""
        pass
    
    def on_load(self) -> None:
        """插件加载时调用"""
        pass
    
    def on_unload(self) -> None:
        """插件卸载时调用"""
        pass
    
    def get_agents(self) -> List[Any]:
        """返回插件提供的Agent列表"""
        return []
    
    def get_tools(self) -> List[Any]:
        """返回插件提供的工具列表"""
        return []
    
    def get_config_schema(self) -> Dict[str, Any]:
        """返回插件配置schema"""
        return {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置插件"""
        pass


@dataclass
class PluginTool:
    """插件提供的工具"""
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    plugin_id: str = ""


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_configs: Dict[str, Dict] = {}
        
        self._load_plugin_configs()
    
    def _load_plugin_configs(self):
        """加载插件配置"""
        config_file = self.plugins_dir / "plugins.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.plugin_configs = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load plugin configs: {e}")
    
    def _save_plugin_configs(self):
        """保存插件配置"""
        config_file = self.plugins_dir / "plugins.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_configs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save plugin configs: {e}")
    
    def discover_plugins(self) -> List[PluginMetadata]:
        """发现可用插件"""
        discovered = []
        
        for path in self.plugins_dir.iterdir():
            if path.is_dir() and (path / "plugin.json").exists():
                try:
                    with open(path / "plugin.json", 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                    meta = PluginMetadata.from_dict(meta_data)
                    discovered.append(meta)
                except Exception as e:
                    logger.warning(f"Failed to load plugin metadata from {path}: {e}")
        
        return discovered
    
    def load_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """加载插件"""
        plugin_path = self.plugins_dir / plugin_id
        
        if not plugin_path.exists():
            logger.error(f"Plugin not found: {plugin_id}")
            return None
        
        try:
            # 查找主模块
            main_file = plugin_path / "main.py"
            if not main_file.exists():
                main_file = plugin_path / "__init__.py"
            
            if not main_file.exists():
                logger.error(f"Plugin main file not found: {plugin_id}")
                return None
            
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_id}",
                main_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, PluginBase) and 
                    obj is not PluginBase):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                logger.error(f"No PluginBase subclass found in: {plugin_id}")
                return None
            
            # 实例化并加载
            plugin = plugin_class()
            plugin.on_load()
            
            # 应用配置
            if plugin_id in self.plugin_configs:
                plugin.configure(self.plugin_configs[plugin_id])
            
            self.plugins[plugin_id] = plugin
            logger.info(f"Loaded plugin: {plugin.metadata.name} v{plugin.metadata.version}")
            
            return plugin
            
        except Exception as e:
            logger.exception(f"Failed to load plugin {plugin_id}: {e}")
            return None
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[plugin_id]
            plugin.on_unload()
            del self.plugins[plugin_id]
            
            # 清理模块
            module_name = f"plugins.{plugin_id}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].metadata.enabled = True
            return True
        return self.load_plugin(plugin_id) is not None
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].metadata.enabled = False
            return self.unload_plugin(plugin_id)
        return False
    
    def configure_plugin(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """配置插件"""
        self.plugin_configs[plugin_id] = config
        self._save_plugin_configs()
        
        if plugin_id in self.plugins:
            self.plugins[plugin_id].configure(config)
        
        return True
    
    def get_all_agents(self) -> List[Any]:
        """获取所有插件提供的Agent"""
        agents = []
        for plugin in self.plugins.values():
            if plugin.metadata.enabled:
                agents.extend(plugin.get_agents())
        return agents
    
    def get_all_tools(self) -> List[PluginTool]:
        """获取所有插件提供的工具"""
        tools = []
        for plugin in self.plugins.values():
            if plugin.metadata.enabled:
                for tool in plugin.get_tools():
                    if isinstance(tool, PluginTool):
                        tool.plugin_id = plugin.metadata.id
                    tools.append(tool)
        return tools
    
    def load_all_plugins(self):
        """加载所有发现的插件"""
        for meta in self.discover_plugins():
            if meta.enabled:
                self.load_plugin(meta.id)
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict]:
        """获取插件信息"""
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            return {
                "metadata": plugin.metadata.to_dict(),
                "config_schema": plugin.get_config_schema(),
                "agents": [str(a) for a in plugin.get_agents()],
                "tools": [t.name for t in plugin.get_tools()],
            }
        return None


# 示例插件模板
PLUGIN_TEMPLATE = '''"""
{name} Plugin
============

{description}
"""

from joinflow_core.plugins import PluginBase, PluginMetadata, PluginTool


class {class_name}Plugin(PluginBase):
    """
    {description}
    """
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="{id}",
            name="{name}",
            version="1.0.0",
            description="{description}",
            author="{author}",
            provides_tools=[],
        )
    
    def on_load(self):
        """插件加载时的初始化"""
        pass
    
    def on_unload(self):
        """插件卸载时的清理"""
        pass
    
    def get_tools(self):
        """返回插件提供的工具"""
        return [
            PluginTool(
                name="example_tool",
                description="示例工具",
                func=self._example_tool,
                parameters={{
                    "type": "object",
                    "properties": {{
                        "input": {{"type": "string", "description": "输入参数"}}
                    }},
                    "required": ["input"]
                }}
            )
        ]
    
    def _example_tool(self, input: str) -> str:
        """示例工具实现"""
        return f"处理结果: {{input}}"
    
    def get_config_schema(self):
        """配置schema"""
        return {{
            "type": "object",
            "properties": {{
                "api_key": {{"type": "string", "description": "API密钥"}},
            }}
        }}
    
    def configure(self, config):
        """应用配置"""
        self.api_key = config.get("api_key", "")
'''


def create_plugin_template(
    plugin_id: str,
    name: str,
    description: str = "",
    author: str = "",
    plugins_dir: str = "./plugins"
) -> Path:
    """创建插件模板"""
    plugins_path = Path(plugins_dir)
    plugin_path = plugins_path / plugin_id
    plugin_path.mkdir(parents=True, exist_ok=True)
    
    # 创建 plugin.json
    meta = PluginMetadata(
        id=plugin_id,
        name=name,
        version="1.0.0",
        description=description,
        author=author,
        installed_at=datetime.now()
    )
    
    with open(plugin_path / "plugin.json", 'w', encoding='utf-8') as f:
        json.dump(meta.to_dict(), f, indent=2, ensure_ascii=False)
    
    # 创建 main.py
    class_name = ''.join(word.capitalize() for word in plugin_id.split('_'))
    
    content = PLUGIN_TEMPLATE.format(
        id=plugin_id,
        name=name,
        class_name=class_name,
        description=description or "自定义插件",
        author=author or "Anonymous"
    )
    
    with open(plugin_path / "main.py", 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Created plugin template: {plugin_path}")
    return plugin_path

