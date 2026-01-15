"""
Local OS API - 本地操作系统控制API
=====================================

提供RESTful API端点来控制本地操作系统
需要用户授权后才能使用
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/os", tags=["Local OS"])

# 全局OS Agent实例
_os_agent = None


def get_os_agent():
    """获取或创建OS Agent实例"""
    global _os_agent
    if _os_agent is None:
        from joinflow_agent.local_os_agent import LocalOSAgent, LocalOSConfig, PermissionLevel
        config = LocalOSConfig(
            permission_level=PermissionLevel.WORKSPACE,
            require_confirmation=True,
            log_all_actions=True
        )
        _os_agent = LocalOSAgent(config)
    return _os_agent


# =====================
# 请求模型
# =====================

class AuthorizationRequest(BaseModel):
    scope: str = "full"  # "readonly", "workspace", "full"
    confirm: bool = False


class FileReadRequest(BaseModel):
    path: str
    encoding: str = "utf-8"


class FileWriteRequest(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"


class DirectoryListRequest(BaseModel):
    path: str = "."
    include_hidden: bool = False


class PathRequest(BaseModel):
    path: str


class CopyMoveRequest(BaseModel):
    src: str
    dst: str


class CommandRequest(BaseModel):
    command: str
    working_dir: Optional[str] = None


class SmartCommandRequest(BaseModel):
    """智能命令请求 - 用自然语言描述意图"""
    query: str  # 自然语言查询
    working_dir: Optional[str] = None


class AppRequest(BaseModel):
    name: str


class UrlRequest(BaseModel):
    url: str


class ClipboardRequest(BaseModel):
    content: str


class NotificationRequest(BaseModel):
    title: str
    message: str


class ProcessRequest(BaseModel):
    pid: int


class ProcessFilterRequest(BaseModel):
    name_filter: Optional[str] = None


class TypeTextRequest(BaseModel):
    text: str
    interval: float = 0.05


class KeyRequest(BaseModel):
    key: str


class HotkeyRequest(BaseModel):
    keys: List[str]


class MouseClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"


class MouseMoveRequest(BaseModel):
    x: int
    y: int
    duration: float = 0.5


class ScreenshotRequest(BaseModel):
    save_path: Optional[str] = None


# =====================
# 授权检查辅助函数
# =====================

def check_authorization(agent) -> bool:
    """检查 Agent 是否已授权，未授权则抛出异常"""
    if not agent.is_authorized():
        raise HTTPException(
            status_code=403,
            detail="未授权：请先在 OS 控制页面授权后才能执行此操作。访问 /os-control 进行授权。"
        )
    return True

# =====================
# 授权管理
# =====================

@router.get("/status")
async def get_status():
    """获取OS Agent状态"""
    agent = get_os_agent()
    return {
        "authorized": agent.is_authorized(),
        "permission_level": agent.config.permission_level.value,
        "platform": agent.platform.value,
        "capabilities": {
            "pyautogui": agent._has_pyautogui,
            "pillow": agent._has_pillow,
            "pyperclip": agent._has_pyperclip
        }
    }


@router.post("/authorize")
async def authorize(request: AuthorizationRequest):
    """请求或确认授权"""
    agent = get_os_agent()
    
    if not request.confirm:
        # 返回授权请求信息
        return agent.request_authorization(request.scope)
    
    # 确认授权
    from joinflow_agent.local_os_agent import PermissionLevel
    level_map = {
        "readonly": PermissionLevel.READONLY,
        "workspace": PermissionLevel.WORKSPACE,
        "full": PermissionLevel.AUTHORIZED
    }
    level = level_map.get(request.scope, PermissionLevel.WORKSPACE)
    
    result = agent.authorize(level)
    return {"success": result.success, "message": result.message, "data": result.data}


@router.post("/revoke")
async def revoke_authorization():
    """撤销授权"""
    agent = get_os_agent()
    result = agent.revoke_authorization()
    return {"success": result.success, "message": result.message}


# =====================
# 文件系统操作
# =====================

@router.post("/file/read")
async def read_file(request: FileReadRequest):
    """读取文件"""
    agent = get_os_agent()
    result = agent.read_file(request.path, request.encoding)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/file/write")
async def write_file(request: FileWriteRequest):
    """写入文件"""
    agent = get_os_agent()
    check_authorization(agent)  # 写入文件需要授权
    result = agent.write_file(request.path, request.content, request.encoding)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/directory/list")
async def list_directory(request: DirectoryListRequest):
    """列出目录"""
    agent = get_os_agent()
    result = agent.list_directory(request.path, request.include_hidden)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/directory/create")
async def create_directory(request: PathRequest):
    """创建目录"""
    agent = get_os_agent()
    check_authorization(agent)  # 创建目录需要授权
    result = agent.create_directory(request.path)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/delete")
async def delete_path(request: PathRequest):
    """删除文件或目录"""
    agent = get_os_agent()
    check_authorization(agent)  # 删除操作需要授权
    result = agent.delete_path(request.path)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/copy")
async def copy_path(request: CopyMoveRequest):
    """复制文件或目录"""
    agent = get_os_agent()
    check_authorization(agent)  # 复制操作需要授权
    result = agent.copy_path(request.src, request.dst)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/move")
async def move_path(request: CopyMoveRequest):
    """移动文件或目录"""
    agent = get_os_agent()
    check_authorization(agent)  # 移动操作需要授权
    result = agent.move_path(request.src, request.dst)
    return {
        "success": result.success,
        "message": result.message
    }


# =====================
# 命令执行
# =====================

@router.post("/command/run")
async def run_command(request: CommandRequest):
    """执行Shell命令（直接执行，不经过大模型）"""
    agent = get_os_agent()
    check_authorization(agent)  # 检查授权
    result = agent.run_command(request.command, request.working_dir)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


def generate_local_summary(query: str, results: list) -> str:
    """当 LLM 汇总失败时，生成本地详细汇总"""
    import re
    
    info = {
        'cpu': None,
        'cpu_cores': None,
        'cpu_speed': None,
        'memory_gb': None,
        'disks': [],
        'os': None,
        'gpu': None,
        'ip': None,
        'gateway': None,
        'process_count': None,
        'top_processes': []
    }
    
    for r in results:
        output = r.get('output', '')
        cmd = r.get('command', '').lower()
        
        # 解析 CPU 信息
        if 'cpu' in cmd:
            lines = [l.strip() for l in output.split('\n') if l.strip()]
            
            for line in lines:
                line_lower = line.lower()
                # 跳过列名行
                if line_lower.startswith('maxclockspeed') or line_lower.startswith('name') or line_lower.startswith('numberofcores'):
                    continue
                
                if 'intel' in line_lower or 'amd' in line_lower or 'ryzen' in line_lower:
                    # 提取 CPU 名称
                    intel_pos = line_lower.find('intel')
                    amd_pos = line_lower.find('amd')
                    start_pos = intel_pos if intel_pos >= 0 else amd_pos
                    
                    if start_pos >= 0:
                        cpu_str = line[start_pos:]
                        # 清理末尾的纯数字（核心数等）
                        cpu_str = re.sub(r'\s+\d+\s*$', '', cpu_str).strip()
                        # 如果 CPU 名称包含 @ 后的频率，保留完整名称
                        if '@' in cpu_str:
                            # 保留到 GHz/MHz 结束
                            ghz_match = re.search(r'^(.+?\d+\.\d+\s*GHz)', cpu_str, re.IGNORECASE)
                            if ghz_match:
                                cpu_str = ghz_match.group(1)
                        info['cpu'] = cpu_str
                    
                    # 提取数字信息
                    parts = line.split()
                    numbers = [p for p in parts if p.isdigit()]
                    
                    # 小数字是核心数（通常 1-128）
                    for num in numbers:
                        n = int(num)
                        if 1 <= n <= 128:
                            info['cpu_cores'] = num
                    
                    # 大数字是频率（MHz，通常 1000-6000）
                    for num in numbers:
                        n = int(num)
                        if 1000 < n < 10000:
                            info['cpu_speed'] = f"{n/1000:.1f}GHz"
                    break
        
        # 解析内存信息
        if 'memorychip' in cmd:
            capacities = re.findall(r'(\d{9,})', output)
            if capacities:
                total_bytes = sum(int(c) for c in capacities)
                info['memory_gb'] = round(total_bytes / (1024**3))
        
        # 解析磁盘信息
        if 'logicaldisk' in cmd:
            lines = output.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 3 and ':' in parts[0]:
                    drive = parts[0]
                    try:
                        # 尝试解析数字
                        nums = [p for p in parts[1:] if p.isdigit()]
                        if len(nums) >= 2:
                            free_bytes = int(nums[0])
                            total_bytes = int(nums[1])
                            free_gb = round(free_bytes / (1024**3))
                            total_gb = round(total_bytes / (1024**3))
                            used_gb = total_gb - free_gb
                            used_pct = round((used_gb / total_gb) * 100) if total_gb > 0 else 0
                            info['disks'].append({
                                'drive': drive,
                                'total': total_gb,
                                'free': free_gb,
                                'used': used_gb,
                                'used_pct': used_pct
                            })
                    except (ValueError, IndexError):
                        pass
        
        # 解析操作系统
        if 'wmic os' in cmd:
            lines = [l.strip() for l in output.split('\n') if l.strip()]
            for line in lines:
                if 'windows' in line.lower():
                    info['os'] = line.strip()
                    break
        
        # 解析显卡
        if 'videocontroller' in cmd:
            lines = [l.strip() for l in output.split('\n') if l.strip()]
            for line in lines:
                if 'nvidia' in line.lower() or 'amd' in line.lower() or 'intel' in line.lower() or 'radeon' in line.lower():
                    info['gpu'] = line.strip()
                    break
        
        # 解析网络信息
        if 'ipconfig' in cmd:
            ipv4_match = re.search(r'IPv4.*?:\s*(\d+\.\d+\.\d+\.\d+)', output)
            if ipv4_match:
                info['ip'] = ipv4_match.group(1)
            gateway_match = re.search(r'Default Gateway.*?:\s*(\d+\.\d+\.\d+\.\d+)', output)
            if gateway_match:
                info['gateway'] = gateway_match.group(1)
        
        # 解析进程信息
        if 'tasklist' in cmd:
            lines = [l for l in output.split('\n') if l.strip()]
            info['process_count'] = len(lines)
        
        # 解析 PowerShell 进程信息
        if 'get-process' in cmd:
            lines = [l.strip() for l in output.split('\n') if l.strip() and not l.startswith('Name')]
            info['top_processes'] = lines[:5]
    
    # 构建汇总
    summary_lines = ["📊 **电脑配置信息**\n"]
    
    if info['cpu']:
        cpu_info = info['cpu']
        if info['cpu_cores']:
            cpu_info += f" ({info['cpu_cores']}核"
            if info['cpu_speed']:
                cpu_info += f", {info['cpu_speed']}"
            cpu_info += ")"
        summary_lines.append(f"💻 **处理器**: {cpu_info}")
    
    if info['memory_gb']:
        summary_lines.append(f"🧠 **内存**: {info['memory_gb']} GB")
    
    if info['disks']:
        summary_lines.append("💾 **存储**:")
        for disk in info['disks']:
            summary_lines.append(f"   - {disk['drive']} 总计 {disk['total']}GB，已用 {disk['used']}GB ({disk['used_pct']}%)，剩余 {disk['free']}GB")
    
    if info['os']:
        summary_lines.append(f"🖥️ **系统**: {info['os']}")
    
    if info['gpu']:
        summary_lines.append(f"🎮 **显卡**: {info['gpu']}")
    
    if info['ip']:
        summary_lines.append(f"🌐 **IP 地址**: {info['ip']}")
    
    if info['gateway']:
        summary_lines.append(f"🚪 **默认网关**: {info['gateway']}")
    
    if info['process_count']:
        summary_lines.append(f"📋 **运行进程**: {info['process_count']} 个")
    
    if info['top_processes']:
        summary_lines.append("📈 **内存占用最高**:")
        for p in info['top_processes'][:3]:
            summary_lines.append(f"   - {p}")
    
    if len(summary_lines) > 1:
        return "\n".join(summary_lines)
    else:
        return "ℹ️ 命令已执行完成，请查看详细输出。"


def local_intent_parser(query: str) -> dict:
    """本地意图解析 - 当 API 限流时使用"""
    import os
    query_lower = query.lower()
    
    # 获取桌面路径
    desktop_path = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\Administrator'), 'Desktop')
    
    # ========== 打开应用类 ==========
    # 记事本
    if '记事本' in query_lower or 'notepad' in query_lower:
        return {
            'intent': '打开记事本',
            'commands': ['start notepad'],
            'explanation': '启动 Windows 记事本应用',
            'dangerous': False
        }
    
    # 计算器
    if '计算器' in query_lower or 'calculator' in query_lower or 'calc' in query_lower:
        return {
            'intent': '打开计算器',
            'commands': ['start calc'],
            'explanation': '启动 Windows 计算器',
            'dangerous': False
        }
    
    # 画图
    if '画图' in query_lower or 'paint' in query_lower or 'mspaint' in query_lower:
        return {
            'intent': '打开画图',
            'commands': ['start mspaint'],
            'explanation': '启动 Windows 画图应用',
            'dangerous': False
        }
    
    # 浏览器
    if '浏览器' in query_lower or 'browser' in query_lower or 'chrome' in query_lower or 'edge' in query_lower:
        return {
            'intent': '打开浏览器',
            'commands': ['start msedge'],
            'explanation': '启动 Microsoft Edge 浏览器',
            'dangerous': False
        }
    
    # 命令提示符/终端
    if 'cmd' in query_lower or '命令提示符' in query_lower or '终端' in query_lower or 'terminal' in query_lower:
        return {
            'intent': '打开命令提示符',
            'commands': ['start cmd'],
            'explanation': '启动 Windows 命令提示符',
            'dangerous': False
        }
    
    # PowerShell
    if 'powershell' in query_lower:
        return {
            'intent': '打开 PowerShell',
            'commands': ['start powershell'],
            'explanation': '启动 Windows PowerShell',
            'dangerous': False
        }
    
    # 资源管理器/文件管理器
    if '资源管理器' in query_lower or '文件管理器' in query_lower or 'explorer' in query_lower:
        return {
            'intent': '打开资源管理器',
            'commands': ['start explorer'],
            'explanation': '启动 Windows 资源管理器',
            'dangerous': False
        }
    
    # 打开桌面
    if '桌面' in query_lower and ('打开' in query_lower or '查看' in query_lower):
        return {
            'intent': '打开桌面文件夹',
            'commands': [f'start explorer "{desktop_path}"'],
            'explanation': '打开桌面文件夹',
            'dangerous': False
        }
    
    # ========== 文件操作类 ==========
    # 列出桌面文件
    if '桌面' in query_lower and ('文件' in query_lower or '列出' in query_lower or '查看' in query_lower):
        return {
            'intent': '列出桌面文件',
            'commands': [f'dir "{desktop_path}"'],
            'explanation': '列出桌面上的所有文件',
            'dangerous': False
        }
    
    # 创建文件/文件夹
    if '创建' in query_lower or '新建' in query_lower:
        if '文件夹' in query_lower or '目录' in query_lower:
            return {
                'intent': '创建文件夹',
                'commands': [f'mkdir "{desktop_path}\\新建文件夹"'],
                'explanation': '在桌面创建新文件夹',
                'dangerous': False
            }
    
    # ========== 系统信息类 ==========
    # 定义意图关键词映射
    intent_mappings = {
        '电脑配置': {
            'intent': '查看电脑配置信息',
            'commands': [
                'wmic cpu get name,numberofcores,maxclockspeed',
                'wmic memorychip get capacity',
                'wmic os get caption,version',
                'wmic logicaldisk get caption,size,freespace',
            ],
            'explanation': '获取 CPU、内存、系统和磁盘信息'
        },
        '系统信息': {
            'intent': '查看系统信息',
            'commands': ['wmic os get caption,version,osarchitecture', 'wmic cpu get name'],
            'explanation': '获取操作系统和 CPU 信息'
        },
        'cpu': {
            'intent': '查看 CPU 信息',
            'commands': ['wmic cpu get name,numberofcores,maxclockspeed'],
            'explanation': '获取 CPU 型号、核心数和频率'
        },
        '处理器': {
            'intent': '查看 CPU 信息',
            'commands': ['wmic cpu get name,numberofcores,maxclockspeed'],
            'explanation': '获取 CPU 型号、核心数和频率'
        },
        '内存': {
            'intent': '查看内存信息',
            'commands': ['wmic memorychip get capacity,speed'],
            'explanation': '获取内存容量和速度'
        },
        '磁盘': {
            'intent': '查看磁盘信息',
            'commands': ['wmic logicaldisk get caption,size,freespace,filesystem'],
            'explanation': '获取所有磁盘的容量和剩余空间'
        },
        'c盘': {
            'intent': '查看 C 盘信息',
            'commands': ['wmic logicaldisk where "caption=\'C:\'" get size,freespace'],
            'explanation': '获取 C 盘容量和剩余空间'
        },
        '进程': {
            'intent': '查看进程信息',
            'commands': ['tasklist /fo table'],
            'explanation': '列出当前运行的进程'
        },
        '网络': {
            'intent': '查看网络配置',
            'commands': ['ipconfig'],
            'explanation': '获取网络配置信息'
        },
        'ip': {
            'intent': '查看 IP 地址',
            'commands': ['ipconfig'],
            'explanation': '获取 IP 地址信息'
        },
    }
    
    # 匹配意图
    matched_commands = []
    matched_intent = '执行系统命令'
    matched_explanation = ''
    
    for keyword, mapping in intent_mappings.items():
        if keyword in query_lower:
            matched_commands.extend(mapping['commands'])
            matched_intent = mapping['intent']
            matched_explanation = mapping['explanation']
    
    # 如果没有匹配到，尝试更通用的匹配
    if not matched_commands:
        # 通用"打开"命令
        if '打开' in query_lower or '启动' in query_lower or 'open' in query_lower or 'start' in query_lower:
            # 尝试提取要打开的应用名称
            app_mappings = {
                '记事本': 'notepad',
                'notepad': 'notepad',
                '计算器': 'calc',
                'calc': 'calc',
                'calculator': 'calc',
                '画图': 'mspaint',
                'paint': 'mspaint',
                '浏览器': 'msedge',
                'browser': 'msedge',
                'edge': 'msedge',
                'chrome': 'chrome',
                'cmd': 'cmd',
                '命令提示符': 'cmd',
                'powershell': 'powershell',
                '资源管理器': 'explorer',
                'explorer': 'explorer',
                'word': 'winword',
                'excel': 'excel',
                'ppt': 'powerpnt',
                'powerpoint': 'powerpnt',
            }
            
            for app_name, app_cmd in app_mappings.items():
                if app_name in query_lower:
                    matched_commands = [f'start {app_cmd}']
                    matched_intent = f'打开 {app_name}'
                    matched_explanation = f'启动 {app_name} 应用程序'
                    break
        
        # 通用"查看配置"命令
        if not matched_commands and ('配置' in query_lower or '信息' in query_lower):
            matched_commands = [
                'wmic cpu get name,numberofcores,maxclockspeed',
                'wmic memorychip get capacity',
                'wmic os get caption,version',
                'wmic logicaldisk get caption,size,freespace',
            ]
            matched_intent = '查看系统配置信息'
            matched_explanation = '获取完整的系统配置信息'
        
        # 通用"写/编辑"命令 - 打开记事本
        if not matched_commands and ('写' in query_lower or '编辑' in query_lower or '编写' in query_lower):
            matched_commands = ['start notepad']
            matched_intent = '打开记事本进行编辑'
            matched_explanation = '启动记事本供您编辑文本'
        
        # 通用"保存"命令 - 提示用户
        if not matched_commands and '保存' in query_lower:
            matched_commands = ['echo 请在应用程序中使用 Ctrl+S 保存文件']
            matched_intent = '保存文件'
            matched_explanation = '在应用程序中按 Ctrl+S 保存文件到桌面'
        
        # 通用"关闭"命令
        if not matched_commands and ('关闭' in query_lower or '退出' in query_lower or 'close' in query_lower):
            if '记事本' in query_lower or 'notepad' in query_lower:
                matched_commands = ['taskkill /f /im notepad.exe']
                matched_intent = '关闭记事本'
                matched_explanation = '强制关闭记事本应用'
        
        # 通用"时间/日期"命令
        if not matched_commands and ('时间' in query_lower or '日期' in query_lower or 'time' in query_lower or 'date' in query_lower):
            matched_commands = ['echo %date% %time%']
            matched_intent = '显示当前时间'
            matched_explanation = '显示系统当前日期和时间'
        
        # 通用"ping"命令
        if not matched_commands and 'ping' in query_lower:
            # 尝试提取目标地址
            import re
            url_match = re.search(r'ping\s+(\S+)', query_lower)
            if url_match:
                target = url_match.group(1)
                matched_commands = [f'ping {target} -n 4']
            else:
                matched_commands = ['ping google.com -n 4']
            matched_intent = '网络连通性测试'
            matched_explanation = '测试网络连接'
    
    # 去重
    matched_commands = list(dict.fromkeys(matched_commands))
    
    return {
        'intent': matched_intent,
        'commands': matched_commands,
        'explanation': matched_explanation,
        'dangerous': False
    }


@router.post("/command/smart")
async def smart_command(request: SmartCommandRequest):
    """智能命令执行 - 使用大模型理解自然语言意图
    
    输入自然语言描述，大模型会：
    1. 理解用户意图
    2. 生成相应的系统命令
    3. 执行命令并返回结果
    
    支持多模型自动切换：当一个模型不可用时自动切换到备用模型
    
    注意：需要先授权才能执行命令
    """
    import os
    import platform
    import subprocess
    import json
    import re
    
    # 检查授权状态
    agent = get_os_agent()
    check_authorization(agent)  # 未授权会抛出 403 异常
    
    # 导入模型管理器
    from joinflow_agent.model_manager import get_model_manager, AgentType
    model_manager = get_model_manager()
    
    # 意图理解提示词 - 更详细和全面
    intent_prompt = f"""你是一个智能操作系统助手。用户会用自然语言告诉你他们想做什么。
请仔细分析用户意图，生成全面的系统命令来满足用户需求。

当前系统: {platform.system()} {platform.release()}
当前目录: {request.working_dir or os.getcwd()}

用户说: "{request.query}"

【重要】请根据用户意图，选择合适的命令组合。如果用户问的比较笼统（如"电脑配置"），请返回全面的信息。

常见意图与推荐命令（请根据需要组合）：

📊 电脑配置/系统信息（全面）:
- CPU信息: wmic cpu get name,numberofcores,maxclockspeed
- 内存信息: wmic memorychip get capacity,speed,manufacturer
- 操作系统: wmic os get caption,version,osarchitecture
- 主板信息: wmic baseboard get product,manufacturer
- 显卡信息: wmic path win32_videocontroller get name,adapterram

💾 磁盘/存储空间:
- 所有磁盘: wmic logicaldisk get caption,size,freespace,filesystem
- C盘详情: wmic logicaldisk where "caption='C:'" get size,freespace

📋 进程信息:
- 进程列表: tasklist /fo csv /nh | findstr /v "^$"
- 内存占用排序: powershell "Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Name,@{{n='Memory(MB)';e={{[math]::Round($_.WorkingSet/1MB,1)}}}}"

🌐 网络配置:
- 网络详情: ipconfig /all
- 连接状态: netstat -an | findstr ESTABLISHED

📁 文件操作:
- 列出文件: dir
- 搜索文件: dir /s /b *关键词*

请返回 JSON 格式（只返回JSON）:
```json
{{
    "intent": "用户意图的简短描述",
    "commands": ["命令1", "命令2", ...],
    "explanation": "简短说明",
    "dangerous": false
}}
```
"""
    
    use_local_parser = False
    intent = None
    
    try:
        # 1. 尝试调用大模型理解意图
        logger.info("Trying LLM for intent understanding with model fallback...")
        
        # 使用模型管理器调用 LLM（支持自动切换模型）
        content = model_manager.call_llm_sync(
            AgentType.OS,
            messages=[{"role": "user", "content": intent_prompt}],
            max_tokens=500,
            temperature=0.1,
        )
        
        if content:
            content = content.strip()
            # 记录使用的模型
            current_model = model_manager.get_model(AgentType.OS)
            logger.info(f"Using model: {current_model.name if current_model else 'unknown'}")
            
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                intent = json.loads(json_match.group())
            else:
                logger.warning("Could not parse LLM response, using local parser")
                use_local_parser = True
        else:
            use_local_parser = True
            
    except Exception as llm_error:
        # 所有模型都失败，使用本地解析
        logger.warning(f"All LLM models failed: {llm_error}, using local parser")
        use_local_parser = True
    
    # 如果 LLM 失败，使用本地意图解析
    if use_local_parser or not intent:
        logger.info("Using local intent parser")
        intent = local_intent_parser(request.query)
    
    try:
        # 2. 获取要执行的命令
        commands = intent.get('commands', [])
        if not commands:
            return {
                "success": True,
                "message": "理解成功，但没有需要执行的命令",
                "data": {
                    "intent": intent.get('intent', ''),
                    "explanation": intent.get('explanation', ''),
                    "commands": [],
                    "results": [],
                    "summary": "抱歉，我不太理解您的意思。请尝试更具体的描述，例如：\n- 查看电脑配置\n- 显示C盘容量\n- 列出当前进程"
                }
            }
        
        # 3. 执行命令（使用正确的编码处理）
        results = []
        for cmd in commands:
            try:
                # Windows 系统使用 chcp 65001 切换到 UTF-8 编码
                if platform.system() == "Windows":
                    full_cmd = f'chcp 65001 >nul && {cmd}'
                else:
                    full_cmd = cmd
                
                result = subprocess.run(
                    full_cmd,
                    shell=True,
                    capture_output=True,
                    timeout=30,
                    cwd=request.working_dir
                )
                
                # 尝试多种编码解码输出
                stdout_text = ""
                stderr_text = ""
                
                for encoding in ['utf-8', 'gbk', 'cp936', 'gb2312']:
                    try:
                        if result.stdout:
                            stdout_text = result.stdout.decode(encoding)
                            break
                    except UnicodeDecodeError:
                        continue
                
                for encoding in ['utf-8', 'gbk', 'cp936', 'gb2312']:
                    try:
                        if result.stderr:
                            stderr_text = result.stderr.decode(encoding)
                            break
                    except UnicodeDecodeError:
                        continue
                
                # 如果都失败了，使用 replace 错误处理
                if not stdout_text and result.stdout:
                    stdout_text = result.stdout.decode('utf-8', errors='replace')
                if not stderr_text and result.stderr:
                    stderr_text = result.stderr.decode('utf-8', errors='replace')
                
                output = stdout_text or stderr_text or "(无输出)"
                results.append({
                    "command": cmd,
                    "success": result.returncode == 0,
                    "output": output[:3000],  # 限制输出长度
                    "return_code": result.returncode
                })
                
            except subprocess.TimeoutExpired:
                results.append({
                    "command": cmd,
                    "success": False,
                    "output": "命令执行超时",
                    "return_code": -1
                })
            except Exception as e:
                results.append({
                    "command": cmd,
                    "success": False,
                    "output": str(e),
                    "return_code": -1
                })
        
        # 4. 使用大模型汇总分析结果
        all_success = all(r['success'] for r in results)
        
        # 构建汇总提示词
        results_text = ""
        for r in results:
            results_text += f"\n命令: {r['command']}\n输出:\n{r['output'][:1500]}\n"
        
        summary_prompt = f"""你是一个友好的智能助手。用户问了: "{request.query}"

我执行了以下命令并获得了结果:
{results_text}

请用**简洁、人性化的中文**给用户一个完整的回答。

【格式要求】使用以下格式输出，让信息一目了然：

📊 **电脑配置信息**

💻 **处理器**: [CPU型号] ([核心数]核, [频率])
🧠 **内存**: [总容量]GB
💾 **存储**:
   - C盘: [总容量]GB，已用[已用]GB，剩余[剩余]GB
   - D盘: ...（如有）
🖥️ **系统**: [操作系统名称和版本]
🎮 **显卡**: [显卡型号]（如有）
📋 **当前运行**: [进程数]个进程

【重要规则】：
1. 数字转换：17179869184 字节 = 16GB，2904 MHz = 2.9GHz
2. 百分比计算：已用空间占比
3. 省略不重要的技术细节
4. 如果某信息没有获取到，就不要显示该项
5. 直接输出内容，不要说"根据命令执行结果"
6. 使用 emoji 让信息更直观

请直接给出汇总，像朋友聊天一样自然。
"""

        try:
            logger.info("Generating summary with LLM (with model fallback)...")
            summary = model_manager.call_llm_sync(
                AgentType.LLM,  # 使用通用 LLM agent 类型
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=800,
                temperature=0.3,
            )
            if summary:
                summary = summary.strip()
                current_model = model_manager.get_model(AgentType.LLM)
                logger.info(f"Summary generated with model: {current_model.name if current_model else 'unknown'}")
            else:
                summary = generate_local_summary(request.query, results)
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            # 如果汇总失败，生成简单的本地汇总
            summary = generate_local_summary(request.query, results)
        
        return {
            "success": all_success,
            "message": intent.get('intent', '命令执行完成'),
            "data": {
                "intent": intent.get('intent', ''),
                "explanation": intent.get('explanation', ''),
                "dangerous": intent.get('dangerous', False),
                "commands": commands,
                "results": results,
                "summary": summary  # 新增：大模型汇总的结果
            }
        }
        
    except Exception as e:
        logger.error(f"Smart command error: {e}")
        return {
            "success": False,
            "message": f"智能命令执行失败: {str(e)}",
            "data": None
        }


# =====================
# 应用程序管理
# =====================

@router.post("/app/open")
async def open_application(request: AppRequest):
    """打开应用程序"""
    agent = get_os_agent()
    result = agent.open_application(request.name)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/file/open")
async def open_file(request: PathRequest):
    """用默认程序打开文件"""
    agent = get_os_agent()
    result = agent.open_file_with_default_app(request.path)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/url/open")
async def open_url(request: UrlRequest):
    """在浏览器中打开URL"""
    agent = get_os_agent()
    result = agent.open_url(request.url)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/process/list")
async def list_processes(request: ProcessFilterRequest):
    """获取进程列表"""
    agent = get_os_agent()
    result = agent.get_running_processes(request.name_filter)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/process/kill")
async def kill_process(request: ProcessRequest):
    """终止进程"""
    agent = get_os_agent()
    result = agent.kill_process(request.pid)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


# =====================
# 系统工具
# =====================

@router.get("/system/info")
async def get_system_info():
    """获取系统信息"""
    agent = get_os_agent()
    result = agent.get_system_info()
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/screenshot")
async def take_screenshot(request: ScreenshotRequest):
    """截取屏幕"""
    agent = get_os_agent()
    result = agent.take_screenshot(request.save_path)
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.get("/clipboard")
async def get_clipboard():
    """获取剪贴板内容"""
    agent = get_os_agent()
    result = agent.get_clipboard()
    return {
        "success": result.success,
        "message": result.message,
        "data": result.data
    }


@router.post("/clipboard")
async def set_clipboard(request: ClipboardRequest):
    """设置剪贴板内容"""
    agent = get_os_agent()
    result = agent.set_clipboard(request.content)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/notification")
async def show_notification(request: NotificationRequest):
    """显示系统通知"""
    agent = get_os_agent()
    result = agent.show_notification(request.title, request.message)
    return {
        "success": result.success,
        "message": result.message
    }


# =====================
# 鼠标键盘控制
# =====================

@router.post("/keyboard/type")
async def type_text(request: TypeTextRequest):
    """模拟键盘输入"""
    agent = get_os_agent()
    result = agent.type_text(request.text, request.interval)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/keyboard/press")
async def press_key(request: KeyRequest):
    """模拟按键"""
    agent = get_os_agent()
    result = agent.press_key(request.key)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/keyboard/hotkey")
async def press_hotkey(request: HotkeyRequest):
    """模拟组合键"""
    agent = get_os_agent()
    result = agent.hotkey(*request.keys)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/mouse/click")
async def mouse_click(request: MouseClickRequest):
    """模拟鼠标点击"""
    agent = get_os_agent()
    result = agent.mouse_click(request.x, request.y, request.button)
    return {
        "success": result.success,
        "message": result.message
    }


@router.post("/mouse/move")
async def mouse_move(request: MouseMoveRequest):
    """移动鼠标"""
    agent = get_os_agent()
    result = agent.mouse_move(request.x, request.y, request.duration)
    return {
        "success": result.success,
        "message": result.message
    }


# =====================
# 操作日志
# =====================

@router.get("/logs")
async def get_action_logs():
    """获取操作日志"""
    agent = get_os_agent()
    return {
        "logs": agent.get_action_log()
    }


@router.delete("/logs")
async def clear_action_logs():
    """清除操作日志"""
    agent = get_os_agent()
    agent.clear_action_log()
    return {"message": "操作日志已清除"}


# =====================
# 模型管理 API
# =====================

@router.get("/models")
async def get_available_models():
    """获取所有可用模型及其状态"""
    from joinflow_agent.model_manager import get_model_manager, AgentType
    
    manager = get_model_manager()
    status = manager.get_status()
    
    return {
        "success": True,
        "data": status
    }


@router.get("/models/{agent_type}")
async def get_models_for_agent(agent_type: str):
    """获取指定 Agent 类型的可用模型"""
    from joinflow_agent.model_manager import get_model_manager, AgentType
    
    manager = get_model_manager()
    
    try:
        agent_enum = AgentType(agent_type)
        models = manager.get_models_for_agent(agent_enum)
        current = manager.get_model(agent_enum)
        
        return {
            "success": True,
            "data": {
                "agent_type": agent_type,
                "current_model": current.to_dict() if current else None,
                "available_models": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "is_free": m.is_free,
                        "supports_vision": m.supports_vision,
                        "description": m.description,
                        "available": manager.is_model_available(m.id),
                    }
                    for m in models
                ]
            }
        }
    except ValueError:
        return {
            "success": False,
            "message": f"未知的 Agent 类型: {agent_type}，可选值: llm, vision, code, browser, os, data"
        }


class ModelSwitchRequest(BaseModel):
    """模型切换请求"""
    agent_type: str  # llm, vision, code, browser, os, data
    model_id: str


@router.post("/models/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换指定 Agent 类型使用的模型"""
    from joinflow_agent.model_manager import get_model_manager, AgentType
    
    manager = get_model_manager()
    
    try:
        agent_enum = AgentType(request.agent_type)
        success = manager.switch_model(agent_enum, request.model_id)
        
        if success:
            current = manager.get_model(agent_enum)
            return {
                "success": True,
                "message": f"已切换到模型: {current.name if current else request.model_id}",
                "data": {
                    "agent_type": request.agent_type,
                    "model_id": request.model_id,
                    "model_name": current.name if current else None
                }
            }
        else:
            return {
                "success": False,
                "message": f"切换失败：模型 {request.model_id} 不存在或未启用"
            }
    except ValueError:
        return {
            "success": False,
            "message": f"未知的 Agent 类型: {request.agent_type}"
        }


logger.info("Local OS API routes registered (with model management)")

