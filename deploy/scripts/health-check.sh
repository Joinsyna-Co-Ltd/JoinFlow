#!/bin/bash
#
# JoinFlow 健康检查脚本
# 定期检查服务状态并自动重启失败的服务
#

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
HEALTH_URL="${HEALTH_URL:-http://localhost:8080/api/health}"
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_INTERVAL="${RETRY_INTERVAL:-10}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_TO="${EMAIL_TO:-}"
LOG_FILE="${LOG_FILE:-/var/log/joinflow/health-check.log}"

# 日志函数
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# 发送通知
send_notification() {
    local title=$1
    local message=$2
    local severity=$3  # info, warning, error

    # Slack 通知
    if [ -n "$SLACK_WEBHOOK" ]; then
        local color="good"
        [ "$severity" = "warning" ] && color="warning"
        [ "$severity" = "error" ] && color="danger"

        curl -s -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"$title\",
                    \"text\": \"$message\",
                    \"footer\": \"JoinFlow 健康检查\",
                    \"ts\": $(date +%s)
                }]
            }" > /dev/null 2>&1 || true
    fi

    # 邮件通知 (如果配置了 sendmail)
    if [ -n "$EMAIL_TO" ] && command -v sendmail &> /dev/null; then
        echo -e "Subject: [JoinFlow] $title\n\n$message" | sendmail "$EMAIL_TO" 2>/dev/null || true
    fi
}

# 检查单个服务健康状态
check_service_health() {
    local service=$1
    local url=$2
    local retries=0

    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf --max-time 10 "$url" > /dev/null 2>&1; then
            return 0
        fi
        retries=$((retries + 1))
        [ $retries -lt $MAX_RETRIES ] && sleep $RETRY_INTERVAL
    done

    return 1
}

# 检查 Docker 容器状态
check_container_status() {
    local container=$1
    local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
    
    if [ "$status" = "running" ]; then
        return 0
    else
        return 1
    fi
}

# 重启服务
restart_service() {
    local service=$1
    log "WARNING" "正在重启服务: $service"
    
    cd /opt/joinflow/deploy
    docker-compose restart "$service"
    
    # 等待服务启动
    sleep 30
    
    if check_container_status "joinflow_${service}_1" || check_container_status "joinflow-${service}-1"; then
        log "INFO" "服务 $service 已成功重启"
        send_notification "服务恢复" "服务 $service 已自动重启并恢复正常" "info"
        return 0
    else
        log "ERROR" "服务 $service 重启失败"
        send_notification "服务重启失败" "服务 $service 多次重启失败，需要人工介入" "error"
        return 1
    fi
}

# 主健康检查
main_health_check() {
    log "INFO" "开始健康检查..."
    local all_healthy=true

    # 检查 Web 服务
    echo -e "${BLUE}检查 Web 服务...${NC}"
    if ! check_service_health "web" "$HEALTH_URL"; then
        log "ERROR" "Web 服务健康检查失败"
        send_notification "服务异常" "JoinFlow Web 服务无响应，尝试自动重启" "warning"
        all_healthy=false
        restart_service "web"
    else
        echo -e "${GREEN}✓ Web 服务正常${NC}"
        log "INFO" "Web 服务健康"
    fi

    # 检查 Nginx
    echo -e "${BLUE}检查 Nginx 服务...${NC}"
    if ! check_service_health "nginx" "http://localhost/health"; then
        log "ERROR" "Nginx 服务健康检查失败"
        send_notification "服务异常" "Nginx 服务无响应，尝试自动重启" "warning"
        all_healthy=false
        restart_service "nginx"
    else
        echo -e "${GREEN}✓ Nginx 服务正常${NC}"
        log "INFO" "Nginx 服务健康"
    fi

    # 检查 Qdrant (向量数据库)
    echo -e "${BLUE}检查 Qdrant 服务...${NC}"
    if ! check_service_health "qdrant" "http://localhost:6333/health"; then
        log "WARNING" "Qdrant 服务可能不可用 (非关键)"
        echo -e "${YELLOW}⚠ Qdrant 服务可能不可用${NC}"
    else
        echo -e "${GREEN}✓ Qdrant 服务正常${NC}"
        log "INFO" "Qdrant 服务健康"
    fi

    # 检查磁盘空间
    echo -e "${BLUE}检查磁盘空间...${NC}"
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$disk_usage" -gt 90 ]; then
        log "WARNING" "磁盘空间不足: ${disk_usage}%"
        send_notification "磁盘告警" "磁盘使用率已达 ${disk_usage}%，请及时清理" "warning"
        echo -e "${YELLOW}⚠ 磁盘使用率: ${disk_usage}%${NC}"
    else
        echo -e "${GREEN}✓ 磁盘使用率: ${disk_usage}%${NC}"
    fi

    # 检查内存
    echo -e "${BLUE}检查内存使用...${NC}"
    local mem_usage=$(free | awk '/Mem:/ {printf("%.0f", $3/$2 * 100)}')
    if [ "$mem_usage" -gt 90 ]; then
        log "WARNING" "内存使用率过高: ${mem_usage}%"
        send_notification "内存告警" "内存使用率已达 ${mem_usage}%，可能影响服务性能" "warning"
        echo -e "${YELLOW}⚠ 内存使用率: ${mem_usage}%${NC}"
    else
        echo -e "${GREEN}✓ 内存使用率: ${mem_usage}%${NC}"
    fi

    # 总结
    echo ""
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}═══════════════════════════════════${NC}"
        echo -e "${GREEN}  ✓ 所有服务运行正常${NC}"
        echo -e "${GREEN}═══════════════════════════════════${NC}"
        log "INFO" "健康检查完成: 所有服务正常"
    else
        echo -e "${YELLOW}═══════════════════════════════════${NC}"
        echo -e "${YELLOW}  ⚠ 部分服务已自动重启${NC}"
        echo -e "${YELLOW}═══════════════════════════════════${NC}"
        log "WARNING" "健康检查完成: 部分服务已重启"
    fi
}

# 系统资源报告
resource_report() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║          系统资源报告                   ║"
    echo "╠════════════════════════════════════════╣"
    
    # CPU
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    printf "║  CPU 使用率:    %-20s  ║\n" "${cpu_usage:-N/A}%"
    
    # 内存
    local mem_info=$(free -h | awk '/Mem:/ {printf "%s / %s", $3, $2}')
    printf "║  内存使用:      %-20s  ║\n" "$mem_info"
    
    # 磁盘
    local disk_info=$(df -h / | awk 'NR==2 {printf "%s / %s", $3, $2}')
    printf "║  磁盘使用:      %-20s  ║\n" "$disk_info"
    
    # Docker 容器数
    local running=$(docker ps -q | wc -l)
    local total=$(docker ps -aq | wc -l)
    printf "║  Docker 容器:   %-20s  ║\n" "$running / $total 运行中"
    
    echo "╚════════════════════════════════════════╝"
}

# 帮助信息
show_help() {
    echo "JoinFlow 健康检查工具"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  check       执行健康检查 (默认)"
    echo "  report      显示系统资源报告"
    echo "  watch       持续监控模式"
    echo "  help        显示帮助信息"
    echo ""
    echo "环境变量:"
    echo "  HEALTH_URL       健康检查 URL (默认: http://localhost:8080/api/health)"
    echo "  MAX_RETRIES      重试次数 (默认: 3)"
    echo "  RETRY_INTERVAL   重试间隔秒数 (默认: 10)"
    echo "  SLACK_WEBHOOK    Slack 通知 Webhook URL"
    echo "  EMAIL_TO         邮件通知地址"
}

# 持续监控模式
watch_mode() {
    local interval=${WATCH_INTERVAL:-60}
    echo "进入持续监控模式，每 ${interval} 秒检查一次 (Ctrl+C 退出)"
    
    while true; do
        clear
        echo "╔════════════════════════════════════════╗"
        echo "║    JoinFlow 实时监控                    ║"
        echo "║    $(date '+%Y-%m-%d %H:%M:%S')              ║"
        echo "╚════════════════════════════════════════╝"
        echo ""
        
        main_health_check
        resource_report
        
        echo ""
        echo "下次检查: $(date -d "+${interval} seconds" '+%H:%M:%S')"
        sleep $interval
    done
}

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 主入口
case "${1:-check}" in
    check)
        main_health_check
        ;;
    report)
        resource_report
        ;;
    watch)
        watch_mode
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "未知命令: $1"
        show_help
        exit 1
        ;;
esac

