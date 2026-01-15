/**
 * JoinFlow UI - Task-Centric Agent Management
 * Flow-based task visualization and multi-task management
 */

// ============================================
// Configuration & State
// ============================================

const config = {
  apiUrl: localStorage.getItem('apiUrl') || window.location.origin,
  theme: localStorage.getItem('theme') || 'dark',
  maxParallelTasks: parseInt(localStorage.getItem('maxParallelTasks')) || 3,
  autoRetry: localStorage.getItem('autoRetry') !== 'false'
};

const state = {
  tasks: new Map(), // taskId -> task object
  currentTaskId: null,
  activeEventSources: new Map(), // taskId -> EventSource
  agentStats: {
    browser: 0,
    llm: 0,
    os: 0,
    code: 0,
    data: 0,
    vision: 0
  },
  totalStats: {
    totalTasks: 0,
    completedTasks: 0,
    totalSteps: 0
  }
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

function initApp() {
  applyTheme(config.theme);
  loadSettings();
  loadTasksFromStorage();
  updateStats();
  setupFileUpload();
  setupKeyboardShortcuts();
  setupTaskActionButtons();
  setupPanelToggle();
  loadSubscriptionStatus();
  
  // Configure marked
  marked.setOptions({
    highlight: (code, lang) => {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true
  });
  
  document.getElementById('quickInput').focus();
  console.log('App initialized');
}

// ============================================
// Subscription Status
// ============================================

async function loadSubscriptionStatus() {
  try {
    const response = await fetch(`${config.apiUrl}/api/subscription`);
    if (!response.ok) return;
    
    const data = await response.json();
    updateSubscriptionUI(data);
  } catch (error) {
    console.log('Subscription API not available');
  }
}

function updateSubscriptionUI(data) {
  const headerBtn = document.getElementById('headerUpgradeBtn');
  const sidebarBtn = document.querySelector('.upgrade-btn');
  
  if (!data.subscription) return;
  
  const planType = data.subscription.plan_type || data.subscription.plan_id || 'free';
  const planNames = {
    free: '免费版',
    pro: '专业版',
    team: '团队版',
    enterprise: '企业版'
  };
  
  if (planType !== 'free') {
    // User has a paid plan
    if (headerBtn) {
      headerBtn.classList.add('pro');
      headerBtn.innerHTML = `<i class="fas fa-crown"></i> <span>${planNames[planType]}</span>`;
      headerBtn.href = '/pricing';
    }
    
    if (sidebarBtn) {
      sidebarBtn.innerHTML = `<i class="fas fa-crown"></i> <span>${planNames[planType]}</span>`;
      sidebarBtn.style.background = 'linear-gradient(135deg, var(--accent-success) 0%, #22c55e 100%)';
      sidebarBtn.style.color = 'white';
      sidebarBtn.querySelector('i').style.color = 'white';
    }
  }
}

// Setup task action buttons with proper event listeners
function setupTaskActionButtons() {
  const pauseBtn = document.getElementById('pauseBtn');
  const cancelBtn = document.getElementById('cancelBtn');
  const deleteBtn = document.getElementById('deleteBtn');
  
  if (pauseBtn) {
    // Remove any existing listeners by cloning
    const newPauseBtn = pauseBtn.cloneNode(true);
    pauseBtn.parentNode.replaceChild(newPauseBtn, pauseBtn);
    newPauseBtn.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('Pause button clicked');
      pauseTask();
    });
  }
  
  if (cancelBtn) {
    const newCancelBtn = cancelBtn.cloneNode(true);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    newCancelBtn.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('Cancel button clicked');
      cancelTask();
    });
  }
  
  if (deleteBtn) {
    const newDeleteBtn = deleteBtn.cloneNode(true);
    deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
    newDeleteBtn.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('Delete button clicked');
      deleteTask();
    });
  }
  
  console.log('Task action buttons setup complete');
}

// Setup right panel toggle
function setupPanelToggle() {
  const toggleBtn = document.getElementById('rightPanelToggle');
  const panelCollapseBtn = document.getElementById('panelCollapseBtn');
  
  if (toggleBtn) {
    // Remove any existing listeners by cloning
    const newToggleBtn = toggleBtn.cloneNode(true);
    toggleBtn.parentNode.replaceChild(newToggleBtn, toggleBtn);
    newToggleBtn.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('External panel toggle clicked');
      toggleRightPanel();
    });
  }
  
  if (panelCollapseBtn) {
    const newPanelCollapseBtn = panelCollapseBtn.cloneNode(true);
    panelCollapseBtn.parentNode.replaceChild(newPanelCollapseBtn, panelCollapseBtn);
    newPanelCollapseBtn.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('Panel collapse button clicked');
      toggleRightPanel();
    });
  }
  
  console.log('Panel toggle setup complete');
}

// ============================================
// Theme Management
// ============================================

function toggleTheme() {
  const newTheme = config.theme === 'dark' ? 'light' : 'dark';
  config.theme = newTheme;
  localStorage.setItem('theme', newTheme);
  applyTheme(newTheme);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
  }
}

// ============================================
// Sidebar & Panel Management
// ============================================

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('active');
}

function toggleRightPanel() {
  console.log('toggleRightPanel called');
  
  const panel = document.getElementById('rightPanel');
  const toggleBtn = document.getElementById('rightPanelToggle');
  const panelCollapseBtn = document.getElementById('panelCollapseBtn');
  
  if (!panel) {
    console.error('Right panel element not found');
    return;
  }
  
  const wasCollapsed = panel.classList.contains('collapsed');
  panel.classList.toggle('collapsed');
  const isCollapsed = panel.classList.contains('collapsed');
  
  console.log('Panel collapsed state:', isCollapsed);
  
  // Show/hide the external toggle button
  if (toggleBtn) {
    toggleBtn.style.display = isCollapsed ? 'flex' : 'none';
    const icon = toggleBtn.querySelector('i');
    if (icon) {
      icon.className = isCollapsed ? 'fas fa-chevron-left' : 'fas fa-chevron-right';
    }
    console.log('External toggle button display:', toggleBtn.style.display);
  }
  
  // Update the button inside the panel header
  if (panelCollapseBtn) {
    const icon = panelCollapseBtn.querySelector('i');
    if (icon) {
      icon.className = isCollapsed ? 'fas fa-chevron-left' : 'fas fa-chevron-right';
    }
  }
  
  // Update quick input bar position
  const quickInputBar = document.querySelector('.quick-input-bar');
  if (quickInputBar) {
    quickInputBar.style.right = isCollapsed ? '0' : 'var(--right-panel-width)';
  }
}

function toggleSection(section) {
  const sectionMap = {
    'active': {
      list: 'activeTaskList',
      toggle: 'activeToggle'
    },
    'completed': {
      list: 'completedTaskList',
      toggle: 'completedToggle'
    }
  };
  
  const config = sectionMap[section];
  if (!config) return;
  
  const list = document.getElementById(config.list);
  const toggle = document.getElementById(config.toggle);
  
  if (list) {
    list.classList.toggle('collapsed');
  }
  if (toggle) {
    toggle.classList.toggle('collapsed');
  }
}

// ============================================
// Task Management
// ============================================

function showNewTaskModal() {
  openModal('newTaskModal');
  document.getElementById('newTaskDescription').focus();
}

function createTaskFromTemplate(template) {
  const templates = {
    research: '搜索最新的科技新闻，整理成摘要报告',
    code: '帮我编写一个Python脚本',
    data: '分析数据并生成可视化图表',
    file: '整理当前目录下的文件'
  };
  
  document.getElementById('quickInput').value = templates[template] || '';
  document.getElementById('quickInput').focus();
}

function handleQuickInput(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    submitQuickInput();
  }
}

async function submitQuickInput() {
  const input = document.getElementById('quickInput');
  const description = input.value.trim();
  
  if (!description) return;
  
  input.value = '';
  
  // 自动识别需要使用的 Agent
  const autoDetectedAgents = detectAgentsFromDescription(description);
  
  // 快速输入默认使用自动规划模式，跳转到工作台执行
  await createTask(description, { 
    mode: 'auto',
    agents: autoDetectedAgents,
    openInWorkspace: true 
  });
}

/**
 * 根据任务描述自动识别需要使用的 Agent
 * @param {string} description - 任务描述
 * @returns {string[]} - 需要使用的 Agent 列表
 */
function detectAgentsFromDescription(description) {
  const desc = description.toLowerCase();
  const agents = [];
  
  // 浏览器 Agent - 搜索、网页、浏览相关
  if (/搜索|查找|查询|search|browse|网页|网站|链接|url|http|www|百度|谷歌|google|bing/.test(desc)) {
    agents.push('browser');
  }
  
  // 系统 Agent - 文件操作、打开应用、系统命令
  if (/打开|关闭|运行|执行|文件|文件夹|目录|复制|移动|删除|记事本|notepad|cmd|命令|系统|桌面|保存/.test(desc)) {
    agents.push('os');
  }
  
  // 代码 Agent - 编程、代码相关
  if (/代码|编程|程序|脚本|python|javascript|java|编写|开发|函数|类|code|script/.test(desc)) {
    agents.push('code');
  }
  
  // 数据 Agent - 数据分析、图表相关
  if (/数据|分析|统计|图表|excel|csv|报表|chart|analyze|data/.test(desc)) {
    agents.push('data');
  }
  
  // 视觉 Agent - 图片、图像相关
  if (/图片|图像|照片|识别|image|photo|picture|视觉|vision|截图/.test(desc)) {
    agents.push('vision');
  }
  
  // 如果没有识别到特定 Agent，或者需要生成内容，使用 LLM
  if (agents.length === 0 || /写|生成|创作|总结|翻译|解释|回答|帮我|请/.test(desc)) {
    agents.push('llm');
  }
  
  // 去重
  return [...new Set(agents)];
}

async function createNewTask() {
  const description = document.getElementById('newTaskDescription').value.trim();
  const priority = document.getElementById('newTaskPriority').value;
  const mode = document.getElementById('newTaskMode').value;
  
  if (!description) {
    showNotification(i18n.t('pleaseInputTask'), 'error');
    return;
  }
  
  // Get selected agents
  const selectedAgents = Array.from(
    document.querySelectorAll('.agent-checkbox input:checked')
  ).map(cb => cb.value);
  
  closeModal('newTaskModal');
  
  // 创建任务并跳转到工作台执行
  // 工作台会根据 mode 自动决定是否立即开始执行
  await createTask(description, { 
    priority, 
    mode, 
    agents: selectedAgents,
    openInWorkspace: true  // 跳转到工作台执行
  });
  
  // Clear form
  document.getElementById('newTaskDescription').value = '';
}

async function createTask(description, options = {}) {
  // Use TaskStore for persistent storage
  let task;
  if (window.taskStore) {
    task = window.taskStore.createTask(description, options);
  } else {
    // Fallback to old behavior
    const taskId = generateId();
    task = {
      id: taskId,
      description: description,
      status: 'pending',
      progress: 0,
      steps: [],
      currentStep: -1,
      output: [],
      result: null,
      createdAt: new Date().toISOString(),
      startedAt: null,
      completedAt: null,
      priority: options.priority || 2,
      mode: options.mode || 'auto',
      agents: options.agents || []
    };
  }
  
  state.tasks.set(task.id, task);
  state.totalStats.totalTasks++;
  
  addTaskToList(task);
  selectTask(task.id);
  
  // Check if user wants to open in workspace
  if (options.openInWorkspace) {
    // Navigate to workspace
    window.location.href = '/workspace';
    return;
  }
  
  // Start execution
  await executeTask(task.id);
  
  saveTasksToStorage();
  updateStats();
}

// Create task and open in visual workspace
async function createTaskInWorkspace(description, options = {}) {
  if (window.taskStore) {
    const task = window.taskStore.createTask(description, options);
    window.location.href = '/workspace';
  }
}

async function executeTask(taskId) {
  const task = state.tasks.get(taskId);
  if (!task) return;
  
  task.status = 'running';
  task.startedAt = new Date();
  updateTaskInList(task);
  updateTaskView(task);
  
  try {
    const response = await fetch(`${config.apiUrl}/task/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        task_id: taskId,
        description: task.description,
        priority: task.priority,
        mode: task.mode,
        agents: task.agents
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    // Start SSE for progress updates
    startTaskProgressStream(taskId);
    
  } catch (error) {
    console.error('Failed to start task:', error);
    
    // Fallback: use regular chat endpoint
    await executeTaskFallback(taskId);
  }
}

async function executeTaskFallback(taskId) {
  const task = state.tasks.get(taskId);
  if (!task) return;
  
  addOutput(taskId, 'system', i18n.t('taskStarting'));
  
  // Simulate planning phase
  await simulatePlanning(taskId);
  
  try {
    const response = await fetch(`${config.apiUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: task.description,
        user_id: 'default'
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Update task with result
    task.result = data.message;
    task.status = 'completed';
    task.progress = 100;
    task.completedAt = new Date();
    
    // Mark all steps as completed
    task.steps.forEach((step, i) => {
      step.status = 'completed';
      step.completedAt = new Date();
    });
    
    state.totalStats.completedTasks++;
    
    updateTaskInList(task);
    updateTaskView(task);
    showResult(taskId);
    
    addOutput(taskId, 'success', i18n.t('taskCompleteSuccess'));
    
  } catch (error) {
    console.error('Task execution failed:', error);
    task.status = 'failed';
    task.error = error.message;
    updateTaskInList(task);
    updateTaskView(task);
    addOutput(taskId, 'error', `${i18n.t('executionFailed')}: ${error.message}`);
  }
  
  saveTasksToStorage();
  updateStats();
}

async function simulatePlanning(taskId) {
  const task = state.tasks.get(taskId);
  if (!task) return;
  
  addOutput(taskId, 'system', i18n.t('taskAnalyzing'));
  await sleep(500);
  
  // Generate simulated steps based on task description
  const steps = generateSteps(task.description);
  task.steps = steps;
  state.totalStats.totalSteps += steps.length;
  
  addOutput(taskId, 'system', `${i18n.t('taskDecomposed')} ${steps.length} ${i18n.t('stepsText')}`);
  
  updateTaskView(task);
  
  // Simulate step execution
  for (let i = 0; i < steps.length; i++) {
    task.currentStep = i;
    steps[i].status = 'running';
    steps[i].startedAt = new Date();
    
    updateTaskView(task);
    updateAgentStatus(steps[i].agent, true);
    
    addOutput(taskId, 'agent', `[${getAgentName(steps[i].agent).toUpperCase()}] ${steps[i].description}`);
    
    // Simulate execution time
    await sleep(1000 + Math.random() * 2000);
    
    steps[i].status = 'completed';
    steps[i].completedAt = new Date();
    steps[i].output = `${i18n.t('stepCompleted')} ${i + 1}`;
    
    task.progress = Math.round(((i + 1) / steps.length) * 100);
    
    updateTaskView(task);
    updateAgentStatus(steps[i].agent, false);
    incrementAgentStats(steps[i].agent);
  }
}

function generateSteps(description) {
  const steps = [];
  const descLower = description.toLowerCase();
  
  // Determine which agents to use based on keywords
  if (descLower.includes('搜索') || descLower.includes('search') || descLower.includes('新闻')) {
    steps.push({
      id: generateId(),
      description: '搜索相关信息',
      agent: 'browser',
      status: 'pending'
    });
  }
  
  if (descLower.includes('代码') || descLower.includes('code') || descLower.includes('python') || descLower.includes('脚本')) {
    steps.push({
      id: generateId(),
      description: '生成代码实现',
      agent: 'code',
      status: 'pending'
    });
  }
  
  if (descLower.includes('文件') || descLower.includes('目录') || descLower.includes('file')) {
    steps.push({
      id: generateId(),
      description: '执行文件操作',
      agent: 'os',
      status: 'pending'
    });
  }
  
  if (descLower.includes('数据') || descLower.includes('分析') || descLower.includes('data') || descLower.includes('图表')) {
    steps.push({
      id: generateId(),
      description: '处理和分析数据',
      agent: 'data',
      status: 'pending'
    });
  }
  
  if (descLower.includes('图片') || descLower.includes('图像') || descLower.includes('image')) {
    steps.push({
      id: generateId(),
      description: '分析图像内容',
      agent: 'vision',
      status: 'pending'
    });
  }
  
  // Always add LLM for thinking/summarizing
  steps.push({
    id: generateId(),
    description: '分析和总结结果',
    agent: 'llm',
    status: 'pending'
  });
  
  return steps;
}

function startTaskProgressStream(taskId) {
  // Close existing stream if any
  if (state.activeEventSources.has(taskId)) {
    state.activeEventSources.get(taskId).close();
  }
  
  const eventSource = new EventSource(`${config.apiUrl}/task/${taskId}/stream`);
  state.activeEventSources.set(taskId, eventSource);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleTaskUpdate(taskId, data);
  };
  
  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
    state.activeEventSources.delete(taskId);
  };
}

function handleTaskUpdate(taskId, data) {
  const task = state.tasks.get(taskId);
  if (!task) return;
  
  // Update task state
  if (data.status) task.status = data.status;
  if (data.progress !== undefined) task.progress = data.progress;
  if (data.steps) task.steps = data.steps;
  if (data.currentStep !== undefined) task.currentStep = data.currentStep;
  if (data.result) task.result = data.result;
  
  // Update UI
  updateTaskInList(task);
  updateTaskView(task);
  
  // Handle completion
  if (data.status === 'completed' || data.status === 'failed') {
    task.completedAt = new Date();
    if (data.status === 'completed') {
      state.totalStats.completedTasks++;
      showResult(taskId);
    }
    
    // Close event source
    if (state.activeEventSources.has(taskId)) {
      state.activeEventSources.get(taskId).close();
      state.activeEventSources.delete(taskId);
    }
    
    saveTasksToStorage();
    updateStats();
  }
  
  // Add output
  if (data.output) {
    addOutput(taskId, data.outputType || 'system', data.output);
  }
}

function pauseTask() {
  console.log('pauseTask called, currentTaskId:', state.currentTaskId);
  
  if (!state.currentTaskId) {
    showNotification(i18n.currentLang === 'zh' ? '请先选择一个任务' : 'Please select a task first', 'warning');
    return;
  }
  
  const task = state.tasks.get(state.currentTaskId);
  if (!task) {
    showNotification(i18n.currentLang === 'zh' ? '任务不存在' : 'Task not found', 'error');
    return;
  }
  
  // TODO: Implement actual task pause via API
  const msg = i18n.currentLang === 'zh' ? '任务暂停功能开发中' : 'Pause feature in development';
  showNotification(msg, 'info');
}

function cancelTask() {
  console.log('cancelTask called, currentTaskId:', state.currentTaskId);
  
  if (!state.currentTaskId) {
    showNotification(i18n.currentLang === 'zh' ? '请先选择一个任务' : 'Please select a task first', 'warning');
    return;
  }
  
  const task = state.tasks.get(state.currentTaskId);
  if (!task) {
    showNotification(i18n.currentLang === 'zh' ? '任务不存在' : 'Task not found', 'error');
    return;
  }
  
  if (task.status === 'completed' || task.status === 'cancelled') {
    showNotification(i18n.currentLang === 'zh' ? '任务已完成或已取消' : 'Task already completed or cancelled', 'info');
    return;
  }
  
  // Confirm before cancelling
  const confirmMsg = i18n.currentLang === 'zh' ? '确定要取消此任务吗？' : 'Are you sure you want to cancel this task?';
  if (!confirm(confirmMsg)) {
    return;
  }
  
  task.status = 'cancelled';
  task.completedAt = new Date();
  
  // Close event source
  if (state.activeEventSources.has(state.currentTaskId)) {
    state.activeEventSources.get(state.currentTaskId).close();
    state.activeEventSources.delete(state.currentTaskId);
  }
  
  updateTaskInList(task);
  updateTaskView(task);
  saveTasksToStorage();
  updateStats();
  
  showNotification(i18n.t('taskCancelled'), 'info');
}

function deleteTask() {
  console.log('deleteTask called, currentTaskId:', state.currentTaskId);
  
  if (!state.currentTaskId) {
    showNotification(i18n.currentLang === 'zh' ? '请先选择一个任务' : 'Please select a task first', 'warning');
    return;
  }
  
  const task = state.tasks.get(state.currentTaskId);
  if (!task) {
    showNotification(i18n.currentLang === 'zh' ? '任务不存在' : 'Task not found', 'error');
    return;
  }
  
  // Confirm before deleting
  const confirmMsg = i18n.currentLang === 'zh' ? '确定要删除此任务吗？此操作无法撤销。' : 'Are you sure you want to delete this task? This cannot be undone.';
  if (!confirm(confirmMsg)) {
    return;
  }
  
  // Close event source if active
  if (state.activeEventSources.has(state.currentTaskId)) {
    state.activeEventSources.get(state.currentTaskId).close();
    state.activeEventSources.delete(state.currentTaskId);
  }
  
  const deletedTaskId = state.currentTaskId;
  
  // 从 TaskStore 删除（这会同步到 localStorage）
  if (window.taskStore) {
    window.taskStore.deleteTask(deletedTaskId);
  }
  
  // Remove from task list UI
  const taskItem = document.getElementById(`task-item-${deletedTaskId}`);
  if (taskItem) {
    taskItem.remove();
  }
  
  // Remove from local state
  state.tasks.delete(deletedTaskId);
  state.currentTaskId = null;
  
  // Clear task view and show welcome view
  document.getElementById('welcomeView').classList.remove('hidden');
  document.getElementById('taskView').classList.add('hidden');
  document.getElementById('pageTitle').textContent = i18n.t('taskCenter');
  
  updateStats();
  updateTaskCounts();
  refreshTaskLists();  // 刷新任务列表
  
  showNotification(i18n.t('taskDeleted'), 'success');
  console.log('Task deleted:', deletedTaskId);
}

// ============================================
// Task List UI
// ============================================

function refreshTaskLists() {
  console.log('refreshTaskLists called');
  
  // 清空现有列表（保留空状态提示）
  const activeList = document.getElementById('activeTaskList');
  const completedList = document.getElementById('completedTaskList');
  const activeEmpty = document.getElementById('activeEmptyState');
  const completedEmpty = document.getElementById('completedEmptyState');
  
  if (activeList) {
    // 只移除任务项，保留空状态元素
    activeList.querySelectorAll('.task-item').forEach(item => item.remove());
  }
  if (completedList) {
    completedList.querySelectorAll('.task-item').forEach(item => item.remove());
  }
  
  // 从 TaskStore 获取最新任务
  let activeCount = 0;
  let completedCount = 0;
  
  if (window.taskStore) {
    const allTasks = window.taskStore.getAllTasks();
    console.log('Tasks from TaskStore:', allTasks.length);
    
    allTasks.forEach(task => {
      if (task.status === 'completed') {
        completedCount++;
      } else {
        activeCount++;
      }
      addTaskToList(task);
    });
  }
  
  // 显示/隐藏空状态
  if (activeEmpty) {
    activeEmpty.style.display = activeCount === 0 ? 'flex' : 'none';
  }
  if (completedEmpty) {
    completedEmpty.style.display = completedCount === 0 ? 'flex' : 'none';
  }
  
  console.log('Task counts - Active:', activeCount, 'Completed:', completedCount);
}

function addTaskToList(task) {
  const listId = task.status === 'completed' ? 'completedTaskList' : 'activeTaskList';
  const list = document.getElementById(listId);
  
  const item = document.createElement('div');
  item.className = 'task-item';
  item.id = `task-item-${task.id}`;
  item.dataset.id = task.id;  // 添加 data-id 属性
  item.onclick = () => selectTask(task.id);
  
  item.innerHTML = `
    <div class="task-item-header">
      <div class="task-item-status ${task.status}"></div>
      <div class="task-item-title">${escapeHtml(task.description)}</div>
    </div>
    <div class="task-item-progress">
      <div class="task-item-progress-fill" style="width: ${task.progress}%"></div>
    </div>
    <div class="task-item-meta">
      <span>${formatTime(task.createdAt)}</span>
      <span>${task.steps.length} ${i18n.t('steps')}</span>
    </div>
  `;
  
  list.insertBefore(item, list.firstChild);
  updateTaskCounts();
}

function updateTaskInList(task) {
  const item = document.getElementById(`task-item-${task.id}`);
  if (!item) return;
  
  // Update status
  const statusEl = item.querySelector('.task-item-status');
  statusEl.className = `task-item-status ${task.status}`;
  
  // Update progress
  const progressFill = item.querySelector('.task-item-progress-fill');
  progressFill.style.width = `${task.progress}%`;
  
  // Move to correct list if needed
  const currentList = item.parentElement.id;
  const targetList = task.status === 'completed' ? 'completedTaskList' : 'activeTaskList';
  
  if (currentList !== targetList) {
    item.remove();
    document.getElementById(targetList).insertBefore(item, document.getElementById(targetList).firstChild);
  }
  
  updateTaskCounts();
}

function selectTask(taskId) {
  state.currentTaskId = taskId;
  const task = state.tasks.get(taskId);
  if (!task) return;
  
  // Update sidebar selection
  document.querySelectorAll('.task-item').forEach(item => {
    item.classList.remove('active');
  });
  const taskItem = document.getElementById(`task-item-${taskId}`);
  if (taskItem) taskItem.classList.add('active');
  
  // Show task view
  document.getElementById('welcomeView').classList.add('hidden');
  document.getElementById('taskView').classList.remove('hidden');
  document.getElementById('pageTitle').textContent = i18n.t('taskDetails');
  
  updateTaskView(task);
}

function updateTaskCounts() {
  // 从 TaskStore 获取真实的任务数量
  if (window.taskStore) {
    const allTasks = window.taskStore.getAllTasks();
    const completedCount = allTasks.filter(t => t.status === 'completed').length;
    const activeCount = allTasks.filter(t => t.status !== 'completed').length;
    
    document.getElementById('activeTaskCount').textContent = activeCount;
    document.getElementById('completedTaskCount').textContent = completedCount;
    
    // 同时更新统计面板
    const totalEl = document.getElementById('statTotalTasks');
    const completedEl = document.getElementById('statCompletedTasks');
    if (totalEl) totalEl.textContent = allTasks.length;
    if (completedEl) completedEl.textContent = completedCount;
  } else {
    // 回退到 DOM 计数
    const activeCount = document.getElementById('activeTaskList').children.length;
    const completedCount = document.getElementById('completedTaskList').children.length;
    
    document.getElementById('activeTaskCount').textContent = activeCount;
    document.getElementById('completedTaskCount').textContent = completedCount;
  }
}

// ============================================
// Task View UI
// ============================================

function updateTaskView(task) {
  // Update header
  document.getElementById('taskTitle').textContent = task.description;
  
  const statusBadge = document.getElementById('taskStatusBadge');
  statusBadge.className = `task-status-badge ${task.status}`;
  statusBadge.innerHTML = getStatusHtml(task.status);
  
  document.getElementById('taskCreatedAt').textContent = formatDateTime(task.createdAt);
  document.getElementById('taskDuration').textContent = formatDuration(task.startedAt, task.completedAt);
  
  // Update progress
  document.getElementById('progressPercent').textContent = `${task.progress}%`;
  document.getElementById('progressBarFill').style.width = `${task.progress}%`;
  
  const completedSteps = task.steps.filter(s => s.status === 'completed').length;
  const runningSteps = task.steps.filter(s => s.status === 'running').length;
  const pendingSteps = task.steps.filter(s => s.status === 'pending').length;
  
  document.getElementById('completedSteps').textContent = completedSteps;
  document.getElementById('runningSteps').textContent = runningSteps;
  document.getElementById('pendingSteps').textContent = pendingSteps;
  
  // Update workflow
  renderWorkflow(task);
  
  // Update action buttons based on task status
  // Always get fresh references to buttons (they might have been cloned)
  const pauseBtnEl = document.getElementById('pauseBtn');
  const cancelBtnEl = document.getElementById('cancelBtn');
  const deleteBtnEl = document.getElementById('deleteBtn');
  const isRunning = task.status === 'running' || task.status === 'pending';
  
  // Pause and cancel buttons only enabled when task is running
  if (pauseBtnEl) {
    pauseBtnEl.disabled = !isRunning;
    pauseBtnEl.title = isRunning ? (i18n.currentLang === 'zh' ? '暂停任务' : 'Pause task') : (i18n.currentLang === 'zh' ? '任务未运行' : 'Task not running');
  }
  if (cancelBtnEl) {
    cancelBtnEl.disabled = !isRunning;
    cancelBtnEl.title = isRunning ? (i18n.currentLang === 'zh' ? '停止任务' : 'Stop task') : (i18n.currentLang === 'zh' ? '任务未运行' : 'Task not running');
  }
  // Delete button is always enabled
  if (deleteBtnEl) {
    deleteBtnEl.disabled = false;
    deleteBtnEl.title = i18n.currentLang === 'zh' ? '删除任务' : 'Delete task';
  }
  
  console.log('Task buttons updated - isRunning:', isRunning, 'pauseBtn disabled:', pauseBtnEl?.disabled, 'deleteBtn disabled:', deleteBtnEl?.disabled);
  
  // Update right panel
  updateCurrentStepPanel(task);
  updateStepsSummary(task);
}

function getStatusHtml(status) {
  const isZh = i18n.currentLang === 'zh';
  const statusMap = {
    pending: `<i class="fas fa-clock"></i><span>${isZh ? '等待中' : 'Pending'}</span>`,
    running: `<i class="fas fa-spinner fa-spin"></i><span>${isZh ? '执行中' : 'Running'}</span>`,
    completed: `<i class="fas fa-check"></i><span>${isZh ? '已完成' : 'Completed'}</span>`,
    failed: `<i class="fas fa-times"></i><span>${isZh ? '失败' : 'Failed'}</span>`,
    cancelled: `<i class="fas fa-ban"></i><span>${isZh ? '已取消' : 'Cancelled'}</span>`
  };
  return statusMap[status] || statusMap.pending;
}

function renderWorkflow(task) {
  const container = document.getElementById('workflowContainer');
  container.innerHTML = '';
  
  task.steps.forEach((step, index) => {
    const stepEl = document.createElement('div');
    stepEl.className = `workflow-step ${step.status}`;
    
    stepEl.innerHTML = `
      <div class="step-indicator">
        ${step.status === 'completed' ? '<i class="fas fa-check"></i>' : 
          step.status === 'running' ? '<i class="fas fa-spinner fa-spin"></i>' : 
          step.status === 'failed' ? '<i class="fas fa-times"></i>' : 
          index + 1}
      </div>
      <div class="step-content">
        <div class="step-header">
          <span class="step-agent-badge ${step.agent}">
            <i class="${getAgentIcon(step.agent)}"></i>
            ${getAgentName(step.agent)}
          </span>
          <span class="step-time">${step.startedAt ? formatDuration(step.startedAt, step.completedAt) : '--'}</span>
        </div>
        <div class="step-description">${escapeHtml(step.description)}</div>
        ${step.output ? `<div class="step-output">${escapeHtml(step.output)}</div>` : ''}
      </div>
    `;
    
    container.appendChild(stepEl);
  });
}

function updateCurrentStepPanel(task) {
  const currentStep = task.steps[task.currentStep];
  
  if (!currentStep) {
    document.getElementById('currentStepNumber').textContent = '-';
    document.getElementById('currentStepDesc').textContent = i18n.t('selectTaskToView');
    return;
  }
  
  document.getElementById('currentStepNumber').textContent = `${task.currentStep + 1}/${task.steps.length}`;
  document.getElementById('currentStepDesc').textContent = currentStep.description;
  
  const agentEl = document.getElementById('currentStepAgent');
  const statusText = currentStep.status === 'running' ? i18n.t('active') : i18n.getStatusText(currentStep.status);
  agentEl.innerHTML = `
    <div class="agent-icon" style="background: var(--agent-${currentStep.agent}); color: white;">
      <i class="${getAgentIcon(currentStep.agent)}"></i>
    </div>
    <div class="agent-info">
      <div class="agent-name">${getAgentName(currentStep.agent)}</div>
      <div class="agent-type">${statusText}</div>
    </div>
  `;
}

function updateStepsSummary(task) {
  const container = document.getElementById('stepsMiniList');
  if (!container) return;
  
  if (!task.steps || task.steps.length === 0) {
    container.innerHTML = `<div class="empty-steps" data-i18n="noStepsYet">${i18n.t('noStepsYet') || '暂无步骤'}</div>`;
    return;
  }
  
  container.innerHTML = task.steps.map((step, index) => {
    const statusIcon = step.status === 'completed' ? 'fa-check' :
                       step.status === 'running' ? 'fa-spinner fa-spin' :
                       step.status === 'failed' ? 'fa-times' : 'fa-circle';
    
    return `
      <div class="step-mini-item ${step.status}">
        <div class="step-mini-icon ${step.status}">
          <i class="fas ${statusIcon}"></i>
        </div>
        <span class="step-mini-text">${index + 1}. ${escapeHtml(step.description)}</span>
        <span class="step-mini-agent">${getAgentName(step.agent)}</span>
      </div>
    `;
  }).join('');
}

function showResult(taskId) {
  const task = state.tasks.get(taskId);
  if (!task || !task.result) return;
  
  const resultSection = document.getElementById('resultSection');
  const resultContent = document.getElementById('resultContent');
  
  resultSection.classList.remove('hidden');
  resultContent.innerHTML = marked.parse(task.result);
  
  // Highlight code blocks
  resultContent.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });
}

// ============================================
// Output Console
// ============================================

function addOutput(taskId, type, message) {
  if (taskId !== state.currentTaskId) return;
  
  const console = document.getElementById('outputConsole');
  const line = document.createElement('div');
  line.className = `output-line ${type}`;
  
  const timestamp = new Date().toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
  
  line.innerHTML = `
    <span class="timestamp">[${timestamp}]</span>
    <span class="content">${escapeHtml(message)}</span>
  `;
  
  console.appendChild(line);
  console.scrollTop = console.scrollHeight;
}

function clearOutput() {
  const console = document.getElementById('outputConsole');
  console.innerHTML = `
    <div class="output-line system">
      <span class="timestamp">[${i18n.t('system')}]</span>
      <span class="content">${i18n.t('outputCleared')}</span>
    </div>
  `;
}

function copyOutput() {
  const console = document.getElementById('outputConsole');
  const text = Array.from(console.querySelectorAll('.output-line'))
    .map(line => line.textContent)
    .join('\n');
  
  navigator.clipboard.writeText(text).then(() => {
    showNotification(i18n.t('copiedToClipboard'), 'success');
  });
}

// ============================================
// Agent Status
// ============================================

function updateAgentStatus(agent, active) {
  // Update header indicator
  const indicator = document.querySelector(`.agent-indicator[data-agent="${agent}"]`);
  if (indicator) {
    indicator.classList.toggle('active', active);
  }
  
  // Update panel card
  const card = document.querySelector(`.agent-card[data-agent="${agent}"]`);
  if (card) {
    card.classList.toggle('active', active);
    const status = card.querySelector('.agent-card-status');
    status.textContent = active ? i18n.t('active') : i18n.t('idle');
    status.classList.toggle('active', active);
  }
}

function incrementAgentStats(agent) {
  state.agentStats[agent]++;
  
  const card = document.querySelector(`.agent-card[data-agent="${agent}"]`);
  if (card) {
    const stats = card.querySelector('.agent-card-stats span');
    stats.textContent = state.agentStats[agent];
  }
}

// ============================================
// Settings
// ============================================

function showSettings() {
  document.getElementById('maxParallelTasks').value = config.maxParallelTasks;
  document.getElementById('autoRetry').checked = config.autoRetry;
  
  // 加载并行搜索引擎设置
  loadParallelEnginesSettings();
  
  openModal('settingsModal');
  checkApiStatus();
  loadModels();
}

// 加载并行搜索引擎设置
function loadParallelEnginesSettings() {
  if (!window.taskStore) return;
  
  const selectedEngines = window.taskStore.getSelectedParallelEngines();
  const checkboxes = document.querySelectorAll('#searchEngineSelector input[type="checkbox"]');
  
  checkboxes.forEach(checkbox => {
    checkbox.checked = selectedEngines.includes(checkbox.value);
  });
}

// 更新并行搜索引擎
function updateParallelEngines() {
  const checkboxes = document.querySelectorAll('#searchEngineSelector input[type="checkbox"]:checked');
  const selectedEngines = Array.from(checkboxes).map(cb => cb.value);
  
  // 至少选择一个搜索引擎
  if (selectedEngines.length === 0) {
    showNotification('请至少选择一个搜索引擎', 'error');
    // 重新加载设置
    loadParallelEnginesSettings();
    return;
  }
  
  if (window.taskStore) {
    window.taskStore.setParallelEngines(selectedEngines);
    console.log('并行搜索引擎已设置为:', selectedEngines);
  }
}

function validateMaxParallel(input) {
  let value = parseInt(input.value);
  if (isNaN(value) || value < 1) value = 1;
  if (value > 5) value = 5;
  input.value = value;
}

function saveSettings() {
  let maxParallel = parseInt(document.getElementById('maxParallelTasks').value);
  // 强制限制为 1-5
  if (isNaN(maxParallel) || maxParallel < 1) maxParallel = 1;
  if (maxParallel > 5) maxParallel = 5;
  
  config.maxParallelTasks = maxParallel;
  config.autoRetry = document.getElementById('autoRetry').checked;
  
  localStorage.setItem('maxParallelTasks', config.maxParallelTasks);
  localStorage.setItem('autoRetry', config.autoRetry);
  
  closeModal('settingsModal');
  showNotification(i18n.t('settingsSaved'), 'success');
}

// 导出验证函数
window.validateMaxParallel = validateMaxParallel;

function loadSettings() {
  // Settings are now loaded from server
}

async function checkApiStatus() {
  const statusIndicator = document.getElementById('apiStatusIndicator');
  const statusText = document.getElementById('apiStatusText');
  const modelDisplay = document.getElementById('currentModelDisplay');
  const keyStatus = document.getElementById('apiKeyStatus');
  
  // Set loading state
  statusIndicator.className = 'status-indicator checking';
  statusText.textContent = i18n.t('checking');
  
  try {
    const response = await fetch(`${config.apiUrl}/api/status`);
    if (!response.ok) throw new Error('Network error');
    
    const data = await response.json();
    
    // Update status display
    if (data.connected) {
      statusIndicator.className = 'status-indicator connected';
      statusText.textContent = i18n.t('connected');
    } else {
      statusIndicator.className = 'status-indicator disconnected';
      statusText.textContent = i18n.t('disconnected');
    }
    
    // Update model display
    modelDisplay.textContent = data.model_name || data.model || '-';
    
    // Update API key status
    if (data.has_api_key) {
      keyStatus.textContent = data.api_key_preview || i18n.t('configured');
      keyStatus.style.color = 'var(--accent-success)';
    } else {
      keyStatus.textContent = i18n.t('notConfigured');
      keyStatus.style.color = 'var(--accent-danger)';
    }
    
  } catch (error) {
    console.error('Failed to check API status:', error);
    statusIndicator.className = 'status-indicator disconnected';
    statusText.textContent = i18n.t('disconnected');
    modelDisplay.textContent = '-';
    keyStatus.textContent = i18n.t('notConfigured');
    keyStatus.style.color = 'var(--accent-danger)';
  }
}

// ============================================
// Model Management
// ============================================

async function loadModels() {
  const modelList = document.getElementById('modelList');
  if (!modelList) return;
  
  try {
    const response = await fetch(`${config.apiUrl}/api/models`);
    if (!response.ok) throw new Error('Failed to load models');
    
    const data = await response.json();
    renderModelList(data.models);
  } catch (error) {
    console.error('Failed to load models:', error);
    modelList.innerHTML = `
      <div class="model-list-empty">
        <i class="fas fa-exclamation-triangle"></i>
        <p>${i18n.currentLang === 'zh' ? '加载模型失败' : 'Failed to load models'}</p>
      </div>
    `;
  }
}

function renderModelList(models) {
  const modelList = document.getElementById('modelList');
  if (!modelList) return;
  
  if (!models || models.length === 0) {
    modelList.innerHTML = `
      <div class="model-list-empty">
        <i class="fas fa-cube"></i>
        <p>${i18n.currentLang === 'zh' ? '暂无模型配置' : 'No models configured'}</p>
      </div>
    `;
    return;
  }
  
  const defaultText = i18n.currentLang === 'zh' ? '默认' : 'Default';
  const editText = i18n.currentLang === 'zh' ? '编辑' : 'Edit';
  const deleteText = i18n.currentLang === 'zh' ? '删除' : 'Delete';
  const setDefaultText = i18n.currentLang === 'zh' ? '设为默认' : 'Set as default';
  
  // Get provider icon based on provider name
  const getProviderIcon = (provider) => {
    const iconMap = {
      openai: 'fa-robot',
      anthropic: 'fa-brain',
      deepseek: 'fa-microchip',
      azure: 'fa-cloud',
      google: 'fa-google',
      other: 'fa-cube'
    };
    return iconMap[provider] || 'fa-cube';
  };
  
  const apiKeyConfigured = i18n.currentLang === 'zh' ? 'Key 已配置' : 'Key configured';
  const apiKeyNotConfigured = i18n.currentLang === 'zh' ? 'Key 未配置' : 'Key not configured';
  
  modelList.innerHTML = models.map(model => {
    const isDefault = model.is_default || model.default;
    const provider = model.provider || 'other';
    const providerDisplay = provider.charAt(0).toUpperCase() + provider.slice(1);
    const hasApiKey = model.has_api_key;
    return `
    <div class="model-item ${model.enabled ? '' : 'disabled'} ${isDefault ? 'default' : ''}" data-model-id="${model.id}">
      <div class="model-item-icon ${provider}">
        <i class="fas ${getProviderIcon(provider)}"></i>
      </div>
      <div class="model-item-info">
        <div class="model-item-name">
          ${escapeHtml(model.name || model.id)}
          ${isDefault ? `<span class="default-badge">${defaultText}</span>` : ''}
        </div>
        <div class="model-item-meta">
          ${providerDisplay}
          <span class="model-key-status ${hasApiKey ? 'configured' : 'not-configured'}">
            <i class="fas fa-key"></i>
            ${hasApiKey ? apiKeyConfigured : apiKeyNotConfigured}
          </span>
        </div>
      </div>
      <div class="model-item-actions">
        ${!isDefault ? `
          <button onclick="setDefaultModel('${model.id}')" title="${setDefaultText}" type="button">
            <i class="fas fa-star"></i>
          </button>
        ` : ''}
        <button onclick="editModel('${model.id}')" title="${editText}" type="button">
          <i class="fas fa-pen"></i>
        </button>
        <button class="danger" onclick="deleteModel('${model.id}')" title="${deleteText}" type="button">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </div>
  `;}).join('');
}

function showAddModelForm() {
  document.getElementById('editModelId').value = '';
  document.getElementById('modelIdInput').value = '';
  document.getElementById('modelApiKeyInput').value = '';
  document.getElementById('modelApiBaseInput').value = '';
  document.getElementById('modelNameInput').value = '';
  document.getElementById('modelEnabledInput').checked = true;
  document.getElementById('modelDefaultInput').checked = false;
  document.getElementById('modelFormTitle').textContent = i18n.currentLang === 'zh' ? '添加模型' : 'Add Model';
  
  // Reset password visibility
  const apiKeyInput = document.getElementById('modelApiKeyInput');
  if (apiKeyInput) apiKeyInput.type = 'password';
  const toggleIcon = document.getElementById('apiKeyToggleIcon');
  if (toggleIcon) toggleIcon.className = 'fas fa-eye';
  
  openModal('modelFormModal');
}

function toggleApiKeyVisibility() {
  const input = document.getElementById('modelApiKeyInput');
  const icon = document.getElementById('apiKeyToggleIcon');
  
  if (input.type === 'password') {
    input.type = 'text';
    icon.className = 'fas fa-eye-slash';
  } else {
    input.type = 'password';
    icon.className = 'fas fa-eye';
  }
}

async function editModel(modelId) {
  try {
    const response = await fetch(`${config.apiUrl}/api/models`);
    const data = await response.json();
    const model = data.models.find(m => m.id === modelId);
    
    if (!model) {
      showNotification(i18n.currentLang === 'zh' ? '模型不存在' : 'Model not found', 'error');
      return;
    }
    
    document.getElementById('editModelId').value = model.id;
    document.getElementById('modelIdInput').value = model.id;
    document.getElementById('modelApiKeyInput').value = ''; // API Key is never returned for security
    document.getElementById('modelApiKeyInput').placeholder = model.has_api_key ? (i18n.currentLang === 'zh' ? '已配置，留空则保持不变' : 'Configured, leave empty to keep') : 'sk-...';
    document.getElementById('modelApiBaseInput').value = model.api_base || '';
    document.getElementById('modelNameInput').value = model.name || '';
    document.getElementById('modelEnabledInput').checked = model.enabled !== false;
    document.getElementById('modelDefaultInput').checked = model.is_default === true || model.default === true;
    document.getElementById('modelFormTitle').textContent = i18n.currentLang === 'zh' ? '编辑模型' : 'Edit Model';
    
    // Reset password visibility
    const apiKeyInput = document.getElementById('modelApiKeyInput');
    if (apiKeyInput) apiKeyInput.type = 'password';
    const toggleIcon = document.getElementById('apiKeyToggleIcon');
    if (toggleIcon) toggleIcon.className = 'fas fa-eye';
    
    openModal('modelFormModal');
  } catch (error) {
    console.error('Failed to load model:', error);
    showNotification(i18n.currentLang === 'zh' ? '加载模型失败' : 'Failed to load model', 'error');
  }
}

async function saveModel() {
  const editId = document.getElementById('editModelId').value;
  const apiKey = document.getElementById('modelApiKeyInput').value.trim();
  const apiBase = document.getElementById('modelApiBaseInput').value.trim();
  
  const modelData = {
    id: document.getElementById('modelIdInput').value.trim(),
    name: document.getElementById('modelNameInput').value.trim(),
    enabled: document.getElementById('modelEnabledInput').checked,
    is_default: document.getElementById('modelDefaultInput').checked
  };
  
  // Only include api_key if provided (for edit, empty means keep existing)
  if (apiKey) {
    modelData.api_key = apiKey;
  }
  
  // Include api_base if provided
  if (apiBase) {
    modelData.api_base = apiBase;
  }
  
  if (!modelData.id) {
    showNotification(i18n.currentLang === 'zh' ? '请输入模型ID' : 'Please enter model ID', 'error');
    return;
  }
  
  if (!modelData.name) {
    modelData.name = modelData.id;
  }
  
  try {
    let response;
    if (editId) {
      // Update existing model
      response = await fetch(`${config.apiUrl}/api/models/${editId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modelData)
      });
    } else {
      // Add new model
      response = await fetch(`${config.apiUrl}/api/models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modelData)
      });
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save model');
    }
    
    closeModal('modelFormModal');
    loadModels();
    checkApiStatus();
    showNotification(i18n.currentLang === 'zh' ? '模型已保存' : 'Model saved', 'success');
  } catch (error) {
    console.error('Failed to save model:', error);
    showNotification(error.message, 'error');
  }
}

async function deleteModel(modelId) {
  const confirmText = i18n.currentLang === 'zh' ? '确定要删除此模型吗？' : 'Are you sure you want to delete this model?';
  if (!confirm(confirmText)) return;
  
  try {
    const response = await fetch(`${config.apiUrl}/api/models/${modelId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete model');
    }
    
    loadModels();
    checkApiStatus();
    showNotification(i18n.currentLang === 'zh' ? '模型已删除' : 'Model deleted', 'success');
  } catch (error) {
    console.error('Failed to delete model:', error);
    showNotification(i18n.currentLang === 'zh' ? '删除模型失败' : 'Failed to delete model', 'error');
  }
}

async function setDefaultModel(modelId) {
  try {
    const response = await fetch(`${config.apiUrl}/api/models/${modelId}/set-default`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to set default model');
    }
    
    loadModels();
    checkApiStatus();
    showNotification(i18n.currentLang === 'zh' ? '已设为默认模型' : 'Set as default model', 'success');
  } catch (error) {
    console.error('Failed to set default model:', error);
    showNotification(i18n.currentLang === 'zh' ? '设置失败' : 'Failed to set default', 'error');
  }
}

async function reloadConfig() {
  try {
    const response = await fetch(`${config.apiUrl}/api/config/reload`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to reload config');
    }
    
    loadModels();
    checkApiStatus();
    showNotification(i18n.currentLang === 'zh' ? '配置已重载' : 'Configuration reloaded', 'success');
  } catch (error) {
    console.error('Failed to reload config:', error);
    showNotification(i18n.currentLang === 'zh' ? '重载配置失败' : 'Failed to reload config', 'error');
  }
}

async function restartServer() {
  const confirmMsg = i18n.currentLang === 'zh' 
    ? '确定要重启服务吗？页面将在服务重启后自动刷新。' 
    : 'Are you sure you want to restart the server? The page will refresh after restart.';
  
  if (!confirm(confirmMsg)) {
    return;
  }
  
  try {
    const response = await fetch(`${config.apiUrl}/api/restart`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to restart server');
    }
    
    showNotification(i18n.currentLang === 'zh' ? '服务正在重启...' : 'Server is restarting...', 'info');
    
    // Wait a bit then try to reconnect
    setTimeout(() => {
      checkServerAndReload();
    }, 2000);
    
  } catch (error) {
    console.error('Failed to restart server:', error);
    showNotification(i18n.currentLang === 'zh' ? '重启服务失败' : 'Failed to restart server', 'error');
  }
}

async function checkServerAndReload() {
  const maxAttempts = 10;
  let attempts = 0;
  
  const checkServer = async () => {
    try {
      const response = await fetch(`${config.apiUrl}/health`);
      if (response.ok) {
        window.location.reload();
        return;
      }
    } catch (e) {
      // Server not ready yet
    }
    
    attempts++;
    if (attempts < maxAttempts) {
      setTimeout(checkServer, 1000);
    } else {
      showNotification(i18n.currentLang === 'zh' ? '服务重启超时，请手动刷新页面' : 'Server restart timed out, please refresh manually', 'error');
    }
  };
  
  checkServer();
}

// ============================================
// Statistics
// ============================================

function updateStats() {
  document.getElementById('statTotalTasks').textContent = state.totalStats.totalTasks;
  document.getElementById('statCompletedTasks').textContent = state.totalStats.completedTasks;
  document.getElementById('statTotalSteps').textContent = state.totalStats.totalSteps;
}

// ============================================
// Storage
// ============================================

function saveTasksToStorage() {
  const tasksArray = Array.from(state.tasks.entries()).map(([id, task]) => ({
    ...task,
    createdAt: task.createdAt?.toISOString(),
    startedAt: task.startedAt?.toISOString(),
    completedAt: task.completedAt?.toISOString()
  }));
  
  localStorage.setItem('joinflow_tasks', JSON.stringify(tasksArray));
  localStorage.setItem('joinflow_stats', JSON.stringify(state.totalStats));
}

function loadTasksFromStorage() {
  try {
    // Load from TaskStore if available
    if (window.taskStore) {
      const tasks = window.taskStore.getAllTasks();
      tasks.forEach(task => {
        state.tasks.set(task.id, task);
        addTaskToList(task);
      });
      
      // Subscribe to changes
      window.taskStore.subscribe((allTasks, currentTask) => {
        // Sync state
        state.tasks.clear();
        allTasks.forEach(task => {
          state.tasks.set(task.id, task);
        });
        updateStats();
        updateTaskCounts();
        refreshTaskLists();
      });
      
      console.log(`Loaded ${tasks.length} tasks from TaskStore`);
      return;
    }
    
    // Fallback to old storage
    const tasksJson = localStorage.getItem('joinflow_tasks');
    const statsJson = localStorage.getItem('joinflow_stats');
    
    if (tasksJson) {
      const tasksArray = JSON.parse(tasksJson);
      tasksArray.forEach(task => {
        task.createdAt = task.createdAt ? new Date(task.createdAt) : null;
        task.startedAt = task.startedAt ? new Date(task.startedAt) : null;
        task.completedAt = task.completedAt ? new Date(task.completedAt) : null;
        state.tasks.set(task.id, task);
        addTaskToList(task);
      });
    }
    
    if (statsJson) {
      Object.assign(state.totalStats, JSON.parse(statsJson));
    }
  } catch (e) {
    console.error('Failed to load tasks from storage:', e);
  }
}

// ============================================
// File Upload
// ============================================

function setupFileUpload() {
  const uploadArea = document.getElementById('fileUploadArea');
  const fileInput = document.getElementById('taskFiles');
  
  if (!uploadArea || !fileInput) return;
  
  uploadArea.onclick = () => fileInput.click();
  
  uploadArea.ondragover = (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--accent-primary)';
  };
  
  uploadArea.ondragleave = () => {
    uploadArea.style.borderColor = 'var(--border-color)';
  };
  
  uploadArea.ondrop = (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--border-color)';
    handleFiles(e.dataTransfer.files);
  };
  
  fileInput.onchange = (e) => {
    handleFiles(e.target.files);
  };
}

function handleFiles(files) {
  const fileList = document.getElementById('uploadedFiles');
  fileList.innerHTML = '';
  
  Array.from(files).forEach(file => {
    const item = document.createElement('div');
    item.style.cssText = 'display: flex; align-items: center; gap: 8px; padding: 8px; background: var(--bg-tertiary); border-radius: 6px; margin-top: 8px;';
    item.innerHTML = `
      <i class="fas fa-file" style="color: var(--accent-primary);"></i>
      <span style="flex: 1;">${escapeHtml(file.name)}</span>
      <span style="color: var(--text-muted); font-size: 0.8rem;">${formatFileSize(file.size)}</span>
    `;
    fileList.appendChild(item);
  });
}

// ============================================
// Modal Management
// ============================================

function openModal(id) {
  document.getElementById(id).classList.add('active');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.onclick = (e) => {
    if (e.target === overlay) {
      overlay.classList.remove('active');
    }
  };
});

// ============================================
// Keyboard Shortcuts
// ============================================

function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K - New task
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      showNewTaskModal();
    }
    
    // Escape - Close modals
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(modal => {
        modal.classList.remove('active');
      });
    }
    
    // Ctrl/Cmd + / - Focus quick input
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault();
      document.getElementById('quickInput').focus();
    }
  });
}

// ============================================
// Utilities
// ============================================

function generateId() {
  return 'task_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatTime(date) {
  if (!date) return '--';
  return new Date(date).toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

function formatDateTime(date) {
  if (!date) return '--';
  return new Date(date).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatDuration(start, end) {
  if (!start) return '--';
  const endTime = end ? new Date(end) : new Date();
  const diff = endTime - new Date(start);
  
  const seconds = Math.floor(diff / 1000) % 60;
  const minutes = Math.floor(diff / 60000) % 60;
  const hours = Math.floor(diff / 3600000);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  } else {
    return `${seconds}s`;
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function getAgentIcon(agent) {
  const icons = {
    browser: 'fas fa-globe',
    llm: 'fas fa-brain',
    os: 'fas fa-terminal',
    code: 'fas fa-code',
    data: 'fas fa-chart-bar',
    vision: 'fas fa-eye'
  };
  return icons[agent] || 'fas fa-robot';
}

function getAgentName(agent) {
  if (i18n && i18n.currentLang === 'zh') {
    const names = {
      browser: '浏览器',
      llm: '大模型',
      os: '系统',
      code: '代码',
      data: '数据',
      vision: '视觉'
    };
    return names[agent] || agent;
  }
  const names = {
    browser: 'Browser',
    llm: 'LLM',
    os: 'OS',
    code: 'Code',
    data: 'Data',
    vision: 'Vision'
  };
  return names[agent] || agent;
}

// Function to update dynamic content when language changes
function updateDynamicI18n() {
  // Update agent card status
  document.querySelectorAll('.agent-card-status').forEach(el => {
    if (el.classList.contains('active')) {
      el.textContent = i18n.t('active');
    } else {
      el.textContent = i18n.t('idle');
    }
  });
  
  // Update task list items if any
  state.tasks.forEach((task, taskId) => {
    updateTaskInList(task);
  });
  
  // Update current task view if viewing one
  if (state.currentTaskId) {
    const task = state.tasks.get(state.currentTaskId);
    if (task) {
      updateTaskView(task);
    }
  }
  
  // Update page title based on current view
  const pageTitle = document.getElementById('pageTitle');
  if (pageTitle) {
    if (state.currentTaskId) {
      pageTitle.textContent = i18n.t('taskDetails');
    } else {
      pageTitle.textContent = i18n.t('taskCenter');
    }
  }
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    bottom: 100px;
    right: 20px;
    padding: 12px 24px;
    background: ${type === 'success' ? 'var(--accent-success)' : 
                  type === 'error' ? 'var(--accent-danger)' : 
                  'var(--accent-primary)'};
    color: white;
    border-radius: 8px;
    font-weight: 500;
    box-shadow: var(--shadow-lg);
    z-index: 9999;
    animation: slideIn 0.3s ease;
  `;
  notification.textContent = message;
  
  // Add animation style
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}
