# JoinFlow 云部署指南

## 🚀 快速开始

### 方式一：本地 Docker 部署

```bash
# 启动所有服务
./start.sh

# 或使用 Docker Compose
docker-compose up -d
```

### 方式二：一键云部署

```bash
# Linux/Mac
./deploy/cloud-deploy.sh

# Windows PowerShell
.\deploy\cloud-deploy.ps1
```

## 📦 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (80/443)                       │
│                    反向代理 & SSL 终端                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ JoinFlow │    │ JoinFlow │    │  Qdrant  │
    │   Web    │    │   Web    │    │  向量库  │
    │  :8080   │    │  :8081   │    │  :6333   │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┴───────────────┘
                           │
                    ┌──────────────┐
                    │   数据卷     │
                    │  持久化存储   │
                    └──────────────┘
```

## 📁 目录结构

```
deploy/
├── docker-compose.yml        # 开发环境配置
├── docker-compose.prod.yml   # 生产环境配置
├── Dockerfile                # 应用镜像构建
├── cloud-deploy.sh           # Linux/Mac 部署脚本
├── cloud-deploy.ps1          # Windows 部署脚本
├── nginx/
│   ├── nginx.conf            # Nginx 主配置
│   └── conf.d/
│       ├── default.conf      # HTTP 站点配置
│       ├── proxy_params.conf # 代理参数
│       └── ssl.conf.template # SSL 配置模板
└── scripts/
    ├── health-check.sh       # 健康检查脚本
    └── systemd/
        ├── joinflow.service       # 主服务单元
        ├── joinflow-health.service # 健康检查服务
        └── joinflow-health.timer   # 定时健康检查
```

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 必填 |
| `DOMAIN` | 域名 | 可选 |
| `EMAIL` | Let's Encrypt 邮箱 | 可选 |
| `QDRANT_HOST` | Qdrant 地址 | qdrant |
| `QDRANT_PORT` | Qdrant 端口 | 6333 |

## 🛡️ SSL 证书

### 自动 Let's Encrypt

```bash
./deploy/cloud-deploy.sh --domain example.com --email admin@example.com
```

### 自定义证书

```bash
# 将证书放置到:
/etc/letsencrypt/live/your-domain/fullchain.pem
/etc/letsencrypt/live/your-domain/privkey.pem
```

## 📊 健康监控

### 手动检查

```bash
./deploy/scripts/health-check.sh check
```

### 查看资源报告

```bash
./deploy/scripts/health-check.sh report
```

### 持续监控模式

```bash
./deploy/scripts/health-check.sh watch
```

### 配置告警

```bash
# 设置环境变量
export SLACK_WEBHOOK="https://hooks.slack.com/..."
export EMAIL_TO="admin@example.com"

# 运行健康检查 (失败时自动告警)
./deploy/scripts/health-check.sh check
```

## 🔄 服务管理

### Systemd (推荐)

```bash
# 安装服务
sudo cp deploy/scripts/systemd/*.service /etc/systemd/system/
sudo cp deploy/scripts/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload

# 启动服务
sudo systemctl enable joinflow
sudo systemctl start joinflow

# 启用健康检查
sudo systemctl enable joinflow-health.timer
sudo systemctl start joinflow-health.timer

# 查看状态
sudo systemctl status joinflow
```

### Docker Compose

```bash
# 启动
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启
docker-compose -f docker-compose.prod.yml restart

# 停止
docker-compose -f docker-compose.prod.yml down
```

## ☁️ 云平台部署

### AWS EC2

```bash
./deploy/cloud-deploy.sh --provider aws \
  --server your-ec2-ip \
  --key-file ~/.ssh/your-key.pem
```

### Azure VM

```bash
./deploy/cloud-deploy.sh --provider azure \
  --server your-vm-ip \
  --key-file ~/.ssh/your-key.pem
```

### 阿里云 ECS

```bash
./deploy/cloud-deploy.sh --provider aliyun \
  --server your-ecs-ip \
  --key-file ~/.ssh/your-key.pem
```

## 🔐 安全建议

1. **使用 HTTPS**: 始终启用 SSL 加密
2. **防火墙**: 仅开放必要端口 (80, 443)
3. **API 密钥**: 使用环境变量，不要硬编码
4. **定期备份**: 配置数据卷自动备份
5. **更新**: 定期更新依赖和镜像

## 📈 性能优化

### Nginx 缓存

```nginx
# 已在配置中启用
proxy_cache_path /var/cache/nginx ...
```

### Docker 资源限制

```yaml
# docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

## 🐛 故障排除

### 服务无法启动

```bash
# 检查日志
docker-compose logs web

# 检查配置
docker-compose config
```

### 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep 8080
lsof -i :8080
```

### 健康检查失败

```bash
# 手动检查
curl http://localhost:8080/api/health
```

## 📞 支持

- 文档: https://docs.joinflow.ai
- GitHub: https://github.com/YOUR_REPO/joinflow
- 问题反馈: https://github.com/YOUR_REPO/joinflow/issues

