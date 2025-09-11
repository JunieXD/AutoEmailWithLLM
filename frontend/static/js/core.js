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
        } else if (path === '/email-generator') {
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
            // 延迟加载用户数据，确保EmailGenerator实例已创建
            setTimeout(() => {
                if (window.EmailGenerator && window.EmailGenerator.loadUsersForDocument) {
                    window.EmailGenerator.loadUsersForDocument();
                }
            }, 100);
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
                // 延迟检查EmailGenerator实例，确保它已经被创建
                setTimeout(() => {
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
                }, 100);
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
    static showToast(message, type = 'info', options = {}) {
        // 默认选项
        const defaultOptions = {
            duration: 3000,
            closable: true,
            position: 'top-right'
        };
        const config = { ...defaultOptions, ...options };
        
        // 创建toast容器（如果不存在）
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = `toast-container position-fixed ${Utils.getToastPositionClass(config.position)} p-3`;
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // 限制同时显示的toast数量
        const existingToasts = toastContainer.querySelectorAll('.toast');
        if (existingToasts.length >= 5) {
            // 移除最旧的toast
            const oldestToast = existingToasts[0];
            Utils.hideToast(oldestToast);
        }
        
        // 获取图标和颜色类
        const iconInfo = Utils.getToastIcon(type);
        const colorClass = Utils.getToastColorClass(type);
        
        // 创建toast元素
        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${colorClass}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <div class="toast-icon ${type}">
                            ${iconInfo.icon}
                        </div>
                        <span class="toast-message">${message}</span>
                    </div>
                    ${config.closable ? '<button type="button" class="btn-close btn-close-white me-2 m-auto" aria-label="关闭"></button>' : ''}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // 获取toast元素并设置事件
        const toastElement = document.getElementById(toastId);
        
        // 添加关闭按钮事件
        if (config.closable) {
            const closeBtn = toastElement.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    Utils.hideToast(toastElement);
                });
            }
        }
        
        // 显示toast with animation
        setTimeout(() => {
            toastElement.classList.add('show');
        }, 10);
        
        // 自动隐藏
        if (config.duration > 0) {
            setTimeout(() => {
                Utils.hideToast(toastElement);
            }, config.duration);
        }
        
        return toastElement;
    }
    
    // 隐藏Toast
    static hideToast(toastElement) {
        if (!toastElement || toastElement.classList.contains('hiding')) {
            return;
        }
        
        toastElement.classList.add('hiding');
        toastElement.classList.remove('show');
        
        // 等待动画完成后移除元素
        setTimeout(() => {
            if (toastElement && toastElement.parentNode) {
                toastElement.remove();
            }
        }, 300);
    }
    
    // 获取Toast位置类
    static getToastPositionClass(position) {
        switch (position) {
            case 'top-left':
                return 'top-0 start-0';
            case 'top-center':
                return 'top-0 start-50 translate-middle-x';
            case 'top-right':
            default:
                return 'top-0 end-0';
            case 'bottom-left':
                return 'bottom-0 start-0';
            case 'bottom-center':
                return 'bottom-0 start-50 translate-middle-x';
            case 'bottom-right':
                return 'bottom-0 end-0';
        }
    }
    
    // 获取Toast图标
    static getToastIcon(type) {
        const icons = {
            success: { icon: '✓', label: '成功' },
            error: { icon: '✕', label: '错误' },
            warning: { icon: '⚠', label: '警告' },
            info: { icon: 'ⓘ', label: '信息' }
        };
        return icons[type] || icons.info;
    }
    
    // 获取Toast颜色类
    static getToastColorClass(type) {
        const colorMap = {
            success: 'bg-success',
            error: 'bg-danger',
            warning: 'bg-warning',
            info: 'bg-primary'
        };
        return colorMap[type] || colorMap.info;
    }
    
    // 清除所有Toast
    static clearAllToasts() {
        const toastContainer = document.getElementById('toast-container');
        if (toastContainer) {
            const toasts = toastContainer.querySelectorAll('.toast');
            toasts.forEach(toast => {
                Utils.hideToast(toast);
            });
        }
    }

    // 显示Alert提示（已弃用，使用showToast代替）
    static showAlert(message, type = 'info') {
        // 将老版Alert调用转换为新版Toast
        const toastType = type === 'danger' ? 'error' : type;
        Utils.showToast(message, toastType);
    }

    // 格式化文件大小
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 格式化日期时间 - 使用用户本地时区
    static formatDateTime(dateInput, options = {}) {
        if (!dateInput) return '未知时间';
        
        let date;
        if (typeof dateInput === 'string') {
            let s = dateInput;
            // 若为无时区的ISO时间（如 2024-09-11T12:34:56 或带毫秒但无Z/偏移），按UTC处理以避免被当作本地时间解析
            const isoNoTZ = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/;
            if (isoNoTZ.test(s)) {
                s += 'Z';
            }
            date = new Date(s);
        } else if (dateInput instanceof Date) {
            date = dateInput;
        } else {
            return '无效时间';
        }
        
        if (isNaN(date.getTime())) return '无效时间';
        
        // 默认格式化选项
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        
        // 合并用户提供的选项
        const formatOptions = { ...defaultOptions, ...options };
        
        // 使用用户浏览器的本地时区和语言设置
        return date.toLocaleString(navigator.language || 'zh-CN', formatOptions);
    }
    
    // 格式化日期时间（简短版本）
    static formatDateTimeShort(dateString) {
        return this.formatDateTime(dateString, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    }
    
    // 格式化相对时间（如：2小时前）
    static formatRelativeTime(dateInput) {
        if (!dateInput) return '未知时间';
        
        let date;
        if (typeof dateInput === 'string') {
            let s = dateInput;
            const isoNoTZ = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/;
            if (isoNoTZ.test(s)) {
                s += 'Z';
            }
            date = new Date(s);
        } else if (dateInput instanceof Date) {
            date = dateInput;
        } else {
            return '无效时间';
        }
        
        if (isNaN(date.getTime())) return '无效时间';
        
        const now = new Date();
        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffMinutes < 1) {
            return '刚刚';
        } else if (diffMinutes < 60) {
            return `${diffMinutes}分钟前`;
        } else if (diffHours < 24) {
            return `${diffHours}小时前`;
        } else if (diffDays < 7) {
            return `${diffDays}天前`;
        } else {
            return this.formatDateTimeShort(dateInput);
        }
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