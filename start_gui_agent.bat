@echo off
chcp 65001 > nul
echo.
echo =====================================
echo   JoinFlow GUI Agent
echo   像人一样操作电脑的 AI
echo =====================================
echo.

cd /d "%~dp0"

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 检查依赖
python -c "import pyautogui" 2>nul
if errorlevel 1 (
    echo [!] 正在安装 GUI Agent 依赖...
    pip install pyautogui pillow pyperclip litellm psutil -q
)

REM 检查 API 密钥
if "%OPENAI_API_KEY%"=="" (
    echo [!] 警告: OPENAI_API_KEY 未设置
    echo     请在 config.json 中配置或设置环境变量
    echo.
)

echo 启动交互式模式...
echo.
python -m joinflow_agent.gui.cli interactive

pause

