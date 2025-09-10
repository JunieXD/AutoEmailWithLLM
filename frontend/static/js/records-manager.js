/**
 * 邮件记录管理模块
 */

class RecordsManager {
    constructor() {
        this.allRecords = [];
        this.filteredRecords = [];
        this.initEventListeners();
    }

    // 初始化事件监听器
    initEventListeners() {
        // 这里可以添加其他事件监听器
    }

    // 加载邮件记录
    async loadEmailRecords() {
        try {
            const records = await Utils.apiRequest('/api/email-records');
            this.allRecords = records;
            this.filteredRecords = records;
            this.displayEmailRecords(records);
            this.updateRecordsCount(records.length);
            this.populateUniversityFilter(records);
            this.populateDepartmentFilter(records);
        } catch (error) {
            console.error('加载邮件记录失败:', error);
            Utils.showToast('加载邮件记录失败: ' + error.message, 'error');
        }
    }

    // 显示邮件记录
    displayEmailRecords(records) {
        const container = document.getElementById('email-records-list');
        if (!container) return;

        if (records.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-envelope-x" style="font-size: 3rem;"></i>
                    <p class="mt-2">暂无邮件记录</p>
                </div>
            `;
            return;
        }

        let html = '';
        records.forEach(record => {
            const statusClass = record.status === 'sent' ? 'success' : 
                               record.status === 'failed' ? 'danger' : 'warning';
            const statusText = record.status === 'sent' ? '已发送' : 
                              record.status === 'failed' ? '发送失败' : '待发送';
            
            const sentTime = record.sent_at ? 
                new Date(record.sent_at).toLocaleString('zh-CN') : 
                new Date(record.created_at).toLocaleString('zh-CN');

            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6 class="card-title">${record.subject}</h6>
                                <p class="card-text">
                                    <i class="bi bi-person"></i> 教授: ${record.professor_name}<br>
                                    <i class="bi bi-envelope"></i> 邮箱: ${record.professor_email}<br>
                                    <i class="bi bi-building"></i> 学校: ${record.professor_university}<br>
                                    <i class="bi bi-person-circle"></i> 发送人: ${record.sender_name} (${record.sender_email})
                                </p>
                            </div>
                            <div class="col-md-4 text-end">
                                <span class="badge bg-${statusClass} mb-2">${statusText}</span><br>
                                <small class="text-muted">
                                    <i class="bi bi-clock"></i> ${sentTime}
                                </small><br>
                                <div class="mt-2">
                                    <button class="btn btn-outline-primary btn-sm" onclick="viewEmailDetail(${record.id})">
                                        <i class="bi bi-eye"></i> 查看详情
                                    </button>
                                    ${record.status === 'failed' ? `
                                        <button class="btn btn-outline-warning btn-sm" onclick="resendEmail(${record.id})">
                                            <i class="bi bi-arrow-clockwise"></i> 重新发送
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

    // 更新记录数量显示
    updateRecordsCount(count) {
        const countElement = document.getElementById('records-count');
        if (countElement) {
            countElement.textContent = `共 ${count} 条记录`;
        }
    }

    // 填充学校筛选选项
    populateUniversityFilter(records) {
        const universitySelect = document.getElementById('filter-university');
        if (!universitySelect) return;

        const universities = [...new Set(records.map(r => r.professor_university))].sort();
        
        // 保留默认选项
        universitySelect.innerHTML = '<option value="">所有学校</option>';
        
        universities.forEach(university => {
            const option = document.createElement('option');
            option.value = university;
            option.textContent = university;
            universitySelect.appendChild(option);
        });
    }

    // 填充学院筛选选项
    populateDepartmentFilter(records) {
        const departmentSelect = document.getElementById('filter-department');
        if (!departmentSelect) return;

        const departments = [...new Set(records.map(r => r.professor_department).filter(d => d))].sort();
        
        // 保留默认选项
        departmentSelect.innerHTML = '<option value="">所有学院</option>';
        
        departments.forEach(department => {
            const option = document.createElement('option');
            option.value = department;
            option.textContent = department;
            departmentSelect.appendChild(option);
        });
    }

    // 学校选择变化时的处理
    onUniversityChangeForRecords() {
        const selectedUniversity = document.getElementById('filter-university')?.value || '';
        this.updateDepartmentFilterByUniversity(selectedUniversity);
        this.filterEmailRecords();
    }

    // 根据选择的学校更新学院选项
    updateDepartmentFilterByUniversity(selectedUniversity) {
        const departmentSelect = document.getElementById('filter-department');
        if (!departmentSelect) return;

        // 重置学院选择
        departmentSelect.value = '';

        if (!selectedUniversity) {
            // 如果没有选择学校，显示所有学院
            this.populateDepartmentFilter(this.allRecords);
        } else {
            // 根据选择的学校筛选学院
            const filteredRecords = this.allRecords.filter(record => 
                record.professor_university === selectedUniversity
            );
            this.populateDepartmentFilter(filteredRecords);
        }
    }

    // 将HTML内容转换为纯文本
    htmlToPlainText(html) {
        // 创建一个临时的div元素
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // 获取纯文本内容
        const plainText = tempDiv.textContent || tempDiv.innerText || '';
        
        // 清理多余的空白字符
        return plainText.replace(/\s+/g, ' ').trim();
    }

    // 筛选邮件记录
    filterEmailRecords() {
        const senderFilter = document.getElementById('filter-sender')?.value.toLowerCase() || '';
        const universityFilter = document.getElementById('filter-university')?.value || '';
        const departmentFilter = document.getElementById('filter-department')?.value || '';
        const professorFilter = document.getElementById('filter-professor')?.value.toLowerCase() || '';
        const statusFilter = document.getElementById('filter-status')?.value || '';
        const dateFromFilter = document.getElementById('filter-date-from')?.value || '';
        const dateToFilter = document.getElementById('filter-date-to')?.value || '';
        const contentFilter = document.getElementById('filter-content')?.value.toLowerCase() || '';

        this.filteredRecords = this.allRecords.filter(record => {
            // 发送人筛选
            if (senderFilter && !record.sender_name.toLowerCase().includes(senderFilter)) {
                return false;
            }

            // 学校筛选
            if (universityFilter && record.professor_university !== universityFilter) {
                return false;
            }

            // 学院筛选
            if (departmentFilter && record.professor_department !== departmentFilter) {
                return false;
            }

            // 教授筛选
            if (professorFilter && !record.professor_name.toLowerCase().includes(professorFilter)) {
                return false;
            }

            // 状态筛选
            if (statusFilter && record.status !== statusFilter) {
                return false;
            }

            // 日期筛选
            const recordDate = new Date(record.sent_at || record.created_at).toISOString().split('T')[0];
            if (dateFromFilter && recordDate < dateFromFilter) {
                return false;
            }
            if (dateToFilter && recordDate > dateToFilter) {
                return false;
            }

            // 内容筛选（搜索主题和邮件内容）
            if (contentFilter) {
                const subjectMatch = record.subject.toLowerCase().includes(contentFilter);
                // 将HTML内容转换为纯文本进行搜索
                const plainTextContent = this.htmlToPlainText(record.content || '').toLowerCase();
                const contentMatch = plainTextContent.includes(contentFilter);
                
                if (!subjectMatch && !contentMatch) {
                    return false;
                }
            }

            return true;
        });

        this.displayEmailRecords(this.filteredRecords);
        this.updateRecordsCount(this.filteredRecords.length);
    }

    // 清除筛选条件
    clearEmailFilters() {
        document.getElementById('filter-sender').value = '';
        document.getElementById('filter-university').value = '';
        document.getElementById('filter-department').value = '';
        document.getElementById('filter-professor').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-date-from').value = '';
        document.getElementById('filter-date-to').value = '';
        document.getElementById('filter-content').value = '';

        // 重置学院选项为所有学院
        this.populateDepartmentFilter(this.allRecords);

        this.filteredRecords = this.allRecords;
        this.displayEmailRecords(this.filteredRecords);
        this.updateRecordsCount(this.filteredRecords.length);
    }

    // 渲染邮件内容
    renderEmailContent(record) {
        const content = record.content || '无内容';
        
        // 检查是否为HTML格式（包含HTML标签）
        const isHtmlContent = /<[a-z][\s\S]*>/i.test(content);
        
        if (isHtmlContent) {
            // HTML格式邮件 - 直接显示HTML内容
            return `
                <div class="border p-3 mt-2" style="max-height: 300px; overflow-y: auto; padding: 15px; border: 1px solid #dee2e6; border-radius: 0.375rem; background-color: #fff; font-family: 'Times New Roman', Times, serif; font-size: 12pt; line-height: 1.6; color: #333; word-wrap: break-word;">
                    ${content}
                </div>
            `;
        } else {
            // 纯文本格式邮件
            return `
                <div class="border p-3" style="max-height: 300px; overflow-y: auto; white-space: pre-wrap; font-family: monospace; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 0.375rem;">
                    ${content}
                </div>
            `;
        }
    }

    // 查看邮件详情
    async viewEmailDetail(recordId) {
        try {
            const record = this.allRecords.find(r => r.id === recordId);
            if (!record) {
                Utils.showToast('找不到邮件记录', 'error');
                return;
            }

            // 显示邮件详情模态框
            const modal = new bootstrap.Modal(document.getElementById('emailDetailModal'));
            
            const detailContent = document.getElementById('email-detail-content');
            if (detailContent) {
                detailContent.innerHTML = `
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>邮件主题:</strong></div>
                        <div class="col-sm-9">${record.subject}</div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>收件人:</strong></div>
                        <div class="col-sm-9">${record.professor_name} &lt;${record.professor_email}&gt;</div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>学校:</strong></div>
                        <div class="col-sm-9">${record.professor_university}</div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>院系:</strong></div>
                        <div class="col-sm-9">${record.professor_department || '未填写'}</div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>发送人:</strong></div>
                        <div class="col-sm-9">${record.sender_name} &lt;${record.sender_email}&gt;</div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>发送状态:</strong></div>
                        <div class="col-sm-9">
                            <span class="badge bg-${record.status === 'sent' ? 'success' : record.status === 'failed' ? 'danger' : 'warning'}">
                                ${record.status === 'sent' ? '已发送' : record.status === 'failed' ? '发送失败' : '待发送'}
                            </span>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>发送时间:</strong></div>
                        <div class="col-sm-9">${record.sent_at ? new Date(record.sent_at).toLocaleString('zh-CN') : '未发送'}</div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-sm-3"><strong>邮件内容:</strong></div>
                        <div class="col-sm-9">
                            ${this.renderEmailContent(record)}
                        </div>
                    </div>
                `;
            }

            // 设置重新发送按钮
            const resendBtn = document.getElementById('resend-email-btn');
            if (resendBtn) {
                if (record.status === 'failed') {
                    resendBtn.style.display = 'inline-block';
                    resendBtn.onclick = () => this.resendEmail(recordId);
                } else {
                    resendBtn.style.display = 'none';
                }
            }

            modal.show();
        } catch (error) {
            console.error('查看邮件详情失败:', error);
            Utils.showToast('查看邮件详情失败: ' + error.message, 'error');
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
                this.loadEmailRecords(); // 重新加载记录
                
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('emailDetailModal'));
                if (modal) {
                    modal.hide();
                }
            } else {
                Utils.showToast('邮件重新发送失败: ' + (result.message || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('重新发送邮件失败:', error);
            Utils.showToast('重新发送邮件失败: ' + error.message, 'error');
        }
    }
}

// 全局函数，供HTML页面调用
function loadEmailRecords() {
    if (window.RecordsManager) {
        window.RecordsManager.loadEmailRecords();
    }
}

function filterEmailRecords() {
    if (window.RecordsManager) {
        window.RecordsManager.filterEmailRecords();
    }
}

function clearEmailFilters() {
    if (window.RecordsManager) {
        window.RecordsManager.clearEmailFilters();
    }
}

function viewEmailDetail(recordId) {
    if (window.RecordsManager) {
        window.RecordsManager.viewEmailDetail(recordId);
    }
}

function resendEmail(recordId) {
    if (window.RecordsManager) {
        window.RecordsManager.resendEmail(recordId);
    }
}

function onUniversityChangeForRecords() {
    if (window.RecordsManager) {
        window.RecordsManager.onUniversityChangeForRecords();
    }
}

window.RecordsManager = new RecordsManager();