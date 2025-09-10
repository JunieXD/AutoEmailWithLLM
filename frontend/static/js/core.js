/**
 * 核心模块 - 全局变量、应用初始化和通用工具函数
 */

// 全局变量
window.AppGlobals = {
    currentProfessor: null,
    generatedEmailContent: '',
    selectedProfessors: [], // 批量选择的教授列表
    emailSettings: {
        name: '',
        email: '',
        password: ''
    },
    llmSettings: {
        provider: 'openai',
        apiKey: '',
        apiBase: 'https://api.openai.com/v1',
        model: 'gpt-3.5-turbo',
        endpointId: ''
    },
    allProfessors: [],
    filteredProfessors: [],
    allEmailRecords: [],
    selectionMode: 'single',
    contentMode: 'ai',
    documentData: null
};

// 应用初始化
class AppCore {
    static init() {
        document.addEventListener('DOMContentLoaded', function() {
            AppCore.initializeApp();
        });
    }

    static initializeApp() {
        // 首先处理导航栏高亮（所有页面都需要）
        AppCore.updateNavHighlightForCurrentPage();
        
        // 检查当前页面路径并加载对应数据
        const path = window.location.pathname;
        
        // 根据页面路径加载对应的数据
        if (path === '/professors' && window.ProfessorManager) {
            window.ProfessorManager.loadProfessors();
        } else if (path === '/email-generator' && window.ProfessorManager) {
            if (window.ProfessorManager.loadProfessorsForSelection) {
                // 为AI生成模式单个选择加载教授数据
                window.ProfessorManager.loadProfessorsForSelection('ai-select-professor', null);
                // 为AI生成模式批量选择加载教授数据（按学院）
                window.ProfessorManager.loadProfessorsByDepartment('ai-select-university', 'ai-select-department', 'ai-batch-professors-list');
                // 为文档模式单个选择加载教授数据
                window.ProfessorManager.loadProfessorsForSelection('doc-select-professor', null);
                // 为文档模式批量选择加载教授数据（按学院）
                window.ProfessorManager.loadProfessorsByDepartment('doc-select-university', 'doc-select-department', 'doc-batch-professors-list');
            }
        } else if (path === '/records' && window.RecordsManager) {
            window.RecordsManager.loadEmailRecords();
        }
        
        // 检查是否在主页面（有tab-content元素的页面）
        const hasTabContent = document.querySelector('.tab-content');
        
        if (hasTabContent) {
            // 初始化标签页切换
            AppCore.initTabSwitching();
            
            // 初始化表单事件
            AppCore.initFormEvents();
            
            // 加载数据
            if (window.ProfessorManager) {
                window.ProfessorManager.loadProfessors();
            }
            if (window.RecordsManager) {
                window.RecordsManager.loadEmailRecords();
            }
            // Settings页面有自己的初始化逻辑
            
            // 根据URL路径或hash显示对应标签页
            let targetTab = 'email-generator'; // 默认标签页
            
            // 首先检查URL路径
            const path = window.location.pathname;
            if (path === '/professors') {
                targetTab = 'professors';
            } else if (path === '/email-generator') {
                targetTab = 'email-generator';
            } else if (path === '/records') {
                targetTab = 'email-records';
            } else if (path === '/settings') {
                targetTab = 'settings';
            } else {
                // 如果路径不匹配，检查hash
                const hash = window.location.hash.substring(1);
                const validTabs = ['professors', 'email-generator', 'email-records', 'settings'];
                if (validTabs.includes(hash)) {
                    targetTab = hash;
                }
            }
            
            AppCore.showTab(targetTab);
        }
    }

    // 标签页切换
    static initTabSwitching() {
        const navLinks = document.querySelectorAll('.nav-link[data-tab]');
        
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const tabName = this.getAttribute('data-tab');
                AppCore.showTab(tabName);
                
                // 更新导航状态
                navLinks.forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    static showTab(tabName) {
        // 隐藏所有标签页内容
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => {
            content.classList.remove('active');
        });
        
        // 显示指定标签页
        const targetTab = document.getElementById(tabName);
        if (targetTab) {
            targetTab.classList.add('active');
        }
        
        // 更新导航栏高亮
        AppCore.updateNavHighlight(tabName);
        
        // 根据标签页加载相应数据
        switch(tabName) {
            case 'professors':
                if (window.ProfessorManager) {
                    window.ProfessorManager.loadProfessors();
                }
                break;
            case 'email-generator':
                if (window.ProfessorManager && window.ProfessorManager.loadProfessorsForSelection) {
                    // 为AI生成模式单个选择加载教授数据
                    window.ProfessorManager.loadProfessorsForSelection('ai-select-professor', null);
                    // 为AI生成模式批量选择加载教授数据（按学院）
                    window.ProfessorManager.loadProfessorsByDepartment('ai-select-university', 'ai-select-department', 'ai-batch-professors-list');
                    // 为文档模式单个选择加载教授数据
                     window.ProfessorManager.loadProfessorsForSelection('doc-select-professor', null);
                     // 为文档模式批量选择加载教授数据（按学院）
                     window.ProfessorManager.loadProfessorsByDepartment('doc-select-university', 'doc-select-department', 'doc-batch-professors-list');
                }
                if (window.EmailGenerator) {
                    // 为AI生成模式加载用户
                    if (window.EmailGenerator.loadUsersForAI) {
                        window.EmailGenerator.loadUsersForAI();
                    }
                    // 为文档模式加载用户
                    if (window.EmailGenerator.loadUsersForDocument) {
                        window.EmailGenerator.loadUsersForDocument();
                    }
                }
                break;
            case 'email-records':
                if (window.RecordsManager) {
                    window.RecordsManager.loadEmailRecords();
                }
                break;
        }
    }

    // 更新导航栏高亮
    static updateNavHighlight(tabName) {
        // 移除所有导航链接的active类
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        // 根据当前标签页添加对应导航链接的active类
        let targetHref = '';
        switch(tabName) {
            case 'professors':
                targetHref = '/professors';
                break;
            case 'email-generator':
                targetHref = '/email-generator';
                break;
            case 'email-records':
                targetHref = '/records';
                break;
            case 'settings':
                targetHref = '/settings';
                break;
        }
        
        if (targetHref) {
            const activeLink = document.querySelector(`.navbar-nav .nav-link[href="${targetHref}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
    }

    // 根据当前页面路径更新导航栏高亮
    static updateNavHighlightForCurrentPage() {
        // 移除所有导航链接的active类
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        // 根据当前页面路径设置高亮
        const currentPath = window.location.pathname;
        const targetLink = document.querySelector(`.navbar-nav .nav-link[href="${currentPath}"]`);
        if (targetLink) {
            targetLink.classList.add('active');
        }
    }

    // 初始化表单事件
    static initFormEvents() {
        // 内容生成方式切换
        const contentModeRadios = document.querySelectorAll('input[name="content-mode"]');
        contentModeRadios.forEach(radio => {
            radio.addEventListener('change', AppCore.handleContentModeChange);
        });
    }

    // 内容生成方式切换处理
    static handleContentModeChange(event) {
        const mode = event.target.value;
        const documentSection = document.getElementById('user-documents');
        const llmSection = document.getElementById('llm-generation-section');
        const generateBtn = document.getElementById('generate-email-btn');
        
        if (mode === 'document') {
            documentSection.style.display = 'block';
            llmSection.style.display = 'none';
            generateBtn.innerHTML = '<i class="bi bi-send"></i> 发送邮件';
        } else {
            documentSection.style.display = 'none';
            llmSection.style.display = 'block';
            generateBtn.innerHTML = '<i class="bi bi-magic"></i> 生成邮件';
        }
    }
}

// 通用工具函数
class Utils {
    // 显示Toast提示
    static showToast(message, type = 'info') {
        // 创建toast容器（如果不存在）
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // 创建toast元素
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'primary'}" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // 显示toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 3000
        });
        toast.show();
        
        // 自动清理
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }

    // 显示Alert提示
    static showAlert(message, type = 'info') {
        // 创建提示框
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // 添加到页面
        document.body.appendChild(alertDiv);
        
        // 自动移除
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // 格式化文件大小
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 格式化日期时间
    static formatDateTime(dateString) {
        return new Date(dateString).toLocaleString('zh-CN');
    }

    // 获取状态文本
    static getStatusText(status) {
        const statusMap = {
            'pending': '待发送',
            'sent': '已发送',
            'failed': '发送失败'
        };
        return statusMap[status] || status;
    }

    // 表单验证错误显示
    static showValidationError(element, message) {
        // 移除之前的错误状态
        Utils.clearValidationError(element);
        
        // 添加错误样式
        element.classList.add('is-invalid');
        
        // 创建错误提示
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        // 插入错误提示
        element.parentNode.appendChild(errorDiv);
    }

    static clearValidationError(element) {
        element.classList.remove('is-invalid');
        const errorDiv = element.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    // API请求封装
    static async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                // 尝试解析错误响应中的JSON信息
                try {
                    const errorData = await response.json();
                    if (errorData.error) {
                        throw new Error(errorData.error);
                    }
                } catch (jsonError) {
                    // 如果无法解析JSON，使用默认错误信息
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
}

// 导出到全局
window.AppCore = AppCore;
window.Utils = Utils;

// 自动初始化
AppCore.init();