# JoinFlow 企业版 Dockerfile
# 支持 Excel/PPT/PDF 导出，定时任务，模板系统等企业级功能

FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    # Playwright 依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    # 字体支持（用于 PDF/PPT 生成）
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml ./

# 安装 Python 依赖（企业版）
RUN pip install --no-cache-dir -e ".[enterprise]" 2>/dev/null || \
    pip install --no-cache-dir -e ".[full]" 2>/dev/null || \
    pip install --no-cache-dir \
    fastapi \
    uvicorn \
    jinja2 \
    python-multipart \
    qdrant-client \
    sentence-transformers \
    litellm \
    openai \
    pandas \
    numpy \
    matplotlib \
    openpyxl \
    python-pptx \
    reportlab \
    pillow \
    psutil \
    aiohttp \
    requests \
    beautifulsoup4

# 安装 Playwright 和浏览器
RUN pip install playwright && playwright install chromium --with-deps

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p \
    /app/workspace/results \
    /app/knowledge_base/files \
    /app/sessions \
    /app/exports \
    /app/templates \
    /app/schedules \
    /app/statistics \
    /app/plugins

# 设置权限
RUN chmod +x start.sh 2>/dev/null || true

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 默认环境变量
ENV JOINFLOW_HOST=0.0.0.0 \
    JOINFLOW_PORT=8000 \
    JOINFLOW_WORKERS=1

# 启动命令
CMD ["python", "-m", "web.server", "--host", "0.0.0.0", "--port", "8000"]
