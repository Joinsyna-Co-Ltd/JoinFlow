#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                              ║
# ║     ██╗ ██████╗ ██╗███╗   ██╗███████╗██╗      ██████╗ ██╗    ██╗            ║
# ║     ██║██╔═══██╗██║████╗  ██║██╔════╝██║     ██╔═══██╗██║    ██║            ║
# ║     ██║██║   ██║██║██╔██╗ ██║█████╗  ██║     ██║   ██║██║ █╗ ██║            ║
# ║██   ██║██║   ██║██║██║╚██╗██║██╔══╝  ██║     ██║   ██║██║███╗██║            ║
# ║╚█████╔╝╚██████╔╝██║██║ ╚████║██║     ███████╗╚██████╔╝╚███╔███╔╝            ║
# ║ ╚════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝             ║
# ║                                                                              ║
# ║                    一键云部署脚本 - 企业版                                    ║
# ║             支持: 阿里云 | 腾讯云 | AWS | Azure | 通用 VPS                   ║
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

# 配置
INSTALL_DIR="/opt/joinflow"
DOMAIN=""
EMAIL=""
OPENAI_API_KEY=""
CLOUD_PROVIDER=""

# 打印 Banner
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              JoinFlow 云服务一键部署                         ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
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

# 检查 root 权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 用户运行此脚本"
        log_info "尝试: sudo bash cloud-deploy.sh"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    log_info "检测到操作系统: $OS $VER"
}

# 安装 Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker 已安装: $(docker --version)"
        return 0
    fi

    log_info "安装 Docker..."
    
    # 根据系统安装
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Alibaba"* ]]; then
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        # 通用安装脚本
        curl -fsSL https://get.docker.com | sh
    fi

    # 启动 Docker
    systemctl enable docker
    systemctl start docker
    
    log_success "Docker 安装完成"
}

# 安装 Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        log_success "Docker Compose 已安装"
        return 0
    fi

    log_info "安装 Docker Compose..."
    
    # 安装 Docker Compose 插件
    mkdir -p ~/.docker/cli-plugins/
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m) -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
    
    # 创建软链接
    ln -sf ~/.docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
    
    log_success "Docker Compose 安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 22/tcp
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --reload
    fi
    
    log_success "防火墙配置完成"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/deploy/nginx/conf.d
    mkdir -p $INSTALL_DIR/deploy/certbot/conf
    mkdir -p $INSTALL_DIR/deploy/certbot/www
    mkdir -p $INSTALL_DIR/data
    mkdir -p $INSTALL_DIR/logs
    
    log_success "目录创建完成"
}

# 下载配置文件
download_configs() {
    log_info "下载配置文件..."
    
    cd $INSTALL_DIR
    
    # 如果是从 git 仓库克隆
    if [ -d ".git" ]; then
        git pull origin main
    else
        # 下载必要的配置文件
        # 这里假设从 GitHub 或其他地方下载
        log_info "请确保配置文件已放置在 $INSTALL_DIR/deploy 目录下"
    fi
    
    log_success "配置文件准备完成"
}

# 创建环境配置文件
create_env_file() {
    log_info "创建环境配置..."
    
    cat > $INSTALL_DIR/deploy/.env << EOF
# JoinFlow 云服务环境配置
# 生成时间: $(date)

# OpenAI API 配置
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://api.openai.com/v1}
DEFAULT_MODEL=${DEFAULT_MODEL:-gpt-4o-mini}

# 服务配置
WORKERS=2
JOINFLOW_ENV=production

# 域名配置
DOMAIN=${DOMAIN}
EMAIL=${EMAIL}

# 数据库配置（可选）
DATABASE_URL=sqlite:///./data/joinflow.db
EOF

    chmod 600 $INSTALL_DIR/deploy/.env
    log_success "环境配置创建完成"
}

# 获取 SSL 证书
setup_ssl() {
    if [ -z "$DOMAIN" ]; then
        log_warning "未配置域名，跳过 SSL 配置"
        return 0
    fi

    log_info "配置 SSL 证书..."
    
    # 首先启动 Nginx 进行 HTTP 验证
    cd $INSTALL_DIR/deploy
    docker compose -f docker-compose.prod.yml up -d nginx
    
    # 等待 Nginx 启动
    sleep 5
    
    # 获取证书
    docker compose -f docker-compose.prod.yml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN
    
    # 更新 Nginx 配置启用 HTTPS
    sed -i 's/# server {/server {/g' nginx/conf.d/joinflow.conf
    sed -i "s/your-domain.com/$DOMAIN/g" nginx/conf.d/joinflow.conf
    
    # 重启 Nginx
    docker compose -f docker-compose.prod.yml restart nginx
    
    log_success "SSL 证书配置完成"
}

# 启动服务
start_services() {
    log_info "启动 JoinFlow 服务..."
    
    cd $INSTALL_DIR/deploy
    
    # 拉取最新镜像
    docker compose -f docker-compose.prod.yml pull 2>/dev/null || true
    
    # 构建并启动
    docker compose -f docker-compose.prod.yml up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败，请检查日志"
        docker compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# 创建 systemd 服务
create_systemd_service() {
    log_info "创建 systemd 服务..."
    
    cat > /etc/systemd/system/joinflow.service << EOF
[Unit]
Description=JoinFlow AI Agent Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR/deploy
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.prod.yml restart

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable joinflow
    
    log_success "systemd 服务创建完成"
}

# 创建管理脚本
create_management_scripts() {
    log_info "创建管理脚本..."
    
    # 状态脚本
    cat > $INSTALL_DIR/status.sh << 'EOF'
#!/bin/bash
cd /opt/joinflow/deploy
docker compose -f docker-compose.prod.yml ps
echo ""
echo "=== 资源使用 ==="
docker stats --no-stream
EOF
    chmod +x $INSTALL_DIR/status.sh

    # 日志脚本
    cat > $INSTALL_DIR/logs.sh << 'EOF'
#!/bin/bash
cd /opt/joinflow/deploy
docker compose -f docker-compose.prod.yml logs -f --tail=100
EOF
    chmod +x $INSTALL_DIR/logs.sh

    # 重启脚本
    cat > $INSTALL_DIR/restart.sh << 'EOF'
#!/bin/bash
cd /opt/joinflow/deploy
docker compose -f docker-compose.prod.yml restart
echo "服务已重启"
EOF
    chmod +x $INSTALL_DIR/restart.sh

    # 更新脚本
    cat > $INSTALL_DIR/update.sh << 'EOF'
#!/bin/bash
cd /opt/joinflow/deploy
echo "拉取最新代码..."
git pull origin main 2>/dev/null || true
echo "重建并重启服务..."
docker compose -f docker-compose.prod.yml up -d --build
echo "更新完成"
EOF
    chmod +x $INSTALL_DIR/update.sh

    # 备份脚本
    cat > $INSTALL_DIR/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/joinflow/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cd /opt/joinflow/deploy
docker compose -f docker-compose.prod.yml exec -T joinflow tar czf - /app/workspace /app/exports /app/sessions > $BACKUP_DIR/data.tar.gz
echo "备份完成: $BACKUP_DIR"
EOF
    chmod +x $INSTALL_DIR/backup.sh

    log_success "管理脚本创建完成"
}

# 显示安装结果
show_result() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║               🎉 JoinFlow 部署成功！                          ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    # 获取服务器 IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
    
    echo -e "${CYAN}访问地址:${NC}"
    if [ -n "$DOMAIN" ]; then
        echo "  🌐 https://$DOMAIN"
    fi
    echo "  🌐 http://$SERVER_IP"
    echo ""
    
    echo -e "${CYAN}管理命令:${NC}"
    echo "  📊 查看状态: $INSTALL_DIR/status.sh"
    echo "  📋 查看日志: $INSTALL_DIR/logs.sh"
    echo "  🔄 重启服务: $INSTALL_DIR/restart.sh"
    echo "  ⬆️  更新服务: $INSTALL_DIR/update.sh"
    echo "  💾 备份数据: $INSTALL_DIR/backup.sh"
    echo ""
    
    echo -e "${CYAN}systemd 命令:${NC}"
    echo "  systemctl status joinflow  # 查看状态"
    echo "  systemctl restart joinflow # 重启服务"
    echo "  systemctl stop joinflow    # 停止服务"
    echo ""
    
    echo -e "${YELLOW}注意事项:${NC}"
    echo "  1. 请确保 OpenAI API Key 已正确配置"
    echo "  2. 建议配置域名和 SSL 证书"
    echo "  3. 定期执行备份脚本保护数据"
    echo ""
}

# 交互式配置
interactive_config() {
    print_banner
    
    echo -e "${CYAN}请输入以下配置信息:${NC}"
    echo ""
    
    # OpenAI API Key
    read -p "OpenAI API Key (必填): " OPENAI_API_KEY
    if [ -z "$OPENAI_API_KEY" ]; then
        log_error "OpenAI API Key 不能为空"
        exit 1
    fi
    
    # API Base URL
    read -p "OpenAI API Base URL [https://api.openai.com/v1]: " OPENAI_BASE_URL
    OPENAI_BASE_URL=${OPENAI_BASE_URL:-"https://api.openai.com/v1"}
    
    # 默认模型
    read -p "默认模型 [gpt-4o-mini]: " DEFAULT_MODEL
    DEFAULT_MODEL=${DEFAULT_MODEL:-"gpt-4o-mini"}
    
    # 域名（可选）
    read -p "域名 (可选，回车跳过): " DOMAIN
    
    # 邮箱（SSL 证书需要）
    if [ -n "$DOMAIN" ]; then
        read -p "邮箱 (SSL 证书通知): " EMAIL
    fi
    
    echo ""
    echo -e "${CYAN}配置确认:${NC}"
    echo "  API Key: ${OPENAI_API_KEY:0:10}..."
    echo "  API URL: $OPENAI_BASE_URL"
    echo "  模型: $DEFAULT_MODEL"
    echo "  域名: ${DOMAIN:-无}"
    echo ""
    
    read -p "确认开始部署? [Y/n]: " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        echo "已取消"
        exit 0
    fi
}

# 快速部署（使用环境变量）
quick_deploy() {
    if [ -z "$OPENAI_API_KEY" ]; then
        log_error "请设置 OPENAI_API_KEY 环境变量"
        echo "示例: export OPENAI_API_KEY=sk-xxx && bash cloud-deploy.sh --quick"
        exit 1
    fi
}

# 显示帮助
show_help() {
    echo "JoinFlow 云服务一键部署脚本"
    echo ""
    echo "用法: bash cloud-deploy.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --quick       快速部署（使用环境变量）"
    echo "  --domain      指定域名"
    echo "  --email       指定邮箱"
    echo "  --help        显示帮助"
    echo ""
    echo "示例:"
    echo "  bash cloud-deploy.sh                    # 交互式部署"
    echo "  OPENAI_API_KEY=sk-xxx bash cloud-deploy.sh --quick"
    echo "  bash cloud-deploy.sh --domain example.com --email admin@example.com"
}

# 主函数
main() {
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                quick_deploy
                shift
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                shift
                ;;
        esac
    done

    # 如果没有必要的配置，进入交互模式
    if [ -z "$OPENAI_API_KEY" ]; then
        interactive_config
    fi

    # 执行部署步骤
    check_root
    detect_os
    install_docker
    install_docker_compose
    configure_firewall
    create_directories
    download_configs
    create_env_file
    start_services
    
    # SSL 配置（如果有域名）
    if [ -n "$DOMAIN" ] && [ -n "$EMAIL" ]; then
        setup_ssl
    fi
    
    create_systemd_service
    create_management_scripts
    show_result
}

# 运行
main "$@"

