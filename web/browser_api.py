"""
Browser Agent API - 增强浏览器 Agent API
=========================================

提供 RESTful API 端点来使用增强的浏览器功能：
- 访问网页并提取内容
- LLM 驱动的页面分析和总结
- 智能信息提取
- 搜索和多页面分析
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/browser", tags=["Browser Agent"])

# 全局浏览器 Agent 实例
_browser_agent = None


def get_browser_agent():
    """获取或创建浏览器 Agent 实例"""
    global _browser_agent
    if _browser_agent is None:
        from joinflow_agent.browser_enhanced import EnhancedBrowserAgent
        _browser_agent = EnhancedBrowserAgent(headless=True)
    return _browser_agent


# =====================
# 请求模型
# =====================

class NavigateRequest(BaseModel):
    """导航请求"""
    url: str
    analyze: bool = False  # 是否使用 LLM 分析
    analysis_prompt: Optional[str] = None  # 自定义分析提示


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    num_results: int = 3  # 分析的结果数量
    analyze: bool = True  # 是否使用 LLM 分析


class ExtractRequest(BaseModel):
    """智能提取请求"""
    url: str
    user_query: str  # 用户需要提取的信息描述


class TaskRequest(BaseModel):
    """任务执行请求"""
    task: str  # 自然语言任务描述


class AnalyzeRequest(BaseModel):
    """分析请求"""
    analysis_prompt: Optional[str] = None
    extract_type: str = "summary"  # summary, key_points, specific


# =====================
# API 端点
# =====================

@router.post("/navigate")
async def navigate_to_url(request: NavigateRequest):
    """
    导航到 URL 并提取页面内容
    
    可选：使用 LLM 分析页面内容
    """
    agent = get_browser_agent()
    
    try:
        # 导航到页面
        page_data = await agent.navigate(request.url)
        
        result = {
            "success": True,
            "url": page_data.url,
            "title": page_data.title,
            "content": page_data.main_content[:5000],
            "links_count": len(page_data.links),
            "images_count": len(page_data.images),
            "tables_count": len(page_data.tables),
            "links": page_data.links[:10],
            "metadata": page_data.metadata
        }
        
        # 如果需要 LLM 分析
        if request.analyze:
            analysis = await agent.analyze_page(
                analysis_prompt=request.analysis_prompt,
                extract_type="summary"
            )
            result["analysis"] = analysis.get("analysis", "")
        
        return result
        
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/search")
async def search_and_analyze(request: SearchRequest):
    """
    搜索并分析多个结果页面
    
    使用 LLM 分析每个页面并生成综合总结
    """
    agent = get_browser_agent()
    
    try:
        result = await agent.search_and_analyze(
            query=request.query,
            num_results=request.num_results,
            analyze=request.analyze
        )
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/extract")
async def smart_extract(request: ExtractRequest):
    """
    智能提取：根据用户需求从网页提取特定信息
    
    使用 LLM 理解用户需求并提取相关信息
    """
    agent = get_browser_agent()
    
    try:
        result = await agent.smart_extract(
            url=request.url,
            user_query=request.user_query
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Smart extraction failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/analyze")
async def analyze_current_page(request: AnalyzeRequest):
    """
    分析当前页面内容
    
    使用 LLM 对当前打开的页面进行分析
    """
    agent = get_browser_agent()
    
    try:
        result = await agent.analyze_page(
            analysis_prompt=request.analysis_prompt,
            extract_type=request.extract_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/task")
async def execute_browser_task(request: TaskRequest):
    """
    执行浏览器任务
    
    根据自然语言描述自动执行浏览器操作
    """
    agent = get_browser_agent()
    
    try:
        result = await agent.execute_task(request.task)
        
        return {
            "success": result.get("success", False),
            **result
        }
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/elements")
async def get_page_elements():
    """
    获取当前页面的可交互元素
    
    返回按钮、链接、输入框等元素列表
    """
    agent = get_browser_agent()
    
    try:
        elements = await agent.get_interactive_elements()
        
        return {
            "success": True,
            "count": len(elements),
            "elements": [
                {
                    "tag": el.tag,
                    "text": el.text,
                    "href": el.href,
                    "clickable": el.clickable,
                    "input_type": el.input_type
                }
                for el in elements[:50]
            ]
        }
        
    except Exception as e:
        logger.error(f"Get elements failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/screenshot")
async def take_screenshot(full_page: bool = False):
    """
    截取当前页面截图
    
    返回 base64 编码的图片
    """
    agent = get_browser_agent()
    
    try:
        screenshot_b64 = await agent.take_screenshot(full_page=full_page)
        
        return {
            "success": True,
            "format": "png",
            "data": screenshot_b64
        }
        
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/click")
async def click_element(selector: str):
    """
    点击页面元素
    """
    agent = get_browser_agent()
    
    try:
        success = await agent.click_element(selector)
        
        return {
            "success": success
        }
        
    except Exception as e:
        logger.error(f"Click failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


class TypeRequest(BaseModel):
    selector: str
    text: str


@router.post("/type")
async def type_text(request: TypeRequest):
    """
    在元素中输入文本
    """
    agent = get_browser_agent()
    
    try:
        success = await agent.type_text(request.selector, request.text)
        
        return {
            "success": success
        }
        
    except Exception as e:
        logger.error(f"Type failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/status")
async def get_browser_status():
    """
    获取浏览器状态
    """
    agent = get_browser_agent()
    
    return {
        "initialized": agent._page is not None,
        "current_url": agent._page.url if agent._page else None,
        "history_count": len(agent._history)
    }


@router.post("/close")
async def close_browser():
    """
    关闭浏览器
    """
    global _browser_agent
    
    if _browser_agent:
        await _browser_agent.close()
        _browser_agent = None
    
    return {"success": True, "message": "Browser closed"}


logger.info("Browser API routes registered")

