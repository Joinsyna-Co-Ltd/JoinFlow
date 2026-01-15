"""
搜索执行器
"""
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

from .base import BaseExecutor
from ..core.runtime import ActionResult


class SearchExecutor(BaseExecutor):
    """搜索执行器"""
    
    name = "search"
    
    def execute(self, action: str, command: str, params: Dict) -> ActionResult:
        """执行搜索操作"""
        try:
            if action == "search.file":
                return self._search_files(command, params)
            elif action == "search.content":
                return self._search_content(command, params)
            elif action == "search.recent":
                return self._search_recent(command, params)
            else:
                return ActionResult(False, action, f"不支持的操作: {action}")
        except Exception as e:
            return ActionResult(False, action, f"搜索失败: {e}", error=str(e))
    
    def _search_files(self, command: str, params: Dict) -> ActionResult:
        """搜索文件"""
        query = params.get("query") or self._extract_query(command)
        search_path = params.get("path") or str(Path.home())
        file_type = params.get("type")
        max_results = params.get("limit", 50)
        
        if not query:
            return ActionResult(False, "search.file", "请指定搜索关键词")
        
        # 从命令中提取文件类型
        type_patterns = {
            "pdf": ".pdf",
            "word": ".docx",
            "doc": ".doc",
            "文档": ".docx",
            "excel": ".xlsx",
            "表格": ".xlsx",
            "图片": ".jpg",
            "照片": ".jpg",
            "视频": ".mp4",
            "音乐": ".mp3",
            "txt": ".txt",
            "文本": ".txt",
        }
        
        for key, ext in type_patterns.items():
            if key in command.lower():
                file_type = ext
                break
        
        # 确定搜索路径
        path_keywords = {
            "桌面": "Desktop",
            "文档": "Documents",
            "下载": "Downloads",
            "图片": "Pictures",
            "desktop": "Desktop",
            "documents": "Documents",
            "downloads": "Downloads",
        }
        
        for key, folder in path_keywords.items():
            if key in command.lower():
                search_path = str(Path.home() / folder)
                break
        
        base_path = Path(search_path).expanduser()
        
        if not base_path.exists():
            return ActionResult(False, "search.file", f"路径不存在: {search_path}")
        
        # 构建搜索模式
        if file_type:
            pattern = f"*{query}*{file_type}" if not file_type.startswith('.') else f"*{query}*{file_type}"
        else:
            pattern = f"*{query}*"
        
        results = []
        try:
            for match in base_path.rglob(pattern):
                if len(results) >= max_results:
                    break
                
                try:
                    stat = match.stat()
                    results.append({
                        "name": match.name,
                        "path": str(match),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "is_dir": match.is_dir(),
                    })
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            pass
        
        self._log("search", f"Found {len(results)} files for: {query}")
        
        if results:
            return ActionResult(
                success=True,
                action="search.file",
                message=f"🔍 找到 {len(results)} 个匹配项",
                data={"query": query, "results": results, "count": len(results)}
            )
        else:
            return ActionResult(
                success=True,
                action="search.file",
                message=f"未找到匹配 '{query}' 的文件",
                data={"query": query, "results": [], "count": 0}
            )
    
    def _search_content(self, command: str, params: Dict) -> ActionResult:
        """搜索文件内容"""
        query = params.get("query") or self._extract_query(command)
        search_path = params.get("path") or str(Path.cwd())
        
        if not query:
            return ActionResult(False, "search.content", "请指定搜索关键词")
        
        base_path = Path(search_path).expanduser()
        results = []
        
        text_extensions = ['.txt', '.md', '.py', '.js', '.json', '.xml', '.html', '.css', '.log']
        
        for ext in text_extensions:
            for file_path in base_path.rglob(f"*{ext}"):
                if len(results) >= 20:
                    break
                
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if query.lower() in content.lower():
                        # 找到匹配的行
                        matches = []
                        for i, line in enumerate(content.split('\n'), 1):
                            if query.lower() in line.lower():
                                matches.append({"line": i, "text": line.strip()[:100]})
                                if len(matches) >= 3:
                                    break
                        
                        results.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "matches": matches,
                        })
                except (PermissionError, OSError):
                    continue
        
        return ActionResult(
            success=True,
            action="search.content",
            message=f"🔍 在 {len(results)} 个文件中找到匹配",
            data={"query": query, "results": results}
        )
    
    def _search_recent(self, command: str, params: Dict) -> ActionResult:
        """搜索最近修改的文件"""
        days = params.get("days", 7)
        search_path = params.get("path") or str(Path.home())
        file_type = params.get("type")
        
        base_path = Path(search_path).expanduser()
        cutoff = datetime.now() - timedelta(days=days)
        
        results = []
        pattern = f"*{file_type}" if file_type else "*"
        
        for file_path in base_path.rglob(pattern):
            if len(results) >= 50:
                break
            
            if not file_path.is_file():
                continue
            
            try:
                stat = file_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                if mtime >= cutoff:
                    results.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "modified": mtime.isoformat(),
                    })
            except (PermissionError, OSError):
                continue
        
        # 按修改时间排序
        results.sort(key=lambda x: x['modified'], reverse=True)
        
        return ActionResult(
            success=True,
            action="search.recent",
            message=f"📅 最近 {days} 天修改的文件 ({len(results)} 个)",
            data={"results": results, "days": days}
        )

