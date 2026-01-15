#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                              ║
# ║      JoinFlow 云服务一键部署脚本                                              ║
# ║      企业级自动化部署                                                          ║
# ║                                                                              ║
# ║      支持: Docker | Kubernetes | 阿里云 | 腾讯云 | AWS | Azure               ║
# ║                                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logo
show_banner() {
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
    echo "  ║              ☁️  云服务部署工具 v1.0                          ║"
    echo "  ║                                                              ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 日志函数
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        return 1
    fi
    return 0
}

# 检查必要的工具
check_prerequisites() {
    log_info "检查必要的工具..."
    
    local missing=()
    
    if ! check_command docker; then
        missing+=("docker")
    fi
    
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        missing+=("docker-compose")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "缺少以下工具: ${missing[*]}"
        log_info "请先安装这些工具后再运行此脚本"
        exit 1
    fi
    
    log_success "所有必要工具已就绪"
}

# 生成安全的随机密钥
generate_secret() {
    openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64
}

# 创建环境配置
create_env_file() {
    log_info "创建环境配置文件..."
    
    if [ -f ".env" ]; then
        log_warning ".env 文件已存在，是否覆盖? (y/n)"
        read -r answer
        if [ "$answer" != "y" ]; then
            log_info "保留现有配置"
            return
        fi
    fi
    
    cat > .env << EOF
# JoinFlow 云服务配置
# 生成时间: $(date)

# ================================
# 必填配置
# ================================

# OpenAI API 密钥 (必填)
OPENAI_API_KEY=${OPENAI_API_KEY:-your-openai-api-key}

# Anthropic API 密钥 (可选)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

# ================================
# 数据库配置
# ================================

# PostgreSQL 密码 (自动生成)
DB_PASSWORD=$(generate_secret)

# Redis 配置
REDIS_PASSWORD=

# ================================
# 安全配置
# ================================

# JWT 密钥 (自动生成)
JWT_SECRET=$(generate_secret)

# Grafana 管理员密码 (自动生成)
GRAFANA_PASSWORD=$(generate_secret | cut -c1-16)

# ================================
# 云存储配置 (可选)
# ================================

# S3 兼容存储
S3_BUCKET=
S3_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=

# ================================
# 域名配置
# ================================

# 主域名
DOMAIN=localhost

# SSL 证书邮箱 (用于 Let's Encrypt)
SSL_EMAIL=

# ================================
# 运行模式
# ================================

# production | development
NODE_ENV=production

# 工作进程数
WORKERS=4

EOF
    
    log_success "环境配置已创建: .env"
    log_warning "请编辑 .env 文件，填写 OPENAI_API_KEY"
}

# Docker 单机部署
deploy_docker() {
    log_info "开始 Docker 单机部署..."
    
    # 创建必要的目录
    mkdir -p deploy/nginx/ssl
    mkdir -p deploy/nginx/html
    mkdir -p deploy/monitoring
    mkdir -p workspace exports sessions
    
    # 创建自签名证书 (开发环境)
    if [ ! -f "deploy/nginx/ssl/fullchain.pem" ]; then
        log_info "生成自签名 SSL 证书..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout deploy/nginx/ssl/privkey.pem \
            -out deploy/nginx/ssl/fullchain.pem \
            -subj "/CN=localhost" 2>/dev/null || true
    fi
    
    # 构建镜像
    log_info "构建 Docker 镜像..."
    docker build -t joinflow/app:latest -f Dockerfile .
    
    # 启动服务
    log_info "启动服务..."
    if docker compose version &> /dev/null; then
        docker compose -f deploy/docker-compose.cloud.yml up -d
    else
        docker-compose -f deploy/docker-compose.cloud.yml up -d
    fi
    
    log_success "Docker 部署完成!"
    show_access_info
}

# Docker 精简部署 (仅核心服务)
deploy_docker_lite() {
    log_info "开始 Docker 精简部署..."
    
    # 创建必要的目录
    mkdir -p workspace exports sessions knowledge_base
    
    # 构建镜像
    log_info "构建 Docker 镜像..."
    docker build -t joinflow/app:latest -f Dockerfile .
    
    # 使用基础 docker-compose
    log_info "启动核心服务..."
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    
    log_success "精简部署完成!"
    echo ""
    echo -e "${GREEN}访问地址: http://localhost:8000${NC}"
}

# Kubernetes 部署
deploy_kubernetes() {
    log_info "开始 Kubernetes 部署..."
    
    if ! check_command kubectl; then
        log_error "未找到 kubectl，请先安装 kubectl"
        exit 1
    fi
    
    # 检查集群连接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "无法连接到 Kubernetes 集群"
        exit 1
    fi
    
    # 创建命名空间
    kubectl create namespace joinflow --dry-run=client -o yaml | kubectl apply -f -
    
    # 创建 Secret
    log_info "创建 Kubernetes Secrets..."
    kubectl create secret generic joinflow-secrets \
        --from-env-file=.env \
        --namespace=joinflow \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # 部署应用
    log_info "部署应用..."
    kubectl apply -f deploy/kubernetes/
    
    # 等待部署完成
    log_info "等待 Pod 就绪..."
    kubectl wait --for=condition=ready pod -l app=joinflow -n joinflow --timeout=300s
    
    log_success "Kubernetes 部署完成!"
    
    # 获取访问信息
    echo ""
    log_info "获取 Ingress IP..."
    kubectl get ingress -n joinflow
}

# 阿里云部署
deploy_aliyun() {
    log_info "开始阿里云 ACK 部署..."
    
    if ! check_command aliyun; then
        log_error "未找到阿里云 CLI，请先安装: pip install aliyun-python-sdk-core"
        log_info "或访问: https://help.aliyun.com/document_detail/139508.html"
        exit 1
    fi
    
    log_info "使用阿里云容器服务 ACK 进行部署..."
    log_info "请确保已配置 aliyun CLI 并拥有 ACK 集群"
    
    # 获取集群凭证
    read -p "请输入 ACK 集群 ID: " cluster_id
    aliyun cs GET /k8s/$cluster_id/user_config | jq -r '.config' > kubeconfig.yaml
    export KUBECONFIG=kubeconfig.yaml
    
    deploy_kubernetes
}

# 腾讯云部署
deploy_tencent() {
    log_info "开始腾讯云 TKE 部署..."
    
    if ! check_command tccli; then
        log_error "未找到腾讯云 CLI，请先安装: pip install tccli"
        exit 1
    fi
    
    log_info "使用腾讯云容器服务 TKE 进行部署..."
    log_info "请确保已配置 tccli 并拥有 TKE 集群"
    
    read -p "请输入 TKE 集群 ID: " cluster_id
    tccli tke DescribeClusterKubeconfig --ClusterId $cluster_id > kubeconfig.yaml
    export KUBECONFIG=kubeconfig.yaml
    
    deploy_kubernetes
}

# AWS 部署
deploy_aws() {
    log_info "开始 AWS EKS 部署..."
    
    if ! check_command aws; then
        log_error "未找到 AWS CLI，请先安装: pip install awscli"
        exit 1
    fi
    
    if ! check_command eksctl; then
        log_warning "建议安装 eksctl 进行 EKS 管理"
    fi
    
    log_info "使用 AWS EKS 进行部署..."
    
    read -p "请输入 EKS 集群名称: " cluster_name
    read -p "请输入 AWS Region: " region
    
    aws eks update-kubeconfig --name $cluster_name --region $region
    
    deploy_kubernetes
}

# 显示访问信息
show_access_info() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 部署成功！                              ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  主页:        http://localhost:8000                          ║${NC}"
    echo -e "${GREEN}║  工作台:      http://localhost:8000/workspace                ║${NC}"
    echo -e "${GREEN}║  API 文档:    http://localhost:8000/docs                     ║${NC}"
    echo -e "${GREEN}║  监控面板:    http://localhost:3000 (admin/admin)            ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  查看日志:    docker logs -f joinflow-app                    ║${NC}"
    echo -e "${GREEN}║  停止服务:    docker-compose down                            ║${NC}"
    echo -e "${GREEN}║  重启服务:    docker-compose restart                         ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "服务健康检查通过!"
            return 0
        fi
        
        log_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "服务启动超时，请检查日志"
    return 1
}

# 卸载
uninstall() {
    log_warning "即将卸载 JoinFlow，这将删除所有数据！"
    read -p "确认卸载? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消卸载"
        return
    fi
    
    log_info "停止并删除容器..."
    docker-compose -f deploy/docker-compose.cloud.yml down -v 2>/dev/null || true
    docker-compose down -v 2>/dev/null || true
    
    log_info "删除镜像..."
    docker rmi joinflow/app:latest 2>/dev/null || true
    docker rmi joinflow/sandbox:latest 2>/dev/null || true
    
    log_success "卸载完成"
}

# 升级
upgrade() {
    log_info "开始升级 JoinFlow..."
    
    # 拉取最新代码
    if [ -d ".git" ]; then
        log_info "拉取最新代码..."
        git pull origin main
    fi
    
    # 重新构建镜像
    log_info "重新构建镜像..."
    docker build -t joinflow/app:latest -f Dockerfile .
    
    # 滚动更新
    log_info "滚动更新服务..."
    if docker compose version &> /dev/null; then
        docker compose -f deploy/docker-compose.cloud.yml up -d --force-recreate
    else
        docker-compose -f deploy/docker-compose.cloud.yml up -d --force-recreate
    fi
    
    health_check
    log_success "升级完成!"
}

# 主菜单
show_menu() {
    echo ""
    echo -e "${CYAN}请选择部署方式:${NC}"
    echo ""
    echo "  1) Docker 完整部署 (推荐)"
    echo "  2) Docker 精简部署 (仅核心服务)"
    echo "  3) Kubernetes 部署"
    echo "  4) 阿里云 ACK 部署"
    echo "  5) 腾讯云 TKE 部署"
    echo "  6) AWS EKS 部署"
    echo "  7) 升级现有部署"
    echo "  8) 卸载"
    echo "  9) 健康检查"
    echo "  0) 退出"
    echo ""
}

# 主函数
main() {
    show_banner
    check_prerequisites
    
    # 检查是否有命令行参数
    if [ $# -gt 0 ]; then
        case "$1" in
            docker)
                create_env_file
                deploy_docker
                ;;
            docker-lite)
                create_env_file
                deploy_docker_lite
                ;;
            k8s|kubernetes)
                create_env_file
                deploy_kubernetes
                ;;
            aliyun)
                create_env_file
                deploy_aliyun
                ;;
            tencent)
                create_env_file
                deploy_tencent
                ;;
            aws)
                create_env_file
                deploy_aws
                ;;
            upgrade)
                upgrade
                ;;
            uninstall)
                uninstall
                ;;
            health)
                health_check
                ;;
            *)
                echo "用法: $0 {docker|docker-lite|k8s|aliyun|tencent|aws|upgrade|uninstall|health}"
                exit 1
                ;;
        esac
        return
    fi
    
    # 交互式菜单
    while true; do
        show_menu
        read -p "请输入选项 [0-9]: " choice
        
        case $choice in
            1)
                create_env_file
                deploy_docker
                ;;
            2)
                create_env_file
                deploy_docker_lite
                ;;
            3)
                create_env_file
                deploy_kubernetes
                ;;
            4)
                create_env_file
                deploy_aliyun
                ;;
            5)
                create_env_file
                deploy_tencent
                ;;
            6)
                create_env_file
                deploy_aws
                ;;
            7)
                upgrade
                ;;
            8)
                uninstall
                ;;
            9)
                health_check
                ;;
            0)
                log_info "再见!"
                exit 0
                ;;
            *)
                log_error "无效选项"
                ;;
        esac
    done
}

# 运行主函数
main "$@"

