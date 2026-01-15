"""
浏览器执行器
"""
import webbrowser
import urllib.parse
from typing import Dict

from .base import BaseExecutor
from ..core.runtime import ActionResult


class BrowserExecutor(BaseExecutor):
    """浏览器操作执行器"""
    
    name = "browser"
    
    # 搜索引擎
    SEARCH_ENGINES = {
        "google": "https://www.google.com/search?q={}",
        "bing": "https://www.bing.com/search?q={}",
        "baidu": "https://www.baidu.com/s?wd={}",
        "duckduckgo": "https://duckduckgo.com/?q={}",
        "github": "https://github.com/search?q={}",
        "youtube": "https://www.youtube.com/results?search_query={}",
        "bilibili": "https://search.bilibili.com/all?keyword={}",
        "zhihu": "https://www.zhihu.com/search?type=content&q={}",
    }
    
    def execute(self, action: str, command: str, params: Dict) -> ActionResult:
        """执行浏览器操作"""
        try:
            if action == "browser.search":
                return self._search(command, params)
            elif action == "browser.navigate":
                return self._navigate(command, params)
            elif action == "browser.open":
                return self._open_browser(params)
            else:
                return ActionResult(False, action, f"不支持的操作: {action}")
        except Exception as e:
            return ActionResult(False, action, f"操作失败: {e}", error=str(e))
    
    def _search(self, command: str, params: Dict) -> ActionResult:
        """浏览器搜索"""
        query = params.get("query") or self._extract_query(command)
        engine = params.get("engine", "google")
        
        if not query:
            return ActionResult(False, "browser.search", "请指定搜索关键词")
        
        # 从命令中检测搜索引擎
        engine_keywords = {
            "百度": "baidu",
            "baidu": "baidu",
            "谷歌": "google",
            "google": "google",
            "bing": "bing",
            "必应": "bing",
            "github": "github",
            "youtube": "youtube",
            "bilibili": "bilibili",
            "b站": "bilibili",
            "知乎": "zhihu",
        }
        
        for keyword, eng in engine_keywords.items():
            if keyword in command.lower():
                engine = eng
                # 从query中移除引擎关键词
                query = query.replace(keyword, "").strip()
                break
        
        # 获取搜索URL
        url_template = self.SEARCH_ENGINES.get(engine, self.SEARCH_ENGINES["google"])
        search_url = url_template.format(urllib.parse.quote(query))
        
        try:
            webbrowser.open(search_url)
            
            self._log("search", f"Searched: {query} on {engine}")
            
            return ActionResult(
                success=True,
                action="browser.search",
                message=f"🔍 已使用 {engine} 搜索: {query}",
                data={"query": query, "engine": engine, "url": search_url}
            )
        except Exception as e:
            return ActionResult(False, "browser.search", f"搜索失败: {e}", error=str(e))
    
    def _navigate(self, command: str, params: Dict) -> ActionResult:
        """访问URL"""
        url = params.get("url")
        
        if not url:
            # 尝试从命令中提取URL
            import re
            url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(?:com|org|net|cn|io)[^\s]*)'
            match = re.search(url_pattern, command)
            if match:
                url = match.group(1)
        
        if not url:
            return ActionResult(False, "browser.navigate", "请指定网址")
        
        # 补全协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        try:
            webbrowser.open(url)
            
            self._log("navigate", f"Opened: {url}")
            
            return ActionResult(
                success=True,
                action="browser.navigate",
                message=f"🌐 已打开: {url}",
                data={"url": url}
            )
        except Exception as e:
            return ActionResult(False, "browser.navigate", f"打开失败: {e}", error=str(e))
    
    def _open_browser(self, params: Dict) -> ActionResult:
        """打开浏览器"""
        try:
            webbrowser.open("about:blank")
            
            return ActionResult(
                success=True,
                action="browser.open",
                message="🌐 浏览器已打开"
            )
        except Exception as e:
            return ActionResult(False, "browser.open", f"打开失败: {e}", error=str(e))

