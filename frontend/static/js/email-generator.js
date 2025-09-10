/**
 * 邮件生成模块 - 使用已上传文档的邮件发送功能
 */

class EmailGenerator {
    constructor() {
        this.currentEmailContent = '';
        this.initEventListeners();
    }

    // 初始化事件监听器
    initEventListeners() {
        // 注意：HTML模板中没有document-select元素，这个功能已经不需要了
        // const documentSelect = document.getElementById('document-select');
        // if (documentSelect) {
        //     documentSelect.addEventListener('change', this.onDocumentChange.bind(this));
        // }
    }

    // 文档选择变化处理（已废弃，因为HTML模板中没有document-select元素）
    // onDocumentChange() {
    //     const documentSelect = document.getElementById('document-select');
    //     if (documentSelect && documentSelect.value) {
    //         // 可以在这里添加文档预览等功能
    //         console.log('选择了文档:', documentSelect.value);
    //     }
    // }

    // 复制邮件内容
    copyEmail(index = 0) {
        const emailData = this.currentEmailPreviews && this.currentEmailPreviews[index];
        if (!emailData) {
            Utils.showToast('没有可复制的邮件内容', 'warning');
            return;
        }

        const content = emailData.content || '';
        
        navigator.clipboard.writeText(content).then(() => {
            Utils.showToast('邮件内容已复制到剪贴板', 'success');
        }).catch(err => {
            console.error('复制失败:', err);
            Utils.showToast('复制失败', 'error');
        });
    }

    // 使用邮件内容填充发送表单
    useEmail(index = 0) {
        const emailData = this.currentEmailPreviews && this.currentEmailPreviews[index];
        if (!emailData) {
            Utils.showToast('没有可使用的邮件内容', 'warning');
            return;
        }

        // 切换到邮件发送标签页
        const sendTab = document.querySelector('a[href="#email-sending"]');
        if (sendTab) {
            const tab = new bootstrap.Tab(sendTab);
            tab.show();
        }

        // 填充邮件发送表单
        if (window.EmailSender) {
            window.EmailSender.fillFromGenerated(emailData);
        }
    }

    // 切换邮件内容显示
    toggleEmailContent(index) {
        const emailData = this.currentEmailPreviews && this.currentEmailPreviews[index];
        if (!emailData) {
            Utils.showToast('邮件数据不存在', 'error');
            return;
        }

        // 重新生成邮件预览，但将指定索引的邮件设为显示完整内容
        this.showDetailedEmail = this.showDetailedEmail || new Set();
        
        if (this.showDetailedEmail.has(index)) {
            this.showDetailedEmail.delete(index);
        } else {
            this.showDetailedEmail.add(index);
        }
        
        // 重新渲染邮件预览
        displayDocumentEmail(this.currentEmailPreviews);
    }

    handleDocSelectionModeChange() {
        const singleMode = document.getElementById('doc-single-mode');
        const batchMode = document.getElementById('doc-batch-mode');
        const singleSelection = document.getElementById('doc-single-selection');
        const batchSelection = document.getElementById('doc-batch-selection');
        
        if (singleMode && singleMode.checked) {
            if (singleSelection) singleSelection.style.display = 'block';
            if (batchSelection) batchSelection.style.display = 'none';
        } else if (batchMode && batchMode.checked) {
            if (singleSelection) singleSelection.style.display = 'none';
            if (batchSelection) batchSelection.style.display = 'block';
        }
    }

    // 为文档模式加载用户列表
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
            console.error('加载用户列表失败:', error);
            Utils.showToast('加载用户列表失败: ' + error.message, 'error');
        }
    }

    handleDocSenderChange() {
        const senderSelect = document.getElementById('doc-sender-user');
        const documentSelection = document.getElementById('doc-document-selection');
        
        if (senderSelect.value) {
            // 显示文档选择区域
            documentSelection.style.display = 'block';
            // 加载该用户的文档
            this.loadUserDocuments(senderSelect.value);
        } else {
            // 隐藏文档选择区域
            documentSelection.style.display = 'none';
        }
    }

    async loadUserDocuments(userId) {
        try {
            const response = await Utils.apiRequest(`/api/users/${userId}/documents`);
            const container = document.getElementById('doc-user-documents-list');
            if (container) {
                const allDocuments = response.documents.files || [];
                // 过滤出套磁信类型的docx文件
                const documents = allDocuments.filter(doc => {
                    const filename = doc.filename.toLowerCase();
                    return (doc.file_type === 'cover_letter' || filename.includes('套磁') || filename.includes('申请')) && filename.endsWith('.docx');
                });
                
                if (documents.length === 0) {
                    container.innerHTML = '<div class="text-muted">该用户暂无上传的套磁信文档（仅显示.docx格式）</div>';
                } else {
                    let html = '';
                    documents.forEach((doc, index) => {
                        html += `
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="doc-document" id="doc-${doc.id}" value="${doc.id}" ${index === 0 ? 'checked' : ''} onchange="handleDocumentChange(${doc.id})">
                                <label class="form-check-label" for="doc-${doc.id}">
                                    ${doc.filename}
                                </label>
                            </div>
                        `;
                    });
                    container.innerHTML = html;
                    
                    // 如果有文档，自动选择第一个并加载内容
                    if (documents.length > 0) {
                        this.loadDocumentContent(documents[0].id);
                    }
                }
            }
        } catch (error) {
            console.error('加载用户文档失败:', error);
            Utils.showToast('加载用户文档失败: ' + error.message, 'error');
        }
    }

    async loadDocumentContent(documentId) {
        try {
            // 获取当前选中的用户ID
            const userSelect = document.getElementById('doc-sender-user');
            if (!userSelect || !userSelect.value) {
                console.error('未选择用户');
                return;
            }
            
            const userId = userSelect.value;
            const response = await Utils.apiRequest(`/api/users/${userId}/files/${documentId}/content?output_format=html`);
            const contentDiv = document.getElementById('doc-document-content');
            if (contentDiv && response.content) {
                contentDiv.innerHTML = response.content;
                contentDiv.style.display = 'block';
                
                // 显示教授选择区域
                const professorSection = document.getElementById('doc-professor-selection');
                if (professorSection) {
                    professorSection.style.display = 'block';
                }
                
                // 显示邮件主题设置区域
                const subjectSection = document.getElementById('doc-subject-setting');
                if (subjectSection) {
                    subjectSection.style.display = 'block';
                }
                
                // 显示附件选择区域
                const attachmentSection = document.getElementById('doc-attachment-setting');
                if (attachmentSection) {
                    attachmentSection.style.display = 'block';
                }
                
                // 加载用户文件列表
                await loadUserFilesForAttachment(userId);
            }
        } catch (error) {
            console.error('加载文档内容失败:', error);
            Utils.showToast('加载文档内容失败: ' + error.message, 'error');
        }
    }
}

// 加载用户文件用于附件选择
window.loadUserFilesForAttachment = async (userId) => {
    try {
        const response = await Utils.apiRequest(`/api/users/${userId}/files`);
        const filesList = document.getElementById('attachment-files-list');
        const noFilesMessage = document.getElementById('no-files-message');
        
        if (response && response.length > 0) {
            noFilesMessage.style.display = 'none';
            
            // 清空现有内容
            filesList.innerHTML = '';
            
            // 创建文件选择列表，过滤掉套磁信类型的文件
            response.filter(file => file.file_type !== 'cover_letter').forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'form-check mb-2';
                fileItem.innerHTML = `
                    <input class="form-check-input" type="checkbox" value="${file.id}" id="attachment-${file.id}">
                    <label class="form-check-label d-flex justify-content-between align-items-center" for="attachment-${file.id}">
                        <div>
                            <i class="bi bi-file-earmark"></i>
                            <span class="ms-2">${file.filename}</span>
                            <small class="text-muted ms-2">(${file.file_type})</small>
                        </div>
                        <small class="text-muted">${formatFileSize(file.file_size)}</small>
                    </label>
                `;
                filesList.appendChild(fileItem);
            });
        } else {
            noFilesMessage.style.display = 'block';
            // 清空其他内容
            const children = Array.from(filesList.children);
            children.forEach(child => {
                if (child.id !== 'no-files-message') {
                    child.remove();
                }
            });
        }
    } catch (error) {
        console.error('加载用户文件失败:', error);
        Utils.showToast('加载用户文件失败: ' + error.message, 'error');
    }
};

// 格式化文件大小
function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 文档邮件生成功能
window.generateDocumentEmail = async () => {
    const documentRadio = document.querySelector('input[name="doc-document"]:checked');
    const senderSelect = document.getElementById('doc-sender-user');
    const subjectInput = document.getElementById('doc-email-subject');
    // 注意：HTML模板中没有doc-additional-content元素，所以这里设为null
    const additionalInput = null; // document.getElementById('doc-additional-content');
    
    // 检查发送模式
    const singleMode = document.getElementById('doc-single-mode');
    const batchMode = document.getElementById('doc-batch-mode');
    const isBatchMode = batchMode && batchMode.checked;
    
    // 验证必填字段
    if (!documentRadio?.value) {
        Utils.showToast('请选择文档', 'error');
        return;
    }
    
    // 根据发送模式验证不同的选择字段
    if (isBatchMode) {
        const universitySelect = document.getElementById('doc-select-university');
        const departmentSelect = document.getElementById('doc-select-department');
        
        if (!universitySelect?.value) {
            Utils.showToast('请选择学校', 'error');
            return;
        }
        
        if (!departmentSelect?.value) {
            Utils.showToast('请选择学院', 'error');
            return;
        }
    } else {
        const professorSelect = document.getElementById('doc-select-professor');
        
        if (!professorSelect?.value) {
            Utils.showToast('请选择教授', 'error');
            return;
        }
    }
    
    if (!senderSelect?.value) {
        Utils.showToast('请选择发送者', 'error');
        return;
    }
    
    // 显示加载状态
    const generateBtn = document.getElementById('doc-generate-email-btn');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 生成中...';
    }
    
    try {
        let selectedProfessors = [];
        
        if (isBatchMode) {
            const departmentSelect = document.getElementById('doc-select-department');
            selectedProfessors = [departmentSelect.value]; // 批量模式使用学院ID
        } else {
            const professorSelect = document.getElementById('doc-select-professor');
            selectedProfessors = [professorSelect.value]; // 单个模式使用教授ID
        }
        
        const formData = {
            selected_documents: [documentRadio.value],
            selected_professors: selectedProfessors,
            sender_id: senderSelect.value,
            custom_subject: subjectInput?.value || '',
            additional_content: additionalInput?.value || '',
            batch_mode: isBatchMode
        };
        
        const response = await fetch('/api/generate-document-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 显示生成的邮件
            displayDocumentEmail(result.email_previews);
            Utils.showToast('邮件生成成功', 'success');
        } else {
            Utils.showToast('邮件生成失败: ' + (result.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('生成邮件失败:', error);
        Utils.showToast('邮件生成失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="bi bi-magic"></i> 生成邮件预览';
        }
    }
};

// 显示文档邮件
function displayDocumentEmail(emailPreviews) {
    const resultContainer = document.getElementById('doc-email-preview');
    if (!resultContainer) return;
    
    // 添加数据验证
    if (!emailPreviews || !Array.isArray(emailPreviews) || emailPreviews.length === 0) {
        resultContainer.innerHTML = '<div class="alert alert-danger">邮件预览数据为空</div>';
        return;
    }
    window.EmailGenerator.currentEmailPreviews = emailPreviews;
    
    // 生成多个邮件预览的HTML，只显示前两封的完整内容
    const emailsHtml = emailPreviews.map((emailData, index) => {
        const showFullContent = index < 2 || (window.EmailGenerator.showDetailedEmail && window.EmailGenerator.showDetailedEmail.has(index)); // 显示前两封或用户点击查看详情的邮件
        
        return `
        <div class="card mb-3">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <i class="bi bi-envelope"></i> 发送给 ${emailData.professor_name} (${emailData.professor_university})
                </h6>
                <div class="btn-group btn-group-sm">
                    ${index >= 2 ? `
                    <button class="btn btn-outline-info" onclick="window.EmailGenerator.toggleEmailContent(${index})">
                        <i class="bi bi-eye${showFullContent ? '-slash' : ''}"></i> ${showFullContent ? '收起详情' : '查看详情'}
                    </button>` : ''}
                </div>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label fw-bold">主题:</label>
                    <div class="border rounded p-2 bg-light">${emailData.subject || '无主题'}</div>
                </div>
                ${showFullContent ? `
                <div class="mb-3">
                    <label class="form-label fw-bold">内容:</label>
                    <div class="document-content" style="min-height: 200px; max-height: 400px; overflow-y: auto;">${emailData.content || '无内容'}</div>
                </div>` : `
                <div class="mb-3">
                    <div class="alert alert-info mb-0">
                        <i class="bi bi-info-circle"></i> 点击"查看详情"按钮查看完整邮件内容
                    </div>
                </div>`}
            </div>
        </div>
        `;
    }).join('');
    
    const html = `
        <div class="mb-3">
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> 共生成 ${emailPreviews.length} 封邮件预览
            </div>
            ${emailsHtml}
        </div>
    `;
    
    resultContainer.innerHTML = html;
    resultContainer.style.display = 'block';
    
    // 显示发送按钮容器
    const sendContainer = document.getElementById('doc-send-container');
    if (sendContainer) {
        sendContainer.style.display = 'block';
    }
}

// 初始化
// 全局函数，供HTML onchange事件调用
window.handleDocSenderChange = function() {
    if (window.EmailGenerator) {
        window.EmailGenerator.handleDocSenderChange();
    }
};

window.handleDocumentChange = function(documentId) {
    const emailGenerator = window.EmailGenerator;
    if (emailGenerator) {
        emailGenerator.loadDocumentContent(documentId);
    }
};

document.addEventListener('DOMContentLoaded', function() {
    window.EmailGenerator = new EmailGenerator();
    
    // 初始化全局函数
    window.handleDocSelectionModeChange = function(event) {
        if (window.EmailGenerator) {
            window.EmailGenerator.handleDocSelectionModeChange();
        }
    };
});