"""
浏览器执行器 - 处理浏览器相关操作
"""
import webbrowser
import urllib.parse
from typing import Any, Dict

from .base import BaseExecutor, ExecutorResult


class BrowserExecutor(BaseExecutor):
    """
    浏览器执行器
    
    处理打开浏览器、搜索、访问URL等操作
    """
    
    name = "browser"
    supported_operations = [
        "browser.open", "browser.search", "browser.navigate",
        "browser.bookmark",
    ]
    
    # 搜索引擎配置
    SEARCH_ENGINES = {
        "google": "https://www.google.com/search?q={}",
        "bing": "https://www.bing.com/search?q={}",
        "baidu": "https://www.baidu.com/s?wd={}",
        "duckduckgo": "https://duckduckgo.com/?q={}",
        "yahoo": "https://search.yahoo.com/search?p={}",
        "github": "https://github.com/search?q={}",
        "stackoverflow": "https://stackoverflow.com/search?q={}",
        "youtube": "https://www.youtube.com/results?search_query={}",
        "bilibili": "https://search.bilibili.com/all?keyword={}",
        "zhihu": "https://www.zhihu.com/search?type=content&q={}",
        "taobao": "https://s.taobao.com/search?q={}",
        "jd": "https://search.jd.com/Search?keyword={}",
    }
    
    # 默认搜索引擎
    DEFAULT_ENGINE = "google"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.default_engine = self.DEFAULT_ENGINE
    
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """执行浏览器操作"""
        try:
            if operation == "browser.open":
                return self._open_browser(parameters)
            elif operation == "browser.search":
                return self._search(parameters)
            elif operation == "browser.navigate":
                return self._navigate(parameters)
            elif operation == "browser.bookmark":
                return self._bookmark(parameters)
            else:
                return ExecutorResult(False, f"不支持的操作: {operation}")
        except Exception as e:
            return ExecutorResult(False, f"操作失败: {e}")
    
    def _open_browser(self, params: Dict) -> ExecutorResult:
        """打开浏览器"""
        url = params.get("url")
        browser = params.get("browser")  # chrome, firefox, edge, safari, etc.
        new_window = params.get("new_window", False)
        
        try:
            if browser:
                # 尝试获取指定浏览器
                try:
                    browser_controller = webbrowser.get(browser)
                except webbrowser.Error:
                    # 尝试常见的浏览器名称
                    browser_aliases = {
                        "chrome": "google-chrome",
                        "firefox": "firefox",
                        "edge": "microsoft-edge",
                        "safari": "safari",
                    }
                    browser_name = browser_aliases.get(browser.lower(), browser)
                    try:
                        browser_controller = webbrowser.get(browser_name)
                    except:
                        browser_controller = webbrowser
            else:
                browser_controller = webbrowser
            
            if url:
                if new_window:
                    browser_controller.open_new(url)
                else:
                    browser_controller.open(url)
                message = f"已在浏览器中打开: {url}"
            else:
                # 打开浏览器主页
                browser_controller.open("about:blank")
                message = "浏览器已打开"
            
            self._log_action("browser_open", message)
            
            return ExecutorResult(
                success=True,
                message=message,
                data={"url": url, "browser": browser}
            )
            
        except Exception as e:
            return ExecutorResult(False, f"打开浏览器失败: {e}")
    
    def _search(self, params: Dict) -> ExecutorResult:
        """浏览器搜索"""
        query = params.get("query") or params.get("keyword") or params.get("q")
        engine = params.get("engine") or params.get("search_engine") or self.default_engine
        
        if not query:
            return ExecutorResult(False, "缺少搜索关键词")
        
        # 获取搜索引擎URL模板
        engine_lower = engine.lower()
        if engine_lower in self.SEARCH_ENGINES:
            url_template = self.SEARCH_ENGINES[engine_lower]
        else:
            # 使用默认搜索引擎
            url_template = self.SEARCH_ENGINES[self.default_engine]
            engine = self.default_engine
        
        # 编码搜索词
        encoded_query = urllib.parse.quote(query)
        search_url = url_template.format(encoded_query)
        
        try:
            webbrowser.open(search_url)
            
            self._log_action("browser_search", f"Searched: {query} on {engine}")
            
            return ExecutorResult(
                success=True,
                message=f"已使用 {engine} 搜索: {query}",
                data={
                    "query": query,
                    "engine": engine,
                    "url": search_url,
                }
            )
            
        except Exception as e:
            return ExecutorResult(False, f"搜索失败: {e}")
    
    def _navigate(self, params: Dict) -> ExecutorResult:
        """访问URL"""
        url = params.get("url")
        new_tab = params.get("new_tab", True)
        
        if not url:
            return ExecutorResult(False, "缺少URL参数")
        
        # 自动补全协议
        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
        
        try:
            if new_tab:
                webbrowser.open_new_tab(url)
            else:
                webbrowser.open(url)
            
            self._log_action("browser_navigate", f"Opened: {url}")
            
            return ExecutorResult(
                success=True,
                message=f"已访问: {url}",
                data={"url": url}
            )
            
        except Exception as e:
            return ExecutorResult(False, f"访问失败: {e}")
    
    def _bookmark(self, params: Dict) -> ExecutorResult:
        """书签操作（有限支持）"""
        action = params.get("action", "list")  # list, add, remove
        
        # 注意：浏览器书签操作需要特定浏览器扩展或配置
        # 这里只提供基本的打开书签管理页面的功能
        
        if action == "list" or action == "manage":
            # 打开浏览器书签管理
            bookmark_urls = {
                "chrome": "chrome://bookmarks/",
                "edge": "edge://favorites/",
                "firefox": "about:preferences#home",
            }
            
            # 尝试打开默认浏览器的书签
            for browser, url in bookmark_urls.items():
                try:
                    webbrowser.open(url)
                    return ExecutorResult(
                        success=True,
                        message="已打开书签管理器",
                        data={"browser": browser}
                    )
                except:
                    continue
            
            return ExecutorResult(
                success=False,
                message="无法打开书签管理器，请手动访问浏览器书签"
            )
        
        return ExecutorResult(
            success=False,
            message="书签操作暂不完全支持，请使用浏览器自带功能"
        )
    
    def set_default_engine(self, engine: str) -> bool:
        """设置默认搜索引擎"""
        if engine.lower() in self.SEARCH_ENGINES:
            self.default_engine = engine.lower()
            return True
        return False
    
    def get_available_engines(self) -> list:
        """获取可用的搜索引擎列表"""
        return list(self.SEARCH_ENGINES.keys())

