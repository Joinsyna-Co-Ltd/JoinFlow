"""
文件执行器 - 处理所有文件和目录操作
"""
import os
import shutil
import glob
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseExecutor, ExecutorResult, PermissionDeniedError, ResourceNotFoundError


class FileExecutor(BaseExecutor):
    """
    文件执行器
    
    处理文件创建、读取、写入、删除、复制、移动等操作
    """
    
    name = "file"
    supported_operations = [
        "file.create", "file.read", "file.write", "file.delete",
        "file.copy", "file.move", "file.open", "file.info",
        "file.exists", "file.find", "file.list",
        "dir.create", "dir.list", "dir.delete", "dir.navigate",
    ]
    
    def __init__(self, config=None):
        super().__init__(config)
        self.max_file_size = (config.max_file_size_mb if config else 100) * 1024 * 1024
        self.current_dir = str(Path.cwd())
    
    def execute(self, operation: str, parameters: Dict[str, Any]) -> ExecutorResult:
        """执行文件操作"""
        start_time = datetime.now()
        
        try:
            if operation == "file.create":
                result = self._create_file(parameters)
            elif operation == "file.read":
                result = self._read_file(parameters)
            elif operation == "file.write":
                result = self._write_file(parameters)
            elif operation == "file.delete":
                result = self._delete_file(parameters)
            elif operation == "file.copy":
                result = self._copy_file(parameters)
            elif operation == "file.move":
                result = self._move_file(parameters)
            elif operation == "file.open":
                result = self._open_file(parameters)
            elif operation == "file.info":
                result = self._file_info(parameters)
            elif operation == "file.exists":
                result = self._file_exists(parameters)
            elif operation == "file.find":
                result = self._find_files(parameters)
            elif operation == "file.list":
                result = self._list_files(parameters)
            elif operation == "dir.create":
                result = self._create_directory(parameters)
            elif operation == "dir.list":
                result = self._list_directory(parameters)
            elif operation == "dir.delete":
                result = self._delete_directory(parameters)
            elif operation == "dir.navigate":
                result = self._navigate_directory(parameters)
            else:
                result = ExecutorResult(
                    success=False,
                    message=f"不支持的操作: {operation}",
                    error="UnsupportedOperation"
                )
            
            # 计算执行时间
            result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return result
            
        except PermissionError as e:
            return ExecutorResult(
                success=False,
                message=f"权限被拒绝: {e}",
                error="PermissionDenied"
            )
        except FileNotFoundError as e:
            return ExecutorResult(
                success=False,
                message=f"文件未找到: {e}",
                error="FileNotFound"
            )
        except Exception as e:
            return ExecutorResult(
                success=False,
                message=f"操作失败: {e}",
                error=str(type(e).__name__)
            )
    
    def _create_file(self, params: Dict) -> ExecutorResult:
        """创建文件"""
        path = params.get("path")
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8")
        
        if not path:
            return ExecutorResult(False, "缺少文件路径参数")
        
        file_path = self._resolve_path(path)
        
        # 检查是否存在
        if file_path.exists() and not params.get("overwrite", False):
            return ExecutorResult(
                success=False,
                message=f"文件已存在: {path}",
                data={"path": str(file_path), "exists": True}
            )
        
        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入内容
        file_path.write_text(content, encoding=encoding)
        
        self._log_action("create_file", f"Created: {file_path}")
        
        return ExecutorResult(
            success=True,
            message=f"文件已创建: {path}",
            data={"path": str(file_path), "size": len(content)}
        )
    
    def _read_file(self, params: Dict) -> ExecutorResult:
        """读取文件"""
        path = params.get("path")
        encoding = params.get("encoding", "utf-8")
        
        if not path:
            return ExecutorResult(False, "缺少文件路径参数")
        
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return ExecutorResult(
                success=False,
                message=f"文件不存在: {path}",
                error="FileNotFound"
            )
        
        # 检查文件大小
        if file_path.stat().st_size > self.max_file_size:
            return ExecutorResult(
                success=False,
                message=f"文件过大，超过 {self.max_file_size // 1024 // 1024}MB 限制",
                error="FileTooLarge"
            )
        
        content = file_path.read_text(encoding=encoding)
        
        self._log_action("read_file", f"Read: {file_path}")
        
        return ExecutorResult(
            success=True,
            message=f"成功读取文件: {path}",
            data={
                "path": str(file_path),
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1
            }
        )
    
    def _write_file(self, params: Dict) -> ExecutorResult:
        """写入文件"""
        path = params.get("path")
        content = params.get("content", "")
        mode = params.get("mode", "overwrite")  # overwrite, append
        encoding = params.get("encoding", "utf-8")
        
        if not path:
            return ExecutorResult(False, "缺少文件路径参数")
        
        file_path = self._resolve_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if mode == "append" and file_path.exists():
            existing = file_path.read_text(encoding=encoding)
            content = existing + content
        
        file_path.write_text(content, encoding=encoding)
        
        self._log_action("write_file", f"Wrote: {file_path}")
        
        return ExecutorResult(
            success=True,
            message=f"文件已写入: {path}",
            data={"path": str(file_path), "size": len(content)}
        )
    
    def _delete_file(self, params: Dict) -> ExecutorResult:
        """删除文件"""
        path = params.get("path")
        
        if not path:
            return ExecutorResult(False, "缺少文件路径参数")
        
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return ExecutorResult(
                success=False,
                message=f"文件不存在: {path}",
                error="FileNotFound"
            )
        
        if file_path.is_dir():
            return ExecutorResult(
                success=False,
                message="目标是目录，请使用 dir.delete 操作",
                error="InvalidOperation"
            )
        
        file_path.unlink()
        
        self._log_action("delete_file", f"Deleted: {file_path}")
        
        return ExecutorResult(
            success=True,
            message=f"文件已删除: {path}"
        )
    
    def _copy_file(self, params: Dict) -> ExecutorResult:
        """复制文件"""
        src = params.get("source") or params.get("path")
        dst = params.get("destination") or params.get("target")
        
        if not src or not dst:
            return ExecutorResult(False, "缺少源路径或目标路径")
        
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        
        if not src_path.exists():
            return ExecutorResult(False, f"源文件不存在: {src}")
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)
        
        self._log_action("copy_file", f"Copied: {src_path} -> {dst_path}")
        
        return ExecutorResult(
            success=True,
            message=f"复制成功: {src} -> {dst}",
            data={"source": str(src_path), "destination": str(dst_path)}
        )
    
    def _move_file(self, params: Dict) -> ExecutorResult:
        """移动/重命名文件"""
        src = params.get("source") or params.get("path")
        dst = params.get("destination") or params.get("target")
        
        if not src or not dst:
            return ExecutorResult(False, "缺少源路径或目标路径")
        
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        
        if not src_path.exists():
            return ExecutorResult(False, f"源文件不存在: {src}")
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        
        self._log_action("move_file", f"Moved: {src_path} -> {dst_path}")
        
        return ExecutorResult(
            success=True,
            message=f"移动成功: {src} -> {dst}",
            data={"source": str(src_path), "destination": str(dst_path)}
        )
    
    def _open_file(self, params: Dict) -> ExecutorResult:
        """使用默认程序打开文件"""
        import platform
        import subprocess
        
        path = params.get("path")
        
        if not path:
            return ExecutorResult(False, "缺少文件路径参数")
        
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return ExecutorResult(False, f"文件不存在: {path}")
        
        system = platform.system()
        
        try:
            if system == "Windows":
                os.startfile(str(file_path))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(file_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(file_path)], check=True)
            
            self._log_action("open_file", f"Opened: {file_path}")
            
            return ExecutorResult(
                success=True,
                message=f"已打开文件: {path}",
                data={"path": str(file_path)}
            )
        except Exception as e:
            return ExecutorResult(False, f"打开文件失败: {e}")
    
    def _file_info(self, params: Dict) -> ExecutorResult:
        """获取文件信息"""
        path = params.get("path")
        
        if not path:
            return ExecutorResult(False, "缺少文件路径参数")
        
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return ExecutorResult(False, f"文件不存在: {path}")
        
        stat = file_path.stat()
        
        info = {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size": stat.st_size,
            "size_human": self._human_size(stat.st_size),
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
        }
        
        # 计算文件哈希（小文件）
        if file_path.is_file() and stat.st_size < 10 * 1024 * 1024:  # < 10MB
            info["md5"] = hashlib.md5(file_path.read_bytes()).hexdigest()
        
        return ExecutorResult(
            success=True,
            message=f"文件信息: {path}",
            data=info
        )
    
    def _file_exists(self, params: Dict) -> ExecutorResult:
        """检查文件是否存在"""
        path = params.get("path")
        
        if not path:
            return ExecutorResult(False, "缺少文件路径参数")
        
        file_path = self._resolve_path(path)
        exists = file_path.exists()
        
        return ExecutorResult(
            success=True,
            message=f"文件{'存在' if exists else '不存在'}: {path}",
            data={"path": str(file_path), "exists": exists}
        )
    
    def _find_files(self, params: Dict) -> ExecutorResult:
        """查找文件"""
        pattern = params.get("pattern") or params.get("query")
        search_path = params.get("path") or params.get("directory") or "."
        recursive = params.get("recursive", True)
        file_type = params.get("file_type")
        max_results = params.get("max_results", 100)
        
        if not pattern:
            return ExecutorResult(False, "缺少搜索模式")
        
        base_path = self._resolve_path(search_path)
        
        if not base_path.exists():
            return ExecutorResult(False, f"目录不存在: {search_path}")
        
        # 构建glob模式
        if file_type:
            pattern = f"*.{file_type.lstrip('.')}"
        
        if recursive:
            glob_pattern = f"**/{pattern}"
        else:
            glob_pattern = pattern
        
        results = []
        for match in base_path.glob(glob_pattern):
            if len(results) >= max_results:
                break
            
            stat = match.stat()
            results.append({
                "path": str(match),
                "name": match.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_dir": match.is_dir(),
            })
        
        self._log_action("find_files", f"Found {len(results)} files matching: {pattern}")
        
        return ExecutorResult(
            success=True,
            message=f"找到 {len(results)} 个匹配项",
            data={"results": results, "pattern": pattern, "count": len(results)}
        )
    
    def _list_files(self, params: Dict) -> ExecutorResult:
        """列出目录中的文件"""
        return self._list_directory(params)
    
    def _create_directory(self, params: Dict) -> ExecutorResult:
        """创建目录"""
        path = params.get("path") or params.get("directory")
        
        if not path:
            return ExecutorResult(False, "缺少目录路径参数")
        
        dir_path = self._resolve_path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        self._log_action("create_directory", f"Created: {dir_path}")
        
        return ExecutorResult(
            success=True,
            message=f"目录已创建: {path}",
            data={"path": str(dir_path)}
        )
    
    def _list_directory(self, params: Dict) -> ExecutorResult:
        """列出目录内容"""
        path = params.get("path") or params.get("directory") or "."
        include_hidden = params.get("include_hidden", False)
        sort_by = params.get("sort_by", "name")  # name, size, modified
        
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            return ExecutorResult(False, f"目录不存在: {path}")
        
        if not dir_path.is_dir():
            return ExecutorResult(False, f"不是目录: {path}")
        
        items = []
        for item in dir_path.iterdir():
            if not include_hidden and item.name.startswith('.'):
                continue
            
            stat = item.stat()
            items.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": stat.st_size,
                "size_human": self._human_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # 排序
        if sort_by == "size":
            items.sort(key=lambda x: x["size"], reverse=True)
        elif sort_by == "modified":
            items.sort(key=lambda x: x["modified"], reverse=True)
        else:
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        return ExecutorResult(
            success=True,
            message=f"目录 {path} 包含 {len(items)} 项",
            data={
                "path": str(dir_path),
                "items": items,
                "count": len(items),
                "dirs": sum(1 for i in items if i["is_dir"]),
                "files": sum(1 for i in items if not i["is_dir"]),
            }
        )
    
    def _delete_directory(self, params: Dict) -> ExecutorResult:
        """删除目录"""
        path = params.get("path") or params.get("directory")
        force = params.get("force", False)
        
        if not path:
            return ExecutorResult(False, "缺少目录路径参数")
        
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            return ExecutorResult(False, f"目录不存在: {path}")
        
        if not dir_path.is_dir():
            return ExecutorResult(False, f"不是目录: {path}")
        
        # 检查是否为空
        if not force and any(dir_path.iterdir()):
            return ExecutorResult(
                success=False,
                message="目录不为空，需要设置 force=true 强制删除",
                data={"path": str(dir_path), "empty": False}
            )
        
        shutil.rmtree(dir_path)
        
        self._log_action("delete_directory", f"Deleted: {dir_path}")
        
        return ExecutorResult(
            success=True,
            message=f"目录已删除: {path}"
        )
    
    def _navigate_directory(self, params: Dict) -> ExecutorResult:
        """导航到目录"""
        path = params.get("path") or params.get("directory")
        
        if not path:
            return ExecutorResult(False, "缺少目录路径参数")
        
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            return ExecutorResult(False, f"目录不存在: {path}")
        
        if not dir_path.is_dir():
            return ExecutorResult(False, f"不是目录: {path}")
        
        self.current_dir = str(dir_path)
        
        self._log_action("navigate", f"Changed to: {dir_path}")
        
        return ExecutorResult(
            success=True,
            message=f"已切换到: {path}",
            data={"path": str(dir_path)}
        )
    
    def _resolve_path(self, path: str) -> Path:
        """解析路径"""
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = Path(self.current_dir) / p
        return p.resolve()
    
    def _human_size(self, size: int) -> str:
        """人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

