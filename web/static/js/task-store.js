/**
 * TaskStore - 全局任务管理服务
 * 
 * 提供任务的创建、存储、同步功能
 * 支持跨页面通信和持久化存储
 */

class TaskStore {
  constructor() {
    this.tasks = new Map();
    this.listeners = new Set();
    this.currentTaskId = null;
    this.storageKey = 'joinflow_tasks';
    
    // 搜索引擎配置 - 根据语言/地区自动选择
    this.searchEngine = this.detectSearchEngine();
    this.resultsPath = this.getResultsPath();
    
    // 从 localStorage 加载任务
    this.loadFromStorage();
    
    // 监听其他标签页的变化
    window.addEventListener('storage', (e) => {
      if (e.key === this.storageKey) {
        this.loadFromStorage();
        this.notifyListeners();
      }
    });
    
    // 监听自定义事件（同页面通信）
    window.addEventListener('task-updated', (e) => {
      this.notifyListeners();
    });
  }

  /**
   * 从 localStorage 加载任务
   */
  loadFromStorage() {
    try {
      const data = localStorage.getItem(this.storageKey);
      if (data) {
        const parsed = JSON.parse(data);
        this.tasks = new Map(parsed.tasks || []);
        this.currentTaskId = parsed.currentTaskId || null;
      }
    } catch (e) {
      console.warn('Failed to load tasks from storage:', e);
    }
  }

  /**
   * 保存到 localStorage
   */
  saveToStorage() {
    try {
      const data = {
        tasks: Array.from(this.tasks.entries()),
        currentTaskId: this.currentTaskId,
        updatedAt: new Date().toISOString()
      };
      localStorage.setItem(this.storageKey, JSON.stringify(data));
      
      // 触发自定义事件通知同页面的其他组件
      window.dispatchEvent(new CustomEvent('task-updated', { detail: data }));
    } catch (e) {
      console.warn('Failed to save tasks to storage:', e);
    }
  }

  /**
   * 创建新任务
   */
  createTask(description, options = {}) {
    const taskId = 'task_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    const task = {
      id: taskId,
      description: description,
      status: 'pending',
      progress: 0,
      steps: [],
      currentStep: -1,
      result: null,
      error: null,
      createdAt: new Date().toISOString(),
      startedAt: null,
      completedAt: null,
      mode: options.mode || 'auto',
      priority: options.priority || 2,
      agents: options.agents || [],  // 保存用户选择的 agents
      logs: [],
      screenshots: [],
      thinking: ''
    };
    
    // 根据任务描述和用户选择的 agents 分析步骤
    task.steps = this.analyzeTask(description, options.agents || []);
    
    this.tasks.set(taskId, task);
    this.currentTaskId = taskId;
    this.saveToStorage();
    this.notifyListeners();
    
    // 同时保存到后端
    this.syncToBackend(task);
    
    return task;
  }

  /**
   * 分析任务并生成执行步骤
   * @param {string} description - 任务描述
   * @param {array} selectedAgents - 用户选择的 agents（可选）
   */
  analyzeTask(description, selectedAgents = []) {
    const steps = [];
    const desc = description.toLowerCase();
    
    // 如果用户只选择了 llm（大模型），则使用纯 LLM 模式
    const isLlmOnlyMode = selectedAgents.length === 1 && selectedAgents.includes('llm');
    // 如果用户只选择了 os（系统），则使用系统操作模式
    const isOsOnlyMode = selectedAgents.length === 1 && selectedAgents.includes('os');
    // 如果用户明确选择了 agents
    const hasUserSelectedAgents = selectedAgents.length > 0;
    
    // 任务分析步骤（必须）
    steps.push({
      id: this.generateStepId(),
      name: '任务分析',
      description: '理解用户意图，制定执行计划',
      agent: 'llm',
      status: 'pending',
      output: null,
      startedAt: null,
      completedAt: null
    });
    
    // 如果是纯 LLM 模式（大模型 Agent）
    if (isLlmOnlyMode) {
      steps.push({
        id: this.generateStepId(),
        name: '大模型处理',
        description: '使用大模型理解并执行任务',
        agent: 'llm',
        status: 'pending',
        output: null,
        startedAt: null,
        completedAt: null
      });
    }
    // 如果是系统操作模式（OS Agent）
    else if (isOsOnlyMode) {
      steps.push({
        id: this.generateStepId(),
        name: '系统操作',
        description: '执行本机系统操作（打开应用、文件操作等）',
        agent: 'os',
        status: 'pending',
        output: null,
        startedAt: null,
        completedAt: null
      });
    }
    // 如果用户选择了特定的 agents
    else if (hasUserSelectedAgents) {
      // 根据用户选择添加对应的步骤
      if (selectedAgents.includes('browser')) {
        steps.push({
          id: this.generateStepId(),
          name: '网页操作',
          description: '使用浏览器执行网页相关操作',
          agent: 'browser',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      if (selectedAgents.includes('code')) {
        steps.push({
          id: this.generateStepId(),
          name: '代码执行',
          description: '生成并执行代码',
          agent: 'code',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      if (selectedAgents.includes('os')) {
        steps.push({
          id: this.generateStepId(),
          name: '系统操作',
          description: '执行本机系统操作',
          agent: 'os',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      if (selectedAgents.includes('data')) {
        steps.push({
          id: this.generateStepId(),
          name: '数据分析',
          description: '分析数据并生成图表',
          agent: 'data',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
    }
    // 自动模式：根据关键词添加步骤
    else {
      if (this.containsAny(desc, ['搜索', 'search', '查询', '查找', '网页', '网站', 'web', 'seo', '新闻', 'news'])) {
        steps.push({
          id: this.generateStepId(),
          name: '网页搜索',
          description: '使用浏览器搜索相关信息',
          agent: 'browser',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      
      if (this.containsAny(desc, ['提取', '获取', '抓取', '爬取', '内容', 'extract', 'scrape'])) {
        steps.push({
          id: this.generateStepId(),
          name: '内容提取',
          description: '从网页中提取关键信息',
          agent: 'browser',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      
      if (this.containsAny(desc, ['代码', 'code', 'python', 'javascript', '编程', '脚本', '计算', '斐波那契'])) {
        steps.push({
          id: this.generateStepId(),
          name: '代码生成',
          description: '生成并执行代码',
          agent: 'code',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      
      // 本机操作关键词
      if (this.containsAny(desc, ['打开', '记事本', '计算器', '画图', 'notepad', 'calc', '应用', '程序', '桌面', '保存到'])) {
        steps.push({
          id: this.generateStepId(),
          name: '本机操作',
          description: '执行本机应用和系统操作',
          agent: 'os',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      
      if (this.containsAny(desc, ['文件', 'file', '读取', '目录', 'folder'])) {
        steps.push({
          id: this.generateStepId(),
          name: '文件操作',
          description: '执行文件系统操作',
          agent: 'os',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
      
      if (this.containsAny(desc, ['数据', 'data', '分析', 'analyze', '图表', 'chart', '统计'])) {
        steps.push({
          id: this.generateStepId(),
          name: '数据分析',
          description: '分析数据并生成图表',
          agent: 'data',
          status: 'pending',
          output: null,
          startedAt: null,
          completedAt: null
        });
      }
    }
    
    // 整理总结步骤（必须）
    steps.push({
      id: this.generateStepId(),
      name: '整理总结',
      description: '整理信息，生成结构化报告',
      agent: 'llm',
      status: 'pending',
      output: null,
      startedAt: null,
      completedAt: null
    });
    
    // 展示结果步骤（新增）
    steps.push({
      id: this.generateStepId(),
      name: '展示结果',
      description: '以清晰美观的方式展示执行结果',
      agent: 'display',
      status: 'pending',
      output: null,
      startedAt: null,
      completedAt: null
    });
    
    // 保存结果步骤（如果任务涉及保存）
    if (!isLlmOnlyMode || this.containsAny(desc, ['保存', 'save', '写入', '存储'])) {
      steps.push({
        id: this.generateStepId(),
        name: '保存结果',
        description: '保存到本地并显示文件位置',
        agent: 'os',
        status: 'pending',
        output: null,
        filePath: null,
        startedAt: null,
        completedAt: null
      });
    }
    
    return steps;
  }

  /**
   * 检测应该使用的搜索引擎
   */
  detectSearchEngine() {
    // 检查浏览器语言
    const lang = navigator.language || navigator.userLanguage || 'zh-CN';
    const isChina = lang.startsWith('zh') || 
                    Intl.DateTimeFormat().resolvedOptions().timeZone === 'Asia/Shanghai';
    
    // 从 localStorage 读取用户设置
    const savedEngine = localStorage.getItem('joinflow_search_engine');
    if (savedEngine) {
      return savedEngine;
    }
    
    // 根据地区自动选择
    return isChina ? 'baidu' : 'google';
  }

  /**
   * 设置搜索引擎
   */
  setSearchEngine(engine) {
    this.searchEngine = engine;
    localStorage.setItem('joinflow_search_engine', engine);
  }

  /**
   * 获取搜索引擎信息
   */
  getSearchEngineInfo() {
    const engines = {
      'baidu': { name: '百度', url: 'https://www.baidu.com', searchUrl: 'https://www.baidu.com/s?wd=', region: 'cn' },
      'bing-cn': { name: '必应(国内)', url: 'https://cn.bing.com', searchUrl: 'https://cn.bing.com/search?q=', region: 'cn' },
      'google': { name: 'Google', url: 'https://www.google.com', searchUrl: 'https://www.google.com/search?q=', region: 'intl' },
      'bing': { name: 'Bing', url: 'https://www.bing.com', searchUrl: 'https://www.bing.com/search?q=', region: 'intl' }
    };
    return engines[this.searchEngine] || engines['baidu'];
  }

  /**
   * 获取所有可用的搜索引擎
   */
  getAllSearchEngines() {
    return [
      { id: 'baidu', name: '百度', url: 'https://www.baidu.com', searchUrl: 'https://www.baidu.com/s?wd=', icon: '🔍', region: 'cn' },
      { id: 'bing-cn', name: '必应(国内)', url: 'https://cn.bing.com', searchUrl: 'https://cn.bing.com/search?q=', icon: '🌐', region: 'cn' },
      { id: 'sogou', name: '搜狗', url: 'https://www.sogou.com', searchUrl: 'https://www.sogou.com/web?query=', icon: '🔎', region: 'cn' },
      { id: '360', name: '360搜索', url: 'https://www.so.com', searchUrl: 'https://www.so.com/s?q=', icon: '🛡️', region: 'cn' },
      { id: 'google', name: 'Google', url: 'https://www.google.com', searchUrl: 'https://www.google.com/search?q=', icon: '🔍', region: 'intl' },
      { id: 'bing', name: 'Bing', url: 'https://www.bing.com', searchUrl: 'https://www.bing.com/search?q=', icon: '🌐', region: 'intl' },
      { id: 'duckduckgo', name: 'DuckDuckGo', url: 'https://duckduckgo.com', searchUrl: 'https://duckduckgo.com/?q=', icon: '🦆', region: 'intl' }
    ];
  }

  /**
   * 获取用户选择的并行搜索引擎
   */
  getSelectedParallelEngines() {
    const saved = localStorage.getItem('joinflow_parallel_engines');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.warn('Failed to parse parallel engines:', e);
      }
    }
    // 默认选择：国内用户选百度+必应，国际用户选Google+Bing
    const lang = navigator.language || navigator.userLanguage || 'zh-CN';
    const isChina = lang.startsWith('zh') || 
                    Intl.DateTimeFormat().resolvedOptions().timeZone === 'Asia/Shanghai';
    return isChina ? ['baidu', 'bing-cn'] : ['google', 'bing'];
  }

  /**
   * 设置并行搜索引擎
   */
  setParallelEngines(engineIds) {
    localStorage.setItem('joinflow_parallel_engines', JSON.stringify(engineIds));
  }

  /**
   * 获取多浏览器搜索引擎列表（用于并行查询）
   */
  getParallelSearchEngines() {
    const allEngines = this.getAllSearchEngines();
    const selectedIds = this.getSelectedParallelEngines();
    
    // 返回用户选择的搜索引擎
    return selectedIds
      .map(id => allEngines.find(e => e.id === id))
      .filter(e => e !== undefined);
  }

  /**
   * 获取结果保存路径
   */
  getResultsPath() {
    return localStorage.getItem('joinflow_results_path') || 'workspace/results';
  }

  /**
   * 设置结果保存路径
   */
  setResultsPath(path) {
    this.resultsPath = path;
    localStorage.setItem('joinflow_results_path', path);
  }

  containsAny(str, keywords) {
    return keywords.some(kw => str.includes(kw));
  }

  generateStepId() {
    return 'step_' + Math.random().toString(36).substr(2, 8);
  }

  /**
   * 获取任务
   */
  getTask(taskId) {
    return this.tasks.get(taskId);
  }

  /**
   * 获取当前任务
   */
  getCurrentTask() {
    return this.currentTaskId ? this.tasks.get(this.currentTaskId) : null;
  }

  /**
   * 设置当前任务
   */
  setCurrentTask(taskId) {
    if (this.tasks.has(taskId)) {
      this.currentTaskId = taskId;
      this.saveToStorage();
      this.notifyListeners();
    }
  }

  /**
   * 获取所有任务
   */
  getAllTasks() {
    return Array.from(this.tasks.values()).sort((a, b) => 
      new Date(b.createdAt) - new Date(a.createdAt)
    );
  }

  /**
   * 获取进行中的任务
   */
  getActiveTasks() {
    return this.getAllTasks().filter(t => 
      t.status === 'pending' || t.status === 'running'
    );
  }

  /**
   * 获取已完成的任务
   */
  getCompletedTasks() {
    return this.getAllTasks().filter(t => 
      t.status === 'completed' || t.status === 'failed'
    );
  }

  /**
   * 更新任务
   */
  updateTask(taskId, updates) {
    const task = this.tasks.get(taskId);
    if (!task) return null;
    
    Object.assign(task, updates);
    this.tasks.set(taskId, task);
    this.saveToStorage();
    this.notifyListeners();
    
    return task;
  }

  /**
   * 更新任务步骤
   */
  updateStep(taskId, stepIndex, updates) {
    const task = this.tasks.get(taskId);
    if (!task || !task.steps[stepIndex]) return null;
    
    Object.assign(task.steps[stepIndex], updates);
    this.tasks.set(taskId, task);
    this.saveToStorage();
    this.notifyListeners();
    
    return task;
  }

  /**
   * 添加日志
   */
  addLog(taskId, type, message) {
    const task = this.tasks.get(taskId);
    if (!task) return;
    
    task.logs.push({
      time: new Date().toLocaleTimeString('en-US', { hour12: false }),
      type: type,
      message: message
    });
    
    this.tasks.set(taskId, task);
    this.saveToStorage();
    this.notifyListeners();
  }

  /**
   * 更新思考内容
   */
  updateThinking(taskId, thinking) {
    const task = this.tasks.get(taskId);
    if (!task) return;
    
    task.thinking = thinking;
    this.tasks.set(taskId, task);
    this.saveToStorage();
    this.notifyListeners();
  }

  /**
   * 开始执行任务
   */
  startTask(taskId) {
    const task = this.tasks.get(taskId);
    if (!task) return null;
    
    task.status = 'running';
    task.startedAt = new Date().toISOString();
    task.currentStep = 0;
    
    if (task.steps.length > 0) {
      task.steps[0].status = 'running';
      task.steps[0].startedAt = new Date().toISOString();
    }
    
    this.currentTaskId = taskId;
    this.saveToStorage();
    this.notifyListeners();
    
    return task;
  }

  /**
   * 完成当前步骤并进入下一步
   */
  completeStep(taskId, stepIndex, output = null) {
    const task = this.tasks.get(taskId);
    if (!task || !task.steps[stepIndex]) return null;
    
    // 完成当前步骤
    task.steps[stepIndex].status = 'completed';
    task.steps[stepIndex].completedAt = new Date().toISOString();
    task.steps[stepIndex].output = output;
    
    // 更新进度
    const completedCount = task.steps.filter(s => s.status === 'completed').length;
    task.progress = Math.round((completedCount / task.steps.length) * 100);
    
    // 进入下一步
    const nextIndex = stepIndex + 1;
    if (nextIndex < task.steps.length) {
      task.currentStep = nextIndex;
      task.steps[nextIndex].status = 'running';
      task.steps[nextIndex].startedAt = new Date().toISOString();
    } else {
      // 所有步骤完成
      task.status = 'completed';
      task.completedAt = new Date().toISOString();
      task.progress = 100;
    }
    
    this.saveToStorage();
    this.notifyListeners();
    
    return task;
  }

  /**
   * 任务失败
   */
  failTask(taskId, error) {
    const task = this.tasks.get(taskId);
    if (!task) return null;
    
    task.status = 'failed';
    task.error = error;
    task.completedAt = new Date().toISOString();
    
    if (task.currentStep >= 0 && task.steps[task.currentStep]) {
      task.steps[task.currentStep].status = 'failed';
    }
    
    this.saveToStorage();
    this.notifyListeners();
    
    return task;
  }

  /**
   * 删除任务
   */
  deleteTask(taskId) {
    if (this.tasks.has(taskId)) {
      this.tasks.delete(taskId);
      
      // 如果删除的是当前任务，清空当前任务ID
      if (this.currentTaskId === taskId) {
        this.currentTaskId = null;
      }
      
      this.saveToStorage();
      this.notifyListeners();
      
      console.log('TaskStore: Task deleted:', taskId);
      return true;
    }
    return false;
  }

  /**
   * 清空所有任务
   */
  clearAllTasks() {
    this.tasks.clear();
    this.currentTaskId = null;
    this.saveToStorage();
    this.notifyListeners();
  }

  /**
   * 同步到后端
   */
  async syncToBackend(task) {
    try {
      const response = await fetch('/task/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: task.id,
          description: task.description,
          priority: task.priority,
          mode: task.mode
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Task synced to backend:', data);
      }
    } catch (e) {
      console.warn('Failed to sync task to backend:', e);
    }
  }

  /**
   * 订阅变化
   */
  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * 通知所有监听器
   */
  notifyListeners() {
    this.listeners.forEach(callback => {
      try {
        callback(this.getAllTasks(), this.getCurrentTask());
      } catch (e) {
        console.error('Listener error:', e);
      }
    });
  }
}

// 创建全局单例
window.taskStore = new TaskStore();

// 导出到全局
window.TaskStore = TaskStore;

