/**
 * 邮件发送模块 - 邮件发送、批量发送和发送历史功能
 */

class EmailSender {
    constructor() {
        this.initEventListeners();
        this.sendingQueue = [];
        this.isSending = false;
    }

    // 初始化事件监听器
    initEventListeners() {
        // 单个邮件发送表单
        const singleEmailForm = document.getElementById('single-email-form');
        if (singleEmailForm) {
            singleEmailForm.addEventListener('submit', this.handleSingleEmailSend.bind(this));
        }

        // 批量邮件发送表单
        const batchEmailForm = document.getElementById('batch-email-form');
        if (batchEmailForm) {
            batchEmailForm.addEventListener('submit', this.handleBatchEmailSend.bind(this));
        }

        // 文档邮件发送表单
        const documentEmailForm = document.getElementById('document-email-form');
        if (documentEmailForm) {
            documentEmailForm.addEventListener('submit', this.handleDocumentEmailSend.bind(this));
        }

        // 邮件发送类型切换
        const sendTypeRadios = document.querySelectorAll('input[name="send-type"]');
        sendTypeRadios.forEach(radio => {
            radio.addEventListener('change', this.onSendTypeChange.bind(this));
        });

        // 附件上传
        const attachmentInput = document.getElementById('email-attachments');
        if (attachmentInput) {
            attachmentInput.addEventListener('change', this.handleAttachmentChange.bind(this));
        }
    }

    // 处理单个邮件发送
    async handleSingleEmailSend(e) {
        e.preventDefault();
        
        const formData = this.getSingleEmailFormData();
        
        if (!this.validateSingleEmailForm(formData)) {
            return;
        }
        
        this.showSendingState('single');
        
        try {
            const result = await this.sendSingleEmail(formData);
            this.handleSendResult(result, 'single');
        } catch (error) {
            Utils.showToast('邮件发送失败: ' + error.message, 'error');
        } finally {
            this.hideSendingState('single');
        }
    }

    // 处理批量邮件发送
    async handleBatchEmailSend(e) {
        e.preventDefault();
        
        const formData = this.getBatchEmailFormData();
        
        if (!this.validateBatchEmailForm(formData)) {
            return;
        }
        
        this.showSendingState('batch');
        
        try {
            const result = await this.sendBatchEmails(formData);
            this.handleBatchSendResult(result);
        } catch (error) {
            Utils.showToast('批量邮件发送失败: ' + error.message, 'error');
        } finally {
            this.hideSendingState('batch');
        }
    }

    // 处理文档邮件发送
    async handleDocumentEmailSend(e) {
        e.preventDefault();
        
        const formData = this.getDocumentEmailFormData();
        
        if (!this.validateDocumentEmailForm(formData)) {
            return;
        }
        
        this.showSendingState('document');
        
        try {
            const result = await this.sendDocumentEmails(formData);
            this.handleBatchSendResult(result);
        } catch (error) {
            Utils.showToast('文档邮件发送失败: ' + error.message, 'error');
        } finally {
            this.hideSendingState('document');
        }
    }

    // 获取单个邮件表单数据
    getSingleEmailFormData() {
        return {
            recipient_email: document.getElementById('recipient-email')?.value,
            recipient_name: document.getElementById('recipient-name')?.value,
            subject: document.getElementById('email-subject')?.value,
            content: document.getElementById('email-content')?.value,
            attachments: this.getAttachments(),
            send_time: document.getElementById('send-time')?.value || null
        };
    }

    // 获取批量邮件表单数据
    getBatchEmailFormData() {
        const selectedProfessors = this.getSelectedProfessors();
        
        return {
            professors: selectedProfessors,
            subject: document.getElementById('batch-subject')?.value,
            content: document.getElementById('batch-content')?.value,
            attachments: this.getAttachments(),
            send_interval: parseInt(document.getElementById('send-interval')?.value) || 5,
            personalize: document.getElementById('personalize-emails')?.checked || false
        };
    }

    // 获取文档邮件表单数据
    getDocumentEmailFormData() {
        const selectedProfessors = this.getDocumentSelectedProfessors();
        const selectedDocuments = this.getSelectedDocuments();
        const selectedAttachments = this.getSelectedAttachments();
        
        return {
            professors: selectedProfessors,
            documents: selectedDocuments,
            subject: document.getElementById('doc-email-subject')?.value,
            content: '', // HTML模板中没有doc-content元素
            send_interval: 5, // HTML模板中没有doc-send-interval元素，使用默认值
            attachments: selectedAttachments
        };
    }

    // 获取选中的附件
    getSelectedAttachments() {
        const checkboxes = document.querySelectorAll('#attachment-files-list input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.value));
    }

    // 获取选中的教授
    getSelectedProfessors() {
        const checkboxes = document.querySelectorAll('input[name="selected-professors"]:checked');
        return Array.from(checkboxes).map(cb => ({
            id: parseInt(cb.value),
            name: cb.dataset.name,
            email: cb.dataset.email,
            university: cb.dataset.university
        }));
    }

    // 获取文档模式下选中的教授
    getDocumentSelectedProfessors() {
        const selectedProfessors = [];
        
        // 检查选择模式
        const selectionMode = document.querySelector('input[name="doc-selection-mode"]:checked')?.value;
        
        if (selectionMode === 'single') {
            // 单个选择模式
            const professorSelect = document.getElementById('doc-select-professor');
            if (professorSelect && professorSelect.value) {
                const selectedOption = professorSelect.options[professorSelect.selectedIndex];
                selectedProfessors.push({
                    id: parseInt(professorSelect.value),
                    name: selectedOption.dataset.name || selectedOption.text,
                    email: selectedOption.dataset.email || '',
                    university: selectedOption.dataset.university || ''
                });
            }
        } else if (selectionMode === 'batch') {
            // 批量选择模式 - 查找复选框
            const checkboxes = document.querySelectorAll('#doc-batch-professors-list input[type="checkbox"]:checked');
            checkboxes.forEach(cb => {
                selectedProfessors.push({
                    id: parseInt(cb.value),
                    name: cb.dataset.name || '',
                    email: cb.dataset.email || '',
                    university: cb.dataset.university || ''
                });
            });
        }
        
        return selectedProfessors;
    }

    // 获取选中的文档
    getSelectedDocuments() {
        const selectedDocuments = [];
        
        // 首先尝试文档模式的单选按钮
        const docRadio = document.querySelector('input[name="doc-document"]:checked');
        if (docRadio) {
            selectedDocuments.push({
                id: parseInt(docRadio.value),
                name: docRadio.dataset.name || '',
                path: docRadio.dataset.path || ''
            });
        } else {
            // 如果没有找到，尝试其他模式的复选框
            const checkboxes = document.querySelectorAll('input[name="selected-documents"]:checked');
            checkboxes.forEach(cb => {
                selectedDocuments.push({
                    id: parseInt(cb.value),
                    name: cb.dataset.name || '',
                    path: cb.dataset.path || ''
                });
            });
        }
        
        return selectedDocuments;
    }

    // 获取附件
    getAttachments() {
        const fileInput = document.getElementById('email-attachments');
        if (!fileInput || !fileInput.files.length) {
            return [];
        }
        
        return Array.from(fileInput.files).map(file => ({
            name: file.name,
            size: file.size,
            type: file.type,
            file: file
        }));
    }

    // 验证单个邮件表单
    validateSingleEmailForm(formData) {
        if (!formData.recipient_email) {
            Utils.showToast('请输入收件人邮箱', 'error');
            return false;
        }
        
        if (!this.isValidEmail(formData.recipient_email)) {
            Utils.showToast('请输入有效的邮箱地址', 'error');
            return false;
        }
        
        if (!formData.subject) {
            Utils.showToast('请输入邮件主题', 'error');
            return false;
        }
        
        if (!formData.content) {
            Utils.showToast('请输入邮件内容', 'error');
            return false;
        }
        
        return true;
    }

    // 验证批量邮件表单
    validateBatchEmailForm(formData) {
        if (!formData.professors || formData.professors.length === 0) {
            Utils.showToast('请选择至少一个教授', 'error');
            return false;
        }
        
        if (!formData.subject) {
            Utils.showToast('请输入邮件主题', 'error');
            return false;
        }
        
        if (!formData.content) {
            Utils.showToast('请输入邮件内容', 'error');
            return false;
        }
        
        return true;
    }

    // 验证文档邮件表单
    validateDocumentEmailForm(formData) {
        if (!formData.professors || formData.professors.length === 0) {
            Utils.showToast('请选择至少一个教授', 'error');
            return false;
        }
        
        if (!formData.documents || formData.documents.length === 0) {
            Utils.showToast('请选择至少一个文档', 'error');
            return false;
        }
        
        if (!formData.subject) {
            Utils.showToast('请输入邮件主题', 'error');
            return false;
        }
        
        // 文档模式下邮件内容通过docx文件生成，不需要验证content字段
        
        return true;
    }

    // 验证邮箱格式
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // 发送单个邮件
    async sendSingleEmail(formData) {
        const response = await Utils.apiRequest('/api/send-email', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        return response;
    }

    // 发送批量邮件
    async sendBatchEmails(formData) {
        const response = await Utils.apiRequest('/api/send-batch-emails', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        return response;
    }

    // 发送文档邮件
    async sendDocumentEmails(formData) {
        const response = await Utils.apiRequest('/api/send-document-email', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        return response;
    }

    // 显示发送中状态
    showSendingState(type) {
        const sendBtn = document.querySelector(`#${type}-email-form button[type="submit"]`);
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 发送中...';
        }
        
        // 显示进度条
        const progressContainer = document.getElementById(`${type}-progress`);
        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
    }

    // 隐藏发送中状态
    hideSendingState(type) {
        const sendBtn = document.querySelector(`#${type}-email-form button[type="submit"]`);
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="bi bi-send"></i> 发送邮件';
        }
        
        // 隐藏进度条
        const progressContainer = document.getElementById(`${type}-progress`);
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
    }

    // 处理发送结果
    handleSendResult(result, type) {
        if (result.success) {
            Utils.showToast('邮件发送成功', 'success');
            
            // 清空表单
            const form = document.getElementById(`${type}-email-form`);
            if (form) {
                form.reset();
            }
            
            // 刷新发送记录
            this.loadSendRecords();
        } else {
            Utils.showToast('邮件发送失败: ' + (result.message || '未知错误'), 'error');
        }
    }

    // 处理批量发送结果
    handleBatchSendResult(result) {
        let message = `批量发送完成！\n成功: ${result.success_count} 封\n失败: ${result.failed_count} 封`;
        
        if (result.failed_emails && result.failed_emails.length > 0) {
            message += '\n\n失败的邮件:\n' + result.failed_emails.map(email => 
                `${email.recipient}: ${email.error}`
            ).join('\n');
        }
        
        Utils.showAlert(message, result.failed_count > 0 ? 'warning' : 'success');
        
        // 刷新发送记录
        this.loadSendRecords();
    }

    // 发送类型切换处理
    onSendTypeChange() {
        const selectedType = document.querySelector('input[name="send-type"]:checked')?.value;
        
        // 隐藏所有表单
        document.getElementById('single-email-section')?.style.setProperty('display', 'none');
        document.getElementById('batch-email-section')?.style.setProperty('display', 'none');
        document.getElementById('document-email-section')?.style.setProperty('display', 'none');
        
        // 显示选中的表单
        if (selectedType) {
            const section = document.getElementById(`${selectedType}-email-section`);
            if (section) {
                section.style.setProperty('display', 'block');
            }
        }
        
        // 加载相关数据
        if (selectedType === 'batch' || selectedType === 'document') {
            this.loadProfessorsForSelection();
        }
        
        if (selectedType === 'document') {
            this.loadDocumentsForSelection();
        }
    }

    // 加载教授列表供选择
    async loadProfessorsForSelection() {
        try {
            const professors = await Utils.apiRequest('/api/professors');
            this.displayProfessorsForSelection(professors);
        } catch (error) {
            console.error('加载教授列表失败:', error);
        }
    }

    // 显示教授选择列表
    displayProfessorsForSelection(professors) {
        const containers = document.querySelectorAll('.professors-selection');
        
        containers.forEach(container => {
            if (professors.length === 0) {
                container.innerHTML = '<p class="text-muted">暂无教授数据</p>';
                return;
            }
            
            let html = '<div class="row">';
            professors.forEach(professor => {
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="selected-professors" 
                                   value="${professor.id}" 
                                   data-name="${professor.name}" 
                                   data-email="${professor.email}" 
                                   data-university="${professor.university}" 
                                   id="prof-${professor.id}">
                            <label class="form-check-label" for="prof-${professor.id}">
                                <strong>${professor.name}</strong><br>
                                <small class="text-muted">${professor.email} - ${professor.university}</small>
                            </label>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            
            // 添加全选/取消全选按钮
            html = `
                <div class="mb-3">
                    <button type="button" class="btn btn-sm btn-outline-primary me-2" onclick="window.EmailSender.selectAllProfessors()">
                        全选
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="window.EmailSender.deselectAllProfessors()">
                        取消全选
                    </button>
                </div>
            ` + html;
            
            container.innerHTML = html;
        });
    }

    // 加载文档列表供选择
    async loadDocumentsForSelection() {
        try {
            const documents = await Utils.apiRequest('/api/documents');
            this.displayDocumentsForSelection(documents);
        } catch (error) {
            console.error('加载文档列表失败:', error);
        }
    }

    // 显示文档选择列表
    displayDocumentsForSelection(documents) {
        const container = document.querySelector('.documents-selection');
        if (!container) return;
        
        if (documents.length === 0) {
            container.innerHTML = '<p class="text-muted">暂无文档数据</p>';
            return;
        }
        
        let html = '<div class="row">';
        documents.forEach(document => {
            html += `
                <div class="col-md-6 mb-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" name="selected-documents" 
                               value="${document.id}" 
                               data-name="${document.name}" 
                               data-path="${document.path}" 
                               id="doc-${document.id}">
                        <label class="form-check-label" for="doc-${document.id}">
                            <strong>${document.name}</strong><br>
                            <small class="text-muted">${Utils.formatFileSize(document.size)} - ${document.type}</small>
                        </label>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        // 添加全选/取消全选按钮
        html = `
            <div class="mb-3">
                <button type="button" class="btn btn-sm btn-outline-primary me-2" onclick="window.EmailSender.selectAllDocuments()">
                    全选
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="window.EmailSender.deselectAllDocuments()">
                    取消全选
                </button>
            </div>
        ` + html;
        
        container.innerHTML = html;
    }

    // 全选教授
    selectAllProfessors() {
        const checkboxes = document.querySelectorAll('input[name="selected-professors"]');
        checkboxes.forEach(cb => cb.checked = true);
    }

    // 取消全选教授
    deselectAllProfessors() {
        const checkboxes = document.querySelectorAll('input[name="selected-professors"]');
        checkboxes.forEach(cb => cb.checked = false);
    }

    // 全选文档
    selectAllDocuments() {
        const checkboxes = document.querySelectorAll('input[name="selected-documents"]');
        checkboxes.forEach(cb => cb.checked = true);
    }

    // 取消全选文档
    deselectAllDocuments() {
        const checkboxes = document.querySelectorAll('input[name="selected-documents"]');
        checkboxes.forEach(cb => cb.checked = false);
    }

    // 处理附件变化
    handleAttachmentChange() {
        const fileInput = document.getElementById('email-attachments');
        const previewContainer = document.getElementById('attachment-preview');
        
        if (!fileInput || !previewContainer) return;
        
        const files = Array.from(fileInput.files);
        
        if (files.length === 0) {
            previewContainer.style.display = 'none';
            return;
        }
        
        let html = '<h6>附件预览:</h6><ul class="list-group">';
        files.forEach((file, index) => {
            html += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <i class="bi bi-paperclip"></i> ${file.name}
                        <small class="text-muted">(${Utils.formatFileSize(file.size)})</small>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="window.EmailSender.removeAttachment(${index})">
                        <i class="bi bi-x"></i>
                    </button>
                </li>
            `;
        });
        html += '</ul>';
        
        previewContainer.innerHTML = html;
        previewContainer.style.display = 'block';
    }

    // 移除附件
    removeAttachment(index) {
        const fileInput = document.getElementById('email-attachments');
        if (!fileInput) return;
        
        const dt = new DataTransfer();
        const files = Array.from(fileInput.files);
        
        files.forEach((file, i) => {
            if (i !== index) {
                dt.items.add(file);
            }
        });
        
        fileInput.files = dt.files;
        this.handleAttachmentChange();
    }

    // 从生成的邮件填充发送表单
    fillFromGenerated(emailContent) {
        // 切换到单个邮件发送
        const singleRadio = document.querySelector('input[name="send-type"][value="single"]');
        if (singleRadio) {
            singleRadio.checked = true;
            this.onSendTypeChange();
        }
        
        // 填充表单
        if (emailContent.recipient) {
            document.getElementById('recipient-email').value = emailContent.recipient;
        }
        
        if (emailContent.subject) {
            document.getElementById('email-subject').value = emailContent.subject;
        }
        
        if (emailContent.content) {
            document.getElementById('email-content').value = emailContent.content;
        }
    }

    // 加载发送记录
    async loadSendRecords() {
        try {
            const records = await Utils.apiRequest('/api/email-records');
            this.displaySendRecords(records);
        } catch (error) {
            console.error('加载发送记录失败:', error);
        }
    }

    // 显示发送记录
    displaySendRecords(records) {
        const container = document.getElementById('send-records');
        if (!container) return;
        
        if (records.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-envelope-x" style="font-size: 3rem;"></i>
                    <p class="mt-2">暂无发送记录</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        records.forEach(record => {
            const statusClass = record.status === 'sent' ? 'success' : 
                               record.status === 'failed' ? 'danger' : 'warning';
            const statusText = record.status === 'sent' ? '已发送' : 
                              record.status === 'failed' ? '发送失败' : '发送中';
            
            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6 class="card-title">${record.subject}</h6>
                                <p class="card-text">
                                    <i class="bi bi-person"></i> 收件人: ${record.recipient_name || record.recipient_email}<br>
                                    <i class="bi bi-envelope"></i> 邮箱: ${record.recipient_email}<br>
                                    <i class="bi bi-clock"></i> 发送时间: ${new Date(record.send_time).toLocaleString()}
                                </p>
                            </div>
                            <div class="col-md-4 text-end">
                                <span class="badge bg-${statusClass} mb-2">${statusText}</span><br>
                                <div class="btn-group-vertical btn-group-sm">
                                    <button class="btn btn-outline-primary" onclick="window.EmailSender.viewEmailContent(${record.id})">
                                        <i class="bi bi-eye"></i> 查看
                                    </button>
                                    ${record.status === 'failed' ? `
                                        <button class="btn btn-outline-warning" onclick="window.EmailSender.resendEmail(${record.id})">
                                            <i class="bi bi-arrow-clockwise"></i> 重发
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    // 查看邮件内容
    async viewEmailContent(recordId) {
        try {
            const record = await Utils.apiRequest(`/api/email-records/${recordId}`);
            
            const modal = new bootstrap.Modal(document.getElementById('viewEmailModal'));
            
            document.getElementById('view-email-subject').textContent = record.subject;
            document.getElementById('view-email-recipient').textContent = record.recipient_email;
            document.getElementById('view-email-time').textContent = new Date(record.send_time).toLocaleString();
            document.getElementById('view-email-content').innerHTML = record.content || '无内容';
            
            modal.show();
        } catch (error) {
            Utils.showToast('获取邮件内容失败: ' + error.message, 'error');
        }
    }

    // 重新发送邮件
    async resendEmail(recordId) {
        if (!confirm('确定要重新发送这封邮件吗？')) {
            return;
        }
        
        try {
            const result = await Utils.apiRequest(`/api/resend-email/${recordId}`, {
                method: 'POST'
            });
            
            if (result.success) {
                Utils.showToast('邮件重新发送成功', 'success');
                this.loadSendRecords();
            } else {
                Utils.showToast('邮件重新发送失败: ' + result.message, 'error');
            }
        } catch (error) {
            Utils.showToast('邮件重新发送失败: ' + error.message, 'error');
        }
    }
}

// 创建全局实例
window.EmailSender = new EmailSender();

// 导出全局函数供HTML调用
window.sendSingleEmail = () => {
    const form = document.getElementById('single-email-form');
    if (form) {
        form.dispatchEvent(new Event('submit'));
    }
};
window.sendBatchEmails = () => {
    const form = document.getElementById('batch-email-form');
    if (form) {
        form.dispatchEvent(new Event('submit'));
    }
};
window.sendDocumentEmails = () => {
    const form = document.getElementById('document-email-form');
    if (form) {
        form.dispatchEvent(new Event('submit'));
    }
};
window.selectAllProfessors = () => window.EmailSender.selectAllProfessors();
window.deselectAllProfessors = () => window.EmailSender.deselectAllProfessors();
window.selectAllDocuments = () => window.EmailSender.selectAllDocuments();
window.deselectAllDocuments = () => window.EmailSender.deselectAllDocuments();
window.removeAttachment = (index) => window.EmailSender.removeAttachment(index);
window.viewEmailContent = (id) => window.EmailSender.viewEmailContent(id);
window.resendEmail = (id) => window.EmailSender.resendEmail(id);