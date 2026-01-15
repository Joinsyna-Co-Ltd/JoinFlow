"""
搜索执行器 - 处理文件搜索、内容搜索
"""
import os
import re
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import BaseExecutor, ExecutorResult


class SearchExecutor(BaseExecutor):
    """
    搜索执行器
    
    处理文件搜索、内容搜索、快速定位等操作
    """
    
    name = "search"
    supported_operations = [
        "search.file", "search.content", "search.recent",
        "search.large", "search.duplicate", "search.quick",
    ]
    
    def __init__(self, config=None):
        super().__init__(config)
        self.system = platform.system()
        self.max_results = config.max_search_results if config else 100
        self.timeout = config.search_timeout if config else 30
    
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """执行搜索操作"""
        try:
            if operation == "search.file":
                return self._search_files(parameters)
            elif operation == "search.content":
                return self._search_content(parameters)
            elif operation == "search.recent":
                return self._search_recent(parameters)
            elif operation == "search.large":
                return self._search_large_files(parameters)
            elif operation == "search.duplicate":
                return self._search_duplicates(parameters)
            elif operation == "search.quick":
                return self._quick_search(parameters)
            else:
                return ExecutorResult(False, f"不支持的操作: {operation}")
        except Exception as e:
            return ExecutorResult(False, f"搜索失败: {e}")
    
    def _search_files(self, params: Dict) -> ExecutorResult:
        """搜索文件"""
        query = params.get("query") or params.get("pattern") or params.get("name")
        search_paths = params.get("paths") or params.get("directories") or [str(Path.home())]
        file_type = params.get("file_type") or params.get("extension")
        recursive = params.get("recursive", True)
        case_sensitive = params.get("case_sensitive", False)
        max_results = params.get("max_results", self.max_results)
        
        if not query:
            return ExecutorResult(False, "缺少搜索关键词")
        
        if isinstance(search_paths, str):
            search_paths = [search_paths]
        
        # 构建glob模式
        if file_type:
            if not file_type.startswith("."):
                file_type = "." + file_type
            glob_pattern = f"*{query}*{file_type}"
        else:
            glob_pattern = f"*{query}*"
        
        results = []
        
        for search_path in search_paths:
            base_path = Path(search_path).expanduser()
            if not base_path.exists():
                continue
            
            try:
                if recursive:
                    matches = base_path.rglob(glob_pattern)
                else:
                    matches = base_path.glob(glob_pattern)
                
                for match in matches:
                    if len(results) >= max_results:
                        break
                    
                    # 大小写匹配
                    if not case_sensitive:
                        if query.lower() not in match.name.lower():
                            continue
                    
                    try:
                        stat = match.stat()
                        results.append({
                            "path": str(match),
                            "name": match.name,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "is_dir": match.is_dir(),
                        })
                    except (PermissionError, OSError):
                        continue
                    
            except PermissionError:
                continue
        
        self._log_action("search_file", f"Found {len(results)} files matching: {query}")
        
        return ExecutorResult(
            success=True,
            message=f"找到 {len(results)} 个匹配文件",
            data={
                "results": results,
                "query": query,
                "count": len(results),
                "truncated": len(results) >= max_results
            }
        )
    
    def _search_content(self, params: Dict) -> ExecutorResult:
        """搜索文件内容"""
        query = params.get("query") or params.get("pattern") or params.get("text")
        search_paths = params.get("paths") or params.get("directories") or [str(Path.cwd())]
        file_types = params.get("file_types") or [".txt", ".md", ".py", ".js", ".json", ".xml", ".html", ".css", ".log"]
        case_sensitive = params.get("case_sensitive", False)
        use_regex = params.get("regex", False)
        max_results = params.get("max_results", self.max_results)
        context_lines = params.get("context_lines", 2)
        
        if not query:
            return ExecutorResult(False, "缺少搜索关键词")
        
        if isinstance(search_paths, str):
            search_paths = [search_paths]
        
        if isinstance(file_types, str):
            file_types = [file_types]
        
        # 编译搜索模式
        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(query, flags)
            except re.error as e:
                return ExecutorResult(False, f"无效的正则表达式: {e}")
        else:
            pattern = None
        
        results = []
        files_searched = 0
        
        for search_path in search_paths:
            base_path = Path(search_path).expanduser()
            if not base_path.exists():
                continue
            
            for file_type in file_types:
                glob_pattern = f"**/*{file_type}"
                
                for file_path in base_path.glob(glob_pattern):
                    if len(results) >= max_results:
                        break
                    
                    if not file_path.is_file():
                        continue
                    
                    # 跳过大文件
                    try:
                        if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                            continue
                    except:
                        continue
                    
                    matches = self._search_in_file(
                        file_path, query, pattern, case_sensitive, context_lines
                    )
                    
                    if matches:
                        results.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "matches": matches,
                            "match_count": len(matches),
                        })
                    
                    files_searched += 1
        
        self._log_action("search_content", f"Found {len(results)} files with matches for: {query}")
        
        return ExecutorResult(
            success=True,
            message=f"在 {files_searched} 个文件中找到 {len(results)} 个包含匹配内容的文件",
            data={
                "results": results,
                "query": query,
                "files_with_matches": len(results),
                "files_searched": files_searched,
            }
        )
    
    def _search_in_file(self, file_path: Path, query: str, pattern: Optional[re.Pattern],
                        case_sensitive: bool, context_lines: int) -> List[Dict]:
        """在单个文件中搜索"""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                found = False
                
                if pattern:
                    if pattern.search(line):
                        found = True
                else:
                    if case_sensitive:
                        if query in line:
                            found = True
                    else:
                        if query.lower() in line.lower():
                            found = True
                
                if found:
                    # 获取上下文
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    context = ''.join(lines[start:end])
                    
                    matches.append({
                        "line_number": i + 1,
                        "line": line.strip(),
                        "context": context.strip(),
                    })
                    
                    if len(matches) >= 10:  # 每个文件最多10个匹配
                        break
                        
        except Exception:
            pass
        
        return matches
    
    def _search_recent(self, params: Dict) -> ExecutorResult:
        """搜索最近修改的文件"""
        search_path = params.get("path") or params.get("directory") or str(Path.home())
        days = params.get("days", 7)
        file_type = params.get("file_type")
        max_results = params.get("max_results", self.max_results)
        
        base_path = Path(search_path).expanduser()
        if not base_path.exists():
            return ExecutorResult(False, f"目录不存在: {search_path}")
        
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=days)
        
        results = []
        
        glob_pattern = f"**/*{file_type}" if file_type else "**/*"
        
        for file_path in base_path.glob(glob_pattern):
            if len(results) >= max_results:
                break
            
            if not file_path.is_file():
                continue
            
            try:
                stat = file_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                if mtime >= cutoff_time:
                    results.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": mtime.isoformat(),
                    })
            except (PermissionError, OSError):
                continue
        
        # 按修改时间排序
        results.sort(key=lambda x: x["modified"], reverse=True)
        
        return ExecutorResult(
            success=True,
            message=f"找到 {len(results)} 个最近 {days} 天修改的文件",
            data={"results": results, "count": len(results)}
        )
    
    def _search_large_files(self, params: Dict) -> ExecutorResult:
        """搜索大文件"""
        search_path = params.get("path") or params.get("directory") or str(Path.home())
        min_size_mb = params.get("min_size_mb", 100)
        max_results = params.get("max_results", self.max_results)
        
        base_path = Path(search_path).expanduser()
        if not base_path.exists():
            return ExecutorResult(False, f"目录不存在: {search_path}")
        
        min_size = min_size_mb * 1024 * 1024
        results = []
        
        for file_path in base_path.rglob("*"):
            if len(results) >= max_results:
                break
            
            if not file_path.is_file():
                continue
            
            try:
                stat = file_path.stat()
                if stat.st_size >= min_size:
                    results.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / 1024 / 1024, 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
            except (PermissionError, OSError):
                continue
        
        # 按大小排序
        results.sort(key=lambda x: x["size"], reverse=True)
        
        total_size = sum(r["size"] for r in results)
        
        return ExecutorResult(
            success=True,
            message=f"找到 {len(results)} 个大于 {min_size_mb}MB 的文件",
            data={
                "results": results,
                "count": len(results),
                "total_size_mb": round(total_size / 1024 / 1024, 2),
            }
        )
    
    def _search_duplicates(self, params: Dict) -> ExecutorResult:
        """搜索重复文件"""
        import hashlib
        
        search_path = params.get("path") or params.get("directory") or str(Path.cwd())
        file_type = params.get("file_type")
        min_size = params.get("min_size", 1024)  # 最小1KB
        
        base_path = Path(search_path).expanduser()
        if not base_path.exists():
            return ExecutorResult(False, f"目录不存在: {search_path}")
        
        # 第一步：按大小分组
        size_groups: Dict[int, List[Path]] = {}
        
        glob_pattern = f"**/*{file_type}" if file_type else "**/*"
        
        for file_path in base_path.glob(glob_pattern):
            if not file_path.is_file():
                continue
            
            try:
                size = file_path.stat().st_size
                if size >= min_size:
                    if size not in size_groups:
                        size_groups[size] = []
                    size_groups[size].append(file_path)
            except (PermissionError, OSError):
                continue
        
        # 第二步：计算哈希找重复
        duplicates = []
        
        for size, files in size_groups.items():
            if len(files) < 2:
                continue
            
            # 计算哈希
            hash_groups: Dict[str, List[Path]] = {}
            
            for file_path in files:
                try:
                    file_hash = self._calculate_hash(file_path)
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file_path)
                except:
                    continue
            
            # 收集重复文件
            for file_hash, dup_files in hash_groups.items():
                if len(dup_files) > 1:
                    duplicates.append({
                        "hash": file_hash,
                        "size": size,
                        "size_mb": round(size / 1024 / 1024, 2),
                        "files": [str(f) for f in dup_files],
                        "count": len(dup_files),
                    })
        
        # 计算可节省空间
        total_wasted = sum(d["size"] * (d["count"] - 1) for d in duplicates)
        
        return ExecutorResult(
            success=True,
            message=f"找到 {len(duplicates)} 组重复文件",
            data={
                "duplicates": duplicates,
                "groups": len(duplicates),
                "wasted_space_mb": round(total_wasted / 1024 / 1024, 2),
            }
        )
    
    def _quick_search(self, params: Dict) -> ExecutorResult:
        """快速搜索（使用系统索引）"""
        query = params.get("query")
        search_type = params.get("type", "all")  # all, file, folder, app
        
        if not query:
            return ExecutorResult(False, "缺少搜索关键词")
        
        if self.system == "Windows":
            return self._windows_search(query, search_type)
        elif self.system == "Darwin":
            return self._spotlight_search(query, search_type)
        else:
            return self._locate_search(query)
    
    def _windows_search(self, query: str, search_type: str) -> ExecutorResult:
        """使用Windows搜索"""
        # 使用 PowerShell 调用 Windows Search
        ps_script = f'''
        $searcher = New-Object -ComObject Windows.Search.Search
        # 简化版本，使用 Get-ChildItem
        Get-ChildItem -Path $env:USERPROFILE -Recurse -ErrorAction SilentlyContinue | 
        Where-Object {{ $_.Name -like "*{query}*" }} | 
        Select-Object -First 50 FullName, Length, LastWriteTime |
        ConvertTo-Json
        '''
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.stdout:
                import json
                data = json.loads(result.stdout)
                if not isinstance(data, list):
                    data = [data]
                
                results = [{
                    "path": item["FullName"],
                    "name": Path(item["FullName"]).name,
                    "size": item.get("Length", 0),
                } for item in data if item]
                
                return ExecutorResult(
                    success=True,
                    message=f"找到 {len(results)} 个结果",
                    data={"results": results}
                )
        except Exception as e:
            pass
        
        # 回退到普通搜索
        return self._search_files({"query": query})
    
    def _spotlight_search(self, query: str, search_type: str) -> ExecutorResult:
        """使用macOS Spotlight搜索"""
        try:
            result = subprocess.run(
                ["mdfind", "-name", query],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            paths = result.stdout.strip().split('\n')[:50]
            
            results = []
            for path in paths:
                if path:
                    p = Path(path)
                    try:
                        stat = p.stat()
                        results.append({
                            "path": path,
                            "name": p.name,
                            "size": stat.st_size,
                            "is_dir": p.is_dir(),
                        })
                    except:
                        continue
            
            return ExecutorResult(
                success=True,
                message=f"找到 {len(results)} 个结果",
                data={"results": results}
            )
        except Exception as e:
            return ExecutorResult(False, f"Spotlight搜索失败: {e}")
    
    def _locate_search(self, query: str) -> ExecutorResult:
        """使用Linux locate搜索"""
        try:
            result = subprocess.run(
                ["locate", "-i", "-l", "50", query],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            paths = result.stdout.strip().split('\n')
            
            results = []
            for path in paths:
                if path:
                    p = Path(path)
                    try:
                        if p.exists():
                            stat = p.stat()
                            results.append({
                                "path": path,
                                "name": p.name,
                                "size": stat.st_size,
                            })
                    except:
                        continue
            
            return ExecutorResult(
                success=True,
                message=f"找到 {len(results)} 个结果",
                data={"results": results}
            )
        except Exception as e:
            return ExecutorResult(False, f"locate搜索失败: {e}")
    
    def _calculate_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """计算文件哈希（仅读取部分内容提高速度）"""
        import hashlib
        
        hasher = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            # 读取开头
            hasher.update(f.read(chunk_size))
            
            # 读取中间
            f.seek(file_path.stat().st_size // 2)
            hasher.update(f.read(chunk_size))
            
            # 读取结尾
            f.seek(-min(chunk_size, file_path.stat().st_size), 2)
            hasher.update(f.read(chunk_size))
        
        return hasher.hexdigest()

