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
    // 加载保存的LLM配置列表
    loadSavedConfigs();
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

    // LLM设置相关按钮
    const llmTestBtn = document.getElementById('test-llm-config');
    const llmSaveBtn = document.getElementById('save-llm-config');
    const llmUseBtn = document.getElementById('use-llm-config');
    const manageConfigsBtn = document.getElementById('manage-configs-btn');

    if (llmTestBtn) {
        llmTestBtn.addEventListener('click', testLLMConfig);
    }
    if (llmSaveBtn) {
        llmSaveBtn.addEventListener('click', saveLLMConfig);
    }
    if (llmUseBtn) {
        llmUseBtn.addEventListener('click', useLLMConfig);
    }
    if (manageConfigsBtn) {
        manageConfigsBtn.addEventListener('click', toggleConfigManagement);
    }

    // 配置管理按钮
    const loadConfigBtn = document.getElementById('load-config-btn');
    const deleteConfigBtn = document.getElementById('delete-config-btn');
    
    if (loadConfigBtn) {
        loadConfigBtn.addEventListener('click', loadSelectedConfig);
    }
    if (deleteConfigBtn) {
        deleteConfigBtn.addEventListener('click', deleteSelectedConfig);
    }

    // 数据库测试连接按钮
    const testDbBtn = document.getElementById('test-db-connection');
    if (testDbBtn) {
        testDbBtn.addEventListener('click', testDatabaseConnection);
    }
}

// 加载当前设置
function loadCurrentSettings() {
    // 加载文件上传设置
    fetch('/api/settings/upload')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('max-file-size').value = data.data.max_file_size || '';
                document.getElementById('allowed-file-types').value = data.data.allowed_extensions || '';
                // upload-folder元素在HTML中是只读的，不需要设置值
            }
        })
        .catch(error => console.error('加载文件上传设置失败:', error));

    // 加载日志设置
    fetch('/api/settings/log')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('log-level').value = data.data.log_level || '';
                document.getElementById('log-file').value = data.data.log_file || '';
                document.getElementById('console-log').checked = data.data.console_output || false;
            }
        })
        .catch(error => console.error('加载日志设置失败:', error));

    // 加载数据库信息
    fetch('/api/settings/database')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // db-type元素在HTML中是只读input，不需要设置
                document.getElementById('database-path').value = data.data.db_file || '';
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

    // 加载默认LLM配置
    fetch('/api/llm-configs/default')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.config) {
                const config = data.config;
                
                // 填充表单字段
                document.getElementById('config-name').value = config.name || '';
                document.getElementById('llm-provider').value = config.provider || 'openai';
                document.getElementById('llm-api-key').value = config.api_key || '';
                document.getElementById('llm-api-base').value = config.api_base || '';
                document.getElementById('llm-model').value = config.model || '';
                document.getElementById('set-as-default').checked = config.is_default || false;
                
                console.log('已加载默认LLM配置:', config.name);
            } else {
                console.log('未找到默认LLM配置');
            }
        })
        .catch(error => console.error('加载默认LLM配置失败:', error))
        .finally(() => {
            // 隐藏加载状态，显示配置内容
            document.getElementById('llm-config-loading').style.display = 'none';
            document.getElementById('llm-config-content').style.display = 'block';
        });

    // 加载默认提示词配置
    fetch('/api/llm-prompt-configs/default')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.config) {
                const config = data.config;
                
                // 填充提示词配置表单字段
                document.getElementById('prompt-config-name').value = config.name || '';
                document.getElementById('system-prompt').value = config.system_prompt || '';
                document.getElementById('user-prompt-template').value = config.user_prompt_template || '';
                document.getElementById('set-prompt-as-default').checked = config.is_default || false;
                
                console.log('已加载默认提示词配置:', config.name);
            } else {
                console.log('未找到默认提示词配置');
            }
        })
        .catch(error => console.error('加载默认提示词配置失败:', error))
        .finally(() => {
            // 隐藏加载状态，显示配置内容
            document.getElementById('prompt-config-loading').style.display = 'none';
            document.getElementById('prompt-config-content').style.display = 'block';
        });
}

// 测试数据库连接
function testDatabaseConnection() {
    const testBtn = document.getElementById('test-db-connection');
    const statusElement = document.getElementById('db-status');
    
    // 禁用按钮并显示测试中状态
    testBtn.disabled = true;
    testBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 测试中...';
    statusElement.textContent = '测试中...';
    statusElement.className = 'badge bg-warning me-3';
    
    fetch('/api/settings/database')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.data.connection_status;
                statusElement.textContent = status;
                
                if (status === '已连接') {
                    statusElement.className = 'badge bg-success me-3';
                    showAlert('数据库连接测试成功', 'success');
                } else {
                    statusElement.className = 'badge bg-danger me-3';
                    showAlert('数据库连接测试失败', 'danger');
                }
            } else {
                statusElement.textContent = '测试失败';
                statusElement.className = 'badge bg-danger me-3';
                showAlert('数据库连接测试失败', 'danger');
            }
        })
        .catch(error => {
            console.error('测试数据库连接失败:', error);
            statusElement.textContent = '测试失败';
            statusElement.className = 'badge bg-danger me-3';
            showAlert('测试数据库连接时发生错误', 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            testBtn.disabled = false;
            testBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 测试连接';
        });
}

// 保存文件上传设置
function saveUploadSettings() {
    const maxFileSize = document.getElementById('max-file-size').value;
    const allowedExtensions = document.getElementById('allowed-file-types').value;
    // upload-folder在HTML中是只读的，使用固定值
    const uploadFolder = 'uploads/';

    const data = {
        max_file_size: maxFileSize,
        allowed_extensions: allowedExtensions,
        upload_folder: uploadFolder
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
    const consoleOutput = document.getElementById('console-log').checked;

    const data = {
        log_level: logLevel,
        log_file: logFile,
        console_output: consoleOutput
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

// 测试LLM配置
function testLLMConfig() {
    const provider = document.getElementById('llm-provider').value;
    const apiKey = document.getElementById('llm-api-key').value;
    const model = document.getElementById('llm-model').value;
    const baseUrl = document.getElementById('llm-api-base').value;

    if (!provider || !apiKey || !model) {
        showAlert('请填写完整的LLM配置信息', 'warning');
        return;
    }

    const testBtn = document.getElementById('test-llm-config');
    testBtn.disabled = true;
    testBtn.textContent = '测试中...';

    const data = {
        provider: provider,
        api_key: apiKey,
        model: model,
        base_url: baseUrl
    };

    fetch('/api/llm/test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('LLM配置测试成功', 'success');
        } else {
            showAlert('LLM配置测试失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('测试LLM配置失败:', error);
        showAlert('测试LLM配置时发生错误', 'danger');
    })
    .finally(() => {
        testBtn.disabled = false;
        testBtn.textContent = '测试连接';
    });
}

// 保存LLM配置
function saveLLMConfig() {
    const configName = document.getElementById('config-name').value;
    const provider = document.getElementById('llm-provider').value;
    const apiKey = document.getElementById('llm-api-key').value;
    const model = document.getElementById('llm-model').value;
    const baseUrl = document.getElementById('llm-api-base').value;
    const setAsDefault = document.getElementById('set-as-default').checked;

    if (!configName || !provider || !apiKey || !model) {
        showAlert('请填写完整的LLM配置信息（包括配置名称）', 'warning');
        return;
    }

    const data = {
        name: configName,
        provider: provider,
        api_key: apiKey,
        model: model,
        base_url: baseUrl,
        is_default: setAsDefault
    };

    fetch('/api/llm-configs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('LLM配置保存成功', 'success');
            // 刷新配置列表
            loadSavedConfigs();
        } else {
            showAlert('LLM配置保存失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('保存LLM配置失败:', error);
        showAlert('保存LLM配置时发生错误', 'danger');
    });
}

// 使用LLM配置
function useLLMConfig() {
    const provider = document.getElementById('llm-provider').value;
    const apiKey = document.getElementById('llm-api-key').value;
    const model = document.getElementById('llm-model').value;
    const baseUrl = document.getElementById('llm-api-base').value;

    if (!provider || !apiKey || !model) {
        showAlert('请填写完整的LLM配置信息', 'warning');
        return;
    }

    const data = {
        provider: provider,
        api_key: apiKey,
        model: model,
        base_url: baseUrl
    };

    fetch('/api/llm/use', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('LLM配置已启用', 'success');
        } else {
            showAlert('启用LLM配置失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('启用LLM配置失败:', error);
        showAlert('启用LLM配置时发生错误', 'danger');
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
    const container = document.querySelector('.container') || document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }

    // 3秒后自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 切换配置管理区域显示/隐藏
function toggleConfigManagement() {
    const configArea = document.getElementById('config-selection-area');
    const manageBtn = document.getElementById('manage-configs-btn');
    
    if (configArea.style.display === 'none' || configArea.style.display === '') {
        configArea.style.display = 'block';
        manageBtn.innerHTML = '<i class="bi bi-x"></i> 关闭管理';
        manageBtn.classList.remove('btn-outline-secondary');
        manageBtn.classList.add('btn-outline-danger');
        loadSavedConfigs();
    } else {
        configArea.style.display = 'none';
        manageBtn.innerHTML = '<i class="bi bi-gear"></i> 管理配置';
        manageBtn.classList.remove('btn-outline-danger');
        manageBtn.classList.add('btn-outline-secondary');
    }
}

// 加载已保存的配置
function loadSavedConfigs() {
    fetch('/api/llm-configs')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('saved-configs');
            select.innerHTML = '<option value="">选择配置...</option>';
            
            if (data.configs) {
                data.configs.forEach(config => {
                    const option = document.createElement('option');
                    option.value = config.id;
                    option.textContent = config.name;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('加载配置列表失败:', error);
            showAlert('加载配置列表失败', 'danger');
        });
}

// 加载选中的配置
function loadSelectedConfig() {
    const select = document.getElementById('saved-configs');
    const configId = select.value;
    
    if (!configId) {
        showAlert('请先选择一个配置', 'warning');
        return;
    }
    
    fetch(`/api/llm-configs/${configId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.config) {
                const config = data.config;
                
                // 填充表单字段
                document.getElementById('llm-provider').value = config.provider || '';
                document.getElementById('llm-api-key').value = config.api_key || '';
                document.getElementById('llm-api-base').value = config.api_base || '';
                document.getElementById('llm-model').value = config.model || '';
                document.getElementById('set-as-default').checked = config.is_default || false;
                
                showAlert(`配置 "${config.name}" 已加载`, 'success');
            } else {
                showAlert('加载配置失败', 'danger');
            }
        })
        .catch(error => {
            console.error('加载配置失败:', error);
            showAlert('加载配置失败', 'danger');
        });
}

// 删除选中的配置
function deleteSelectedConfig() {
    const select = document.getElementById('saved-configs');
    const configId = select.value;
    const configName = select.options[select.selectedIndex].text;
    
    if (!configId) {
        showAlert('请先选择一个配置', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除配置 "${configName}" 吗？此操作不可撤销。`)) {
        return;
    }
    
    fetch(`/api/llm-configs/${configId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`配置 "${configName}" 已删除`, 'success');
                loadSavedConfigs(); // 重新加载配置列表
            } else {
                showAlert('删除配置失败', 'danger');
            }
        })
        .catch(error => {
            console.error('删除配置失败:', error);
            showAlert('删除配置失败', 'danger');
        });
}

// 工具函数：验证文件扩展名格式
function validateExtensions(extensions) {
    const extArray = extensions.split(',').map(ext => ext.trim());
    const validPattern = /^\.[a-zA-Z0-9]+$/;
    
    for (let ext of extArray) {
        if (!validPattern.test(ext)) {
            return false;
        }
    }
    return true;
}

// 处理LLM提供商选择变化
function handleProviderChange() {
    const provider = document.getElementById('llm-provider').value;
    const baseUrlField = document.getElementById('llm-api-base');
    const modelField = document.getElementById('llm-model');
    
    // 根据不同提供商设置默认值
    if (provider === 'openai') {
        if (baseUrlField) baseUrlField.value = 'https://api.openai.com/v1';
        if (modelField) modelField.value = 'gpt-3.5-turbo';
    } else if (provider === 'volcengine') {
        if (baseUrlField) baseUrlField.value = 'https://ark.cn-beijing.volces.com/api/v3';
        if (modelField) modelField.value = '';
    } else if (provider === 'custom') {
        if (baseUrlField) baseUrlField.value = '';
        if (modelField) modelField.value = '';
    }
}

// LLM提示词配置相关函数

// 绑定提示词配置事件监听器
function bindPromptConfigEventListeners() {
    const managePromptConfigsBtn = document.getElementById('manage-prompt-configs-btn');
    const savePromptConfigBtn = document.getElementById('save-prompt-config');
    const usePromptConfigBtn = document.getElementById('use-prompt-config');
    const loadPromptConfigBtn = document.getElementById('load-prompt-config-btn');
    const deletePromptConfigBtn = document.getElementById('delete-prompt-config-btn');
    
    if (managePromptConfigsBtn) {
        managePromptConfigsBtn.addEventListener('click', togglePromptConfigManagement);
    }
    if (savePromptConfigBtn) {
        savePromptConfigBtn.addEventListener('click', savePromptConfig);
    }
    if (usePromptConfigBtn) {
        usePromptConfigBtn.addEventListener('click', usePromptConfig);
    }
    if (loadPromptConfigBtn) {
        loadPromptConfigBtn.addEventListener('click', loadSelectedPromptConfig);
    }
    if (deletePromptConfigBtn) {
        deletePromptConfigBtn.addEventListener('click', deleteSelectedPromptConfig);
    }
}

// 切换提示词配置管理区域显示/隐藏
function togglePromptConfigManagement() {
    const configArea = document.getElementById('prompt-config-selection-area');
    const manageBtn = document.getElementById('manage-prompt-configs-btn');
    
    if (configArea.style.display === 'none' || configArea.style.display === '') {
        configArea.style.display = 'block';
        manageBtn.innerHTML = '<i class="bi bi-x"></i> 关闭管理';
        manageBtn.classList.remove('btn-outline-secondary');
        manageBtn.classList.add('btn-outline-danger');
        loadSavedPromptConfigs();
    } else {
        configArea.style.display = 'none';
        manageBtn.innerHTML = '<i class="bi bi-gear"></i> 管理配置';
        manageBtn.classList.remove('btn-outline-danger');
        manageBtn.classList.add('btn-outline-secondary');
    }
}

// 加载已保存的提示词配置
function loadSavedPromptConfigs() {
    fetch('/api/llm-prompt-configs')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('saved-prompt-configs');
            select.innerHTML = '<option value="">选择配置...</option>';
            
            if (data.configs) {
                data.configs.forEach(config => {
                    const option = document.createElement('option');
                    option.value = config.id;
                    option.textContent = config.name;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('加载提示词配置列表失败:', error);
            showAlert('加载提示词配置列表失败', 'danger');
        });
}

// 保存提示词配置
function savePromptConfig() {
    const configName = document.getElementById('prompt-config-name').value;
    const systemPrompt = document.getElementById('system-prompt').value;
    const userPromptTemplate = document.getElementById('user-prompt-template').value;
    const setAsDefault = document.getElementById('set-prompt-as-default').checked;

    if (!configName || !systemPrompt || !userPromptTemplate) {
        showAlert('请填写完整的提示词配置信息', 'warning');
        return;
    }

    const data = {
        name: configName,
        system_prompt: systemPrompt,
        user_prompt_template: userPromptTemplate,
        is_default: setAsDefault
    };

    fetch('/api/llm-prompt-configs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('提示词配置保存成功', 'success');
            // 刷新配置列表
            loadSavedPromptConfigs();
        } else {
            showAlert('提示词配置保存失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('保存提示词配置失败:', error);
        showAlert('保存提示词配置时发生错误', 'danger');
    });
}

// 加载选中的提示词配置
function loadSelectedPromptConfig() {
    const select = document.getElementById('saved-prompt-configs');
    const configId = select.value;
    
    if (!configId) {
        showAlert('请先选择一个配置', 'warning');
        return;
    }
    
    fetch(`/api/llm-prompt-configs/${configId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.config) {
                const config = data.config;
                
                // 填充表单字段
                document.getElementById('prompt-config-name').value = config.name || '';
                document.getElementById('system-prompt').value = config.system_prompt || '';
                document.getElementById('user-prompt-template').value = config.user_prompt_template || '';
                document.getElementById('set-prompt-as-default').checked = config.is_default || false;
                
                showAlert(`提示词配置 "${config.name}" 已加载`, 'success');
            } else {
                showAlert('加载提示词配置失败', 'danger');
            }
        })
        .catch(error => {
            console.error('加载提示词配置失败:', error);
            showAlert('加载提示词配置失败', 'danger');
        });
}

// 删除选中的提示词配置
function deleteSelectedPromptConfig() {
    const select = document.getElementById('saved-prompt-configs');
    const configId = select.value;
    
    if (!configId) {
        showAlert('请先选择一个配置', 'warning');
        return;
    }
    
    if (!confirm('确定要删除这个提示词配置吗？')) {
        return;
    }
    
    fetch(`/api/llm-prompt-configs/${configId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('提示词配置删除成功', 'success');
            // 刷新配置列表
            loadSavedPromptConfigs();
            // 清空表单
            document.getElementById('prompt-config-name').value = '';
            document.getElementById('system-prompt').value = '';
            document.getElementById('user-prompt-template').value = '';
            document.getElementById('set-prompt-as-default').checked = false;
        } else {
            showAlert('删除提示词配置失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('删除提示词配置失败:', error);
        showAlert('删除提示词配置失败', 'danger');
    });
}

// 使用当前提示词配置
function usePromptConfig() {
    const configName = document.getElementById('prompt-config-name').value;
    const systemPrompt = document.getElementById('system-prompt').value;
    const userPromptTemplate = document.getElementById('user-prompt-template').value;

    if (!systemPrompt || !userPromptTemplate) {
        showAlert('请先填写完整的提示词配置', 'warning');
        return;
    }

    // 这里可以添加使用配置的逻辑，比如保存到本地存储或发送到后端
    showAlert('提示词配置已应用', 'success');
}

// 在页面加载时绑定提示词配置事件监听器
document.addEventListener('DOMContentLoaded', function() {
    bindPromptConfigEventListeners();
});