# JoinFlow 云服务一键部署 - Windows PowerShell 版本
# 用于在本地 Windows 机器上部署到远程服务器

param(
    [string]$ServerIP,
    [string]$Username = "root",
    [string]$KeyFile,
    [string]$OpenAIKey,
    [string]$Domain,
    [string]$Email
)

$ErrorActionPreference = "Stop"

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              JoinFlow 云服务远程部署工具                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta

# 检查 SSH
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] 未找到 SSH，请安装 OpenSSH" -ForegroundColor Red
    exit 1
}

# 交互式输入
if (-not $ServerIP) {
    $ServerIP = Read-Host "请输入服务器 IP"
}
if (-not $OpenAIKey) {
    $OpenAIKey = Read-Host "请输入 OpenAI API Key"
}

# 构建 SSH 命令
$sshArgs = @("-o", "StrictHostKeyChecking=no")
if ($KeyFile) {
    $sshArgs += @("-i", $KeyFile)
}

Write-Host "[INFO] 连接到服务器 $ServerIP..." -ForegroundColor Cyan

# 上传部署脚本
$deployScript = @"
#!/bin/bash
export OPENAI_API_KEY='$OpenAIKey'
export DOMAIN='$Domain'
export EMAIL='$Email'

# 下载并执行部署脚本
curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/joinflow/main/deploy/cloud-deploy.sh | bash -s -- --quick
"@

# 执行远程部署
$deployScript | ssh $sshArgs "$Username@$ServerIP" "bash -s"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                   🎉 部署成功！                               ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "访问地址: http://$ServerIP" -ForegroundColor Cyan
    if ($Domain) {
        Write-Host "域名访问: https://$Domain" -ForegroundColor Cyan
    }
} else {
    Write-Host "[ERROR] 部署失败" -ForegroundColor Red
}

