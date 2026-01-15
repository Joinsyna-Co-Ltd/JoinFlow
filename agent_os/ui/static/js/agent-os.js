/**
 * Agent OS - 智能操作系统代理
 * Version: 2.5 Neural
 * 前端交互系统
 */

const AgentOS = {
    // ==================== 配置 ====================
    config: {
        apiBase: '/api',
        autoConfirm: false,
        soundEnabled: true,
        animationsEnabled: true,
        theme: 'dark'
    },
    
    // ==================== 状态 ====================
    state: {
        sidebarCollapsed: false,
        mobileSidebarOpen: false,
        currentPanel: 'terminal',
        commandHistory: [],
        historyIndex: -1,
        tasks: [],
        systemInfo: null,
        isLoading: false
    },
    
    // ==================== 初始化 ====================
    init() {
        console.log(
            '%c🚀 Agent OS v2.5 Neural',
            'background: linear-gradient(135deg, #00E5FF, #7C4DFF); color: #0A0E14; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 16px;'
        );
        
        this.setupNavigation();
        this.setupInput();
        this.setupKeyboardShortcuts();
        this.loadSettings();
        this.loadSystemInfo();
        this.startSystemMonitor();
        this.initAnimations();
        this.createParticles();
    },
    
    // ==================== 动画初始化 ====================
    initAnimations() {
        if (!this.config.animationsEnabled) return;
        
        // 欢迎界面元素动画
        const animatedElements = document.querySelectorAll('.capability-card, .chip, .info-card');
        animatedElements.forEach((el, i) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            setTimeout(() => {
                el.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, 100 + i * 60);
        });
    },
    
    // 创建背景粒子
    createParticles() {
        const container = document.getElementById('particles');
        if (!container) return;
        
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: ${Math.random() * 4 + 2}px;
                height: ${Math.random() * 4 + 2}px;
                background: rgba(0, 229, 255, ${Math.random() * 0.3 + 0.1});
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: particleFloat ${Math.random() * 10 + 10}s ease-in-out infinite;
                animation-delay: ${Math.random() * 5}s;
            `;
            container.appendChild(particle);
        }
        
        // 添加粒子动画样式
        if (!document.getElementById('particleStyles')) {
            const style = document.createElement('style');
            style.id = 'particleStyles';
            style.textContent = `
                @keyframes particleFloat {
                    0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
                    25% { transform: translate(20px, -20px) scale(1.2); opacity: 0.5; }
                    50% { transform: translate(-10px, 20px) scale(0.8); opacity: 0.2; }
                    75% { transform: translate(15px, 10px) scale(1.1); opacity: 0.4; }
                }
            `;
            document.head.appendChild(style);
        }
    },
    
    // ==================== 导航系统 ====================
    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const panel = item.dataset.panel;
                if (panel) {
                    this.switchPanel(panel);
                    // 关闭移动端侧边栏
                    this.closeMobileSidebar();
                }
            });
        });
    },
    
    switchPanel(panelName) {
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.panel === panelName);
        });
        
        // 切换面板
        document.querySelectorAll('.panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        const targetPanel = document.getElementById(`${panelName}-panel`);
        if (targetPanel) {
            targetPanel.classList.add('active');
        }
        
        // 更新页面标题
        const titles = {
            'terminal': '智能终端',
            'workflow': '工作流',
            'files': '文件管理',
            'browser': '浏览器',
            'monitor': '性能监控',
            'processes': '进程管理',
            'history': '执行历史',
            'settings': '系统设置'
        };
        
        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle) {
            pageTitle.textContent = titles[panelName] || panelName;
        }
        
        this.state.currentPanel = panelName;
        
        // 面板特定操作
        if (panelName === 'monitor') {
            this.loadSystemInfo();
        } else if (panelName === 'files') {
            this.loadFiles();
        } else if (panelName === 'history') {
            this.loadHistory();
        }
    },
    
    // 侧边栏控制
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            this.state.sidebarCollapsed = sidebar.classList.contains('collapsed');
        }
    },
    
    toggleMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('mobile-open');
            this.state.mobileSidebarOpen = sidebar.classList.contains('mobile-open');
        }
    },
    
    closeMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('mobile-open');
            this.state.mobileSidebarOpen = false;
        }
    },
    
    // ==================== 输入处理 ====================
    setupInput() {
        const input = document.getElementById('commandInput');
        if (!input) return;
        
        // 自动调整高度
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });
    },
    
    handleKeyDown(event) {
        const input = document.getElementById('commandInput');
        
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.send();
        } else if (event.key === 'ArrowUp' && !event.shiftKey) {
            // 历史命令向上
            if (this.state.historyIndex < this.state.commandHistory.length - 1) {
                this.state.historyIndex++;
                input.value = this.state.commandHistory[this.state.historyIndex];
                // 移动光标到末尾
                setTimeout(() => {
                    input.selectionStart = input.selectionEnd = input.value.length;
                }, 0);
            }
            event.preventDefault();
        } else if (event.key === 'ArrowDown' && !event.shiftKey) {
            // 历史命令向下
            if (this.state.historyIndex > 0) {
                this.state.historyIndex--;
                input.value = this.state.commandHistory[this.state.historyIndex];
            } else if (this.state.historyIndex === 0) {
                this.state.historyIndex = -1;
                input.value = '';
            }
            event.preventDefault();
        }
    },
    
    handleInput(event) {
        // 可以在这里添加输入预测等功能
    },
    
    // ==================== 命令发送 ====================
    async send(command) {
        const input = document.getElementById('commandInput');
        const text = command || input?.value?.trim();
        
        if (!text || this.state.isLoading) return;
        
        // 清空输入
        if (!command && input) {
            input.value = '';
            input.style.height = 'auto';
        }
        
        // 添加到历史
        this.state.commandHistory.unshift(text);
        this.state.historyIndex = -1;
        
        // 隐藏欢迎界面
        const welcomeHero = document.getElementById('welcomeHero');
        if (welcomeHero) {
            welcomeHero.style.display = 'none';
        }
        
        // 添加用户消息
        this.addMessage('user', text);
        
        // 显示思考动画
        const thinkingId = this.showThinking();
        this.state.isLoading = true;
        
        const startTime = Date.now();
        
        try {
            const response = await fetch(`${this.config.apiBase}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: text,
                    auto_confirm: this.config.autoConfirm
                })
            });
            
            const result = await response.json();
            const duration = Date.now() - startTime;
            
            // 移除思考动画
            this.hideThinking(thinkingId);
            this.state.isLoading = false;
            
            // 添加回复
            this.addMessage('agent', result.message, result);
            
            // 添加任务记录
            this.addTask({
                command: text,
                success: result.success,
                message: result.message,
                duration: duration,
                timestamp: new Date()
            });
            
            // 显示通知
            if (result.success) {
                this.toast('success', '执行成功', this.truncate(result.message, 50));
                if (this.config.soundEnabled) {
                    this.playSound('success');
                }
            } else {
                this.toast('error', '执行失败', result.error || result.message);
            }
            
        } catch (error) {
            this.hideThinking(thinkingId);
            this.state.isLoading = false;
            this.addMessage('agent', `❌ 请求失败: ${error.message}`);
            this.toast('error', '网络错误', error.message);
        }
    },
    
    // 快捷操作
    quickAction(command) {
        this.send(command);
    },
    
    // ==================== 消息系统 ====================
    addMessage(role, content, data = null) {
        const container = document.getElementById('messagesList');
        if (!container) return;
        
        const time = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const avatarIcon = role === 'agent'
            ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                 <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                 <path d="M2 17l10 5 10-5"/>
                 <path d="M2 12l10 5 10-5"/>
               </svg>`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                 <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                 <circle cx="12" cy="7" r="4"/>
               </svg>`;
        
        const messageHtml = `
            <div class="message ${role}">
                <div class="message-avatar">${avatarIcon}</div>
                <div class="message-body">
                    <div class="message-bubble">${this.formatMessage(content)}</div>
                    <div class="message-time">${time}</div>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', messageHtml);
        
        // 滚动到底部
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    },
    
    formatMessage(text) {
        if (!text) return '';
        
        // 转义HTML
        text = text.replace(/&/g, '&amp;')
                   .replace(/</g, '&lt;')
                   .replace(/>/g, '&gt;');
        
        // 转换换行
        text = text.replace(/\n/g, '<br>');
        
        // 转换代码
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // 转换粗体
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        return text;
    },
    
    showThinking() {
        const container = document.getElementById('messagesList');
        if (!container) return null;
        
        const id = 'thinking-' + Date.now();
        
        const html = `
            <div class="message agent" id="${id}">
                <div class="message-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <div class="message-body">
                    <div class="thinking-indicator">
                        <div class="thinking-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <span class="thinking-text">正在分析并处理...</span>
                    </div>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', html);
        
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        return id;
    },
    
    hideThinking(id) {
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    },
    
    // ==================== 任务管理 ====================
    addTask(task) {
        this.state.tasks.unshift(task);
        if (this.state.tasks.length > 100) {
            this.state.tasks.pop();
        }
        this.updateTasksList();
    },
    
    updateTasksList() {
        const container = document.getElementById('tasksList');
        const countEl = document.getElementById('taskCount');
        
        if (!container) return;
        
        if (this.state.tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-tasks">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
                            <rect x="9" y="3" width="6" height="4" rx="1"/>
                            <path d="M9 14l2 2 4-4"/>
                        </svg>
                    </div>
                    <p>暂无任务记录</p>
                </div>
            `;
            return;
        }
        
        const recentTasks = this.state.tasks.slice(0, 5);
        container.innerHTML = recentTasks.map(task => `
            <div class="task-item">
                <div class="task-status-dot ${task.success ? 'success' : 'error'}"></div>
                <div class="task-info">
                    <div class="task-name">${this.escapeHtml(this.truncate(task.command, 30))}</div>
                    <div class="task-time">${this.formatTime(task.timestamp)}</div>
                </div>
            </div>
        `).join('');
        
        if (countEl) {
            countEl.textContent = this.state.tasks.length;
        }
    },
    
    // ==================== 系统监控 ====================
    async loadSystemInfo() {
        try {
            const response = await fetch(`${this.config.apiBase}/system/info`);
            const result = await response.json();
            
            if (result.success && result.data) {
                this.state.systemInfo = result.data;
                this.updateSystemDisplay(result.data);
            }
        } catch (error) {
            console.error('加载系统信息失败:', error);
        }
    },
    
    updateSystemDisplay(data) {
        // 更新环形进度条
        const circumference = 2 * Math.PI * 18; // r=18
        
        if (data.cpu) {
            const cpuPercent = data.cpu.usage_percent || 0;
            this.updateRingProgress('cpuRing', cpuPercent, circumference);
            this.updateText('cpuPercent', cpuPercent + '%');
            this.updateText('sidebarCpu', cpuPercent + '%');
            
            // 监控面板
            this.updateText('monitorCpuValue', cpuPercent + '%');
            this.updateText('cpuCores', (data.cpu.cores_logical || '--') + ' 核');
            this.updateText('cpuFreq', (data.cpu.frequency || '--') + ' GHz');
        }
        
        if (data.memory) {
            const memPercent = data.memory.used_percent || 0;
            this.updateRingProgress('memRing', memPercent, circumference);
            this.updateText('memPercent', memPercent + '%');
            this.updateText('sidebarMem', memPercent + '%');
            
            this.updateText('monitorMemValue', memPercent + '%');
            this.updateText('memUsed', (data.memory.used_gb || '--') + ' GB');
            this.updateText('memTotal', (data.memory.total_gb || '--') + ' GB');
        }
        
        if (data.disk) {
            const diskPercent = data.disk.used_percent || 0;
            this.updateRingProgress('diskRing', diskPercent, circumference);
            this.updateText('diskPercent', diskPercent + '%');
            
            this.updateText('monitorDiskValue', diskPercent + '%');
            const diskBar = document.getElementById('monitorDiskBar');
            if (diskBar) diskBar.style.width = diskPercent + '%';
            
            this.updateText('diskUsed', (data.disk.used_gb || '--') + ' GB');
            this.updateText('diskFree', (data.disk.free_gb || '--') + ' GB');
        }
        
        // 系统信息
        if (data.platform) {
            const infoList = document.getElementById('systemInfoList');
            if (infoList) {
                infoList.innerHTML = `
                    <div class="system-info-item">
                        <span class="label">操作系统</span>
                        <span class="value">${data.platform.system || '--'}</span>
                    </div>
                    <div class="system-info-item">
                        <span class="label">版本</span>
                        <span class="value">${data.platform.release || '--'}</span>
                    </div>
                    <div class="system-info-item">
                        <span class="label">主机名</span>
                        <span class="value">${data.platform.hostname || '--'}</span>
                    </div>
                    <div class="system-info-item">
                        <span class="label">架构</span>
                        <span class="value">${data.platform.architecture || 'x64'}</span>
                    </div>
                `;
            }
        }
    },
    
    updateRingProgress(id, percent, circumference) {
        const ring = document.getElementById(id);
        if (ring) {
            const offset = (percent / 100) * circumference;
            ring.setAttribute('stroke-dasharray', `${offset} ${circumference}`);
        }
    },
    
    updateText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    },
    
    startSystemMonitor() {
        // 每30秒更新一次
        setInterval(() => {
            if (this.state.currentPanel === 'monitor' || this.state.currentPanel === 'terminal') {
                this.loadSystemInfo();
            }
        }, 30000);
    },
    
    refreshSystemInfo() {
        this.loadSystemInfo();
        this.toast('info', '刷新中', '正在获取最新系统信息...');
    },
    
    // ==================== 文件管理 ====================
    async loadFiles(path) {
        try {
            const response = await fetch(`${this.config.apiBase}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: `列出目录 ${path || '~'}`,
                    auto_confirm: true
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.data && result.data.items) {
                this.renderFilesList(result.data.items);
            }
        } catch (error) {
            console.error('加载文件列表失败:', error);
        }
    },
    
    renderFilesList(items) {
        const container = document.getElementById('filesContent');
        if (!container) return;
        
        if (!items || items.length === 0) {
            container.innerHTML = `
                <div class="empty-tasks">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
                        </svg>
                    </div>
                    <p>文件夹为空</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = items.map(item => `
            <div class="file-item" onclick="AgentOS.${item.is_dir ? 'navigateTo' : 'openFile'}('${this.escapeHtml(item.path.replace(/'/g, "\\'"))}')">
                <div class="file-icon">${item.is_dir ? '📁' : this.getFileIcon(item.name)}</div>
                <div class="file-info">
                    <div class="file-name">${this.escapeHtml(item.name)}</div>
                    <div class="file-meta">${item.is_dir ? '文件夹' : this.formatSize(item.size)}</div>
                </div>
            </div>
        `).join('');
    },
    
    getFileIcon(name) {
        const ext = name.split('.').pop().toLowerCase();
        const icons = {
            'txt': '📄', 'md': '📝', 'pdf': '📕',
            'doc': '📘', 'docx': '📘', 'xls': '📗', 'xlsx': '📗',
            'ppt': '📙', 'pptx': '📙',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'webp': '🖼️',
            'mp3': '🎵', 'wav': '🎵', 'flac': '🎵',
            'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬', 'mov': '🎬',
            'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
            'py': '🐍', 'js': '💛', 'ts': '💙', 'html': '🌐', 'css': '🎨',
            'json': '📋', 'xml': '📋', 'yml': '📋', 'yaml': '📋',
            'exe': '⚙️', 'msi': '⚙️', 'bat': '⚙️', 'sh': '⚙️'
        };
        return icons[ext] || '📄';
    },
    
    navigateTo(path) {
        this.loadFiles(path);
    },
    
    navigateBack() {
        this.send('返回上级目录');
    },
    
    navigateUp() {
        this.send('返回上级目录');
    },
    
    openFile(path) {
        this.send(`打开文件 "${path}"`);
    },
    
    refreshFiles() {
        this.loadFiles();
        this.toast('info', '刷新中', '正在刷新文件列表...');
    },
    
    createFolder() {
        const name = prompt('请输入文件夹名称:');
        if (name) {
            this.send(`创建文件夹 ${name}`);
            setTimeout(() => this.loadFiles(), 1000);
        }
    },
    
    // ==================== 历史记录 ====================
    loadHistory() {
        const container = document.getElementById('historyList');
        if (!container) return;
        
        if (this.state.tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-tasks">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12 6 12 12 16 14"/>
                        </svg>
                    </div>
                    <p>暂无执行历史</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.state.tasks.map(task => `
            <div class="history-item">
                <div class="history-status ${task.success ? 'success' : 'error'}"></div>
                <div class="history-content">
                    <div class="history-command">${this.escapeHtml(task.command)}</div>
                    <div class="history-result">${this.escapeHtml(this.truncate(task.message || '', 100))}</div>
                    <div class="history-meta">
                        <span>${this.formatTime(task.timestamp)}</span>
                        <span>耗时: ${task.duration}ms</span>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    clearHistory() {
        if (confirm('确定要清空所有历史记录吗？')) {
            this.state.tasks = [];
            this.loadHistory();
            this.updateTasksList();
            this.toast('success', '已清空', '历史记录已清空');
        }
    },
    
    // ==================== Toast 通知 ====================
    toast(type, title, message) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const id = 'toast-' + Date.now();
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        const html = `
            <div class="toast ${type}" id="${id}">
                <div class="toast-icon">${icons[type] || 'ℹ'}</div>
                <div class="toast-body">
                    <div class="toast-title">${this.escapeHtml(title)}</div>
                    <div class="toast-message">${this.escapeHtml(message)}</div>
                </div>
                <button class="toast-close" onclick="AgentOS.closeToast('${id}')">×</button>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', html);
        
        // 自动关闭
        setTimeout(() => this.closeToast(id), 5000);
    },
    
    closeToast(id) {
        const toast = document.getElementById(id);
        if (toast) {
            toast.style.animation = 'toastIn 0.3s reverse';
            setTimeout(() => toast.remove(), 300);
        }
    },
    
    // ==================== 命令面板 ====================
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+K 打开命令面板
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.showCommandPalette();
            }
            
            // ESC 关闭命令面板
            if (e.key === 'Escape') {
                this.hideCommandPalette();
            }
        });
    },
    
    showCommandPalette() {
        const palette = document.getElementById('commandPalette');
        if (palette) {
            palette.classList.add('active');
            const input = document.getElementById('paletteInput');
            if (input) {
                input.focus();
                input.value = '';
            }
            this.renderPaletteResults('');
        }
    },
    
    hideCommandPalette() {
        const palette = document.getElementById('commandPalette');
        if (palette) {
            palette.classList.remove('active');
        }
    },
    
    filterPalette(event) {
        const query = event.target.value;
        this.renderPaletteResults(query);
        
        if (event.key === 'Enter') {
            // 执行第一个结果
            const firstItem = document.querySelector('.palette-item.selected');
            if (firstItem) {
                firstItem.click();
            }
        }
    },
    
    renderPaletteResults(query) {
        const container = document.getElementById('paletteResults');
        if (!container) return;
        
        const commands = [
            { icon: '🚀', text: '打开应用', cmd: '打开记事本' },
            { icon: '🔍', text: '搜索文件', cmd: '搜索文件' },
            { icon: '📸', text: '截图保存', cmd: '截图保存到桌面' },
            { icon: '💻', text: '系统信息', cmd: '系统信息' },
            { icon: '📁', text: '文件管理', panel: 'files' },
            { icon: '📊', text: '系统监控', panel: 'monitor' },
            { icon: '📜', text: '执行历史', panel: 'history' },
            { icon: '⚙️', text: '系统设置', panel: 'settings' }
        ];
        
        const filtered = query
            ? commands.filter(c => c.text.toLowerCase().includes(query.toLowerCase()))
            : commands;
        
        container.innerHTML = filtered.map((cmd, i) => `
            <div class="palette-item ${i === 0 ? 'selected' : ''}" 
                 onclick="AgentOS.executePaletteItem(${JSON.stringify(cmd).replace(/"/g, '&quot;')})">
                <span class="palette-icon">${cmd.icon}</span>
                <span class="palette-text">${cmd.text}</span>
            </div>
        `).join('');
    },
    
    executePaletteItem(item) {
        this.hideCommandPalette();
        if (item.panel) {
            this.switchPanel(item.panel);
        } else if (item.cmd) {
            this.send(item.cmd);
        }
    },
    
    // ==================== 快捷操作 ====================
    screenshot() {
        this.send('截图保存到桌面');
    },
    
    toggleNotifications() {
        this.toast('info', '通知', '暂无新通知');
    },
    
    toggleTheme() {
        document.body.classList.toggle('light-theme');
        this.config.theme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        this.saveSettings();
    },
    
    startVoice() {
        this.toast('info', '语音输入', '语音识别功能开发中...');
    },
    
    attachFile() {
        this.toast('info', '附件', '文件附件功能开发中...');
    },
    
    // ==================== 设置管理 ====================
    loadSettings() {
        try {
            const settings = localStorage.getItem('agentOS_settings');
            if (settings) {
                Object.assign(this.config, JSON.parse(settings));
            }
            
            // 应用设置
            const darkModeSwitch = document.getElementById('darkModeSwitch');
            const animationsSwitch = document.getElementById('animationsSwitch');
            const autoConfirmSwitch = document.getElementById('autoConfirmSwitch');
            const soundSwitch = document.getElementById('soundSwitch');
            
            if (darkModeSwitch) darkModeSwitch.checked = this.config.theme === 'dark';
            if (animationsSwitch) animationsSwitch.checked = this.config.animationsEnabled;
            if (autoConfirmSwitch) autoConfirmSwitch.checked = this.config.autoConfirm;
            if (soundSwitch) soundSwitch.checked = this.config.soundEnabled;
            
            if (this.config.theme === 'light') {
                document.body.classList.add('light-theme');
            }
        } catch (e) {
            console.error('加载设置失败:', e);
        }
    },
    
    updateSettings() {
        try {
            this.config.theme = document.getElementById('darkModeSwitch')?.checked ? 'dark' : 'light';
            this.config.animationsEnabled = document.getElementById('animationsSwitch')?.checked ?? true;
            this.config.autoConfirm = document.getElementById('autoConfirmSwitch')?.checked ?? false;
            this.config.soundEnabled = document.getElementById('soundSwitch')?.checked ?? true;
            
            // 应用主题
            if (this.config.theme === 'light') {
                document.body.classList.add('light-theme');
            } else {
                document.body.classList.remove('light-theme');
            }
            
            this.saveSettings();
        } catch (e) {
            console.error('更新设置失败:', e);
        }
    },
    
    saveSettings() {
        try {
            localStorage.setItem('agentOS_settings', JSON.stringify(this.config));
        } catch (e) {
            console.error('保存设置失败:', e);
        }
    },
    
    // ==================== 工具函数 ====================
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    truncate(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    
    formatTime(date) {
        if (!date) return '';
        const d = new Date(date);
        const now = new Date();
        const diff = now - d;
        
        if (diff < 60000) return '刚刚';
        if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
        if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
        
        return d.toLocaleDateString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    formatSize(bytes) {
        if (!bytes) return '--';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
        return (bytes / 1024 / 1024 / 1024).toFixed(1) + ' GB';
    },
    
    playSound(type) {
        // 可以添加音效
    },
    
    // ==================== 加载控制 ====================
    showLoading(text = 'Agent 正在处理...') {
        const overlay = document.getElementById('loadingOverlay');
        const textEl = overlay?.querySelector('.loading-text');
        if (textEl) textEl.textContent = text;
        overlay?.classList.add('active');
    },
    
    hideLoading() {
        document.getElementById('loadingOverlay')?.classList.remove('active');
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    AgentOS.init();
});

// 点击侧边栏外部关闭移动端侧边栏
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.querySelector('.mobile-menu-btn');
    
    if (AgentOS.state.mobileSidebarOpen && 
        sidebar && 
        !sidebar.contains(e.target) && 
        menuBtn && 
        !menuBtn.contains(e.target)) {
        AgentOS.closeMobileSidebar();
    }
});
