"""
Enhanced Browser Agent with LLM-powered Analysis
=================================================

类似 browser-use 的增强浏览器 Agent，提供：
- LLM 驱动的页面内容分析和总结
- 智能信息提取（根据用户需求）
- 页面元素识别和交互
- 多标签管理
- 自动任务执行
"""

import asyncio
import base64
import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List, Dict
from urllib.parse import urlparse, urljoin
import logging

logger = logging.getLogger(__name__)


@dataclass
class PageElement:
    """页面元素"""
    tag: str
    text: str
    href: Optional[str] = None
    xpath: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)
    clickable: bool = False
    input_type: Optional[str] = None


@dataclass  
class ExtractedData:
    """提取的页面数据"""
    url: str
    title: str
    main_content: str
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)
    links: List[Dict] = field(default_factory=list)
    images: List[Dict] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    raw_html: Optional[str] = None


@dataclass
class BrowserTask:
    """浏览器任务"""
    task_type: str  # "navigate", "extract", "analyze", "interact", "search", "multi_page"
    url: Optional[str] = None
    query: Optional[str] = None
    selector: Optional[str] = None
    action: Optional[str] = None
    extract_rules: Optional[Dict] = None
    analysis_prompt: Optional[str] = None


class EnhancedBrowserAgent:
    """
    增强版浏览器 Agent
    
    功能：
    - 访问网页并提取内容
    - 使用 LLM 分析和总结页面内容
    - 智能提取用户需要的信息
    - 页面元素识别和交互
    - 多步骤自动化任务
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._headless = headless
        self._timeout = timeout
        self._history: List[str] = []
        
    async def _ensure_browser(self) -> None:
        """确保浏览器已初始化"""
        if self._page is not None:
            return
            
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self._timeout)
            
            logger.info("Browser initialized successfully")
            
        except ImportError:
            raise RuntimeError(
                "Playwright is required. Install it with: pip install playwright && playwright install"
            )
    
    async def close(self) -> None:
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
    
    # =============================
    # 核心功能：导航和内容提取
    # =============================
    
    async def navigate(self, url: str, wait_for: str = "domcontentloaded") -> ExtractedData:
        """
        导航到 URL 并提取页面内容
        
        Args:
            url: 目标 URL
            wait_for: 等待条件 (domcontentloaded, load, networkidle)
        
        Returns:
            ExtractedData: 提取的页面数据
        """
        await self._ensure_browser()
        
        logger.info(f"Navigating to: {url}")
        await self._page.goto(url, wait_until=wait_for)
        await self._page.wait_for_timeout(1500)  # 等待动态内容
        
        self._history.append(url)
        
        return await self.extract_page_content()
    
    async def extract_page_content(self) -> ExtractedData:
        """
        提取当前页面的完整内容
        
        Returns:
            ExtractedData: 包含标题、正文、链接、图片、表格等的数据
        """
        await self._ensure_browser()
        
        url = self._page.url
        title = await self._page.title()
        
        # 提取主要文本内容
        main_content = await self._page.evaluate("""
            () => {
                // 移除不需要的元素
                const removeSelectors = 'script, style, noscript, iframe, nav, header, footer, .ad, .ads, .advertisement, .sidebar, .comment, .comments';
                document.querySelectorAll(removeSelectors).forEach(el => el.remove());
                
                // 优先获取主要内容区域
                const mainSelectors = ['main', 'article', '[role="main"]', '.content', '#content', '.post', '.article', '.main-content'];
                for (const selector of mainSelectors) {
                    const el = document.querySelector(selector);
                    if (el && el.innerText.trim().length > 200) {
                        return el.innerText.trim();
                    }
                }
                
                return document.body.innerText.trim();
            }
        """)
        
        # 提取链接
        links = await self._page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    const text = a.innerText.trim();
                    const href = a.href;
                    if (text && href && !href.startsWith('javascript:')) {
                        links.push({
                            text: text.substring(0, 200),
                            href: href,
                            title: a.title || ''
                        });
                    }
                });
                return links.slice(0, 50);
            }
        """)
        
        # 提取图片
        images = await self._page.evaluate("""
            () => {
                const images = [];
                document.querySelectorAll('img[src]').forEach(img => {
                    if (img.width > 100 && img.height > 100) {
                        images.push({
                            src: img.src,
                            alt: img.alt || '',
                            width: img.width,
                            height: img.height
                        });
                    }
                });
                return images.slice(0, 20);
            }
        """)
        
        # 提取表格
        tables = await self._page.evaluate("""
            () => {
                const tables = [];
                document.querySelectorAll('table').forEach(table => {
                    const rows = [];
                    table.querySelectorAll('tr').forEach(tr => {
                        const cells = [];
                        tr.querySelectorAll('th, td').forEach(cell => {
                            cells.push(cell.innerText.trim());
                        });
                        if (cells.length > 0) rows.push(cells);
                    });
                    if (rows.length > 0) tables.push(rows);
                });
                return tables.slice(0, 5);
            }
        """)
        
        # 提取元数据
        metadata = await self._page.evaluate("""
            () => {
                const meta = {};
                document.querySelectorAll('meta').forEach(m => {
                    const name = m.name || m.getAttribute('property');
                    const content = m.content;
                    if (name && content) {
                        meta[name] = content;
                    }
                });
                return meta;
            }
        """)
        
        return ExtractedData(
            url=url,
            title=title,
            main_content=self._clean_text(main_content)[:15000],
            links=links,
            images=images,
            tables=tables,
            metadata=metadata
        )
    
    # =============================
    # LLM 驱动的智能分析
    # =============================
    
    async def analyze_page(
        self, 
        analysis_prompt: str = None,
        extract_type: str = "summary"
    ) -> Dict:
        """
        使用 LLM 分析当前页面内容
        
        Args:
            analysis_prompt: 自定义分析提示词
            extract_type: 提取类型 (summary, key_points, specific, qa)
        
        Returns:
            Dict: 分析结果
        """
        from .model_manager import get_model_manager, AgentType
        
        # 先提取页面内容
        page_data = await self.extract_page_content()
        
        # 构建分析提示词
        if analysis_prompt:
            prompt = f"""请根据以下网页内容回答问题或执行任务。

网页标题: {page_data.title}
网页 URL: {page_data.url}

网页内容:
{page_data.main_content[:8000]}

用户请求: {analysis_prompt}

请直接给出分析结果，用中文回答。"""
        
        elif extract_type == "summary":
            prompt = f"""请总结以下网页的主要内容。

网页标题: {page_data.title}
网页 URL: {page_data.url}

网页内容:
{page_data.main_content[:8000]}

请用中文提供：
1. 一句话概述（30字以内）
2. 主要内容摘要（200字以内）
3. 关键信息点（列表形式，最多5点）"""
        
        elif extract_type == "key_points":
            prompt = f"""请从以下网页内容中提取关键信息点。

网页标题: {page_data.title}
网页内容:
{page_data.main_content[:8000]}

请列出最重要的信息点（5-10个），每个点用一句话概括。"""
        
        else:
            prompt = f"""请分析以下网页内容。

网页标题: {page_data.title}
网页内容:
{page_data.main_content[:8000]}

请提供详细分析。"""
        
        # 调用 LLM
        manager = get_model_manager()
        try:
            analysis = manager.call_llm_sync(
                AgentType.BROWSER,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            return {
                "success": True,
                "url": page_data.url,
                "title": page_data.title,
                "analysis": analysis,
                "page_data": {
                    "links_count": len(page_data.links),
                    "images_count": len(page_data.images),
                    "tables_count": len(page_data.tables)
                }
            }
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": page_data.url,
                "title": page_data.title,
                "fallback_summary": page_data.main_content[:500]
            }
    
    async def smart_extract(
        self, 
        url: str, 
        user_query: str
    ) -> Dict:
        """
        智能提取：根据用户查询从网页提取相关信息
        
        Args:
            url: 目标 URL
            user_query: 用户的查询/需求描述
        
        Returns:
            Dict: 提取的信息
        """
        from .model_manager import get_model_manager, AgentType
        
        # 导航到页面
        await self.navigate(url)
        page_data = await self.extract_page_content()
        
        # 使用 LLM 根据用户需求提取信息
        prompt = f"""你是一个智能信息提取助手。请根据用户的需求，从网页内容中提取相关信息。

用户需求: {user_query}

网页信息:
- 标题: {page_data.title}
- URL: {page_data.url}

网页内容:
{page_data.main_content[:10000]}

相关链接:
{json.dumps(page_data.links[:10], ensure_ascii=False, indent=2)}

请提取用户需要的信息，并以结构化的方式呈现。如果信息不在页面中，请明确说明。
用中文回答。"""

        manager = get_model_manager()
        try:
            result = manager.call_llm_sync(
                AgentType.BROWSER,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.2
            )
            
            return {
                "success": True,
                "query": user_query,
                "url": page_data.url,
                "title": page_data.title,
                "extracted_info": result,
                "source_links": page_data.links[:10]
            }
        except Exception as e:
            logger.error(f"Smart extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": page_data.url,
                "raw_content": page_data.main_content[:2000]
            }
    
    # =============================
    # 搜索和多页面操作
    # =============================
    
    async def search_and_analyze(
        self, 
        query: str, 
        num_results: int = 3,
        analyze: bool = True
    ) -> Dict:
        """
        搜索并分析多个结果页面
        
        Args:
            query: 搜索关键词
            num_results: 要分析的结果数量
            analyze: 是否使用 LLM 分析
        
        Returns:
            Dict: 搜索结果和分析
        """
        await self._ensure_browser()
        
        search_results = []
        
        # 对查询进行 URL 编码
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)
        
        # 尝试多个搜索引擎
        search_engines = [
            {
                "name": "Bing",
                "url": f"https://cn.bing.com/search?q={encoded_query}",
                "extract": """
                    () => {
                        const results = [];
                        // 尝试多种 Bing 搜索结果选择器
                        const selectors = [
                            'li.b_algo',           // 标准结果
                            '.b_algo',             // 新版结果
                            'div.b_algo',          // div 版本
                            '.b_results > li'      // 结果列表
                        ];
                        
                        for (const selector of selectors) {
                            document.querySelectorAll(selector).forEach(item => {
                                // 尝试多种链接选择器
                                const link = item.querySelector('h2 a') || 
                                            item.querySelector('h3 a') || 
                                            item.querySelector('a.tilk') ||
                                            item.querySelector('a[href^="http"]');
                                // 尝试多种摘要选择器
                                const snippet = item.querySelector('.b_caption p') || 
                                               item.querySelector('.b_caption') ||
                                               item.querySelector('p') ||
                                               item.querySelector('.b_lineclamp2');
                                if (link && link.href && !link.href.includes('bing.com/ck/a')) {
                                    results.push({
                                        title: link.innerText.trim() || link.textContent.trim(),
                                        url: link.href,
                                        snippet: snippet ? snippet.innerText.trim() : ''
                                    });
                                } else if (link && link.href) {
                                    // 即使是 bing 跟踪链接也保留，后面会处理重定向
                                    results.push({
                                        title: link.innerText.trim() || link.textContent.trim(),
                                        url: link.href,
                                        snippet: snippet ? snippet.innerText.trim() : ''
                                    });
                                }
                            });
                            if (results.length > 0) break;
                        }
                        return results;
                    }
                """
            },
            {
                "name": "Baidu",
                "url": f"https://www.baidu.com/s?wd={encoded_query}",
                "extract": """
                    () => {
                        const results = [];
                        // 尝试多种百度搜索结果选择器
                        const selectors = [
                            '.result.c-container',     // 标准结果
                            '.c-container',            // 新版结果
                            '#content_left > div',     // 内容区域
                            '.result'                  // 旧版结果
                        ];
                        
                        for (const selector of selectors) {
                            document.querySelectorAll(selector).forEach(item => {
                                // 尝试多种链接选择器
                                const link = item.querySelector('h3 a') || 
                                            item.querySelector('a[href^="http"]') ||
                                            item.querySelector('.t a');
                                // 尝试多种摘要选择器
                                const snippet = item.querySelector('.c-abstract') || 
                                               item.querySelector('.content-right_8Zs40') ||
                                               item.querySelector('.c-span-last') ||
                                               item.querySelector('span.content-right_8Zs40');
                                if (link && link.href) {
                                    results.push({
                                        title: link.innerText.trim() || link.textContent.trim(),
                                        url: link.href,
                                        snippet: snippet ? snippet.innerText.trim() : ''
                                    });
                                }
                            });
                            if (results.length > 0) break;
                        }
                        return results;
                    }
                """
            }
        ]
        
        for engine in search_engines:
            try:
                logger.info(f"Trying search engine: {engine['name']}")
                await self._page.goto(engine["url"], wait_until="domcontentloaded")
                await self._page.wait_for_timeout(2000)
                
                search_results = await self._page.evaluate(engine["extract"])
                
                if search_results and len(search_results) > 0:
                    logger.info(f"Found {len(search_results)} results from {engine['name']}")
                    break
            except Exception as e:
                logger.warning(f"Search engine {engine['name']} failed: {e}")
                continue
        
        # 如果所有搜索引擎都失败，尝试通用提取
        if not search_results:
            logger.warning("All search engines failed, trying generic extraction")
            search_results = await self._page.evaluate("""
                () => {
                    const results = [];
                    document.querySelectorAll('a').forEach(a => {
                        const href = a.href;
                        const text = a.innerText.trim();
                        if (href && text && 
                            !href.includes('bing.com') && 
                            !href.includes('baidu.com') &&
                            href.startsWith('http') &&
                            text.length > 10 &&
                            text.length < 200) {
                            results.push({
                                title: text,
                                url: href,
                                snippet: ''
                            });
                        }
                    });
                    return results.slice(0, 10);
                }
            """)
        
        # 分析前 N 个结果
        analyzed_results = []
        for i, result in enumerate(search_results[:num_results]):
            try:
                url = result['url']
                logger.info(f"Analyzing result {i+1}: {url[:60]}...")
                
                # 处理 Bing 跟踪链接 - 直接导航并等待重定向
                try:
                    await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await self._page.wait_for_timeout(2000)
                    
                    # 获取重定向后的实际 URL
                    actual_url = self._page.url
                    result['actual_url'] = actual_url
                    logger.info(f"Redirected to: {actual_url[:60]}...")
                    
                except Exception as nav_error:
                    logger.warning(f"Navigation error: {nav_error}, retrying...")
                    # 重试一次
                    await self._page.goto(url, wait_until="networkidle", timeout=20000)
                    await self._page.wait_for_timeout(1000)
                    result['actual_url'] = self._page.url
                
                if analyze:
                    analysis = await self.analyze_page(
                        analysis_prompt=f"请总结这个页面与'{query}'相关的主要内容"
                    )
                    result['analysis'] = analysis.get('analysis', '')
                else:
                    page_data = await self.extract_page_content()
                    result['content'] = page_data.main_content[:1000]
                    result['title'] = page_data.title  # 更新为实际页面标题
                
                analyzed_results.append(result)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {result.get('url', 'unknown')}: {e}")
                result['error'] = str(e)
                # 即使失败也保留搜索结果的基本信息
                if result.get('snippet'):
                    result['content'] = result['snippet']
                analyzed_results.append(result)
        
        # 生成综合分析
        if analyze and analyzed_results:
            from .model_manager import get_model_manager, AgentType
            
            combined_content = "\n\n".join([
                f"【{r.get('title', 'Unknown')}】\n{r.get('analysis', r.get('content', ''))[:500]}"
                for r in analyzed_results if 'error' not in r
            ])
            
            summary_prompt = f"""请根据以下多个网页的分析结果，对"{query}"这个主题进行综合总结。

搜索结果分析:
{combined_content}

请提供：
1. 综合概述（100字以内）
2. 主要发现（3-5点）
3. 相关建议或结论

用中文回答。"""

            manager = get_model_manager()
            try:
                final_summary = manager.call_llm_sync(
                    AgentType.BROWSER,
                    messages=[{"role": "user", "content": summary_prompt}],
                    max_tokens=1000,
                    temperature=0.3
                )
            except:
                final_summary = "综合分析失败，请查看各页面的单独分析。"
        else:
            final_summary = None
        
        return {
            "query": query,
            "total_results": len(search_results),
            "analyzed_count": len(analyzed_results),
            "results": analyzed_results,
            "final_summary": final_summary
        }
    
    # =============================
    # 页面交互功能
    # =============================
    
    async def get_interactive_elements(self) -> List[PageElement]:
        """
        获取页面上的可交互元素
        
        Returns:
            List[PageElement]: 可交互元素列表
        """
        await self._ensure_browser()
        
        elements = await self._page.evaluate("""
            () => {
                const elements = [];
                
                // 按钮
                document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]').forEach((el, idx) => {
                    elements.push({
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText.trim() || el.value || '',
                        xpath: `//${el.tagName.toLowerCase()}[${idx + 1}]`,
                        clickable: true,
                        type: 'button'
                    });
                });
                
                // 链接
                document.querySelectorAll('a[href]').forEach((el, idx) => {
                    if (el.innerText.trim()) {
                        elements.push({
                            tag: 'a',
                            text: el.innerText.trim().substring(0, 100),
                            href: el.href,
                            xpath: `//a[${idx + 1}]`,
                            clickable: true,
                            type: 'link'
                        });
                    }
                });
                
                // 输入框
                document.querySelectorAll('input[type="text"], input[type="search"], input[type="email"], textarea').forEach((el, idx) => {
                    elements.push({
                        tag: el.tagName.toLowerCase(),
                        text: el.placeholder || el.name || '',
                        xpath: `//${el.tagName.toLowerCase()}[${idx + 1}]`,
                        clickable: false,
                        input_type: el.type || 'text',
                        type: 'input'
                    });
                });
                
                return elements.slice(0, 100);
            }
        """)
        
        return [PageElement(**el) for el in elements]
    
    async def click_element(self, selector: str) -> bool:
        """点击元素"""
        await self._ensure_browser()
        try:
            await self._page.click(selector)
            await self._page.wait_for_timeout(1000)
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    async def type_text(self, selector: str, text: str) -> bool:
        """在元素中输入文本"""
        await self._ensure_browser()
        try:
            await self._page.fill(selector, text)
            return True
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False
    
    async def take_screenshot(self, full_page: bool = False) -> str:
        """截图并返回 base64"""
        await self._ensure_browser()
        screenshot_bytes = await self._page.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode()
    
    # =============================
    # 高级功能：自动化任务
    # =============================
    
    async def execute_task(self, task_description: str) -> Dict:
        """
        根据自然语言描述执行浏览器任务
        
        Args:
            task_description: 任务描述，如 "打开百度搜索今天的新闻"
        
        Returns:
            Dict: 任务执行结果
        """
        from .model_manager import get_model_manager, AgentType
        
        # 使用 LLM 解析任务
        parse_prompt = f"""你是一个浏览器自动化助手。请解析用户的任务，生成执行计划。

用户任务: {task_description}

请以 JSON 格式返回执行计划，包含以下步骤类型：
- navigate: 导航到 URL
- search: 搜索
- extract: 提取内容
- analyze: 分析页面
- click: 点击元素
- type: 输入文本

示例格式：
{{
    "steps": [
        {{"type": "navigate", "url": "https://example.com"}},
        {{"type": "search", "query": "关键词"}},
        {{"type": "analyze", "prompt": "总结内容"}}
    ]
}}

只返回 JSON，不要其他内容。"""

        manager = get_model_manager()
        try:
            plan_json = manager.call_llm_sync(
                AgentType.BROWSER,
                messages=[{"role": "user", "content": parse_prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            # 解析 JSON
            json_match = re.search(r'\{[\s\S]*\}', plan_json)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                # 默认执行搜索
                plan = {"steps": [{"type": "search", "query": task_description}]}
            
        except Exception as e:
            logger.warning(f"Task parsing failed: {e}")
            plan = {"steps": [{"type": "search", "query": task_description}]}
        
        # 执行计划
        results = []
        for step in plan.get("steps", []):
            step_type = step.get("type")
            
            try:
                if step_type == "navigate":
                    data = await self.navigate(step.get("url"))
                    results.append({"step": "navigate", "url": data.url, "title": data.title})
                    
                elif step_type == "search":
                    data = await self.search_and_analyze(step.get("query"), num_results=2)
                    results.append({"step": "search", "query": step.get("query"), "data": data})
                    
                elif step_type == "extract":
                    data = await self.extract_page_content()
                    results.append({"step": "extract", "content": data.main_content[:1000]})
                    
                elif step_type == "analyze":
                    data = await self.analyze_page(analysis_prompt=step.get("prompt"))
                    results.append({"step": "analyze", "analysis": data.get("analysis")})
                    
                elif step_type == "click":
                    success = await self.click_element(step.get("selector"))
                    results.append({"step": "click", "success": success})
                    
                elif step_type == "type":
                    success = await self.type_text(step.get("selector"), step.get("text"))
                    results.append({"step": "type", "success": success})
                    
            except Exception as e:
                results.append({"step": step_type, "error": str(e)})
        
        return {
            "task": task_description,
            "plan": plan,
            "results": results,
            "success": len([r for r in results if "error" not in r]) > 0
        }
    
    # =============================
    # 工具方法
    # =============================
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned = []
        prev_line = None
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and line != prev_line:
                cleaned.append(line)
                prev_line = line
        
        return '\n'.join(cleaned)


# 便捷函数
async def browse_and_analyze(url: str, query: str = None) -> Dict:
    """
    便捷函数：访问网页并分析
    
    Args:
        url: 目标 URL
        query: 可选的查询需求
    
    Returns:
        Dict: 分析结果
    """
    agent = EnhancedBrowserAgent(headless=True)
    try:
        await agent.navigate(url)
        if query:
            return await agent.analyze_page(analysis_prompt=query)
        else:
            return await agent.analyze_page(extract_type="summary")
    finally:
        await agent.close()


async def search_web(query: str, num_results: int = 3) -> Dict:
    """
    便捷函数：搜索网页并分析
    
    Args:
        query: 搜索关键词
        num_results: 分析结果数量
    
    Returns:
        Dict: 搜索结果和分析
    """
    agent = EnhancedBrowserAgent(headless=True)
    try:
        return await agent.search_and_analyze(query, num_results=num_results)
    finally:
        await agent.close()

