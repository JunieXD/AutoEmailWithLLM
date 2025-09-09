/**
 * 邮件生成模块 - AI邮件生成、模板邮件、内容优化等功能
 */

class EmailGenerator {
    constructor() {
        this.currentEmailContent = '';
        this.initEventListeners();
    }

    // 初始化事件监听器
    initEventListeners() {
        // 邮件生成表单提交
        const emailForm = document.getElementById('email-form');
        if (emailForm) {
            emailForm.addEventListener('submit', this.handleEmailGeneration.bind(this));
        }

        // 教授选择变化
        const professorSelect = document.getElementById('select-professor');
        if (professorSelect) {
            professorSelect.addEventListener('change', this.onProfessorChange.bind(this));
        }

        // 邮件类型变化
        const emailTypeSelect = document.getElementById('email-type');
        if (emailTypeSelect) {
            emailTypeSelect.addEventListener('change', this.onEmailTypeChange.bind(this));
        }

        // 模板选择变化
        const templateSelect = document.getElementById('template-select');
        if (templateSelect) {
            templateSelect.addEventListener('change', this.onTemplateChange.bind(this));
        }

        // 文档选择变化
        const documentSelect = document.getElementById('document-select');
        if (documentSelect) {
            documentSelect.addEventListener('change', this.onDocumentChange.bind(this));
        }
    }

    // 处理邮件生成表单提交
    async handleEmailGeneration(e) {
        e.preventDefault();
        
        const formData = this.getFormData();
        
        if (!this.validateForm(formData)) {
            return;
        }
        
        this.showGeneratingState();
        
        try {
            const result = await this.generateEmail(formData);
            this.displayGeneratedEmail(result);
        } catch (error) {
            Utils.showToast('邮件生成失败: ' + error.message, 'error');
        } finally {
            this.hideGeneratingState();
        }
    }

    // 获取表单数据
    getFormData() {
        return {
            professor_id: document.getElementById('select-professor')?.value,
            email_type: document.getElementById('email-type')?.value,
            template_id: document.getElementById('template-select')?.value,
            document_id: document.getElementById('document-select')?.value,
            custom_content: document.getElementById('custom-content')?.value,
            tone: document.getElementById('tone-select')?.value || 'formal',
            language: document.getElementById('language-select')?.value || 'chinese',
            include_attachments: document.getElementById('include-attachments')?.checked || false,
            custom_subject: document.getElementById('ai-email-subject')?.value || ''
        };
    }

    // 验证表单
    validateForm(formData) {
        if (!formData.professor_id) {
            Utils.showToast('请选择教授', 'error');
            return false;
        }
        
        if (!formData.email_type) {
            Utils.showToast('请选择邮件类型', 'error');
            return false;
        }
        
        if (formData.email_type === 'custom' && !formData.custom_content) {
            Utils.showToast('请输入自定义内容', 'error');
            return false;
        }
        
        return true;
    }

    // 生成邮件
    async generateEmail(formData) {
        const response = await Utils.apiRequest('/api/generate-email', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        return response;
    }

    // 显示生成中状态
    showGeneratingState() {
        const generateBtn = document.querySelector('#email-form button[type="submit"]');
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 生成中...';
        }
        
        const resultContainer = document.getElementById('email-result');
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">生成中...</span>
                    </div>
                    <p class="mt-2 text-muted">AI正在为您生成邮件，请稍候...</p>
                </div>
            `;
            resultContainer.style.display = 'block';
        }
    }

    // 隐藏生成中状态
    hideGeneratingState() {
        const generateBtn = document.querySelector('#email-form button[type="submit"]');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="bi bi-magic"></i> 生成邮件';
        }
    }

    // 显示生成的邮件
    displayGeneratedEmail(result) {
        this.currentEmailContent = result;
        
        const resultContainer = document.getElementById('email-result');
        if (!resultContainer) return;
        
        const html = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="bi bi-envelope"></i> 生成的邮件</h6>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="window.EmailGenerator.copyEmail()">
                            <i class="bi bi-clipboard"></i> 复制
                        </button>
                        <button class="btn btn-outline-success" onclick="window.EmailGenerator.editEmail()">
                            <i class="bi bi-pencil"></i> 编辑
                        </button>
                        <button class="btn btn-primary" onclick="window.EmailGenerator.sendEmail()">
                            <i class="bi bi-send"></i> 发送
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="email-preview">
                        <div class="mb-3">
                            <strong>主题:</strong> ${result.subject || '无主题'}
                        </div>
                        <div class="mb-3">
                            <strong>收件人:</strong> ${result.recipient || result.professor_name || '未指定'}
                        </div>
                        <div class="email-content">
                            <strong>内容:</strong>
                            <div class="mt-2 p-3 bg-light rounded" style="white-space: pre-wrap;">${result.content || result.email_content || '无内容'}</div>
                        </div>
                        ${result.attachments && result.attachments.length > 0 ? `
                            <div class="mt-3">
                                <strong>附件:</strong>
                                <ul class="list-unstyled mt-2">
                                    ${result.attachments.map(att => `<li><i class="bi bi-paperclip"></i> ${att.name}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        resultContainer.innerHTML = html;
        resultContainer.style.display = 'block';
        
        // 滚动到结果区域
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // 教授选择变化处理
    async onProfessorChange() {
        const professorId = document.getElementById('select-professor')?.value;
        
        if (professorId) {
            try {
                const professor = await Utils.apiRequest(`/api/professors/${professorId}`);
                this.updateProfessorInfo(professor);
            } catch (error) {
                console.error('获取教授信息失败:', error);
            }
        } else {
            this.clearProfessorInfo();
        }
    }

    // 更新教授信息显示
    updateProfessorInfo(professor) {
        const infoContainer = document.getElementById('professor-info');
        if (!infoContainer) return;
        
        const html = `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">${professor.name}</h6>
                    <p class="card-text">
                        <small class="text-muted">
                            ${professor.university} - ${professor.department || '未指定院系'}<br>
                            研究领域: ${professor.research_area || '未指定'}
                        </small>
                    </p>
                </div>
            </div>
        `;
        
        infoContainer.innerHTML = html;
        infoContainer.style.display = 'block';
    }

    // 清除教授信息显示
    clearProfessorInfo() {
        const infoContainer = document.getElementById('professor-info');
        if (infoContainer) {
            infoContainer.style.display = 'none';
        }
    }

    // 邮件类型变化处理
    onEmailTypeChange() {
        const emailType = document.getElementById('email-type')?.value;
        const customContentGroup = document.getElementById('custom-content-group');
        const templateGroup = document.getElementById('template-group');
        
        if (emailType === 'custom') {
            if (customContentGroup) customContentGroup.style.display = 'block';
            if (templateGroup) templateGroup.style.display = 'none';
        } else if (emailType === 'template') {
            if (customContentGroup) customContentGroup.style.display = 'none';
            if (templateGroup) templateGroup.style.display = 'block';
            this.loadTemplates();
        } else {
            if (customContentGroup) customContentGroup.style.display = 'none';
            if (templateGroup) templateGroup.style.display = 'none';
        }
    }

    // 加载邮件模板
    async loadTemplates() {
        try {
            const templates = await Utils.apiRequest('/api/templates');
            const select = document.getElementById('template-select');
            
            if (select) {
                select.innerHTML = '<option value="">请选择模板</option>';
                
                templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('加载模板失败:', error);
        }
    }

    // 模板选择变化处理
    async onTemplateChange() {
        const templateId = document.getElementById('template-select')?.value;
        
        if (templateId) {
            try {
                const template = await Utils.apiRequest(`/api/templates/${templateId}`);
                this.displayTemplatePreview(template);
            } catch (error) {
                console.error('获取模板失败:', error);
            }
        } else {
            this.clearTemplatePreview();
        }
    }

    // 显示模板预览
    displayTemplatePreview(template) {
        const previewContainer = document.getElementById('template-preview');
        if (!previewContainer) return;
        
        const html = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">模板预览: ${template.name}</h6>
                </div>
                <div class="card-body">
                    <div class="mb-2"><strong>主题:</strong> ${template.subject}</div>
                    <div class="template-content" style="white-space: pre-wrap; background: #f8f9fa; padding: 1rem; border-radius: 0.375rem;">${template.content}</div>
                </div>
            </div>
        `;
        
        previewContainer.innerHTML = html;
        previewContainer.style.display = 'block';
    }

    // 清除模板预览
    clearTemplatePreview() {
        const previewContainer = document.getElementById('template-preview');
        if (previewContainer) {
            previewContainer.style.display = 'none';
        }
    }

    // 文档选择变化处理
    async onDocumentChange() {
        const documentId = document.getElementById('document-select')?.value;
        
        if (documentId) {
            try {
                const document = await Utils.apiRequest(`/api/documents/${documentId}`);
                this.displayDocumentInfo(document);
            } catch (error) {
                console.error('获取文档信息失败:', error);
            }
        } else {
            this.clearDocumentInfo();
        }
    }

    // 显示文档信息
    displayDocumentInfo(document) {
        const infoContainer = document.getElementById('document-info');
        if (!infoContainer) return;
        
        const html = `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">${document.name}</h6>
                    <p class="card-text">
                        <small class="text-muted">
                            类型: ${document.type}<br>
                            大小: ${Utils.formatFileSize(document.size)}<br>
                            上传时间: ${new Date(document.upload_time).toLocaleString()}
                        </small>
                    </p>
                </div>
            </div>
        `;
        
        infoContainer.innerHTML = html;
        infoContainer.style.display = 'block';
    }

    // 清除文档信息
    clearDocumentInfo() {
        const infoContainer = document.getElementById('document-info');
        if (infoContainer) {
            infoContainer.style.display = 'none';
        }
    }

    // 显示文档主题设置和操作按钮
    showDocumentSubjectAndActions() {
        const subjectSetting = document.getElementById('doc-subject-setting');
        const actionsContainer = document.getElementById('doc-actions-container');
        
        if (subjectSetting) {
            subjectSetting.style.display = 'block';
        }
        if (actionsContainer) {
            actionsContainer.style.display = 'block';
        }
    }

    // 隐藏文档主题设置和操作按钮
    hideDocumentSubjectAndActions() {
        const subjectSetting = document.getElementById('doc-subject-setting');
        const actionsContainer = document.getElementById('doc-actions-container');
        
        if (subjectSetting) {
            subjectSetting.style.display = 'none';
        }
        if (actionsContainer) {
            actionsContainer.style.display = 'none';
        }
    }

    showAISubjectAndActions() {
        const subjectSetting = document.getElementById('ai-subject-setting');
        const actionsContainer = document.getElementById('ai-actions-container');
        
        if (subjectSetting) {
            subjectSetting.style.display = 'block';
        }
        if (actionsContainer) {
            actionsContainer.style.display = 'block';
        }
    }

    hideAISubjectAndActions() {
        const subjectSetting = document.getElementById('ai-subject-setting');
        const actionsContainer = document.getElementById('ai-actions-container');
        
        if (subjectSetting) {
            subjectSetting.style.display = 'none';
        }
        if (actionsContainer) {
            actionsContainer.style.display = 'none';
        }
    }

    // 文档模式文档选择改变处理
    async onDocumentSelectionChange() {
        const previewContainer = document.getElementById('doc-document-preview');
        
        if (!previewContainer) return;
        
        // 获取选中的文档ID
        const selectedRadio = document.querySelector('input[name="doc-selected-file"]:checked');
        const fileId = selectedRadio ? selectedRadio.value : null;
        
        if (fileId) {
            try {
                // 获取用户ID
                const userSelect = document.getElementById('doc-sender-user');
                if (!userSelect || !userSelect.value) {
                    Utils.showToast('请先选择发送用户', 'error');
                    return;
                }
                
                const userId = userSelect.value;
                
                // 获取文档信息
                const response = await Utils.apiRequest(`/api/users/${userId}/documents`);
                const selectedFile = response.documents.files.find(file => file.id == fileId);
                
                if (selectedFile) {
                    // 显示文档信息
                    const html = `
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-title">${selectedFile.filename}</h6>
                                <p class="card-text">
                                    <small class="text-muted">
                                        类型: ${selectedFile.file_type}<br>
                                        大小: ${Utils.formatFileSize(selectedFile.file_size || 0)}<br>
                                        上传时间: ${selectedFile.upload_time ? new Date(selectedFile.upload_time).toLocaleString() : '未知'}
                                    </small>
                                </p>
                            </div>
                        </div>
                    `;
                    
                    previewContainer.innerHTML = html;
                    previewContainer.style.display = 'block';
                    
                    // 获取并显示文档HTML内容
                    try {
                        const contentResponse = await Utils.apiRequest(`/api/users/${userId}/files/${fileId}/content?output_format=html`);
                        const documentContentDiv = document.getElementById('doc-document-content');
                        if (documentContentDiv && contentResponse.content) {
                            documentContentDiv.innerHTML = contentResponse.content;
                            documentContentDiv.style.display = 'block';
                        }
                    } catch (error) {
                        console.error('获取文档HTML内容失败:', error);
                        const documentContentDiv = document.getElementById('doc-document-content');
                        if (documentContentDiv) {
                            documentContentDiv.innerHTML = '<p class="text-muted">无法加载文档内容预览</p>';
                            documentContentDiv.style.display = 'block';
                        }
                    }
                    
                    // 显示主题设置和操作按钮
                    this.showDocumentSubjectAndActions();
                } else {
                    previewContainer.style.display = 'none';
                    this.hideDocumentSubjectAndActions();
                }
            } catch (error) {
                console.error('获取文档信息失败:', error);
                previewContainer.style.display = 'none';
                this.hideDocumentSubjectAndActions();
            }
        } else {
            previewContainer.style.display = 'none';
            this.hideDocumentSubjectAndActions();
        }
    }

    // 复制邮件内容
    copyEmail() {
        if (!this.currentEmailContent) {
            Utils.showToast('没有可复制的邮件内容', 'error');
            return;
        }
        
        const textToCopy = `主题: ${this.currentEmailContent.subject}\n\n${this.currentEmailContent.content}`;
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            Utils.showToast('邮件内容已复制到剪贴板', 'success');
        }).catch(err => {
            console.error('复制失败:', err);
            Utils.showToast('复制失败', 'error');
        });
    }

    // 编辑邮件
    editEmail() {
        if (!this.currentEmailContent) {
            Utils.showToast('没有可编辑的邮件内容', 'error');
            return;
        }
        
        // 显示编辑模态框
        this.showEditModal();
    }

    // 显示编辑模态框
    showEditModal() {
        const modal = new bootstrap.Modal(document.getElementById('editEmailModal'));
        
        // 填充当前内容
        document.getElementById('edit-email-subject').value = this.currentEmailContent.subject || '';
        document.getElementById('edit-email-content').value = this.currentEmailContent.content || '';
        
        modal.show();
    }

    // 保存编辑的邮件
    saveEditedEmail() {
        const subject = document.getElementById('edit-email-subject').value;
        const content = document.getElementById('edit-email-content').value;
        
        if (!subject.trim() || !content.trim()) {
            Utils.showToast('主题和内容不能为空', 'error');
            return;
        }
        
        // 更新当前邮件内容
        this.currentEmailContent.subject = subject;
        this.currentEmailContent.content = content;
        
        // 重新显示邮件
        this.displayGeneratedEmail(this.currentEmailContent);
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('editEmailModal'));
        modal.hide();
        
        Utils.showToast('邮件内容已更新', 'success');
    }

    // 发送邮件
    sendEmail() {
        if (!this.currentEmailContent) {
            Utils.showToast('没有可发送的邮件内容', 'error');
            return;
        }
        
        // 切换到邮件发送页面
        window.AppCore.showTab('email-sender');
        document.querySelector('.nav-link[data-tab="email-sender"]')?.classList.add('active');
        document.querySelectorAll('.nav-link:not([data-tab="email-sender"])')?.forEach(l => l.classList.remove('active'));
        
        // 填充发送表单
        if (window.EmailSender) {
            window.EmailSender.fillFromGenerated(this.currentEmailContent);
        }
    }

    // 为特定教授生成邮件（从教授管理页面调用）
    async generateEmailForProfessor(professorId) {
        // 选择教授
        const professorSelect = document.getElementById('select-professor');
        if (professorSelect) {
            professorSelect.value = professorId;
            await this.onProfessorChange();
        }
        
        // 设置默认邮件类型
        const emailTypeSelect = document.getElementById('email-type');
        if (emailTypeSelect) {
            emailTypeSelect.value = 'introduction';
            this.onEmailTypeChange();
        }
    }

    // 重新生成邮件
    async regenerateEmail() {
        const formData = this.getFormData();
        
        if (!this.validateForm(formData)) {
            return;
        }
        
        this.showGeneratingState();
        
        try {
            // 添加重新生成标志
            formData.regenerate = true;
            const result = await this.generateEmail(formData);
            this.displayGeneratedEmail(result);
        } catch (error) {
            Utils.showToast('邮件重新生成失败: ' + error.message, 'error');
        } finally {
            this.hideGeneratingState();
        }
    }

    // 优化邮件内容
    async optimizeEmail() {
        if (!this.currentEmailContent) {
            Utils.showToast('没有可优化的邮件内容', 'error');
            return;
        }
        
        try {
            const result = await Utils.apiRequest('/api/optimize-email', {
                method: 'POST',
                body: JSON.stringify({
                    subject: this.currentEmailContent.subject,
                    content: this.currentEmailContent.content
                })
            });
            
            this.currentEmailContent = result;
            this.displayGeneratedEmail(result);
            Utils.showToast('邮件内容已优化', 'success');
        } catch (error) {
            Utils.showToast('邮件优化失败: ' + error.message, 'error');
        }
    }

    // 加载文档列表
    async loadDocuments() {
        try {
            const documents = await Utils.apiRequest('/api/documents');
            const select = document.getElementById('document-select');
            
            if (select) {
                select.innerHTML = '<option value="">不使用文档</option>';
                
                documents.forEach(doc => {
                    const option = document.createElement('option');
                    option.value = doc.id;
                    option.textContent = `${doc.name} (${Utils.formatFileSize(doc.size)})`;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('加载文档列表失败:', error);
        }
    }

    // 为AI模式加载用户数据
    async loadUsersForAI() {
        try {
            const users = await Utils.apiRequest('/api/users');
            const select = document.getElementById('ai-sender-user');
            
            if (select) {
                select.innerHTML = '<option value="">请选择发送用户</option>';
                
                users.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = `${user.name} (${user.email})`;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('加载用户失败:', error);
        }
    }

    // 为文档模式加载用户数据
    async loadUsersForDocument() {
        try {
            const users = await Utils.apiRequest('/api/users');
            const select = document.getElementById('doc-sender-user');
            
            if (select) {
                select.innerHTML = '<option value="">请选择发送用户</option>';
                
                users.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = `${user.name} (${user.email})`;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('加载用户失败:', error);
        }
    }

    // 为文档模式加载文档选择列表
    async loadDocumentsForSelection(userId = null) {
        try {
            const container = document.getElementById('doc-user-documents-list');
            
            if (!container) return;
            
            // 清空容器
            container.innerHTML = '';
            
            // 如果没有指定用户ID，从用户选择框获取
            if (!userId) {
                const userSelect = document.getElementById('doc-sender-user');
                if (!userSelect || !userSelect.value) {
                    return;
                }
                userId = userSelect.value;
            }
            
            // 获取用户文档
            const response = await Utils.apiRequest(`/api/users/${userId}/documents`);
            
            if (response && response.documents && response.documents.files && response.documents.files.length > 0) {
                response.documents.files.forEach((file, index) => {
                    const radioId = `doc-file-${file.id}`;
                    const radioHtml = `
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="radio" name="doc-selected-file" id="${radioId}" value="${file.id}" onchange="handleDocumentSelectionChange()">
                            <label class="form-check-label" for="${radioId}">
                                <strong>${file.filename}</strong>
                                <br>
                                <small class="text-muted">
                                    类型: ${file.file_type} | 大小: ${Utils.formatFileSize(file.file_size || 0)}
                                    ${file.upload_time ? ' | 上传时间: ' + new Date(file.upload_time).toLocaleString() : ''}
                                </small>
                            </label>
                        </div>
                    `;
                    container.innerHTML += radioHtml;
                });
            } else {
                container.innerHTML = '<div class="text-muted">该用户暂无上传文档</div>';
            }
        } catch (error) {
            console.error('加载用户文档失败:', error);
            const container = document.getElementById('doc-user-documents-list');
            if (container) {
                container.innerHTML = '<div class="text-danger">加载文档失败</div>';
            }
        }
    }
}

// 创建全局实例
window.EmailGenerator = new EmailGenerator();

// 导出全局函数供HTML调用
window.generateEmail = () => {
    const form = document.getElementById('email-form');
    if (form) {
        form.dispatchEvent(new Event('submit'));
    }
};
window.copyEmail = () => window.EmailGenerator.copyEmail();
window.editEmail = () => window.EmailGenerator.editEmail();
window.saveEditedEmail = () => window.EmailGenerator.saveEditedEmail();
window.sendEmail = () => window.EmailGenerator.sendEmail();
window.regenerateEmail = () => window.EmailGenerator.regenerateEmail();
window.optimizeEmail = () => window.EmailGenerator.optimizeEmail();
window.generateEmailForProfessor = (professorId) => window.EmailGenerator.generateEmailForProfessor(professorId);

// AI发送人选择变化处理
window.handleAISenderChange = () => {
    const senderSelect = document.getElementById('ai-sender-user');
    const professorSelection = document.getElementById('ai-professor-selection');
    
    if (senderSelect && senderSelect.value) {
        // 显示教授选择部分
        if (professorSelection) {
            professorSelection.style.display = 'block';
        }
        
        // 显示主题设置和操作按钮
        window.EmailGenerator.showAISubjectAndActions();
        
        // 加载教授数据
        if (window.ProfessorManager && window.ProfessorManager.loadProfessorsForSelection) {
            window.ProfessorManager.loadProfessorsForSelection('ai-select-professor', 'ai-select-university');
        }
    } else {
        // 隐藏教授选择部分
        if (professorSelection) {
            professorSelection.style.display = 'none';
        }
        
        // 隐藏主题设置和操作按钮
        window.EmailGenerator.hideAISubjectAndActions();
    }
};

// AI选择模式变化处理
window.handleAISelectionModeChange = (event) => {
    const mode = event.target.value;
    const singleSelection = document.getElementById('ai-single-selection');
    const batchSelection = document.getElementById('ai-batch-selection');
    
    if (mode === 'single') {
        if (singleSelection) singleSelection.style.display = 'block';
        if (batchSelection) batchSelection.style.display = 'none';
    } else if (mode === 'batch') {
        if (singleSelection) singleSelection.style.display = 'none';
        if (batchSelection) batchSelection.style.display = 'block';
    }
};

// 文档发送人选择变化处理
window.handleDocSenderChange = () => {
    const senderSelect = document.getElementById('doc-sender-user');
    const professorSelection = document.getElementById('doc-professor-selection');
    const documentSelection = document.getElementById('doc-document-selection');
    
    if (senderSelect && senderSelect.value) {
        // 显示教授选择部分
        if (professorSelection) {
            professorSelection.style.display = 'block';
        }
        
        // 显示文档选择部分
        if (documentSelection) {
            documentSelection.style.display = 'block';
        }
        
        // 加载教授数据
        if (window.ProfessorManager && window.ProfessorManager.loadProfessorsForSelection) {
            window.ProfessorManager.loadProfessorsForSelection('doc-select-professor', 'doc-select-university');
        }
        
        // 加载用户文档
        if (window.EmailGenerator && window.EmailGenerator.loadDocumentsForSelection) {
            window.EmailGenerator.loadDocumentsForSelection(senderSelect.value);
        }
    } else {
        // 隐藏教授选择部分
        if (professorSelection) {
            professorSelection.style.display = 'none';
        }
        
        // 隐藏文档选择部分
        if (documentSelection) {
            documentSelection.style.display = 'none';
        }
    }
};

// 文档选择模式变化处理
window.handleDocSelectionModeChange = (event) => {
    const mode = event.target.value;
    const singleSelection = document.getElementById('doc-single-selection');
    const batchSelection = document.getElementById('doc-batch-selection');
    
    if (mode === 'single') {
        if (singleSelection) singleSelection.style.display = 'block';
        if (batchSelection) batchSelection.style.display = 'none';
    } else if (mode === 'batch') {
        if (singleSelection) singleSelection.style.display = 'none';
        if (batchSelection) batchSelection.style.display = 'block';
    }
};

// 文档模式文档选择改变处理
window.handleDocumentSelectionChange = () => {
    if (window.EmailGenerator && window.EmailGenerator.onDocumentSelectionChange) {
        window.EmailGenerator.onDocumentSelectionChange();
    }
};

// 清除文档预览函数
window.clearDocumentPreview = () => {
    const previewContainer = document.getElementById('doc-document-content');
    if (previewContainer) {
        previewContainer.innerHTML = '';
    }
    
    const documentCard = document.querySelector('.card:has(#doc-document-content)');
    if (documentCard) {
        documentCard.style.display = 'none';
    }
    
    // 重置文档选择
    const documentSelect = document.getElementById('doc-select-document');
    if (documentSelect) {
        documentSelect.value = '';
    }
};

// 发送方式选择函数
window.selectSendingMode = (mode) => {
    // 清除之前的选择状态
    document.querySelectorAll('.card[id$="-card"]').forEach(card => {
        card.classList.remove('border-success', 'border-info');
        card.style.backgroundColor = '';
    });
    
    // 隐藏所有界面
    document.getElementById('ai-generation-interface').style.display = 'none';
    document.getElementById('document-usage-interface').style.display = 'none';
    
    // 取消所有radio选择
    document.querySelectorAll('input[name="sending-mode"]').forEach(radio => {
        radio.checked = false;
    });
    
    if (mode === 'ai') {
        // 选择AI生成模式
        const aiCard = document.getElementById('ai-generation-card');
        const aiRadio = document.getElementById('ai-mode');
        const aiInterface = document.getElementById('ai-generation-interface');
        
        if (aiCard) {
            aiCard.classList.add('border-success');
            aiCard.style.backgroundColor = 'rgba(25, 135, 84, 0.05)';
        }
        if (aiRadio) aiRadio.checked = true;
        if (aiInterface) aiInterface.style.display = 'block';
        
        // 加载用户数据
        if (window.EmailGenerator.loadUsersForAI) {
            window.EmailGenerator.loadUsersForAI();
        }
        
    } else if (mode === 'document') {
        // 选择文档模式
        const docCard = document.getElementById('document-usage-card');
        const docRadio = document.getElementById('document-mode');
        const docInterface = document.getElementById('document-usage-interface');
        
        if (docCard) {
            docCard.classList.add('border-info');
            docCard.style.backgroundColor = 'rgba(13, 202, 240, 0.05)';
        }
        if (docRadio) docRadio.checked = true;
        if (docInterface) docInterface.style.display = 'block';
        
        // 加载用户和文档数据
        if (window.EmailGenerator.loadUsersForDocument) {
            window.EmailGenerator.loadUsersForDocument();
        }
        if (window.EmailGenerator.loadDocumentsForSelection) {
            window.EmailGenerator.loadDocumentsForSelection();
        }
    }
};

// 文档模式生成邮件预览
window.generateDocumentEmail = async () => {
    const form = document.getElementById('document-email-form');
    const previewContainer = document.getElementById('doc-email-preview');
    const actionButtons = document.getElementById('doc-action-buttons');
    
    if (!form || !previewContainer) {
        Utils.showToast('表单或预览容器未找到', 'error');
        return;
    }
    
    // 获取表单数据
    const formData = new FormData(form);
    const selectedDocuments = [];
    const documentRadio = form.querySelector('input[name="doc-selected-file"]:checked');
    if (documentRadio) {
        selectedDocuments.push(documentRadio.value);
    }
    
    if (selectedDocuments.length === 0) {
        Utils.showToast('请选择至少一个文档', 'warning');
        return;
    }
    
    const selectedProfessors = [];
    
    // 检查选择模式
    const selectionMode = form.querySelector('input[name="doc-selection-mode"]:checked')?.value;
    
    if (selectionMode === 'single') {
        // 单个选择模式
        const professorSelect = form.querySelector('#doc-select-professor');
        if (professorSelect && professorSelect.value) {
            selectedProfessors.push(professorSelect.value);
        }
    } else if (selectionMode === 'batch') {
        // 批量选择模式
        const professorCheckboxes = form.querySelectorAll('input[name="selected_professors"]:checked');
        professorCheckboxes.forEach(checkbox => {
            selectedProfessors.push(checkbox.value);
        });
    }
    
    if (selectedProfessors.length === 0) {
        Utils.showToast('请选择至少一个教授', 'warning');
        return;
    }
    
    try {
        // 显示生成中状态
        previewContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> 正在生成邮件预览...</div>';
        
        // 调用API生成邮件
        const response = await fetch('/api/generate-document-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sender_id: document.getElementById('doc-sender-user').value,
                selected_documents: selectedDocuments,
                selected_professors: selectedProfessors,
                school: document.getElementById('doc-select-university')?.value || '',
                college: document.getElementById('doc-select-department')?.value || '',
                custom_subject: document.getElementById('doc-email-subject')?.value || ''
            })
        });
        
        if (!response.ok) {
            throw new Error('生成邮件失败');
        }
        
        const result = await response.json();
        
        if (result.success) {
            // 显示邮件预览
            let previewHtml = `
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">套磁信邮件预览</h5>
                        <small class="text-muted">基于模板: ${result.template_filename || '未知'}</small>
                    </div>
                    <div class="card-body">
            `;
            
            // 为每个教授显示邮件预览（最多显示前两个）
            const previewsToShow = result.email_previews.slice(0, 2);
            previewsToShow.forEach((preview, index) => {
                previewHtml += `
                    <div class="mb-4 ${index > 0 ? 'border-top pt-3' : ''}">
                        <h6 class="text-primary">教授 ${index + 1}: ${preview.professor_name}</h6>
                        <small class="text-muted">${preview.professor_university || ''}</small>
                        <div class="mt-2">
                            <strong>主题:</strong> ${preview.subject}
                        </div>
                        <div class="mt-2">
                            <strong>内容:</strong>
                            <div class="border p-3 mt-2" style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">${preview.content}</div>
                        </div>
                    </div>
                `;
            });
            
            // 如果有更多教授，显示提示信息
            if (result.email_previews.length > 2) {
                previewHtml += `
                    <div class="mb-4 border-top pt-3">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i> 还有 ${result.email_previews.length - 2} 位教授的邮件将使用相同模板生成
                        </div>
                    </div>
                `;
            }
            
            previewHtml += `
                        <div class="mt-3 pt-3 border-top">
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>发送人:</strong> ${result.sender.name} (${result.sender.email})
                                </div>
                                <div class="col-md-6">
                                    <strong>目标教授:</strong> ${result.total_professors} 位
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            previewContainer.innerHTML = previewHtml;
            
            // 显示操作按钮
            if (actionButtons) {
                actionButtons.style.display = 'block';
            }
            
            Utils.showToast('邮件预览生成成功', 'success');
        } else {
            throw new Error(result.message || '生成邮件失败');
        }
    } catch (error) {
        console.error('生成文档邮件预览失败:', error);
        previewContainer.innerHTML = '<div class="alert alert-danger">生成邮件预览失败: ' + error.message + '</div>';
        Utils.showToast('生成邮件预览失败: ' + error.message, 'error');
    }
};