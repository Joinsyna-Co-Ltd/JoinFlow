/**
 * JoinFlow - Internationalization (i18n) Module
 * Supports Chinese and English language switching
 */

const i18n = {
  currentLang: 'zh',
  
  translations: {
    zh: {
      // Header
      taskCenter: '任务中心',
      taskDetails: '任务详情',
      
      // Sidebar
      newTask: '新建任务',
      inProgress: '进行中',
      completed: '已完成',
      settings: '设置',
      noActiveTasks: '暂无进行中的任务',
      noCompletedTasks: '暂无已完成的任务',
      
      // Welcome
      heroSubtitle: '智能多Agent协作系统 - 自动规划、分解、执行复杂任务',
      quickStart: '快速开始',
      templateResearch: '信息检索',
      templateResearchDesc: '搜索、整理、总结网络信息',
      templateCode: '代码生成',
      templateCodeDesc: '编写、调试、优化代码',
      templateData: '数据分析',
      templateDataDesc: '处理、分析、可视化数据',
      templateFile: '文件处理',
      templateFileDesc: '读取、转换、管理文件',
      
      // Stats
      totalTasks: '总任务数',
      completedTasks: '已完成',
      executionSteps: '执行步骤',
      availableAgents: '可用Agent',
      
      // Task View
      pending: '等待中',
      executing: '执行中',
      running: '执行中',
      taskCompleted: '已完成',
      taskFailed: '失败',
      failed: '失败',
      taskCancelled: '已取消',
      cancelled: '已取消',
      overallProgress: '总体进度',
      stepsCompleted: '已完成',
      stepsRunning: '执行中',
      stepsPending: '待执行',
      executionFlow: '执行流程',
      liveOutput: '实时输出',
      finalResult: '最终结果',
      system: '系统',
      waitingStart: '等待任务开始...',
      
      // Right Panel
      taskProgress: '任务进度',
      currentStep: '当前步骤',
      taskSteps: '任务步骤',
      noStepsYet: '暂无步骤',
      waiting: '等待中',
      selectTaskToView: '选择一个任务以查看详情',
      idle: '空闲',
      active: '执行中',
      executionCount: '执行次数',
      
      // Input
      inputPlaceholder: '输入任务描述，按 Enter 开始执行...',
      
      // New Task Modal
      createNewTask: '创建新任务',
      taskDescription: '任务描述',
      taskDescPlaceholder: '详细描述你想要完成的任务...\n\n例如：搜索最新的AI技术趋势，整理成报告',
      priority: '优先级',
      priorityUrgent: '🔴 紧急',
      priorityNormal: '🟡 普通',
      priorityLow: '🟢 低优先级',
      executionMode: '执行模式',
      modeAuto: '🤖 自动规划',
      modeStep: '👣 逐步确认',
      specifyAgents: '指定Agent (可选)',
      attachments: '附件 (可选)',
      dragFiles: '拖拽文件到此处，或',
      clickUpload: '点击上传',
      cancel: '取消',
      startExecution: '开始执行',
      
      // Settings Modal
      systemSettings: '系统设置',
      apiStatus: 'API 状态',
      connectionStatus: '连接状态',
      currentModel: '当前模型',
      apiKeyStatus: 'API Key',
      checking: '检测中...',
      connected: '已连接',
      disconnected: '未连接',
      configured: '已配置',
      notConfigured: '未配置',
      refreshStatus: '刷新状态',
      displaySettings: '显示设置',
      autoRetry: '自动重试失败步骤',
      maxParallelTasks: '最大并行任务数',
      close: '关闭',
      saveSettings: '保存设置',
      reloadConfig: '重载配置',
      apiConfiguredOnServer: 'API 配置由服务端管理',
      
      // Model Management
      modelManagement: '模型管理',
      addModel: '添加模型',
      editModel: '编辑模型',
      modelId: '模型 ID',
      modelIdHint: '输入模型ID，系统将自动识别提供商',
      apiKey: 'API Key',
      apiKeyHint: 'API Key 将安全存储在服务端',
      apiBaseUrl: 'API Base URL（可选）',
      apiBaseUrlHint: '留空则使用默认地址',
      modelName: '模型名称（可选）',
      provider: '服务商',
      enabled: '启用',
      setAsDefault: '设为默认',
      save: '保存',
      default: '默认',
      restart: '重启服务',
      
      // Actions
      pause: '暂停',
      stop: '停止',
      resume: '继续',
      clear: '清空',
      copy: '复制',
      deleteTask: '删除任务',
      
      // Notifications
      settingsSaved: '设置已保存',
      taskCreated: '任务已创建',
      taskCancelled: '任务已取消',
      taskDeleted: '任务已删除',
      copiedToClipboard: '已复制到剪贴板',
      outputCleared: '输出已清空',
      apiConnected: 'API 连接正常',
      apiError: 'API 连接失败',
      pleaseInputTask: '请输入任务描述',
      
      // Step descriptions
      searchInfo: '搜索相关信息',
      generateCode: '生成代码实现',
      fileOperation: '执行文件操作',
      processData: '处理和分析数据',
      analyzeImage: '分析图像内容',
      analyzeResult: '分析和总结结果',
      stepCompleted: '步骤执行完成',
      
      // Agent names
      browserAgent: '浏览器 Agent',
      llmAgent: '大模型 Agent',
      osAgent: '系统 Agent',
      codeAgent: '代码 Agent',
      dataAgent: '数据 Agent',
      visionAgent: '视觉 Agent',
      executionCount: '执行次数',
      
      // Time
      justNow: '刚刚',
      minutesAgo: '分钟前',
      hoursAgo: '小时前',
      steps: '步骤',
      
      // Task execution
      taskStarting: '开始执行任务...',
      taskAnalyzing: '正在分析任务...',
      taskDecomposed: '任务已分解为',
      stepsText: '个步骤',
      taskCompleteSuccess: '任务执行完成！',
      executionFailed: '执行失败',
      
      // Feature navigation
      workspace: '工作台',
      knowledgeBase: '知识库',
      workflows: '工作流',
      statistics: '统计',
      schedules: '定时',
      
      // Knowledge Base
      documents: '文档',
      collections: '集合',
      uploadDocument: '上传文档',
      noDocuments: '暂无文档，点击上方按钮上传',
      addCollection: '添加集合',
      selectFile: '选择文件',
      dropFileHere: '拖拽文件到此处或点击选择',
      collection: '知识库集合',
      tags: '标签 (逗号分隔)',
      upload: '上传',
      loading: '加载中...',
      
      // Workflows
      workflowTemplates: '工作流模板',
      
      // Statistics
      usageStatistics: '使用统计',
      successRate: '成功率',
      totalTokens: 'Tokens',
      estimatedCost: '预估成本',
      statsChartPlaceholder: '统计图表将在此显示',
      exportJSON: '导出 JSON',
      exportMarkdown: '导出 Markdown',
      
      // Schedules
      scheduledTasks: '定时任务',
      addSchedule: '添加定时任务',
      noSchedules: '暂无定时任务',
      
      // Task Templates
      templates: '模板',
      taskTemplates: '任务模板',
      builtinTemplates: '内置模板',
      customTemplates: '自定义模板',
      useTemplate: '使用模板',
      noTemplates: '暂无模板',
      templateVariables: '模板变量',
      outputFormat: '输出格式',
      
      // Export Formats
      exportAs: '导出为...',
      exportMarkdown: 'Markdown (.md)',
      exportHtml: 'HTML (.html)',
      exportJson: 'JSON (.json)',
      exportExcel: 'Excel (.xlsx)',
      exportPpt: 'PowerPoint (.pptx)',
      exportPdf: 'PDF (.pdf)',
      enterpriseFeature: '企业版',
      exporting: '导出中...',
      exportSuccess: '导出成功',
      exportFailed: '导出失败',
      
      // Workspace
      wsInputPlaceholder: '输入任务指令... (按 Enter 执行)',
      wsHistory: '历史记录',
      wsSettings: '设置',
      wsBackHome: '返回主页',
      wsExecutionFlow: '执行流程',
      wsTaskList: '任务列表',
      wsHistoryTasks: '历史任务',
      wsClear: '清空',
      wsWaitingTask: '等待任务...',
      wsSteps: '步骤',
      wsEnterTaskToStart: '输入任务开始执行',
      wsAgentVision: 'Agent 视野',
      wsEnterCommandToStart: '输入任务指令开始执行',
      wsPause: '暂停',
      wsStartExecution: '开始执行',
      wsStop: '终止',
      wsViewResult: '查看结果',
      wsRerun: '重新执行',
      wsAgentConsole: 'Agent 控制台',
      wsAgentThinking: 'Agent 思考中',
      wsExecutionLogs: '执行日志',
      wsFilterAll: '全部',
      wsFilterAction: '操作',
      wsFilterError: '错误',
      wsDuration: '运行时长',
      wsStepsCount: '执行步骤',
      wsTaskSuccess: '🎉 任务执行成功！',
      wsSelectAction: '选择以下操作查看结果',
      wsOpenFile: '打开文件',
      wsCopyPath: '复制路径',
      wsClosePanel: '关闭此面板',
      wsStandby: '待命',
      wsSearching: '搜索中',
      wsAnalyzing: '分析中',
      wsCompleted: '完成',
      wsConfirmNextStep: '确认下一步',
      wsConfirmExecute: '确认执行',
      wsExpandContent: '展开完整内容',
      wsCollapseContent: '收起内容',
      wsCopied: '已复制!',
      wsDefaultThinking: '正在分析任务需求，确定最佳执行策略...',
      
      // Cloud Services
      cloudServices: '云服务',
      home: '主页',
      services: '服务',
      deploy: '部署',
      online: '在线',
      offline: '离线',
      servicesRunning: '服务运行中',
      cpuUsage: 'CPU 使用率',
      memoryUsage: '内存使用',
      storageUsage: '存储使用',
      serviceManagement: '服务管理',
      mainWebService: '主 Web 服务',
      reverseProxy: '反向代理 & 负载均衡',
      vectorDatabase: '向量数据库',
      port: '端口',
      uptime: '运行时间',
      requests: '请求/分',
      security: '安全',
      vectors: '向量数',
      restart: '重启',
      logs: '日志',
      oneClickDeploy: '一键部署',
      dockerDeploy: 'Docker 本地部署',
      dockerDeployDesc: '适合本地开发和测试环境',
      dockerFeature1: '一键启动所有服务',
      dockerFeature2: '自动配置网络和卷',
      dockerFeature3: '支持热重载开发',
      dockerFeature4: '集成健康检查',
      cloudDeploy: '云服务器部署',
      cloudDeployDesc: '支持 AWS / Azure / GCP / 阿里云',
      cloudFeature1: '自动配置 SSL 证书',
      cloudFeature2: 'Nginx 反向代理',
      cloudFeature3: '自动扩缩容支持',
      cloudFeature4: '监控告警集成',
      startDeploy: '开始部署',
      configureDeploy: '配置部署',
      realTimeLogs: '实时日志',
      cloudDeployConfig: '云部署配置',
      cloudProvider: '云服务提供商',
      serverIP: '服务器 IP / 域名',
      sshKey: 'SSH 密钥 / 密码',
      domainName: '域名 (可选)',
      enableSSL: '启用 SSL',
      yesAutoLetsEncrypt: '是 - 自动申请 Let\'s Encrypt 证书',
      yesCustomCert: '是 - 使用自定义证书',
      noSSL: '否 - 仅 HTTP',
      
      // Token Usage
      tokenUsage: 'Token 使用统计',
      promptTokens: 'Prompt Tokens',
      completionTokens: 'Completion Tokens',
      cacheHits: '缓存命中',
      tokensSaved: '节省 Tokens',
      estimatedSavings: '预估节省',
      refresh: '刷新',
      reset: '重置',
      clearCache: '清除缓存',
      healthCheck: '健康检查',
      reconnect: '重连',
      mode: '模式',
    },
    
    en: {
      // Header
      taskCenter: 'Task Center',
      taskDetails: 'Task Details',
      
      // Sidebar
      newTask: 'New Task',
      inProgress: 'In Progress',
      completed: 'Completed',
      settings: 'Settings',
      noActiveTasks: 'No active tasks',
      noCompletedTasks: 'No completed tasks',
      
      // Welcome
      heroSubtitle: 'Intelligent Multi-Agent System - Auto Planning, Decomposition, and Execution',
      quickStart: 'Quick Start',
      templateResearch: 'Research',
      templateResearchDesc: 'Search, organize, summarize web info',
      templateCode: 'Code Generation',
      templateCodeDesc: 'Write, debug, optimize code',
      templateData: 'Data Analysis',
      templateDataDesc: 'Process, analyze, visualize data',
      templateFile: 'File Processing',
      templateFileDesc: 'Read, convert, manage files',
      
      // Stats
      totalTasks: 'Total Tasks',
      completedTasks: 'Completed',
      executionSteps: 'Steps',
      availableAgents: 'Agents',
      
      // Task View
      pending: 'Pending',
      executing: 'Executing',
      running: 'Running',
      taskCompleted: 'Completed',
      taskFailed: 'Failed',
      failed: 'Failed',
      taskCancelled: 'Cancelled',
      cancelled: 'Cancelled',
      overallProgress: 'Overall Progress',
      stepsCompleted: 'Completed',
      stepsRunning: 'Running',
      stepsPending: 'Pending',
      executionFlow: 'Execution Flow',
      liveOutput: 'Live Output',
      finalResult: 'Final Result',
      system: 'System',
      waitingStart: 'Waiting for task to start...',
      
      // Right Panel
      taskProgress: 'Task Progress',
      currentStep: 'Current Step',
      taskSteps: 'Task Steps',
      noStepsYet: 'No steps yet',
      waiting: 'Waiting',
      selectTaskToView: 'Select a task to view details',
      idle: 'Idle',
      active: 'Active',
      executionCount: 'Executions',
      
      // Input
      inputPlaceholder: 'Enter task description, press Enter to execute...',
      
      // New Task Modal
      createNewTask: 'Create New Task',
      taskDescription: 'Task Description',
      taskDescPlaceholder: 'Describe your task in detail...\n\nExample: Search for the latest AI trends and create a report',
      priority: 'Priority',
      priorityUrgent: '🔴 Urgent',
      priorityNormal: '🟡 Normal',
      priorityLow: '🟢 Low',
      executionMode: 'Execution Mode',
      modeAuto: '🤖 Auto Planning',
      modeStep: '👣 Step by Step',
      specifyAgents: 'Specify Agents (Optional)',
      attachments: 'Attachments (Optional)',
      dragFiles: 'Drag files here, or',
      clickUpload: 'click to upload',
      cancel: 'Cancel',
      startExecution: 'Start Execution',
      
      // Settings Modal
      systemSettings: 'System Settings',
      apiStatus: 'API Status',
      connectionStatus: 'Connection',
      currentModel: 'Current Model',
      apiKeyStatus: 'API Key',
      checking: 'Checking...',
      connected: 'Connected',
      disconnected: 'Disconnected',
      configured: 'Configured',
      notConfigured: 'Not Configured',
      refreshStatus: 'Refresh Status',
      displaySettings: 'Display Settings',
      autoRetry: 'Auto Retry Failed Steps',
      maxParallelTasks: 'Max Parallel Tasks',
      close: 'Close',
      saveSettings: 'Save Settings',
      reloadConfig: 'Reload Config',
      apiConfiguredOnServer: 'API is configured on the server',
      
      // Model Management
      modelManagement: 'Model Management',
      addModel: 'Add Model',
      editModel: 'Edit Model',
      modelId: 'Model ID',
      modelIdHint: 'Enter model ID, provider will be auto-detected',
      apiKey: 'API Key',
      apiKeyHint: 'API Key will be securely stored on server',
      apiBaseUrl: 'API Base URL (Optional)',
      apiBaseUrlHint: 'Leave empty to use default',
      modelName: 'Model Name (Optional)',
      provider: 'Provider',
      enabled: 'Enabled',
      setAsDefault: 'Set as Default',
      save: 'Save',
      default: 'Default',
      restart: 'Restart Server',
      
      // Actions
      pause: 'Pause',
      stop: 'Stop',
      resume: 'Resume',
      clear: 'Clear',
      copy: 'Copy',
      deleteTask: 'Delete Task',
      
      // Notifications
      settingsSaved: 'Settings saved',
      taskCreated: 'Task created',
      taskCancelled: 'Task cancelled',
      taskDeleted: 'Task deleted',
      copiedToClipboard: 'Copied to clipboard',
      outputCleared: 'Output cleared',
      apiConnected: 'API connected',
      apiError: 'API connection failed',
      pleaseInputTask: 'Please enter task description',
      
      // Step descriptions
      searchInfo: 'Search related information',
      generateCode: 'Generate code implementation',
      fileOperation: 'Execute file operation',
      processData: 'Process and analyze data',
      analyzeImage: 'Analyze image content',
      analyzeResult: 'Analyze and summarize results',
      stepCompleted: 'Step completed',
      
      // Agent names
      browserAgent: 'Browser Agent',
      llmAgent: 'LLM Agent',
      osAgent: 'OS Agent',
      codeAgent: 'Code Agent',
      dataAgent: 'Data Agent',
      visionAgent: 'Vision Agent',
      executionCount: 'Executions',
      
      // Time
      justNow: 'Just now',
      minutesAgo: ' min ago',
      hoursAgo: ' hours ago',
      steps: 'steps',
      
      // Task execution
      taskStarting: 'Starting task execution...',
      taskAnalyzing: 'Analyzing task...',
      taskDecomposed: 'Task decomposed into',
      stepsText: 'steps',
      taskCompleteSuccess: 'Task completed successfully!',
      executionFailed: 'Execution failed',
      
      // Feature navigation
      workspace: 'Workspace',
      knowledgeBase: 'Knowledge Base',
      workflows: 'Workflows',
      statistics: 'Statistics',
      schedules: 'Schedules',
      
      // Knowledge Base
      documents: 'Documents',
      collections: 'Collections',
      uploadDocument: 'Upload Document',
      noDocuments: 'No documents yet, click to upload',
      addCollection: 'Add Collection',
      selectFile: 'Select File',
      dropFileHere: 'Drop file here or click to select',
      collection: 'Collection',
      tags: 'Tags (comma separated)',
      upload: 'Upload',
      loading: 'Loading...',
      
      // Workflows
      workflowTemplates: 'Workflow Templates',
      
      // Statistics
      usageStatistics: 'Usage Statistics',
      successRate: 'Success Rate',
      totalTokens: 'Tokens',
      estimatedCost: 'Est. Cost',
      statsChartPlaceholder: 'Charts will be displayed here',
      exportJSON: 'Export JSON',
      exportMarkdown: 'Export Markdown',
      
      // Schedules
      scheduledTasks: 'Scheduled Tasks',
      addSchedule: 'Add Schedule',
      noSchedules: 'No scheduled tasks',
      
      // Task Templates
      templates: 'Templates',
      taskTemplates: 'Task Templates',
      builtinTemplates: 'Built-in Templates',
      customTemplates: 'Custom Templates',
      useTemplate: 'Use Template',
      noTemplates: 'No templates',
      templateVariables: 'Template Variables',
      outputFormat: 'Output Format',
      
      // Export Formats
      exportAs: 'Export as...',
      exportMarkdown: 'Markdown (.md)',
      exportHtml: 'HTML (.html)',
      exportJson: 'JSON (.json)',
      exportExcel: 'Excel (.xlsx)',
      exportPpt: 'PowerPoint (.pptx)',
      exportPdf: 'PDF (.pdf)',
      enterpriseFeature: 'Enterprise',
      exporting: 'Exporting...',
      exportSuccess: 'Export successful',
      exportFailed: 'Export failed',
      
      // Workspace
      wsInputPlaceholder: 'Enter command... (Press Enter to execute)',
      wsHistory: 'History',
      wsSettings: 'Settings',
      wsBackHome: 'Back to Home',
      wsExecutionFlow: 'Execution Flow',
      wsTaskList: 'Task List',
      wsHistoryTasks: 'Task History',
      wsClear: 'Clear',
      wsWaitingTask: 'Waiting for task...',
      wsSteps: 'steps',
      wsEnterTaskToStart: 'Enter task to start',
      wsAgentVision: 'Agent Vision',
      wsEnterCommandToStart: 'Enter command to start execution',
      wsPause: 'Pause',
      wsStartExecution: 'Start Execution',
      wsStop: 'Stop',
      wsViewResult: 'View Result',
      wsRerun: 'Re-run',
      wsAgentConsole: 'Agent Console',
      wsAgentThinking: 'Agent Thinking',
      wsExecutionLogs: 'Execution Logs',
      wsFilterAll: 'All',
      wsFilterAction: 'Actions',
      wsFilterError: 'Errors',
      wsDuration: 'Duration',
      wsStepsCount: 'Steps',
      wsTaskSuccess: '🎉 Task Completed Successfully!',
      wsSelectAction: 'Select an action to view results',
      wsOpenFile: 'Open File',
      wsCopyPath: 'Copy Path',
      wsClosePanel: 'Close this panel',
      wsStandby: 'Standby',
      wsSearching: 'Searching',
      wsAnalyzing: 'Analyzing',
      wsCompleted: 'Done',
      wsConfirmNextStep: 'Confirm Next Step',
      wsConfirmExecute: 'Confirm Execute',
      wsExpandContent: 'Expand Full Content',
      wsCollapseContent: 'Collapse Content',
      wsCopied: 'Copied!',
      wsDefaultThinking: 'Analyzing task requirements, determining optimal strategy...',
      
      // Cloud Services
      cloudServices: 'Cloud Services',
      home: 'Home',
      services: 'Services',
      deploy: 'Deploy',
      online: 'Online',
      offline: 'Offline',
      servicesRunning: 'Services Running',
      cpuUsage: 'CPU Usage',
      memoryUsage: 'Memory Usage',
      storageUsage: 'Storage Usage',
      serviceManagement: 'Service Management',
      mainWebService: 'Main Web Service',
      reverseProxy: 'Reverse Proxy & Load Balancer',
      vectorDatabase: 'Vector Database',
      port: 'Port',
      uptime: 'Uptime',
      requests: 'Req/min',
      security: 'Security',
      vectors: 'Vectors',
      restart: 'Restart',
      logs: 'Logs',
      oneClickDeploy: 'One-Click Deploy',
      dockerDeploy: 'Docker Local Deploy',
      dockerDeployDesc: 'For local development and testing',
      dockerFeature1: 'One-click start all services',
      dockerFeature2: 'Auto configure networks and volumes',
      dockerFeature3: 'Hot reload support',
      dockerFeature4: 'Integrated health checks',
      cloudDeploy: 'Cloud Server Deploy',
      cloudDeployDesc: 'Support AWS / Azure / GCP / Alibaba Cloud',
      cloudFeature1: 'Auto SSL certificate setup',
      cloudFeature2: 'Nginx reverse proxy',
      cloudFeature3: 'Auto-scaling support',
      cloudFeature4: 'Monitoring & alerts',
      startDeploy: 'Start Deploy',
      configureDeploy: 'Configure Deploy',
      realTimeLogs: 'Real-time Logs',
      cloudDeployConfig: 'Cloud Deploy Configuration',
      cloudProvider: 'Cloud Provider',
      serverIP: 'Server IP / Domain',
      sshKey: 'SSH Key / Password',
      domainName: 'Domain (Optional)',
      enableSSL: 'Enable SSL',
      yesAutoLetsEncrypt: 'Yes - Auto Let\'s Encrypt',
      yesCustomCert: 'Yes - Custom Certificate',
      noSSL: 'No - HTTP Only',
      
      // Token Usage
      tokenUsage: 'Token Usage Statistics',
      promptTokens: 'Prompt Tokens',
      completionTokens: 'Completion Tokens',
      cacheHits: 'Cache Hits',
      tokensSaved: 'Tokens Saved',
      estimatedSavings: 'Est. Savings',
      refresh: 'Refresh',
      reset: 'Reset',
      clearCache: 'Clear Cache',
      healthCheck: 'Health Check',
      reconnect: 'Reconnect',
      mode: 'Mode',
    }
  },
  
  /**
   * Initialize i18n
   */
  init() {
    // Load saved language preference
    const savedLang = localStorage.getItem('joinflow_lang') || 'zh';
    this.setLanguage(savedLang, false);
  },
  
  /**
   * Get translation for key
   */
  t(key) {
    return this.translations[this.currentLang][key] || key;
  },
  
  /**
   * Set language
   */
  setLanguage(lang, save = true) {
    if (!this.translations[lang]) {
      console.warn(`Language ${lang} not supported`);
      return;
    }
    
    this.currentLang = lang;
    document.documentElement.setAttribute('data-lang', lang);
    
    if (save) {
      localStorage.setItem('joinflow_lang', lang);
    }
    
    // Update all elements with data-i18n attribute
    this.updatePageText();
    
    // Update language toggle button
    const langLabel = document.getElementById('langLabel');
    if (langLabel) {
      langLabel.textContent = lang === 'zh' ? '中' : 'EN';
    }
  },
  
  /**
   * Toggle between languages
   */
  toggle() {
    const newLang = this.currentLang === 'zh' ? 'en' : 'zh';
    this.setLanguage(newLang);
  },
  
  /**
   * Update all page text based on current language
   */
  updatePageText() {
    // Update elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (this.translations[this.currentLang][key]) {
        el.textContent = this.translations[this.currentLang][key];
      }
    });
    
    // Update elements with data-i18n-placeholder attribute
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (this.translations[this.currentLang][key]) {
        el.placeholder = this.translations[this.currentLang][key];
      }
    });
    
    // Update elements with data-i18n-title attribute
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      if (this.translations[this.currentLang][key]) {
        el.title = this.translations[this.currentLang][key];
      }
    });
    
    // Update page title
    document.title = `JoinFlow - ${this.t('taskCenter')}`;
    
    // Update dynamic content if app is loaded
    if (typeof updateDynamicI18n === 'function') {
      updateDynamicI18n();
    }
  },
  
  /**
   * Get localized agent name
   */
  getAgentName(agent) {
    const agentMap = {
      browser: this.currentLang === 'zh' ? '浏览器' : 'Browser',
      llm: this.currentLang === 'zh' ? '大模型' : 'LLM',
      os: this.currentLang === 'zh' ? '系统' : 'OS',
      code: this.currentLang === 'zh' ? '代码' : 'Code',
      data: this.currentLang === 'zh' ? '数据' : 'Data',
      vision: this.currentLang === 'zh' ? '视觉' : 'Vision'
    };
    return agentMap[agent] || agent;
  },
  
  /**
   * Get localized status text
   */
  getStatusText(status) {
    const statusMap = {
      pending: this.t('pending'),
      running: this.t('running'),
      completed: this.t('taskCompleted'),
      failed: this.t('failed'),
      cancelled: this.t('cancelled')
    };
    return statusMap[status] || status;
  }
};

// Initialize i18n on load
document.addEventListener('DOMContentLoaded', () => {
  i18n.init();
});

// Global function for toggle button
function toggleLanguage() {
  i18n.toggle();
}

