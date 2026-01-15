#!/bin/bash

echo ""
echo "====================================="
echo "  JoinFlow GUI Agent"
echo "  像人一样操作电脑的 AI"
echo "====================================="
echo ""

cd "$(dirname "$0")"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 检查依赖
if ! python -c "import pyautogui" 2>/dev/null; then
    echo "[!] 正在安装 GUI Agent 依赖..."
    pip install pyautogui pillow pyperclip litellm psutil -q
fi

# 检查 API 密钥
if [ -z "$OPENAI_API_KEY" ]; then
    echo "[!] 警告: OPENAI_API_KEY 未设置"
    echo "    请设置环境变量: export OPENAI_API_KEY=your-key"
    echo ""
fi

echo "启动交互式模式..."
echo ""
python -m joinflow_agent.gui.cli interactive

