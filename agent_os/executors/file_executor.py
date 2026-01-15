"""
文件执行器
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from .base import BaseExecutor
from ..core.runtime import ActionResult


class FileExecutor(BaseExecutor):
    """文件和目录操作执行器"""
    
    name = "file"
    
    def execute(self, action: str, command: str, params: Dict) -> ActionResult:
        """执行文件操作"""
        try:
            if action == "file.create":
                return self._create_file(command, params)
            elif action == "file.read":
                return self._read_file(command, params)
            elif action == "file.write":
                return self._write_file(command, params)
            elif action == "file.delete":
                return self._delete_file(command, params)
            elif action == "file.copy":
                return self._copy_file(command, params)
            elif action == "file.move":
                return self._move_file(command, params)
            elif action == "file.open":
                return self._open_file(command, params)
            elif action == "dir.create":
                return self._create_dir(command, params)
            elif action == "dir.list":
                return self._list_dir(command, params)
            else:
                return ActionResult(False, action, f"不支持的操作: {action}")
        except Exception as e:
            return ActionResult(False, action, f"操作失败: {e}", error=str(e))
    
    def _create_file(self, command: str, params: Dict) -> ActionResult:
        """创建文件"""
        path = params.get("path") or self._extract_path(command)
        content = params.get("content", "")
        
        if not path:
            return ActionResult(False, "file.create", "请指定文件路径")
        
        file_path = Path(path).expanduser()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        self._log("create", f"Created: {file_path}")
        
        return ActionResult(
            success=True,
            action="file.create",
            message=f"✓ 文件已创建: {path}",
            data={"path": str(file_path), "size": len(content)}
        )
    
    def _read_file(self, command: str, params: Dict) -> ActionResult:
        """读取文件"""
        path = params.get("path") or self._extract_path(command)
        
        if not path:
            return ActionResult(False, "file.read", "请指定文件路径")
        
        file_path = Path(path).expanduser()
        
        if not file_path.exists():
            return ActionResult(False, "file.read", f"文件不存在: {path}")
        
        content = file_path.read_text(encoding="utf-8")
        
        return ActionResult(
            success=True,
            action="file.read",
            message=f"✓ 已读取文件: {path}",
            data={"path": str(file_path), "content": content, "size": len(content)}
        )
    
    def _write_file(self, command: str, params: Dict) -> ActionResult:
        """写入文件"""
        path = params.get("path") or self._extract_path(command)
        content = params.get("content", "")
        
        if not path:
            return ActionResult(False, "file.write", "请指定文件路径")
        
        file_path = Path(path).expanduser()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        self._log("write", f"Wrote: {file_path}")
        
        return ActionResult(
            success=True,
            action="file.write",
            message=f"✓ 文件已保存: {path}",
            data={"path": str(file_path), "size": len(content)}
        )
    
    def _delete_file(self, command: str, params: Dict) -> ActionResult:
        """删除文件"""
        path = params.get("path") or self._extract_path(command)
        
        if not path:
            return ActionResult(False, "file.delete", "请指定文件路径")
        
        file_path = Path(path).expanduser()
        
        if not file_path.exists():
            return ActionResult(False, "file.delete", f"文件不存在: {path}")
        
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()
        
        self._log("delete", f"Deleted: {file_path}")
        
        return ActionResult(
            success=True,
            action="file.delete",
            message=f"✓ 已删除: {path}"
        )
    
    def _copy_file(self, command: str, params: Dict) -> ActionResult:
        """复制文件"""
        src = params.get("source") or self._extract_path(command)
        dst = params.get("destination")
        
        if not src:
            return ActionResult(False, "file.copy", "请指定源文件路径")
        
        src_path = Path(src).expanduser()
        
        if not src_path.exists():
            return ActionResult(False, "file.copy", f"源文件不存在: {src}")
        
        if not dst:
            dst = str(src_path.parent / f"{src_path.stem}_copy{src_path.suffix}")
        
        dst_path = Path(dst).expanduser()
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)
        
        self._log("copy", f"Copied: {src_path} -> {dst_path}")
        
        return ActionResult(
            success=True,
            action="file.copy",
            message=f"✓ 已复制: {src} -> {dst}",
            data={"source": str(src_path), "destination": str(dst_path)}
        )
    
    def _move_file(self, command: str, params: Dict) -> ActionResult:
        """移动/重命名文件"""
        src = params.get("source") or self._extract_path(command)
        dst = params.get("destination")
        
        if not src or not dst:
            return ActionResult(False, "file.move", "请指定源路径和目标路径")
        
        src_path = Path(src).expanduser()
        dst_path = Path(dst).expanduser()
        
        if not src_path.exists():
            return ActionResult(False, "file.move", f"源文件不存在: {src}")
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        
        self._log("move", f"Moved: {src_path} -> {dst_path}")
        
        return ActionResult(
            success=True,
            action="file.move",
            message=f"✓ 已移动: {src} -> {dst}",
            data={"source": str(src_path), "destination": str(dst_path)}
        )
    
    def _open_file(self, command: str, params: Dict) -> ActionResult:
        """用默认程序打开文件"""
        import platform
        import subprocess
        
        path = params.get("path") or self._extract_path(command)
        
        if not path:
            return ActionResult(False, "file.open", "请指定文件路径")
        
        file_path = Path(path).expanduser()
        
        if not file_path.exists():
            return ActionResult(False, "file.open", f"文件不存在: {path}")
        
        system = platform.system()
        
        if system == "Windows":
            os.startfile(str(file_path))
        elif system == "Darwin":
            subprocess.run(["open", str(file_path)])
        else:
            subprocess.run(["xdg-open", str(file_path)])
        
        self._log("open", f"Opened: {file_path}")
        
        return ActionResult(
            success=True,
            action="file.open",
            message=f"✓ 已打开: {path}",
            data={"path": str(file_path)}
        )
    
    def _create_dir(self, command: str, params: Dict) -> ActionResult:
        """创建目录"""
        path = params.get("path") or self._extract_path(command)
        
        # 尝试从命令中提取目录名
        if not path:
            for keyword in ["文件夹", "目录", "folder", "directory"]:
                if keyword in command.lower():
                    parts = command.lower().split(keyword)
                    if len(parts) > 1:
                        path = parts[1].strip().split()[0] if parts[1].strip() else None
                    elif len(parts) > 0 and parts[0].strip():
                        words = parts[0].strip().split()
                        path = words[-1] if words else None
                    break
        
        if not path:
            return ActionResult(False, "dir.create", "请指定目录名称")
        
        dir_path = Path(path).expanduser()
        dir_path.mkdir(parents=True, exist_ok=True)
        
        self._log("create_dir", f"Created: {dir_path}")
        
        return ActionResult(
            success=True,
            action="dir.create",
            message=f"✓ 目录已创建: {path}",
            data={"path": str(dir_path)}
        )
    
    def _list_dir(self, command: str, params: Dict) -> ActionResult:
        """列出目录内容"""
        path = params.get("path") or self._extract_path(command) or "."
        
        dir_path = Path(path).expanduser()
        
        if not dir_path.exists():
            return ActionResult(False, "dir.list", f"目录不存在: {path}")
        
        items = []
        for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            stat = item.stat()
            items.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        return ActionResult(
            success=True,
            action="dir.list",
            message=f"📂 {path} ({len(items)} 项)",
            data={"path": str(dir_path), "items": items, "count": len(items)}
        )

