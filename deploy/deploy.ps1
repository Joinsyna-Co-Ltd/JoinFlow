# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                              ║
# ║      JoinFlow 云服务一键部署脚本 (Windows PowerShell)                        ║
# ║      企业级自动化部署                                                          ║
# ║                                                                              ║
# ║      支持: Docker Desktop | WSL2 + Kubernetes                                ║
# ║                                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

param(
    [string]$Action = "menu",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# 颜色函数
function Write-Color {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Write-Info { Write-Color "[INFO] $args" "Cyan" }
function Write-Success { Write-Color "[SUCCESS] $args" "Green" }
function Write-Warning { Write-Color "[WARNING] $args" "Yellow" }
function Write-Error { Write-Color "[ERROR] $args" "Red" }

# 显示 Banner
function Show-Banner {
    Write-Host ""
    Write-Color "  ╔══════════════════════════════════════════════════════════════╗" "Magenta"
    Write-Color "  ║                                                              ║" "Magenta"
    Write-Color "  ║       ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗      ██████╗     ║" "Magenta"
    Write-Color "  ║       ██║██╔═══██╗██║████╗  ██║██╔════╝██║     ██╔═══██╗    ║" "Magenta"
    Write-Color "  ║       ██║██║   ██║██║██╔██╗ ██║█████╗  ██║     ██║   ██║    ║" "Magenta"
    Write-Color "  ║  ██   ██║██║   ██║██║██║╚██╗██║██╔══╝  ██║     ██║   ██║    ║" "Magenta"
    Write-Color "  ║  ╚█████╔╝╚██████╔╝██║██║ ╚████║██║     ███████╗╚██████╔╝    ║" "Magenta"
    Write-Color "  ║   ╚════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝     ╚══════╝ ╚═════╝     ║" "Magenta"
    Write-Color "  ║                                                              ║" "Magenta"
    Write-Color "  ║              ☁️  云服务部署工具 v1.0 (Windows)               ║" "Magenta"
    Write-Color "  ║                                                              ║" "Magenta"
    Write-Color "  ╚══════════════════════════════════════════════════════════════╝" "Magenta"
    Write-Host ""
}

# 检查 Docker
function Test-Docker {
    try {
        $null = docker version 2>&1
        return $true
    } catch {
        return $false
    }
}

# 检查先决条件
function Test-Prerequisites {
    Write-Info "检查必要的工具..."
    
    if (-not (Test-Docker)) {
        Write-Error "Docker 未安装或未运行"
        Write-Info "请安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    # 检查 Docker 是否正在运行
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker 服务未运行，请启动 Docker Desktop"
        exit 1
    }
    
    Write-Success "Docker 已就绪"
}

# 生成随机密钥
function New-Secret {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

# 创建环境配置
function New-EnvFile {
    Write-Info "创建环境配置文件..."
    
    $envPath = ".env"
    
    if ((Test-Path $envPath) -and -not $Force) {
        Write-Warning ".env 文件已存在，是否覆盖? (y/n)"
        $answer = Read-Host
        if ($answer -ne "y") {
            Write-Info "保留现有配置"
            return
        }
    }
    
    $dbPassword = New-Secret
    $jwtSecret = New-Secret
    $grafanaPassword = (New-Secret).Substring(0, 16)
    
    $envContent = @"
# JoinFlow 云服务配置
# 生成时间: $(Get-Date)

# ================================
# 必填配置
# ================================

# OpenAI API 密钥 (必填)
OPENAI_API_KEY=$($env:OPENAI_API_KEY ?? "your-openai-api-key")

# Anthropic API 密钥 (可选)
ANTHROPIC_API_KEY=$($env:ANTHROPIC_API_KEY ?? "")

# ================================
# 数据库配置
# ================================

# PostgreSQL 密码 (自动生成)
DB_PASSWORD=$dbPassword

# Redis 配置
REDIS_PASSWORD=

# ================================
# 安全配置
# ================================

# JWT 密钥 (自动生成)
JWT_SECRET=$jwtSecret

# Grafana 管理员密码 (自动生成)
GRAFANA_PASSWORD=$grafanaPassword

# ================================
# 域名配置
# ================================

# 主域名
DOMAIN=localhost

# ================================
# 运行模式
# ================================

# production | development
NODE_ENV=production

# 工作进程数
WORKERS=4
"@
    
    Set-Content -Path $envPath -Value $envContent
    Write-Success "环境配置已创建: .env"
    Write-Warning "请编辑 .env 文件，填写 OPENAI_API_KEY"
}

# 创建必要目录
function New-Directories {
    $dirs = @(
        "workspace",
        "exports", 
        "sessions",
        "knowledge_base",
        "deploy/nginx/ssl",
        "deploy/nginx/html",
        "deploy/monitoring"
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
}

# Docker 完整部署
function Deploy-Docker {
    Write-Info "开始 Docker 完整部署..."
    
    New-Directories
    
    # 构建镜像
    Write-Info "构建 Docker 镜像..."
    docker build -t joinflow/app:latest -f Dockerfile .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "镜像构建失败"
        exit 1
    }
    
    # 启动服务
    Write-Info "启动服务..."
    docker compose -f deploy/docker-compose.cloud.yml up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "服务启动失败"
        exit 1
    }
    
    Write-Success "Docker 部署完成!"
    Show-AccessInfo
}

# Docker 精简部署
function Deploy-DockerLite {
    Write-Info "开始 Docker 精简部署..."
    
    New-Directories
    
    # 构建镜像
    Write-Info "构建 Docker 镜像..."
    docker build -t joinflow/app:latest -f Dockerfile .
    
    # 启动服务
    Write-Info "启动核心服务..."
    docker compose up -d
    
    Write-Success "精简部署完成!"
    Write-Host ""
    Write-Color "访问地址: http://localhost:8000" "Green"
}

# 健康检查
function Test-Health {
    Write-Info "执行健康检查..."
    
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "服务健康检查通过!"
                return $true
            }
        } catch {
            # 继续尝试
        }
        
        Write-Info "等待服务启动... ($attempt/$maxAttempts)"
        Start-Sleep -Seconds 2
        $attempt++
    }
    
    Write-Error "服务启动超时，请检查日志"
    return $false
}

# 显示访问信息
function Show-AccessInfo {
    Write-Host ""
    Write-Color "╔══════════════════════════════════════════════════════════════╗" "Green"
    Write-Color "║                    🎉 部署成功！                              ║" "Green"
    Write-Color "╠══════════════════════════════════════════════════════════════╣" "Green"
    Write-Color "║                                                              ║" "Green"
    Write-Color "║  主页:        http://localhost:8000                          ║" "Green"
    Write-Color "║  工作台:      http://localhost:8000/workspace                ║" "Green"
    Write-Color "║  API 文档:    http://localhost:8000/docs                     ║" "Green"
    Write-Color "║                                                              ║" "Green"
    Write-Color "╠══════════════════════════════════════════════════════════════╣" "Green"
    Write-Color "║  查看日志:    docker logs -f joinflow-app                    ║" "Green"
    Write-Color "║  停止服务:    docker-compose down                            ║" "Green"
    Write-Color "║  重启服务:    docker-compose restart                         ║" "Green"
    Write-Color "╚══════════════════════════════════════════════════════════════╝" "Green"
}

# 卸载
function Uninstall-JoinFlow {
    Write-Warning "即将卸载 JoinFlow，这将删除所有数据！"
    $confirm = Read-Host "确认卸载? (yes/no)"
    
    if ($confirm -ne "yes") {
        Write-Info "取消卸载"
        return
    }
    
    Write-Info "停止并删除容器..."
    docker compose -f deploy/docker-compose.cloud.yml down -v 2>&1 | Out-Null
    docker compose down -v 2>&1 | Out-Null
    
    Write-Info "删除镜像..."
    docker rmi joinflow/app:latest 2>&1 | Out-Null
    
    Write-Success "卸载完成"
}

# 升级
function Update-JoinFlow {
    Write-Info "开始升级 JoinFlow..."
    
    if (Test-Path ".git") {
        Write-Info "拉取最新代码..."
        git pull origin main
    }
    
    Write-Info "重新构建镜像..."
    docker build -t joinflow/app:latest -f Dockerfile .
    
    Write-Info "滚动更新服务..."
    docker compose -f deploy/docker-compose.cloud.yml up -d --force-recreate
    
    Test-Health | Out-Null
    Write-Success "升级完成!"
}

# 显示菜单
function Show-Menu {
    Write-Host ""
    Write-Color "请选择部署方式:" "Cyan"
    Write-Host ""
    Write-Host "  1) Docker 完整部署 (推荐)"
    Write-Host "  2) Docker 精简部署 (仅核心服务)"
    Write-Host "  3) 升级现有部署"
    Write-Host "  4) 卸载"
    Write-Host "  5) 健康检查"
    Write-Host "  0) 退出"
    Write-Host ""
}

# 主函数
function Main {
    Show-Banner
    Test-Prerequisites
    
    switch ($Action.ToLower()) {
        "docker" {
            New-EnvFile
            Deploy-Docker
        }
        "docker-lite" {
            New-EnvFile
            Deploy-DockerLite
        }
        "upgrade" {
            Update-JoinFlow
        }
        "uninstall" {
            Uninstall-JoinFlow
        }
        "health" {
            Test-Health
        }
        default {
            # 交互式菜单
            while ($true) {
                Show-Menu
                $choice = Read-Host "请输入选项 [0-5]"
                
                switch ($choice) {
                    "1" {
                        New-EnvFile
                        Deploy-Docker
                    }
                    "2" {
                        New-EnvFile
                        Deploy-DockerLite
                    }
                    "3" {
                        Update-JoinFlow
                    }
                    "4" {
                        Uninstall-JoinFlow
                    }
                    "5" {
                        Test-Health
                    }
                    "0" {
                        Write-Info "再见!"
                        exit 0
                    }
                    default {
                        Write-Error "无效选项"
                    }
                }
            }
        }
    }
}

# 运行
Main

