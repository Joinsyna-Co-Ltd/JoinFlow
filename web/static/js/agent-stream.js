/**
 * Agent Stream - 实时展示 Agent 操作画面
 * 
 * 这是让用户"看到" Agent 在做什么的核心模块
 */

class AgentStream {
  constructor(options = {}) {
    this.wsUrl = options.wsUrl || `ws://${location.host}/ws/agent-stream`;
    this.container = null;
    this.ws = null;
    this.isConnected = false;
    this.currentTaskId = null;
    this.onStatusChange = options.onStatusChange || (() => {});
    this.onStepUpdate = options.onStepUpdate || (() => {});
  }

  /**
   * 初始化实时画面容器
   */
  init(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error('Agent stream container not found');
      return;
    }

    this.container.innerHTML = `
      <div class="agent-stream-wrapper">
        <!-- 浏览器实时画面 -->
        <div class="stream-viewport">
          <div class="stream-header">
            <div class="stream-status">
              <span class="status-dot"></span>
              <span class="status-text">等待连接...</span>
            </div>
            <div class="stream-controls">
              <button class="stream-btn" id="streamPauseBtn" title="暂停">
                <i class="fas fa-pause"></i>
              </button>
              <button class="stream-btn" id="streamFullscreenBtn" title="全屏">
                <i class="fas fa-expand"></i>
              </button>
            </div>
          </div>
          <div class="stream-canvas-container">
            <img id="streamCanvas" class="stream-canvas" alt="Agent 实时画面">
            <div class="stream-placeholder" id="streamPlaceholder">
              <i class="fas fa-robot"></i>
              <p>Agent 准备就绪</p>
              <span>任务开始后将在此显示实时操作画面</span>
            </div>
            <!-- 操作指示器 -->
            <div class="action-indicator" id="actionIndicator"></div>
          </div>
        </div>

        <!-- 实时日志 -->
        <div class="stream-logs">
          <div class="logs-header">
            <i class="fas fa-terminal"></i>
            <span>执行日志</span>
            <button class="logs-clear-btn" id="logsClearBtn">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
          <div class="logs-content" id="logsContent"></div>
        </div>
      </div>
    `;

    this.bindEvents();
    this.applyStyles();
  }

  /**
   * 连接 WebSocket
   */
  connect(taskId) {
    this.currentTaskId = taskId;
    
    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket(`${this.wsUrl}?task_id=${taskId}`);
    
    this.ws.onopen = () => {
      this.isConnected = true;
      this.updateStatus('connected', '已连接');
      this.addLog('system', '🔗 已连接到 Agent');
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(JSON.parse(event.data));
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      this.updateStatus('disconnected', '已断开');
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.updateStatus('error', '连接错误');
    };
  }

  /**
   * 处理接收到的消息
   */
  handleMessage(data) {
    switch (data.type) {
      case 'screenshot':
        // 更新浏览器画面
        this.updateScreenshot(data.image);
        break;
      
      case 'action':
        // 显示操作动画
        this.showAction(data.action, data.position);
        this.addLog('action', `🖱️ ${data.action}`);
        break;
      
      case 'step':
        // 更新步骤状态
        this.onStepUpdate(data.step);
        this.addLog('step', `📌 ${data.step.name}`, data.step.status);
        break;
      
      case 'thinking':
        // Agent 正在思考
        this.addLog('thinking', `🤔 ${data.content}`);
        break;
      
      case 'result':
        // 步骤结果
        this.addLog('result', `✅ ${data.content}`);
        break;
      
      case 'error':
        this.addLog('error', `❌ ${data.message}`);
        break;
      
      case 'complete':
        this.addLog('success', '🎉 任务完成！');
        this.updateStatus('completed', '已完成');
        break;
    }
  }

  /**
   * 更新浏览器截图
   */
  updateScreenshot(imageData) {
    const canvas = document.getElementById('streamCanvas');
    const placeholder = document.getElementById('streamPlaceholder');
    
    if (canvas && imageData) {
      canvas.src = `data:image/png;base64,${imageData}`;
      canvas.style.display = 'block';
      if (placeholder) placeholder.style.display = 'none';
    }
  }

  /**
   * 显示操作动画（如点击、输入）
   */
  showAction(action, position) {
    const indicator = document.getElementById('actionIndicator');
    if (!indicator || !position) return;

    // 根据操作类型显示不同动画
    let icon = '🖱️';
    let className = 'action-click';
    
    if (action.includes('type') || action.includes('input')) {
      icon = '⌨️';
      className = 'action-type';
    } else if (action.includes('scroll')) {
      icon = '📜';
      className = 'action-scroll';
    }

    indicator.innerHTML = `<span class="${className}">${icon}</span>`;
    indicator.style.left = `${position.x}%`;
    indicator.style.top = `${position.y}%`;
    indicator.style.opacity = '1';
    indicator.style.transform = 'translate(-50%, -50%) scale(1)';

    setTimeout(() => {
      indicator.style.opacity = '0';
      indicator.style.transform = 'translate(-50%, -50%) scale(1.5)';
    }, 500);
  }

  /**
   * 添加日志
   */
  addLog(type, content, status = '') {
    const logsContent = document.getElementById('logsContent');
    if (!logsContent) return;

    const time = new Date().toLocaleTimeString();
    const statusClass = status ? ` log-${status}` : '';
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}${statusClass}`;
    logEntry.innerHTML = `
      <span class="log-time">${time}</span>
      <span class="log-content">${content}</span>
    `;

    logsContent.appendChild(logEntry);
    logsContent.scrollTop = logsContent.scrollHeight;
  }

  /**
   * 更新状态
   */
  updateStatus(status, text) {
    const statusDot = this.container.querySelector('.status-dot');
    const statusText = this.container.querySelector('.status-text');
    
    if (statusDot) {
      statusDot.className = `status-dot status-${status}`;
    }
    if (statusText) {
      statusText.textContent = text;
    }
    
    this.onStatusChange(status, text);
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    const pauseBtn = document.getElementById('streamPauseBtn');
    const fullscreenBtn = document.getElementById('streamFullscreenBtn');
    const clearBtn = document.getElementById('logsClearBtn');

    if (pauseBtn) {
      pauseBtn.onclick = () => this.togglePause();
    }

    if (fullscreenBtn) {
      fullscreenBtn.onclick = () => this.toggleFullscreen();
    }

    if (clearBtn) {
      clearBtn.onclick = () => {
        const logsContent = document.getElementById('logsContent');
        if (logsContent) logsContent.innerHTML = '';
      };
    }
  }

  /**
   * 切换暂停
   */
  togglePause() {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify({ action: 'toggle_pause' }));
    }
  }

  /**
   * 切换全屏
   */
  toggleFullscreen() {
    const viewport = this.container.querySelector('.stream-viewport');
    if (viewport) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        viewport.requestFullscreen();
      }
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  /**
   * 应用样式
   */
  applyStyles() {
    if (document.getElementById('agent-stream-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'agent-stream-styles';
    styles.textContent = `
      .agent-stream-wrapper {
        display: flex;
        flex-direction: column;
        gap: 16px;
        height: 100%;
      }

      .stream-viewport {
        flex: 1;
        background: #0d1117;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #30363d;
      }

      .stream-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: #161b22;
        border-bottom: 1px solid #30363d;
      }

      .stream-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
      }

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #8b949e;
      }

      .status-dot.status-connected {
        background: #3fb950;
        box-shadow: 0 0 8px #3fb950;
      }

      .status-dot.status-disconnected {
        background: #f85149;
      }

      .status-dot.status-completed {
        background: #58a6ff;
      }

      .stream-controls {
        display: flex;
        gap: 8px;
      }

      .stream-btn {
        width: 32px;
        height: 32px;
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        color: #8b949e;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
      }

      .stream-btn:hover {
        background: #30363d;
        color: #f0f6fc;
      }

      .stream-canvas-container {
        position: relative;
        aspect-ratio: 16/9;
        background: #010409;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .stream-canvas {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: none;
      }

      .stream-placeholder {
        text-align: center;
        color: #8b949e;
      }

      .stream-placeholder i {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
      }

      .stream-placeholder p {
        font-size: 1.1rem;
        margin-bottom: 8px;
      }

      .stream-placeholder span {
        font-size: 0.85rem;
        opacity: 0.7;
      }

      .action-indicator {
        position: absolute;
        pointer-events: none;
        opacity: 0;
        transition: all 0.3s ease-out;
        font-size: 24px;
      }

      .action-click {
        animation: clickPulse 0.5s ease-out;
      }

      @keyframes clickPulse {
        0% { transform: scale(0.5); opacity: 1; }
        100% { transform: scale(2); opacity: 0; }
      }

      .stream-logs {
        height: 200px;
        background: #161b22;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #30363d;
      }

      .logs-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: #21262d;
        border-bottom: 1px solid #30363d;
        font-size: 0.9rem;
        font-weight: 600;
      }

      .logs-clear-btn {
        margin-left: auto;
        background: none;
        border: none;
        color: #8b949e;
        cursor: pointer;
        padding: 4px;
      }

      .logs-clear-btn:hover {
        color: #f85149;
      }

      .logs-content {
        padding: 12px 16px;
        height: calc(100% - 45px);
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
      }

      .log-entry {
        display: flex;
        gap: 12px;
        padding: 6px 0;
        border-bottom: 1px solid #21262d;
      }

      .log-time {
        color: #8b949e;
        flex-shrink: 0;
      }

      .log-content {
        color: #c9d1d9;
      }

      .log-entry.log-error .log-content {
        color: #f85149;
      }

      .log-entry.log-success .log-content {
        color: #3fb950;
      }

      .log-entry.log-thinking .log-content {
        color: #a371f7;
        font-style: italic;
      }
    `;
    document.head.appendChild(styles);
  }
}

// 导出
window.AgentStream = AgentStream;

