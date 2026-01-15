"""
Agent OS - 智能操作系统代理
============================

一个基于AI的智能操作系统代理，能够：
- 理解自然语言指令
- 自动规划和执行复杂任务
- 全面控制操作系统
- 智能搜索和资源管理

使用示例:
    from agent_os import AgentOS
    
    agent = AgentOS()
    agent.run("打开浏览器搜索Python教程")
    agent.run("查找桌面上所有PDF文件")
    agent.run("创建项目文件夹并初始化README")
"""

from .core.agent import AgentOS
from .core.config import AgentConfig
from .core.session import Session

__version__ = "2.0.0"
__all__ = ["AgentOS", "AgentConfig", "Session"]

