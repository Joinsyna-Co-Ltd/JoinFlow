"""
Browser Agent
=============

Provides web automation capabilities:
- Navigate to URLs
- Extract page content
- Fill forms and click buttons
- Take screenshots
- Execute JavaScript
"""

import asyncio
import base64
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse
import logging

from .base import (
    BaseAgent, AgentResult, AgentConfig, AgentType, 
    AgentAction, AgentStatus, Tool
)

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    """Extracted page content"""
    url: str
    title: str
    text: str
    html: Optional[str] = None
    links: list[dict] = None
    images: list[dict] = None
    metadata: dict = None
    
    def __post_init__(self):
        self.links = self.links or []
        self.images = self.images or []
        self.metadata = self.metadata or {}


@dataclass
class BrowserAction:
    """A browser action to execute"""
    action_type: str  # "navigate", "click", "type", "scroll", "screenshot", "extract"
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    wait_ms: int = 1000


class BrowserAgent(BaseAgent):
    """
    Agent for web browser automation.
    
    Capabilities:
    - Navigate to URLs and extract content
    - Interact with page elements (click, type, scroll)
    - Take screenshots
    - Execute search queries
    - Fill forms
    
    Uses Playwright for browser automation.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.BROWSER
    
    @property
    def name(self) -> str:
        return "Browser Agent"
    
    @property
    def description(self) -> str:
        return """Web browser automation agent capable of:
        - Navigating to websites and extracting content
        - Performing searches on search engines
        - Interacting with web pages (clicking, typing, scrolling)
        - Taking screenshots of pages
        - Extracting structured data from web pages
        """
    
    def can_handle(self, task: str) -> bool:
        """Check if this is a browser-related task"""
        browser_keywords = [
            "网页", "网站", "浏览", "搜索", "打开", "访问",
            "链接", "url", "http", "www", "页面", "点击",
            "web", "browse", "search", "navigate", "website",
            "google", "百度", "bing", "抓取", "爬取", "提取"
        ]
        task_lower = task.lower()
        return any(kw in task_lower for kw in browser_keywords)
    
    async def _ensure_browser(self) -> None:
        """Ensure browser is initialized"""
        if self._page is not None:
            return
            
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.config.browser_headless
            )
            self._context = await self._browser.new_context(
                viewport={
                    "width": self.config.browser_viewport_width,
                    "height": self.config.browser_viewport_height
                }
            )
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.config.browser_timeout)
            
        except ImportError:
            raise RuntimeError(
                "Playwright is required for BrowserAgent. "
                "Install it with: pip install playwright && playwright install"
            )
    
    async def _close_browser(self) -> None:
        """Close browser resources"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Execute a browser task"""
        return asyncio.get_event_loop().run_until_complete(
            self._execute_async(task, context)
        )
    
    async def _execute_async(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Async execution of browser task"""
        result = self._create_result()
        
        try:
            await self._ensure_browser()
            
            # Parse task to determine actions
            actions = self._parse_task(task, context)
            
            outputs = []
            for action in actions:
                action_result = await self._execute_action(action, result)
                if action_result:
                    outputs.append(action_result)
            
            # Combine outputs
            result.output = "\n\n".join(str(o) for o in outputs)
            result.data = outputs
            result.finalize(success=True)
            
        except Exception as e:
            self._handle_error(result, e)
        finally:
            # Keep browser open for potential follow-up actions
            pass
        
        return result
    
    def _parse_task(self, task: str, context: Optional[dict]) -> list[BrowserAction]:
        """Parse task description into browser actions"""
        actions = []
        
        # Check for URL in task
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, task)
        
        if urls:
            # Navigate to URL
            actions.append(BrowserAction(
                action_type="navigate",
                url=urls[0]
            ))
            actions.append(BrowserAction(
                action_type="extract"
            ))
        
        # Check for search intent
        search_patterns = [
            r"搜索[：:\s]*(.+)",
            r"search[:\s]+(.+)",
            r"查找[：:\s]*(.+)",
            r"google[:\s]+(.+)",
            r"百度[:\s]+(.+)",
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                actions.append(BrowserAction(
                    action_type="search",
                    value=query
                ))
                break
        
        # Default: if no specific action, try to extract info from current task
        if not actions:
            # Check if it's asking for content extraction
            if any(kw in task.lower() for kw in ["提取", "获取", "内容", "extract", "content"]):
                actions.append(BrowserAction(action_type="extract"))
            # Check for screenshot request
            elif any(kw in task.lower() for kw in ["截图", "screenshot", "截屏"]):
                actions.append(BrowserAction(action_type="screenshot"))
            else:
                # Default: search for the task content
                actions.append(BrowserAction(
                    action_type="search",
                    value=task
                ))
        
        return actions
    
    async def _execute_action(self, action: BrowserAction, result: AgentResult) -> Any:
        """Execute a single browser action"""
        
        if action.action_type == "navigate":
            return await self._navigate(action.url, result)
        
        elif action.action_type == "search":
            return await self._search(action.value, result)
        
        elif action.action_type == "extract":
            return await self._extract_content(result)
        
        elif action.action_type == "screenshot":
            return await self._take_screenshot(result)
        
        elif action.action_type == "click":
            return await self._click(action.selector, result)
        
        elif action.action_type == "type":
            return await self._type_text(action.selector, action.value, result)
        
        elif action.action_type == "scroll":
            return await self._scroll(action.value, result)
        
        return None
    
    async def _navigate(self, url: str, result: AgentResult) -> PageContent:
        """Navigate to a URL"""
        self._log_action(result, "navigate", f"Navigating to {url}", url=url)
        
        await self._page.goto(url, wait_until="domcontentloaded")
        await self._page.wait_for_timeout(1000)  # Wait for dynamic content
        
        return await self._extract_content(result)
    
    async def _search(self, query: str, result: AgentResult) -> PageContent:
        """Perform a web search"""
        self._log_action(result, "search", f"Searching for: {query}", query=query)
        
        # Use DuckDuckGo for search (no captcha)
        search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        await self._page.goto(search_url, wait_until="domcontentloaded")
        await self._page.wait_for_timeout(2000)
        
        return await self._extract_content(result)
    
    async def _extract_content(self, result: AgentResult) -> PageContent:
        """Extract content from current page"""
        self._log_action(result, "extract", "Extracting page content")
        
        # Get basic info
        url = self._page.url
        title = await self._page.title()
        
        # Extract text content
        text = await self._page.evaluate("""
            () => {
                // Remove script and style elements
                const scripts = document.querySelectorAll('script, style, noscript');
                scripts.forEach(s => s.remove());
                
                // Get main content
                const main = document.querySelector('main, article, .content, #content, .main');
                if (main) return main.innerText;
                
                return document.body.innerText;
            }
        """)
        
        # Extract links
        links = await self._page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    if (a.href && a.innerText.trim()) {
                        links.push({
                            text: a.innerText.trim().substring(0, 100),
                            href: a.href
                        });
                    }
                });
                return links.slice(0, 20);  // Limit to 20 links
            }
        """)
        
        # Clean text
        text = self._clean_text(text)
        
        return PageContent(
            url=url,
            title=title,
            text=text[:10000],  # Limit text length
            links=links,
            metadata={"extracted_at": datetime.now().isoformat()}
        )
    
    async def _take_screenshot(self, result: AgentResult) -> dict:
        """Take a screenshot of current page"""
        self._log_action(result, "screenshot", "Taking screenshot")
        
        screenshot_bytes = await self._page.screenshot(full_page=False)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
        
        return {
            "type": "screenshot",
            "url": self._page.url,
            "data": screenshot_b64,
            "format": "png"
        }
    
    async def _click(self, selector: str, result: AgentResult) -> bool:
        """Click an element"""
        self._log_action(result, "click", f"Clicking: {selector}", selector=selector)
        
        await self._page.click(selector)
        await self._page.wait_for_timeout(500)
        return True
    
    async def _type_text(self, selector: str, text: str, result: AgentResult) -> bool:
        """Type text into an element"""
        self._log_action(result, "type", f"Typing into: {selector}", selector=selector)
        
        await self._page.fill(selector, text)
        return True
    
    async def _scroll(self, direction: str, result: AgentResult) -> bool:
        """Scroll the page"""
        self._log_action(result, "scroll", f"Scrolling: {direction}")
        
        if direction == "down":
            await self._page.evaluate("window.scrollBy(0, 500)")
        elif direction == "up":
            await self._page.evaluate("window.scrollBy(0, -500)")
        elif direction == "bottom":
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        elif direction == "top":
            await self._page.evaluate("window.scrollTo(0, 0)")
        
        return True
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:  # Skip very short lines
                cleaned_lines.append(line)
        
        # Remove duplicate consecutive lines
        result = []
        prev_line = None
        for line in cleaned_lines:
            if line != prev_line:
                result.append(line)
                prev_line = line
        
        return '\n'.join(result)
    
    # -------------------------
    # Tool Interface
    # -------------------------
    
    def get_tools(self) -> list[Tool]:
        """Get tools for LLM function calling"""
        return [
            Tool(
                name="browser_navigate",
                description="Navigate to a URL and extract page content",
                func=lambda url: asyncio.get_event_loop().run_until_complete(
                    self._navigate_tool(url)
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"}
                    },
                    "required": ["url"]
                }
            ),
            Tool(
                name="browser_search",
                description="Search the web for information",
                func=lambda query: asyncio.get_event_loop().run_until_complete(
                    self._search_tool(query)
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="browser_screenshot",
                description="Take a screenshot of the current page",
                func=lambda: asyncio.get_event_loop().run_until_complete(
                    self._screenshot_tool()
                ),
                parameters={"type": "object", "properties": {}}
            ),
        ]
    
    async def _navigate_tool(self, url: str) -> str:
        """Tool wrapper for navigation"""
        await self._ensure_browser()
        result = self._create_result()
        content = await self._navigate(url, result)
        return f"Title: {content.title}\n\nContent:\n{content.text[:3000]}"
    
    async def _search_tool(self, query: str) -> str:
        """Tool wrapper for search"""
        await self._ensure_browser()
        result = self._create_result()
        content = await self._search(query, result)
        return f"Search results for '{query}':\n\n{content.text[:3000]}"
    
    async def _screenshot_tool(self) -> str:
        """Tool wrapper for screenshot"""
        await self._ensure_browser()
        result = self._create_result()
        data = await self._take_screenshot(result)
        return f"Screenshot taken of {data['url']}"
    
    def __del__(self):
        """Cleanup browser on deletion"""
        if self._browser:
            try:
                asyncio.get_event_loop().run_until_complete(self._close_browser())
            except:
                pass

