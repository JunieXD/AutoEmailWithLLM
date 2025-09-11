// 全局变量
let currentEditingUserId = null;
let users = [];
let userFiles = []; // 存储当前用户的文件列表
let fileCounter = 0; // 文件计数器，用于生成唯一ID

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initFileUploads();
    initFormEvents();
    loadUsers();
});

// 初始化文件上传
function initFileUploads() {
    const hiddenFileInput = document.getElementById('hiddenFileInput');
    hiddenFileInput.addEventListener('change', handleMultipleFileSelect);
}

// 添加文件上传
function addFileUpload(fileType) {
    const hiddenFileInput = document.getElementById('hiddenFileInput');
    hiddenFileInput.setAttribute('data-file-type', fileType);
    
    // 根据文件类型设置接受的文件格式
    switch(fileType) {
        case 'cover_letter':
            hiddenFileInput.setAttribute('accept', '.docx,.doc');
            break;
        case 'resume':
            hiddenFileInput.setAttribute('accept', '.pdf,.docx,.doc');
            break;
        case 'transcript':
            hiddenFileInput.setAttribute('accept', '.pdf,.jpg,.jpeg,.png,.docx,.doc');
            break;
        case 'other':
            hiddenFileInput.setAttribute('accept', '.pdf,.docx,.doc,.txt,.jpg,.jpeg,.png');
            break;
        default:
            hiddenFileInput.setAttribute('accept', '.pdf,.docx,.doc,.txt,.jpg,.jpeg,.png');
    }
    
    hiddenFileInput.click();
}

// 处理多文件选择
function handleMultipleFileSelect(e) {
    const files = Array.from(e.target.files);
    const fileType = e.target.getAttribute('data-file-type');
    
    if (files.length === 0) return;
    
    files.forEach(file => {
        if (validateFile(file, fileType)) {
            addFileToList(file, fileType);
        }
    });
    
    // 清空文件输入框
    e.target.value = '';
    updateFilesDisplay();
}

// 验证文件
function validateFile(file, fileType) {
    const fileName = file.name.toLowerCase();
    const fileSize = file.size;
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    // 检查文件大小
    if (fileSize > maxSize) {
        showAlert(`文件 "${file.name}" 超过10MB限制`, 'danger');
        return false;
    }
    
    // 检查文件格式
    let allowedExtensions = [];
    switch(fileType) {
        case 'cover_letter':
            allowedExtensions = ['.docx', '.doc'];
            break;
        case 'resume':
            allowedExtensions = ['.pdf', '.docx', '.doc'];
            break;
        case 'transcript':
            allowedExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.doc'];
            break;
        case 'other':
            allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png'];
            break;
    }
    
    const isValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    if (!isValidExtension) {
        showAlert(`文件 "${file.name}" 格式不支持，支持格式: ${allowedExtensions.join(', ')}`, 'danger');
        return false;
    }
    
    return true;
}

// 添加文件到列表
function addFileToList(file, fileType) {
    const fileId = `file_${++fileCounter}`;
    const fileObj = {
        id: fileId,
        file: file,
        name: file.name,
        type: fileType,
        size: file.size
    };
    
    userFiles.push(fileObj);
}

// 更新文件显示
function updateFilesDisplay() {
    const filesList = document.getElementById('filesList');
    const noFilesMessage = document.getElementById('noFilesMessage');
    
    if (userFiles.length === 0) {
        noFilesMessage.style.display = 'block';
        // 清空除了noFilesMessage之外的内容
        Array.from(filesList.children).forEach(child => {
            if (child.id !== 'noFilesMessage') {
                child.remove();
            }
        });
        return;
    }
    
    noFilesMessage.style.display = 'none';
    
    // 清空现有文件显示
    Array.from(filesList.children).forEach(child => {
        if (child.id !== 'noFilesMessage') {
            child.remove();
        }
    });
    
    // 添加文件项
    userFiles.forEach(fileObj => {
        const fileItem = createFileItem(fileObj);
        filesList.appendChild(fileItem);
    });
}

// 创建文件项
function createFileItem(fileObj) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item d-flex align-items-center justify-content-between p-2 mb-2 border rounded';
    fileItem.style.backgroundColor = '#ffffff';
    
    const fileTypeColors = {
        'cover_letter': 'primary',
        'resume': 'success', 
        'transcript': 'info',
        'other': 'secondary'
    };
    
    const fileTypeNames = {
        'cover_letter': '套磁信',
        'resume': '简历',
        'transcript': '成绩单', 
        'other': '其他文件'
    };
    
    const fileTypeIcons = {
        'cover_letter': 'bi-file-earmark-text',
        'resume': 'bi-file-earmark-person',
        'transcript': 'bi-file-earmark-bar-graph',
        'other': 'bi-file-earmark'
    };
    
    const color = fileTypeColors[fileObj.type] || 'secondary';
    const typeName = fileTypeNames[fileObj.type] || '文件';
    const icon = fileTypeIcons[fileObj.type] || 'bi-file-earmark';
    
    fileItem.innerHTML = `
        <div class="d-flex align-items-center flex-grow-1">
            <i class="bi ${icon} fs-4 text-${color} me-3"></i>
            <div>
                <div class="fw-medium">${fileObj.name}</div>
                <small class="text-muted">
                    <span class="badge bg-${color} me-2">${typeName}</span>
                    ${formatFileSize(fileObj.size)}
                </small>
            </div>
        </div>
        <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeFile('${fileObj.id}')">
            <i class="bi bi-trash"></i>
        </button>
    `;
    
    return fileItem;
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 移除文件
async function removeFile(fileId) {
    const fileToRemove = userFiles.find(file => file.id === fileId);
    if (!fileToRemove) {
        console.error('文件不存在:', fileId);
        return;
    }
    
    // 如果是服务器文件，需要调用API删除
    if (fileToRemove.isServerFile && fileToRemove.serverId) {
        try {
            const response = await fetch(`/api/users/${currentEditingUserId}/files/${fileToRemove.serverId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                showAlert(result.error || '删除文件失败', 'danger');
                return;
            }
            
            showAlert('文件删除成功', 'success');
        } catch (error) {
            console.error('删除文件失败:', error);
            showAlert('删除文件失败，请检查网络连接', 'danger');
            return;
        }
    }
    
    // 从本地数组中移除文件
    userFiles = userFiles.filter(file => file.id !== fileId);
    updateFilesDisplay();
}

// 加载用户文件
async function loadUserFiles(userId) {
    if (!userId) {
        userFiles = [];
        updateFilesDisplay();
        return;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}/files`);
        const data = await response.json();
        
        if (response.ok) {
            // 将服务器返回的文件转换为前端格式
            userFiles = data.map(file => ({
                id: `server_${file.id}`,
                serverId: file.id,
                name: file.filename,
                type: file.file_type,
                size: file.file_size || 0,
                isServerFile: true
            }));
            updateFilesDisplay();
        } else {
            console.error('加载用户文件失败:', data.error);
            userFiles = [];
            updateFilesDisplay();
        }
    } catch (error) {
        console.error('加载用户文件失败:', error);
        userFiles = [];
        updateFilesDisplay();
    }
}

// 初始化表单事件
function initFormEvents() {
    const userForm = document.getElementById('userForm');
    userForm.addEventListener('submit', handleUserSubmit);
    
    // 模态框关闭时重置表单
    const userModal = document.getElementById('userModal');
    userModal.addEventListener('hidden.bs.modal', resetForm);
}

// 处理用户表单提交
async function handleUserSubmit(e) {
    e.preventDefault();
    
    const saveBtn = document.getElementById('saveUserBtn');
    const spinner = saveBtn.querySelector('.spinner-border');
    
    try {
        saveBtn.disabled = true;
        spinner.style.display = 'inline-block';
        
        const formData = new FormData(e.target);
        
        // 添加新上传的文件到FormData
        userFiles.forEach((fileObj, index) => {
            if (fileObj.file && !fileObj.isServerFile) {
                formData.append('files', fileObj.file);
                formData.append(`file_types`, fileObj.type);
            }
        });
        
        let url = '/api/users';
        let method = 'POST';
        
        if (currentEditingUserId) {
            url = `/api/users/${currentEditingUserId}`;
            method = 'PUT';
        }
        
        const response = await fetch(url, {
            method: method,
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
            loadUsers();
        } else {
            if (result.errors) {
                showAlert(result.errors.join('<br>'), 'danger');
            } else {
                showAlert(result.error || '操作失败', 'danger');
            }
        }
        
    } catch (error) {
        console.error('提交用户信息失败:', error);
        showAlert('提交失败，请检查网络连接', 'danger');
    } finally {
        saveBtn.disabled = false;
        spinner.style.display = 'none';
    }
}

// 加载用户列表
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const data = await response.json();
        
        if (response.ok) {
            users = data;
            displayUsers(users);
        } else {
            showAlert('加载用户列表失败', 'danger');
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
        showAlert('加载用户列表失败，请检查网络连接', 'danger');
    }
}

// 显示用户列表
function displayUsers(userList) {
    const userListContainer = document.getElementById('userList');
    
    if (userList.length === 0) {
        userListContainer.innerHTML = `
            <div class="col-12">
                <div class="text-center py-5">
                    <i class="bi bi-people fs-1 text-muted"></i>
                    <p class="text-muted mt-3">暂无用户，点击右上角添加用户</p>
                </div>
            </div>
        `;
        return;
    }
    
    userListContainer.innerHTML = userList.map(user => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card user-card h-100 position-relative">
                ${user.is_default ? '<span class="badge bg-success default-badge">默认</span>' : ''}
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <div class="bg-primary text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 50px; height: 50px;">
                            <i class="bi bi-person-fill fs-4"></i>
                        </div>
                        <div class="ms-3">
                            <h5 class="card-title mb-1">${user.name}</h5>
                            <p class="card-text text-muted small mb-0">${user.email}</p>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        ${user.smtp_server ? `<p class="small mb-1"><i class="bi bi-server me-1"></i>SMTP: ${user.smtp_server}:${user.smtp_port || 587}</p>` : ''}
                        ${user.description ? `<p class="small mb-1"><i class="bi bi-info-circle me-1"></i>${user.description}</p>` : ''}
                        ${user.cover_letter_path ? '<p class="small mb-1"><i class="bi bi-file-earmark-text me-1 text-success"></i>已上传套磁信</p>' : ''}
                        ${user.resume_path ? '<p class="small mb-1"><i class="bi bi-file-earmark-pdf me-1 text-danger"></i>已上传简历</p>' : ''}
                    </div>
                    
                    <div class="d-flex gap-2">
                        <button class="btn btn-outline-primary btn-sm flex-fill" onclick="editUser(${user.id})">
                            <i class="bi bi-pencil me-1"></i>编辑
                        </button>
                        ${!user.is_default ? `
                            <button class="btn btn-outline-success btn-sm" onclick="setDefaultUser(${user.id})" title="设为默认">
                                <i class="bi bi-star"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-outline-danger btn-sm" onclick="deleteUser(${user.id}, '${user.name}')" title="删除">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="card-footer text-muted small">
                    创建时间: ${Utils.formatDateTime(user.created_at)}
                </div>
            </div>
        </div>
    `).join('');
}

// 编辑用户
function editUser(userId) {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    currentEditingUserId = userId;
    
    // 填充表单
    document.getElementById('userName').value = user.name || '';
    document.getElementById('userEmail').value = user.email || '';
    // 编辑时不填充邮箱授权码，保持为空让用户选择是否更新
    document.getElementById('emailPassword').value = '';
    document.getElementById('smtpServer').value = user.smtp_server || '';
    document.getElementById('smtpPort').value = user.smtp_port || '';
    document.getElementById('description').value = user.description || '';
    
    // 编辑模式下邮箱授权码不是必填的
    const emailPasswordField = document.getElementById('emailPassword');
    emailPasswordField.removeAttribute('required');
    emailPasswordField.placeholder = '留空则保持原密码不变';
    
    // 加载用户文件
    loadUserFiles(userId);
    
    // 更新模态框标题
    document.getElementById('userModalTitle').textContent = '编辑用户';
    
    // 显示模态框
    new bootstrap.Modal(document.getElementById('userModal')).show();
}

// 删除用户
function deleteUser(userId, userName) {
    document.getElementById('deleteUserName').textContent = userName;
    
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    deleteModal.show();
    
    document.getElementById('confirmDeleteBtn').onclick = async function() {
        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showAlert(result.message, 'success');
                deleteModal.hide();
                loadUsers();
            } else {
                showAlert(result.error || '删除失败', 'danger');
            }
        } catch (error) {
            console.error('删除用户失败:', error);
            showAlert('删除失败，请检查网络连接', 'danger');
        }
    };
}

// 设置默认用户
async function setDefaultUser(userId) {
    try {
        const response = await fetch(`/api/users/${userId}/set-default`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            loadUsers();
        } else {
            showAlert(result.error || '设置失败', 'danger');
        }
    } catch (error) {
        console.error('设置默认用户失败:', error);
        showAlert('设置失败，请检查网络连接', 'danger');
    }
}

// 重置表单
function resetForm() {
    currentEditingUserId = null;
    document.getElementById('userForm').reset();
    document.getElementById('userModalTitle').textContent = '添加用户';
    
    // 重置邮箱授权码字段为必填
    const emailPasswordField = document.getElementById('emailPassword');
    emailPasswordField.setAttribute('required', '');
    emailPasswordField.placeholder = '';
    
    // 重置文件列表
    userFiles = [];
    updateFilesDisplay();
}

// 显示提示信息（已弃用，使用Utils.showToast代替）
function showAlert(message, type) {
    // 将老版Alert调用转换为新版Toast
    const toastType = type === 'danger' ? 'error' : type;
    Utils.showToast(message, toastType);
}