@echo off
chcp 65001 >nul
title JoinFlow - AI Agent 工作台

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║       ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗      ██████╗     ║
echo  ║       ██║██╔═══██╗██║████╗  ██║██╔════╝██║     ██╔═══██╗    ║
echo  ║       ██║██║   ██║██║██╔██╗ ██║█████╗  ██║     ██║   ██║    ║
echo  ║  ██   ██║██║   ██║██║██║╚██╗██║██╔══╝  ██║     ██║   ██║    ║
echo  ║  ╚█████╔╝╚██████╔╝██║██║ ╚████║██║     ███████╗╚██████╔╝    ║
echo  ║   ╚════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝     ╚══════╝ ╚═════╝     ║
echo  ║                                                              ║
echo  ║              AI Agent 智能工作台 - 企业版                    ║
echo  ║                                                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查 Python
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo      √ Python 已安装

:: 检查虚拟环境
echo [2/5] 检查虚拟环境...
if not exist "venv" (
    echo      创建虚拟环境中...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)
echo      √ 虚拟环境就绪

:: 激活虚拟环境
echo [3/5] 激活虚拟环境...
call venv\Scripts\activate.bat
echo      √ 虚拟环境已激活

:: 安装依赖
echo [4/5] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo      安装依赖中（首次运行可能需要几分钟）...
    pip install -e ".[enterprise]" -q
    if errorlevel 1 (
        echo [警告] 企业版依赖安装失败，尝试安装基础版...
        pip install -e ".[full]" -q
    )
)
echo      √ 依赖已就绪

:: 安装 Playwright 浏览器（如果需要）
playwright install chromium >nul 2>&1

:: 启动服务
echo [5/5] 启动服务...
echo.
echo  ┌────────────────────────────────────────────────────────────┐
echo  │                                                            │
echo  │   JoinFlow 正在启动...                                     │
echo  │                                                            │
echo  │   访问地址: http://localhost:8000                          │
echo  │   工作台:   http://localhost:8000/workspace                │
echo  │                                                            │
echo  │   按 Ctrl+C 停止服务                                       │
echo  │                                                            │
echo  └────────────────────────────────────────────────────────────┘
echo.

:: 自动打开浏览器
start http://localhost:8000

:: 启动服务器
python -m web.server --port 8000

