/**
 * 邮件模板管理模块 - 模板CRUD和模板应用功能
 */

class TemplateManager {
    constructor() {
        this.templates = [];
        this.initEventListeners();
    }

    // 初始化事件监听器
    initEventListeners() {
        // 模板相关事件监听器可以在这里添加
        console.log('TemplateManager initialized');
    }

    // 获取所有模板
    async getTemplates() {
        try {
            const response = await Utils.apiRequest('/api/templates');
            this.templates = response;
            return this.templates;
        } catch (error) {
            console.error('获取模板失败:', error);
            return [];
        }
    }

    // 创建新模板
    async createTemplate(templateData) {
        try {
            const response = await Utils.apiRequest('/api/templates', {
                method: 'POST',
                body: JSON.stringify(templateData)
            });
            Utils.showToast('模板创建成功', 'success');
            return response;
        } catch (error) {
            console.error('创建模板失败:', error);
            Utils.showToast('创建模板失败: ' + error.message, 'error');
            throw error;
        }
    }

    // 更新模板
    async updateTemplate(templateId, templateData) {
        try {
            const response = await Utils.apiRequest(`/api/templates/${templateId}`, {
                method: 'PUT',
                body: JSON.stringify(templateData)
            });
            Utils.showToast('模板更新成功', 'success');
            return response;
        } catch (error) {
            console.error('更新模板失败:', error);
            Utils.showToast('更新模板失败: ' + error.message, 'error');
            throw error;
        }
    }

    // 删除模板
    async deleteTemplate(templateId) {
        try {
            await Utils.apiRequest(`/api/templates/${templateId}`, {
                method: 'DELETE'
            });
            Utils.showToast('模板删除成功', 'success');
        } catch (error) {
            console.error('删除模板失败:', error);
            Utils.showToast('删除模板失败: ' + error.message, 'error');
            throw error;
        }
    }

    // 获取单个模板
    async getTemplate(templateId) {
        try {
            return await Utils.apiRequest(`/api/templates/${templateId}`);
        } catch (error) {
            console.error('获取模板失败:', error);
            throw error;
        }
    }
}

// 全局实例
window.TemplateManager = new TemplateManager();

// 导出全局函数
window.getTemplates = () => window.TemplateManager.getTemplates();
window.createTemplate = (data) => window.TemplateManager.createTemplate(data);
window.updateTemplate = (id, data) => window.TemplateManager.updateTemplate(id, data);
window.deleteTemplate = (id) => window.TemplateManager.deleteTemplate(id);
window.getTemplate = (id) => window.TemplateManager.getTemplate(id);