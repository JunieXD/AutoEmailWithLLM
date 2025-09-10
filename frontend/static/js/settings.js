// 设置页面JavaScript逻辑

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeSettings();
    bindEventListeners();
    loadCurrentSettings();
});

// 初始化设置页面
function initializeSettings() {
    console.log('设置页面初始化完成');
}

// 绑定事件监听器
function bindEventListeners() {
    // 文件上传设置保存按钮
    const uploadSaveBtn = document.getElementById('save-upload-settings');
    if (uploadSaveBtn) {
        uploadSaveBtn.addEventListener('click', saveUploadSettings);
    }

    // 日志设置保存按钮
    const logSaveBtn = document.getElementById('save-log-settings');
    if (logSaveBtn) {
        logSaveBtn.addEventListener('click', saveLogSettings);
    }

    // 数据库测试连接按钮
    const testDbBtn = document.getElementById('test-db-connection');
    if (testDbBtn) {
        testDbBtn.addEventListener('click', testDatabaseConnection);
    }
}

// 加载当前设置
function loadCurrentSettings() {
    // 加载数据库信息
    fetch('/api/database/info')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('database-path').value = data.data.database_path || 'auto_email.db';
                document.getElementById('db-status').textContent = data.data.connection_status || '未知';
                
                // 根据连接状态设置样式
                const statusElement = document.getElementById('db-status');
                if (data.data.connection_status === '已连接') {
                    statusElement.className = 'badge bg-success me-3';
                } else {
                    statusElement.className = 'badge bg-danger me-3';
                }
            }
        })
        .catch(error => console.error('加载数据库信息失败:', error));
}

// 保存文件上传设置
function saveUploadSettings() {
    const maxFileSize = document.getElementById('max-file-size').value;
    
    const data = {
        max_file_size: parseInt(maxFileSize)
    };

    fetch('/api/settings/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('文件上传设置保存成功', 'success');
        } else {
            showAlert('文件上传设置保存失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('保存文件上传设置失败:', error);
        showAlert('保存文件上传设置时发生错误', 'danger');
    });
}

// 保存日志设置
function saveLogSettings() {
    const logLevel = document.getElementById('log-level').value;
    const logFile = document.getElementById('log-file').value;
    const consoleLog = document.getElementById('console-log').checked;
    
    const data = {
        log_level: logLevel,
        log_file: logFile,
        console_log: consoleLog
    };

    fetch('/api/settings/log', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('日志设置保存成功', 'success');
        } else {
            showAlert('日志设置保存失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('保存日志设置失败:', error);
        showAlert('保存日志设置时发生错误', 'danger');
    });
}

// 测试数据库连接
function testDatabaseConnection() {
    const testBtn = document.getElementById('test-db-connection');
    testBtn.disabled = true;
    testBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 测试中...';

    fetch('/api/database/test', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('数据库连接测试成功', 'success');
            // 更新连接状态
            const statusElement = document.getElementById('db-status');
            statusElement.textContent = '已连接';
            statusElement.className = 'badge bg-success me-3';
        } else {
            showAlert('数据库连接测试失败: ' + data.message, 'danger');
            // 更新连接状态
            const statusElement = document.getElementById('db-status');
            statusElement.textContent = '连接失败';
            statusElement.className = 'badge bg-danger me-3';
        }
    })
    .catch(error => {
        console.error('测试数据库连接失败:', error);
        showAlert('测试数据库连接时发生错误', 'danger');
        // 更新连接状态
        const statusElement = document.getElementById('db-status');
        statusElement.textContent = '连接错误';
        statusElement.className = 'badge bg-danger me-3';
    })
    .finally(() => {
        testBtn.disabled = false;
        testBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 测试连接';
    });
}

// 显示提示信息
function showAlert(message, type) {
    // 创建提示框
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 插入到页面顶部
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 3秒后自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}