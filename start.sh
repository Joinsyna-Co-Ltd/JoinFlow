#!/bin/bash

# JoinFlow - AI Agent 工作台 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logo
echo ""
echo -e "${PURPLE}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║                                                              ║"
echo "  ║       ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗      ██████╗     ║"
echo "  ║       ██║██╔═══██╗██║████╗  ██║██╔════╝██║     ██╔═══██╗    ║"
echo "  ║       ██║██║   ██║██║██╔██╗ ██║█████╗  ██║     ██║   ██║    ║"
echo "  ║  ██   ██║██║   ██║██║██║╚██╗██║██╔══╝  ██║     ██║   ██║    ║"
echo "  ║  ╚█████╔╝╚██████╔╝██║██║ ╚████║██║     ███████╗╚██████╔╝    ║"
echo "  ║   ╚════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝     ╚══════╝ ╚═════╝     ║"
echo "  ║                                                              ║"
echo "  ║              AI Agent 智能工作台 - 企业版                    ║"
echo "  ║                                                              ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 检查 Python
echo -e "${CYAN}[1/5] 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] 未找到 Python3，请先安装 Python 3.9+${NC}"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS: brew install python3"
    exit 1
fi
echo -e "     ${GREEN}√ Python 已安装$(python3 --version)${NC}"

# 检查虚拟环境
echo -e "${CYAN}[2/5] 检查虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    echo "     创建虚拟环境中..."
    python3 -m venv venv
fi
echo -e "     ${GREEN}√ 虚拟环境就绪${NC}"

# 激活虚拟环境
echo -e "${CYAN}[3/5] 激活虚拟环境...${NC}"
source venv/bin/activate
echo -e "     ${GREEN}√ 虚拟环境已激活${NC}"

# 安装依赖
echo -e "${CYAN}[4/5] 检查依赖...${NC}"
if ! pip show fastapi &> /dev/null; then
    echo "     安装依赖中（首次运行可能需要几分钟）..."
    pip install -e ".[enterprise]" -q 2>/dev/null || pip install -e ".[full]" -q
fi
echo -e "     ${GREEN}√ 依赖已就绪${NC}"

# 安装 Playwright 浏览器
playwright install chromium &> /dev/null || true

# 启动服务
echo -e "${CYAN}[5/5] 启动服务...${NC}"
echo ""
echo -e "${GREEN}"
echo "  ┌────────────────────────────────────────────────────────────┐"
echo "  │                                                            │"
echo "  │   JoinFlow 正在启动...                                     │"
echo "  │                                                            │"
echo "  │   访问地址: http://localhost:8000                          │"
echo "  │   工作台:   http://localhost:8000/workspace                │"
echo "  │                                                            │"
echo "  │   按 Ctrl+C 停止服务                                       │"
echo "  │                                                            │"
echo "  └────────────────────────────────────────────────────────────┘"
echo -e "${NC}"
echo ""

# 尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000 &> /dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:8000 &> /dev/null &
fi

# 启动服务器
python -m web.server --port 8000

