/**
 * JoinFlow Features Module
 * =======================
 * 
 * Handles extended features:
 * - Knowledge Base Management
 * - Workflow Templates
 * - Statistics & Analytics
 * - Scheduled Tasks
 * - Webhooks
 * - Export
 */

// ============================================
// Workspace - 工作台
// ============================================

/**
 * 打开工作台（新标签页）
 */
function openWorkspace() {
  // 在新标签页打开工作台
  window.open('/workspace', '_blank');
}

/**
 * 创建任务并在工作台打开
 * @param {string} description - 任务描述
 * @param {object} options - 选项 { mode: 'auto' | 'step-by-step' }
 */
function createTaskAndOpenWorkspace(description, options = {}) {
  if (window.taskStore) {
    const task = window.taskStore.createTask(description, {
      ...options,
      mode: options.mode || 'auto'  // 'auto' 或 'step-by-step'
    });
    
    // 在新标签页打开工作台
    window.open('/workspace', '_blank');
  }
}

// ============================================
// Knowledge Base
// ============================================

let kbCurrentTab = 'documents';

async function showKnowledgeBase() {
  openModal('knowledgeBaseModal');
  await loadKBContent();
}

async function loadKBContent() {
  const content = document.getElementById('kbContent');
  content.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i></div>';
  
  try {
    if (kbCurrentTab === 'documents') {
      await loadDocuments();
    } else {
      await loadCollections();
    }
  } catch (error) {
    content.innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i> ${error.message}</div>`;
  }
}

function switchKBTab(tab) {
  kbCurrentTab = tab;
  document.querySelectorAll('.kb-tabs .tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.includes(tab === 'documents' ? '文档' : '集合'));
  });
  loadKBContent();
}

async function loadDocuments() {
  const response = await fetch('/api/knowledge/documents');
  const data = await response.json();
  
  const content = document.getElementById('kbContent');
  
  if (!data.documents || data.documents.length === 0) {
    content.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-file-alt"></i>
        <p data-i18n="noDocuments">暂无文档，点击上方按钮上传</p>
      </div>
    `;
    return;
  }
  
  content.innerHTML = `
    <div class="document-list">
      ${data.documents.map(doc => `
        <div class="document-item ${doc.status}" data-id="${doc.id}">
          <div class="doc-icon ${doc.doc_type}">
            <i class="fas ${getDocIcon(doc.doc_type)}"></i>
          </div>
          <div class="doc-info">
            <div class="doc-name">${escapeHtml(doc.name || doc.original_filename)}</div>
            <div class="doc-meta">
              <span class="doc-collection">${doc.collection}</span>
              <span class="doc-size">${formatFileSize(doc.file_size)}</span>
              <span class="doc-status ${doc.status}">${getStatusText(doc.status)}</span>
            </div>
          </div>
          <div class="doc-actions">
            <button class="icon-btn small danger" onclick="deleteDocument('${doc.id}')" title="删除">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

async function loadCollections() {
  const response = await fetch('/api/knowledge-base/collections');
  const data = await response.json();
  
  const content = document.getElementById('kbContent');
  
  content.innerHTML = `
    <div class="collection-grid">
      ${(data.collections || []).map(col => `
        <div class="collection-card" data-id="${col.id}">
          <div class="collection-icon">
            <i class="fas fa-folder"></i>
          </div>
          <div class="collection-info">
            <div class="collection-name">${escapeHtml(col.name)}</div>
            <div class="collection-desc">${escapeHtml(col.description || '')}</div>
            <div class="collection-stats">
              <span><i class="fas fa-file"></i> ${col.document_count || 0} 文档</span>
              <span><i class="fas fa-cube"></i> ${col.chunk_count || 0} 块</span>
            </div>
          </div>
        </div>
      `).join('')}
      <div class="collection-card add-new" onclick="showAddCollection()">
        <div class="collection-icon"><i class="fas fa-plus"></i></div>
        <div class="collection-info">
          <div class="collection-name" data-i18n="addCollection">添加集合</div>
        </div>
      </div>
    </div>
  `;
}

function getDocIcon(docType) {
  const icons = {
    'text': 'fa-file-alt',
    'pdf': 'fa-file-pdf',
    'markdown': 'fa-file-code',
    'html': 'fa-file-code',
    'code': 'fa-file-code',
    'docx': 'fa-file-word',
    'xlsx': 'fa-file-excel',
    'csv': 'fa-file-csv',
    'json': 'fa-file-code',
    'image': 'fa-file-image',
  };
  return icons[docType] || 'fa-file';
}

function getStatusText(status) {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'indexed': '已索引',
    'failed': '失败',
    'archived': '已归档',
  };
  return texts[status] || status;
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

function showUploadDocument() {
  closeModal('knowledgeBaseModal');
  loadCollectionsForUpload();
  openModal('uploadDocumentModal');
  setupFileDropZone();
}

async function loadCollectionsForUpload() {
  try {
    const response = await fetch('/api/knowledge-base/collections');
    const data = await response.json();
    
    const select = document.getElementById('uploadCollection');
    select.innerHTML = (data.collections || []).map(col => 
      `<option value="${col.name}">${col.name}</option>`
    ).join('') || '<option value="default">default</option>';
  } catch (error) {
    console.error('Failed to load collections:', error);
  }
}

function setupFileDropZone() {
  const dropZone = document.getElementById('fileDropZone');
  const fileInput = document.getElementById('documentFileInput');
  
  dropZone.onclick = () => fileInput.click();
  
  dropZone.ondragover = (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  };
  
  dropZone.ondragleave = () => {
    dropZone.classList.remove('dragover');
  };
  
  dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };
  
  fileInput.onchange = () => {
    if (fileInput.files.length > 0) {
      handleFileSelect(fileInput.files[0]);
    }
  };
}

function handleFileSelect(file) {
  const selectedFile = document.getElementById('selectedFile');
  selectedFile.innerHTML = `
    <div class="file-preview">
      <i class="fas ${getDocIcon(file.name.split('.').pop())}"></i>
      <span>${escapeHtml(file.name)}</span>
      <span class="file-size">(${formatFileSize(file.size)})</span>
    </div>
  `;
  document.getElementById('uploadBtn').disabled = false;
}

async function uploadDocument() {
  const fileInput = document.getElementById('documentFileInput');
  const file = fileInput.files[0];
  if (!file) return;
  
  const uploadBtn = document.getElementById('uploadBtn');
  uploadBtn.disabled = true;
  uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 上传中...';
  
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection', document.getElementById('uploadCollection').value);
    formData.append('tags', document.getElementById('uploadTags').value);
    
    const response = await fetch('/api/knowledge/upload', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.success) {
      showNotification('文档上传成功', 'success');
      closeModal('uploadDocumentModal');
      showKnowledgeBase();
    } else {
      throw new Error(data.error || '上传失败');
    }
  } catch (error) {
    showNotification('上传失败: ' + error.message, 'error');
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = '<i class="fas fa-upload"></i> <span data-i18n="upload">上传</span>';
  }
}

async function deleteDocument(docId) {
  if (!confirm('确定要删除这个文档吗？')) return;
  
  try {
    const response = await fetch(`/api/knowledge/documents/${docId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      showNotification('文档已删除', 'success');
      loadKBContent();
    } else {
      throw new Error('删除失败');
    }
  } catch (error) {
    showNotification('删除失败: ' + error.message, 'error');
  }
}

// ============================================
// Workflow Templates
// ============================================

async function showWorkflows() {
  openModal('workflowsModal');
  await loadWorkflows();
}

async function loadWorkflows() {
  const grid = document.getElementById('workflowGrid');
  grid.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i></div>';
  
  try {
    const response = await fetch('/api/workflows');
    const data = await response.json();
    
    const workflows = data.workflows || [];
    
    // 创建新模板卡片
    let html = `
      <div class="workflow-card add-new" onclick="showCreateWorkflow()">
        <div class="workflow-icon add" style="background: var(--bg-tertiary); color: var(--text-muted)">
          <i class="fas fa-plus"></i>
        </div>
        <div class="workflow-info">
          <div class="workflow-name">创建自定义工作流</div>
          <div class="workflow-desc">创建你自己的工作流模板</div>
        </div>
      </div>
    `;
    
    // 工作流卡片
    html += workflows.map(wf => {
      const categoryNames = {
        'research': '研究',
        'code': '代码',
        'data': '数据',
        'file': '文件',
        'automation': '自动化',
        'custom': '自定义'
      };
      
      return `
        <div class="workflow-card ${wf.is_system ? 'system' : ''}" data-id="${wf.id}" style="--wf-color: ${wf.color || '#58a6ff'}">
          <div class="workflow-icon" style="background: ${wf.color || '#58a6ff'}20; color: ${wf.color || '#58a6ff'}">
            <i class="${wf.icon || 'fas fa-project-diagram'}"></i>
          </div>
          <div class="workflow-info">
            <div class="workflow-name">${escapeHtml(wf.name)}</div>
            <div class="workflow-desc">${escapeHtml(wf.description)}</div>
            <div class="workflow-meta">
              <span class="workflow-category">${categoryNames[wf.category] || wf.category}</span>
              ${wf.is_system ? '<span class="system-badge">系统</span>' : '<span class="custom-badge">自定义</span>'}
              <span class="use-count"><i class="fas fa-play"></i> ${wf.use_count || 0}</span>
            </div>
            ${wf.tags && wf.tags.length > 0 ? `
              <div class="workflow-tags">
                ${wf.tags.slice(0, 3).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
              </div>
            ` : ''}
          </div>
          <div class="workflow-actions">
            <button class="btn primary small" onclick="executeWorkflow('${wf.id}')">
              <i class="fas fa-play"></i> 执行
            </button>
            ${!wf.is_system ? `
              <button class="btn secondary small" onclick="deleteWorkflow('${wf.id}')" title="删除">
                <i class="fas fa-trash"></i>
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
    
    grid.innerHTML = html;
  } catch (error) {
    grid.innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i> ${error.message}</div>`;
  }
}

function showCreateWorkflow() {
  // 重置表单
  document.getElementById('newWorkflowName').value = '';
  document.getElementById('newWorkflowDesc').value = '';
  document.getElementById('newWorkflowTemplate').value = '';
  document.getElementById('newWorkflowIcon').value = 'fas fa-cog';
  document.getElementById('newWorkflowColor').value = '#8b5cf6';
  document.getElementById('colorPreview').textContent = '#8b5cf6';
  document.getElementById('newWorkflowTags').value = '';
  
  // 添加颜色选择器事件
  const colorInput = document.getElementById('newWorkflowColor');
  colorInput.oninput = function() {
    document.getElementById('colorPreview').textContent = this.value;
  };
  
  closeModal('workflowsModal');
  openModal('createWorkflowModal');
  
  // 聚焦到名称输入框
  setTimeout(() => document.getElementById('newWorkflowName').focus(), 100);
}

async function submitCreateWorkflow() {
  const name = document.getElementById('newWorkflowName').value.trim();
  const description = document.getElementById('newWorkflowDesc').value.trim();
  const template = document.getElementById('newWorkflowTemplate').value.trim();
  const icon = document.getElementById('newWorkflowIcon').value;
  const color = document.getElementById('newWorkflowColor').value;
  const tagsStr = document.getElementById('newWorkflowTags').value.trim();
  
  // 验证
  if (!name) {
    showNotification('请输入工作流名称', 'error');
    document.getElementById('newWorkflowName').focus();
    return;
  }
  
  if (!template) {
    showNotification('请输入任务模板', 'error');
    document.getElementById('newWorkflowTemplate').focus();
    return;
  }
  
  const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : ['自定义'];
  
  try {
    const response = await fetch('/api/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        description: description || '',
        icon: icon,
        color: color,
        tags: tags,
        steps: [{
          id: 'main',
          name: '执行任务',
          description: template,
          agent: 'llm',
          prompt_template: template
        }],
        input_schema: {
          type: 'object',
          properties: extractVariablesWithDescriptions(template),
          required: Object.keys(extractVariables(template))
        }
      })
    });
    
    const data = await response.json();
    if (data.success) {
      showNotification('工作流创建成功！', 'success');
      closeModal('createWorkflowModal');
      openModal('workflowsModal');
      loadWorkflows();
    } else {
      throw new Error(data.error || '创建失败');
    }
  } catch (error) {
    showNotification('创建失败: ' + error.message, 'error');
  }
}

function extractVariablesWithDescriptions(template) {
  const regex = /\{(\w+)\}/g;
  const variables = {};
  let match;
  while ((match = regex.exec(template)) !== null) {
    const varName = match[1];
    variables[varName] = {
      type: 'string',
      description: formatFieldName(varName),
      // 根据变量名猜测是否需要多行输入
      multiline: ['code', 'content', 'text', 'description', 'body'].some(k => varName.toLowerCase().includes(k))
    };
  }
  return variables;
}

async function createCustomWorkflow(name, description, taskTemplate) {
  try {
    const response = await fetch('/api/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        description: description || '',
        icon: 'fas fa-cog',
        color: '#8b5cf6',
        tags: ['自定义'],
        steps: [{
          id: 'main',
          name: '执行任务',
          description: taskTemplate,
          agent: 'llm',
          prompt_template: taskTemplate
        }],
        input_schema: {
          type: 'object',
          properties: extractVariables(taskTemplate),
          required: Object.keys(extractVariables(taskTemplate))
        }
      })
    });
    
    const data = await response.json();
    if (data.success) {
      showNotification('工作流创建成功', 'success');
      loadWorkflows();
    } else {
      throw new Error(data.error || '创建失败');
    }
  } catch (error) {
    showNotification('创建失败: ' + error.message, 'error');
  }
}

function extractVariables(template) {
  const regex = /\{(\w+)\}/g;
  const variables = {};
  let match;
  while ((match = regex.exec(template)) !== null) {
    variables[match[1]] = {
      type: 'string',
      description: match[1]
    };
  }
  return variables;
}

async function deleteWorkflow(workflowId) {
  if (!confirm('确定要删除这个工作流吗？')) return;
  
  try {
    const response = await fetch(`/api/workflows/${workflowId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      showNotification('工作流已删除', 'success');
      loadWorkflows();
    } else {
      const data = await response.json();
      throw new Error(data.detail || '删除失败');
    }
  } catch (error) {
    showNotification('删除失败: ' + error.message, 'error');
  }
}

// 当前执行的工作流信息
let currentExecuteWorkflow = null;

async function executeWorkflow(workflowId) {
  try {
    const response = await fetch(`/api/workflows/${workflowId}`);
    const data = await response.json();
    
    if (!data.workflow) {
      throw new Error('工作流不存在');
    }
    
    const workflow = data.workflow;
    currentExecuteWorkflow = workflow;
    
    // 设置模态框头部信息
    const iconEl = document.getElementById('executeWorkflowIcon');
    iconEl.innerHTML = `<i class="${workflow.icon || 'fas fa-project-diagram'}"></i>`;
    iconEl.style.background = `${workflow.color || '#58a6ff'}20`;
    iconEl.style.color = workflow.color || '#58a6ff';
    
    document.getElementById('executeWorkflowName').textContent = workflow.name;
    document.getElementById('executeWorkflowDesc').textContent = workflow.description || '请填写以下参数以执行此工作流';
    
    // 生成输入表单
    const container = document.getElementById('workflowInputsContainer');
    
    if (workflow.input_schema && workflow.input_schema.properties && Object.keys(workflow.input_schema.properties).length > 0) {
      const properties = workflow.input_schema.properties;
      const required = workflow.input_schema.required || [];
      
      let html = `
        <div class="workflow-var-info">
          <i class="fas fa-info-circle"></i>
          <div class="workflow-var-info-text">
            <strong>填写参数</strong> - 请输入工作流所需的参数值，这些值将用于生成任务描述。
          </div>
        </div>
      `;
      
      html += Object.entries(properties).map(([key, prop]) => {
        const isRequired = required.includes(key);
        const inputType = getInputType(prop);
        const fieldIcon = getFieldIcon(prop);
        const placeholder = prop.default || getPlaceholder(key, prop);
        
        return `
          <div class="workflow-input-field">
            <label>
              ${fieldIcon ? `<i class="${fieldIcon}"></i>` : ''}
              ${escapeHtml(prop.description || formatFieldName(key))}
              ${isRequired ? '<span class="required-mark">*</span>' : ''}
              <span class="input-type-tag ${prop.type || 'string'}">${getTypeLabel(prop)}</span>
            </label>
            ${prop.hint ? `<div class="input-hint">${escapeHtml(prop.hint)}</div>` : ''}
            ${renderInputField(key, prop, inputType, placeholder, isRequired)}
          </div>
        `;
      }).join('');
      
      container.innerHTML = html;
      
      // 添加字符计数器功能
      container.querySelectorAll('textarea').forEach(textarea => {
        updateCharCounter(textarea);
        textarea.addEventListener('input', () => updateCharCounter(textarea));
      });
      
      // 聚焦第一个输入框
      const firstInput = container.querySelector('input, textarea');
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
      }
    } else {
      container.innerHTML = `
        <div class="workflow-inputs-empty">
          <i class="fas fa-check-circle"></i>
          <p>此工作流无需额外参数，点击下方按钮直接执行。</p>
        </div>
      `;
    }
    
    // 关闭工作流列表模态框，打开执行模态框
    closeModal('workflowsModal');
    openModal('workflowExecuteModal');
    
  } catch (error) {
    showNotification('执行失败: ' + error.message, 'error');
  }
}

function getInputType(prop) {
  if (prop.format === 'code' || prop.multiline) return 'textarea';
  if (prop.type === 'number' || prop.type === 'integer') return 'number';
  if (prop.type === 'boolean') return 'checkbox';
  if (prop.enum) return 'select';
  if (prop.format === 'textarea' || (prop.description && prop.description.includes('描述'))) return 'textarea';
  return 'text';
}

function getFieldIcon(prop) {
  const icons = {
    'code': 'fas fa-code',
    'email': 'fas fa-envelope',
    'url': 'fas fa-link',
    'date': 'fas fa-calendar',
    'number': 'fas fa-hashtag',
    'file': 'fas fa-file',
  };
  if (prop.format && icons[prop.format]) return icons[prop.format];
  if (prop.type === 'number' || prop.type === 'integer') return 'fas fa-hashtag';
  return null;
}

function getPlaceholder(key, prop) {
  const placeholders = {
    'query': '输入您的查询内容...',
    'topic': '输入研究主题...',
    'url': 'https://example.com',
    'code': '// 输入代码或代码需求...',
    'requirement': '描述您的需求...',
    'description': '请详细描述...',
    'input': '输入内容...',
    'data': '输入数据...',
    'file_path': '/path/to/file',
    'n': '输入数字...',
  };
  return placeholders[key.toLowerCase()] || `输入${formatFieldName(key)}...`;
}

function formatFieldName(key) {
  // 将 snake_case 或 camelCase 转换为可读格式
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
}

function getTypeLabel(prop) {
  const labels = {
    'string': '文本',
    'number': '数字',
    'integer': '整数',
    'boolean': '布尔',
    'array': '数组',
    'object': '对象',
  };
  if (prop.format === 'code') return '代码';
  return labels[prop.type] || '文本';
}

function renderInputField(key, prop, inputType, placeholder, isRequired) {
  const requiredAttr = isRequired ? 'required' : '';
  const dataKey = `data-key="${key}"`;
  
  if (inputType === 'textarea') {
    const isCode = prop.format === 'code';
    return `
      <div class="workflow-input-wrapper" style="position: relative;">
        <textarea 
          ${dataKey}
          ${requiredAttr}
          class="workflow-field ${isCode ? 'code-input' : ''}"
          placeholder="${escapeHtml(placeholder)}"
          maxlength="${prop.maxLength || 2000}"
        >${escapeHtml(prop.default || '')}</textarea>
        <span class="input-counter">0 / ${prop.maxLength || 2000}</span>
      </div>
    `;
  }
  
  if (inputType === 'select') {
    return `
      <select ${dataKey} ${requiredAttr} class="workflow-field">
        ${prop.enum.map(opt => `<option value="${escapeHtml(opt)}">${escapeHtml(opt)}</option>`).join('')}
      </select>
    `;
  }
  
  if (inputType === 'number') {
    return `
      <div class="workflow-input-wrapper">
        <input 
          type="number"
          ${dataKey}
          ${requiredAttr}
          class="workflow-field"
          placeholder="${escapeHtml(placeholder)}"
          value="${prop.default || ''}"
          ${prop.minimum !== undefined ? `min="${prop.minimum}"` : ''}
          ${prop.maximum !== undefined ? `max="${prop.maximum}"` : ''}
        />
        <i class="input-icon fas fa-hashtag"></i>
      </div>
    `;
  }
  
  if (inputType === 'checkbox') {
    return `
      <label class="toggle">
        <input type="checkbox" ${dataKey} ${requiredAttr} class="workflow-field" ${prop.default ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
    `;
  }
  
  // Default text input
  return `
    <div class="workflow-input-wrapper">
      <input 
        type="text"
        ${dataKey}
        ${requiredAttr}
        class="workflow-field"
        placeholder="${escapeHtml(placeholder)}"
        value="${escapeHtml(prop.default || '')}"
        ${prop.maxLength ? `maxlength="${prop.maxLength}"` : ''}
      />
      ${getFieldIcon(prop) ? `<i class="input-icon ${getFieldIcon(prop)}"></i>` : ''}
    </div>
  `;
}

function updateCharCounter(textarea) {
  const counter = textarea.parentElement.querySelector('.input-counter');
  if (!counter) return;
  
  const current = textarea.value.length;
  const max = parseInt(textarea.getAttribute('maxlength')) || 2000;
  counter.textContent = `${current} / ${max}`;
  
  counter.classList.remove('warning', 'danger');
  if (current > max * 0.9) {
    counter.classList.add('danger');
  } else if (current > max * 0.7) {
    counter.classList.add('warning');
  }
}

async function submitWorkflowExecution() {
  if (!currentExecuteWorkflow) return;
  
  const container = document.getElementById('workflowInputsContainer');
  const inputs = {};
  let isValid = true;
  
  // 收集所有输入值
  container.querySelectorAll('.workflow-field').forEach(field => {
    const key = field.dataset.key;
    if (!key) return;
    
    let value;
    if (field.type === 'checkbox') {
      value = field.checked;
    } else if (field.type === 'number') {
      value = field.value ? parseFloat(field.value) : null;
    } else {
      value = field.value.trim();
    }
    
    inputs[key] = value;
    
    // 验证必填字段
    if (field.hasAttribute('required') && !value && value !== false && value !== 0) {
      isValid = false;
      field.style.borderColor = 'var(--accent-danger)';
      field.addEventListener('input', function handler() {
        field.style.borderColor = '';
        field.removeEventListener('input', handler);
      }, { once: true });
    }
  });
  
  if (!isValid) {
    showNotification('请填写所有必填字段', 'error');
    return;
  }
  
  const executeBtn = document.getElementById('executeWorkflowBtn');
  executeBtn.disabled = true;
  executeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 执行中...';
  
  try {
    const execResponse = await fetch(`/api/workflows/${currentExecuteWorkflow.id}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inputs })
    });
    
    const execData = await execResponse.json();
    
    if (execData.success && execData.task_description) {
      closeModal('workflowExecuteModal');
      document.getElementById('quickInput').value = execData.task_description;
      submitQuickInput();
      showNotification('工作流已启动', 'success');
    } else {
      throw new Error(execData.error || '执行失败');
    }
  } catch (error) {
    showNotification('执行失败: ' + error.message, 'error');
  } finally {
    executeBtn.disabled = false;
    executeBtn.innerHTML = '<i class="fas fa-rocket"></i> <span data-i18n="execute">开始执行</span>';
  }
}

// ============================================
// Statistics
// ============================================

async function showStatistics() {
  openModal('statisticsModal');
  await loadStatistics();
}

async function loadStatistics() {
  try {
    const response = await fetch('/api/statistics/summary?days=30');
    const data = await response.json();
    
    document.getElementById('statsTotalTasks').textContent = data.total_tasks || 0;
    document.getElementById('statsSuccessRate').textContent = (data.success_rate || 0) + '%';
    document.getElementById('statsTotalTokens').textContent = formatNumber(data.total_tokens || 0);
    document.getElementById('statsTotalCost').textContent = '$' + (data.total_cost || 0).toFixed(4);
    
    // Load trend data
    const trendResponse = await fetch('/api/statistics/trend?days=30');
    const trendData = await trendResponse.json();
    
    renderStatisticsChart(trendData.trend || []);
  } catch (error) {
    console.error('Failed to load statistics:', error);
  }
}

function renderStatisticsChart(trend) {
  const container = document.getElementById('statsCharts');
  
  if (!trend || trend.length === 0) {
    container.innerHTML = '<div class="chart-placeholder"><i class="fas fa-chart-bar"></i><p>暂无数据</p></div>';
    return;
  }
  
  // Simple ASCII chart representation
  const maxTasks = Math.max(...trend.map(d => d.tasks), 1);
  
  container.innerHTML = `
    <div class="simple-chart">
      <div class="chart-title">近30天任务趋势</div>
      <div class="chart-bars">
        ${trend.slice(-14).map(d => `
          <div class="chart-bar-container">
            <div class="chart-bar" style="height: ${(d.tasks / maxTasks) * 100}%" title="${d.date}: ${d.tasks} 任务"></div>
            <div class="chart-label">${d.date.slice(-5)}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

async function exportStatistics(format) {
  try {
    const response = await fetch(`/api/statistics/export?days=30&format=${format}`);
    
    if (format === 'markdown') {
      const blob = await response.blob();
      downloadBlob(blob, 'statistics.md');
    } else {
      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      downloadBlob(blob, 'statistics.json');
    }
    
    showNotification('导出成功', 'success');
  } catch (error) {
    showNotification('导出失败: ' + error.message, 'error');
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

// ============================================
// Scheduled Tasks
// ============================================

async function showSchedules() {
  openModal('schedulesModal');
  await loadSchedules();
}

async function loadSchedules() {
  const list = document.getElementById('schedulesList');
  list.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i></div>';
  
  try {
    const response = await fetch('/api/schedules');
    const data = await response.json();
    
    if (!data.schedules || data.schedules.length === 0) {
      list.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-calendar-times"></i>
          <p data-i18n="noSchedules">暂无定时任务</p>
        </div>
      `;
      return;
    }
    
    list.innerHTML = data.schedules.map(schedule => `
      <div class="schedule-item ${schedule.enabled ? '' : 'disabled'}" data-id="${schedule.id}">
        <div class="schedule-info">
          <div class="schedule-name">${escapeHtml(schedule.name)}</div>
          <div class="schedule-meta">
            <span class="schedule-type">${getScheduleTypeText(schedule.schedule_type)}</span>
            <span class="schedule-next">
              <i class="fas fa-clock"></i> 
              ${schedule.next_run ? new Date(schedule.next_run).toLocaleString() : '未调度'}
            </span>
          </div>
        </div>
        <div class="schedule-actions">
          <label class="toggle small">
            <input type="checkbox" ${schedule.enabled ? 'checked' : ''} onchange="toggleSchedule('${schedule.id}', this.checked)">
            <span class="toggle-slider"></span>
          </label>
          <button class="icon-btn small danger" onclick="deleteSchedule('${schedule.id}')" title="删除">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    `).join('');
  } catch (error) {
    list.innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i> ${error.message}</div>`;
  }
}

function getScheduleTypeText(type) {
  const types = {
    'once': '一次性',
    'interval': '固定间隔',
    'cron': 'Cron',
    'daily': '每日',
    'weekly': '每周',
    'monthly': '每月',
  };
  return types[type] || type;
}

function showAddSchedule() {
  // 先关闭定时任务列表模态框
  closeModal('schedulesModal');
  
  // 创建定时任务模态框
  let modal = document.getElementById('addScheduleModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'addScheduleModal';
    modal.className = 'modal-overlay';
    modal.style.zIndex = '10001';  // 确保在最上层
    modal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h2><i class="fas fa-clock"></i> 添加定时任务</h2>
          <button class="modal-close" onclick="closeAddScheduleModal()">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form id="addScheduleForm" onsubmit="submitAddSchedule(event)">
            <div class="form-group">
              <label>任务名称</label>
              <input type="text" id="scheduleName" required placeholder="例如：每日数据备份">
            </div>
            <div class="form-group">
              <label>任务描述</label>
              <textarea id="scheduleDescription" rows="2" placeholder="任务执行的具体内容"></textarea>
            </div>
            <div class="form-group">
              <label>执行频率</label>
              <select id="scheduleType">
                <option value="interval">间隔执行</option>
                <option value="cron">Cron 表达式</option>
                <option value="daily">每天定时</option>
                <option value="weekly">每周定时</option>
              </select>
            </div>
            <div class="form-group" id="intervalGroup">
              <label>执行间隔（分钟）</label>
              <input type="number" id="scheduleInterval" value="60" min="1">
            </div>
            <div class="form-group" id="cronGroup" style="display:none;">
              <label>Cron 表达式</label>
              <input type="text" id="scheduleCron" placeholder="0 0 * * * (每小时)">
              <small style="color: var(--text-muted);">格式: 分 时 日 月 周</small>
            </div>
            <div class="form-group" id="dailyGroup" style="display:none;">
              <label>每天执行时间</label>
              <input type="time" id="scheduleTime" value="09:00">
            </div>
            <div class="form-group">
              <label>关联工作流（可选）</label>
              <select id="scheduleWorkflow">
                <option value="">-- 选择工作流 --</option>
              </select>
            </div>
            <div class="form-actions">
              <button type="button" class="btn secondary" onclick="closeAddScheduleModal()">取消</button>
              <button type="submit" class="btn primary">创建任务</button>
            </div>
          </form>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    
    // 监听执行频率变化
    document.getElementById('scheduleType').addEventListener('change', (e) => {
      document.getElementById('intervalGroup').style.display = e.target.value === 'interval' ? 'block' : 'none';
      document.getElementById('cronGroup').style.display = e.target.value === 'cron' ? 'block' : 'none';
      document.getElementById('dailyGroup').style.display = ['daily', 'weekly'].includes(e.target.value) ? 'block' : 'none';
    });
  }
  
  // 加载工作流列表
  loadWorkflowsForSchedule();
  
  modal.classList.add('active');
}

async function loadWorkflowsForSchedule() {
  try {
    const response = await fetch('/api/workflows');
    const data = await response.json();
    const select = document.getElementById('scheduleWorkflow');
    
    select.innerHTML = '<option value="">-- 选择工作流 --</option>';
    if (data.workflows) {
      data.workflows.forEach(wf => {
        select.innerHTML += `<option value="${wf.id}">${wf.name}</option>`;
      });
    }
  } catch (e) {
    console.error('Failed to load workflows:', e);
  }
}

function closeAddScheduleModal() {
  const modal = document.getElementById('addScheduleModal');
  if (modal) {
    modal.classList.remove('active');
  }
}

async function submitAddSchedule(event) {
  event.preventDefault();
  
  const scheduleType = document.getElementById('scheduleType').value;
  const name = document.getElementById('scheduleName').value;
  const description = document.getElementById('scheduleDescription').value;
  
  let scheduleConfig = { type: scheduleType };
  
  if (scheduleType === 'interval') {
    scheduleConfig.interval_minutes = parseInt(document.getElementById('scheduleInterval').value);
  } else if (scheduleType === 'cron') {
    scheduleConfig.cron = document.getElementById('scheduleCron').value;
  } else if (scheduleType === 'daily' || scheduleType === 'weekly') {
    scheduleConfig.time = document.getElementById('scheduleTime').value;
  }
  
  const workflowId = document.getElementById('scheduleWorkflow').value;
  
  try {
    const response = await fetch('/api/schedules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        description,
        schedule_type: scheduleType,
        schedule_config: scheduleConfig,
        workflow_id: workflowId || null,
        enabled: true
      })
    });
    
    const data = await response.json();
    
    if (data.success || data.schedule) {
      showNotification('定时任务创建成功', 'success');
      closeAddScheduleModal();
      loadSchedules();
    } else {
      throw new Error(data.error || '创建失败');
    }
  } catch (e) {
    console.error('Failed to create schedule:', e);
    showNotification('创建失败: ' + e.message, 'error');
  }
}

// 导出新函数
window.closeAddScheduleModal = closeAddScheduleModal;
window.submitAddSchedule = submitAddSchedule;

async function toggleSchedule(scheduleId, enabled) {
  try {
    await fetch(`/api/schedules/${scheduleId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    showNotification(enabled ? '已启用' : '已禁用', 'success');
  } catch (error) {
    showNotification('操作失败', 'error');
    loadSchedules();
  }
}

async function deleteSchedule(scheduleId) {
  if (!confirm('确定要删除这个定时任务吗？')) return;
  
  try {
    const response = await fetch(`/api/schedules/${scheduleId}`, { method: 'DELETE' });
    if (response.ok) {
      showNotification('已删除', 'success');
      loadSchedules();
    }
  } catch (error) {
    showNotification('删除失败', 'error');
  }
}

// ============================================
// Utility Functions
// ============================================

function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
    <span>${escapeHtml(message)}</span>
  `;
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => notification.classList.add('show'), 10);
  
  // Remove after delay
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

// ============================================
// Task Templates (Enterprise Feature)
// ============================================

let taskTemplatesData = [];
let selectedTemplateId = null;

async function showTaskTemplates() {
  openModal('taskTemplatesModal');
  await loadTaskTemplates();
}

async function loadTaskTemplates() {
  const container = document.getElementById('templatesContainer');
  if (!container) {
    console.error('Templates container not found');
    return;
  }
  
  container.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i> 加载中...</div>';
  
  try {
    const response = await fetch('/api/templates');
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    taskTemplatesData = data.templates || [];
    const categories = data.categories || [];
    
    if (taskTemplatesData.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-layer-group"></i>
          <p>暂无任务模板</p>
          <p class="text-muted">内置模板将在首次加载时自动创建</p>
        </div>`;
      return;
    }
    
    // Group templates by category
    const grouped = {};
    taskTemplatesData.forEach(tpl => {
      const cat = tpl.category || 'custom';
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(tpl);
    });
    
    // Category display names
    const categoryNames = {
      'research': '🔍 信息检索',
      'data_analysis': '📊 数据分析',
      'content': '✍️ 内容创作',
      'code': '💻 代码开发',
      'document': '📝 文档处理',
      'automation': '⚙️ 自动化任务',
      'custom': '📋 自定义'
    };
    
    let html = '<div class="templates-grid">';
    
    for (const [cat, templates] of Object.entries(grouped)) {
      html += `
        <div class="template-category">
          <h3 class="category-title">${categoryNames[cat] || cat}</h3>
          <div class="template-list">
      `;
      
      templates.forEach(tpl => {
        html += `
          <div class="template-item" onclick="selectTemplate('${tpl.id}')">
            <div class="template-icon-large">${tpl.icon || '📋'}</div>
            <div class="template-info">
              <div class="template-name">${tpl.name}</div>
              <div class="template-desc">${tpl.description || ''}</div>
              <div class="template-meta">
                <span><i class="fas fa-play"></i> ${tpl.use_count || 0} 次使用</span>
                ${tpl.is_builtin ? '<span class="builtin-badge">内置</span>' : ''}
              </div>
            </div>
            <div class="template-actions">
              <button class="template-use-btn" onclick="event.stopPropagation(); useTemplate('${tpl.id}')">
                <i class="fas fa-play"></i> 使用
              </button>
            </div>
          </div>
        `;
      });
      
      html += '</div></div>';
    }
    
    html += '</div>';
    container.innerHTML = html;
    
  } catch (error) {
    console.error('Failed to load templates:', error);
    container.innerHTML = `
      <div class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>加载失败: ${error.message}</p>
        <button onclick="loadTaskTemplates()" class="retry-btn">重试</button>
      </div>`;
  }
}

function selectTemplate(templateId) {
  selectedTemplateId = templateId;
  const template = taskTemplatesData.find(t => t.id === templateId);
  
  if (!template) return;
  
  // Show template detail panel
  showTemplateDetail(template);
}

function showTemplateDetail(template) {
  const modal = document.getElementById('templateDetailModal') || createTemplateDetailModal();
  
  // Build variables form
  let variablesHtml = '';
  if (template.variables && template.variables.length > 0) {
    variablesHtml = template.variables.map(v => {
      const required = v.required ? 'required' : '';
      const placeholder = v.placeholder || '';
      
      if (v.type === 'textarea') {
        return `
          <div class="form-group">
            <label>${v.label || v.name}${v.required ? ' *' : ''}</label>
            <textarea name="${v.name}" ${required} placeholder="${placeholder}" rows="3">${v.default || ''}</textarea>
          </div>`;
      } else if (v.type === 'select' && v.options) {
        return `
          <div class="form-group">
            <label>${v.label || v.name}${v.required ? ' *' : ''}</label>
            <select name="${v.name}" ${required}>
              ${v.options.map(opt => `<option value="${opt}" ${opt === v.default ? 'selected' : ''}>${opt}</option>`).join('')}
            </select>
          </div>`;
      } else {
        return `
          <div class="form-group">
            <label>${v.label || v.name}${v.required ? ' *' : ''}</label>
            <input type="${v.type || 'text'}" name="${v.name}" ${required} placeholder="${placeholder}" value="${v.default || ''}">
          </div>`;
      }
    }).join('');
  }
  
  modal.innerHTML = `
    <div class="modal-content template-detail">
      <div class="modal-header">
        <div class="template-header-info">
          <span class="template-icon-xl">${template.icon || '📋'}</span>
          <div>
            <h2>${template.name}</h2>
            <p>${template.description || ''}</p>
          </div>
        </div>
        <button class="close-btn" onclick="closeModal('templateDetailModal')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <form id="templateForm" onsubmit="executeTemplate(event, '${template.id}')">
          ${variablesHtml || '<p class="no-vars">此模板无需额外参数</p>'}
          
          <div class="form-group">
            <label>输出格式</label>
            <div class="format-options">
              ${(template.output_formats || ['markdown']).map(fmt => `
                <label class="format-option">
                  <input type="checkbox" name="output_format" value="${fmt}" ${fmt === 'markdown' ? 'checked' : ''}>
                  <span>${{'markdown': '📝 Markdown', 'html': '🌐 HTML', 'excel': '📈 Excel', 'pptx': '📽️ PPT', 'pdf': '📄 PDF'}[fmt] || fmt}</span>
                </label>
              `).join('')}
            </div>
          </div>
          
          <div class="form-actions">
            <button type="button" class="btn-secondary" onclick="closeModal('templateDetailModal')">取消</button>
            <button type="submit" class="btn-primary">
              <i class="fas fa-play"></i> 执行任务
            </button>
          </div>
        </form>
      </div>
    </div>
  `;
  
  modal.style.display = 'flex';
  modal.classList.add('active');
}

function createTemplateDetailModal() {
  const modal = document.createElement('div');
  modal.id = 'templateDetailModal';
  modal.className = 'modal';
  document.body.appendChild(modal);
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal('templateDetailModal');
    }
  });
  
  return modal;
}

async function executeTemplate(event, templateId) {
  event.preventDefault();
  
  const form = event.target;
  const formData = new FormData(form);
  const variables = {};
  
  // Collect variables
  for (const [key, value] of formData.entries()) {
    if (key !== 'output_format') {
      variables[key] = value;
    }
  }
  
  // Collect output formats
  const outputFormats = formData.getAll('output_format');
  
  try {
    // Render template
    const response = await fetch(`/api/templates/${templateId}/render`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variables })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.detail || '模板渲染失败');
    }
    
    // Close modals
    closeModal('templateDetailModal');
    closeModal('taskTemplatesModal');
    
    // Create task with rendered prompt
    if (typeof createNewTask === 'function') {
      createNewTask(data.task_prompt, {
        mode: data.default_mode || 'auto',
        outputFormats: outputFormats,
        openInWorkspace: true
      });
    } else if (typeof window.taskStore !== 'undefined') {
      const task = window.taskStore.createTask(data.task_prompt);
      window.taskStore.setCurrentTask(task.id);
      window.location.href = '/workspace';
    }
    
    showNotification('任务已创建', 'success');
    
  } catch (error) {
    console.error('Template execution failed:', error);
    showNotification('执行失败: ' + error.message, 'error');
  }
}

function useTemplate(templateId) {
  const template = taskTemplatesData.find(t => t.id === templateId);
  if (template) {
    showTemplateDetail(template);
  }
}

// Export functions for global access
window.showKnowledgeBase = showKnowledgeBase;
window.showWorkflows = showWorkflows;
window.showStatistics = showStatistics;
window.showSchedules = showSchedules;
window.showTaskTemplates = showTaskTemplates;
window.selectTemplate = selectTemplate;
window.useTemplate = useTemplate;
window.executeTemplate = executeTemplate;
window.showUploadDocument = showUploadDocument;
window.uploadDocument = uploadDocument;
window.deleteDocument = deleteDocument;
window.executeWorkflow = executeWorkflow;
window.exportStatistics = exportStatistics;
window.toggleSchedule = toggleSchedule;
window.deleteSchedule = deleteSchedule;
window.switchKBTab = switchKBTab;
window.showAddSchedule = showAddSchedule;
window.showCreateWorkflow = showCreateWorkflow;
window.deleteWorkflow = deleteWorkflow;
window.showAddCollection = showAddCollection;
window.submitCreateWorkflow = submitCreateWorkflow;
window.submitWorkflowExecution = submitWorkflowExecution;

function showAddCollection() {
  const name = prompt('集合名称:', '');
  if (!name) return;
  
  const description = prompt('集合描述:', '');
  
  createCollection(name, description);
}

async function createCollection(name, description) {
  try {
    const response = await fetch('/api/knowledge-base/collections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description })
    });
    
    const data = await response.json();
    if (data.success) {
      showNotification('集合创建成功', 'success');
      loadKBContent();
    } else {
      throw new Error(data.error || '创建失败');
    }
  } catch (error) {
    showNotification('创建失败: ' + error.message, 'error');
  }
}

console.log('JoinFlow Features module loaded');

