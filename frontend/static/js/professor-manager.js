/**
 * 教授管理模块 - 教授CRUD、搜索筛选、导入导出等功能
 */

class ProfessorManager {
    constructor() {
        this.initEventListeners();
    }

    // 初始化事件监听器
    initEventListeners() {
        // 教授表单提交
        const professorForm = document.getElementById('professor-form');
        if (professorForm) {
            professorForm.addEventListener('submit', this.handleProfessorSubmit.bind(this));
        }

        // 搜索和筛选
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keyup', this.filterProfessors.bind(this));
        }

        const universityFilter = document.getElementById('universityFilter');
        if (universityFilter) {
            universityFilter.addEventListener('change', this.onUniversityChange.bind(this));
        }

        const departmentFilter = document.getElementById('departmentFilter');
        if (departmentFilter) {
            departmentFilter.addEventListener('change', this.filterProfessors.bind(this));
        }

        // CSV导入相关
        const csvFileInput = document.getElementById('csv-file');
        if (csvFileInput) {
            csvFileInput.addEventListener('change', this.previewCSV.bind(this));
        }
    }

    // 处理教授表单提交
    async handleProfessorSubmit(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('prof-name').value,
            email: document.getElementById('prof-email').value,
            university: document.getElementById('prof-university').value,
            department: document.getElementById('prof-department').value,
            research_area: document.getElementById('prof-research').value,
            introduction: document.getElementById('prof-introduction').value
        };
        
        try {
            const result = await Utils.apiRequest('/api/professors', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            
            Utils.showToast('教授信息添加成功', 'success');
            document.getElementById('professor-form').reset();
            this.loadProfessors();
        } catch (error) {
            Utils.showToast('添加失败: ' + error.message, 'error');
        }
    }

    // 加载教授列表
    async loadProfessors() {
        try {
            const professors = await Utils.apiRequest('/api/professors');
            
            // 更新全局变量
            window.AppGlobals.allProfessors = professors;
            window.AppGlobals.filteredProfessors = professors;
            
            // 更新筛选选项
            this.updateUniversityFilter();
            // 只有在没有选择学校时才更新院系选项
            const universityFilter = document.getElementById('universityFilter');
            if (!universityFilter || !universityFilter.value) {
                this.updateDepartmentFilter();
            }
            
            // 显示教授列表
            this.displayProfessors(professors);
            
            console.log('教授数据加载成功:', professors.length, '条记录');
        } catch (error) {
            console.error('Error loading professors:', error);
            Utils.showToast('加载教授列表失败: ' + error.message, 'error');
        }
    }

    // 为选择框加载教授列表
    async loadProfessorsForSelect() {
        try {
            const professors = await Utils.apiRequest('/api/professors');
            
            const select = document.getElementById('select-professor');
            if (select) {
                select.innerHTML = '<option value="">请选择教授</option>';
                
                professors.forEach(prof => {
                    const option = document.createElement('option');
                    option.value = prof.id;
                    option.textContent = `${prof.name} - ${prof.university}`;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading professors for select:', error);
            Utils.showToast('加载教授列表失败: ' + error.message, 'error');
        }
    }

    // 为指定选择框加载教授列表（支持自定义选择框ID）
    async loadProfessorsForSelection(professorSelectId, universitySelectId) {
        try {
            const professors = await Utils.apiRequest('/api/professors');
            
            const filteredProfessors = professors;
            
            // 加载教授选择框
            const professorSelect = document.getElementById(professorSelectId);
            if (professorSelect) {
                professorSelect.innerHTML = '<option value="">请选择教授</option>';
                
                filteredProfessors.forEach(prof => {
                    const option = document.createElement('option');
                    option.value = prof.id;
                    // 显示更详细的信息：姓名 - 学校 - 学院 - 邮箱
                    const displayText = `${prof.name} - ${prof.university}${prof.department ? ' - ' + prof.department : ''} - ${prof.email}`;
                    option.textContent = displayText;
                    option.dataset.university = prof.university;
                    option.dataset.department = prof.department || '';
                    option.dataset.email = prof.email;
                    option.dataset.name = prof.name;
                    option.dataset.researchArea = prof.research_area || '';
                    professorSelect.appendChild(option);
                });
            }
            
            // 如果提供了大学选择框ID，也填充大学列表
            if (universitySelectId) {
                const universitySelect = document.getElementById(universitySelectId);
                if (universitySelect) {
                    const universities = [...new Set(filteredProfessors.map(prof => prof.university))].sort();
                    universitySelect.innerHTML = '<option value="">请选择大学</option>';
                    
                    universities.forEach(university => {
                        const option = document.createElement('option');
                        option.value = university;
                        option.textContent = university;
                        universitySelect.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading professors for selection:', error);
            Utils.showToast('加载教授列表失败: ' + error.message, 'error');
        }
    }

    // 按学院加载教授列表（用于批量选择）
    async loadProfessorsByDepartment(universitySelectId, departmentSelectId, professorListId) {
        try {
            const professors = await Utils.apiRequest('/api/professors');
            
            // 填充大学选择框
            const universitySelect = document.getElementById(universitySelectId);
            if (universitySelect) {
                const universities = [...new Set(professors.map(prof => prof.university))].sort();
                universitySelect.innerHTML = '<option value="">请选择大学</option>';
                
                universities.forEach(university => {
                    const option = document.createElement('option');
                    option.value = university;
                    option.textContent = university;
                    universitySelect.appendChild(option);
                });
                
                // 监听大学选择变化
                universitySelect.onchange = () => {
                    this.updateDepartmentsByUniversity(professors, universitySelect.value, departmentSelectId, professorListId);
                };
            }
        } catch (error) {
            console.error('Error loading professors by department:', error);
            Utils.showToast('加载教授列表失败: ' + error.message, 'error');
        }
    }

    // 根据选择的大学更新学院列表
    updateDepartmentsByUniversity(professors, selectedUniversity, departmentSelectId, professorListId) {
        const departmentSelect = document.getElementById(departmentSelectId);
        const professorList = document.getElementById(professorListId);
        
        if (!departmentSelect) return;
        
        if (!selectedUniversity) {
            departmentSelect.innerHTML = '<option value="">请先选择大学</option>';
            departmentSelect.disabled = true;
            if (professorList) professorList.style.display = 'none';
            return;
        }
        
        // 获取该大学的所有学院
        const universityProfessors = professors.filter(prof => prof.university === selectedUniversity);
        const departments = [...new Set(universityProfessors.map(prof => prof.department).filter(dept => dept))].sort();
        
        departmentSelect.innerHTML = '<option value="">请选择学院</option>';
        departments.forEach(department => {
            const option = document.createElement('option');
            option.value = department;
            option.textContent = department;
            departmentSelect.appendChild(option);
        });
        
        // 添加"选择多个学院"选项
        const multiOption = document.createElement('option');
        multiOption.value = 'multiple';
        multiOption.textContent = '选择多个学院...';
        departmentSelect.appendChild(multiOption);
        
        departmentSelect.disabled = false;
        
        // 监听学院选择变化
        departmentSelect.onchange = () => {
            if (departmentSelect.value === 'multiple') {
                this.showMultipleDepartmentSelection(universityProfessors, departments, professorListId);
            } else if (departmentSelect.value) {
                this.showProfessorsByDepartment(universityProfessors, [departmentSelect.value], professorListId);
            } else {
                if (professorList) professorList.style.display = 'none';
            }
        };
    }

    // 显示多学院选择界面
    showMultipleDepartmentSelection(professors, departments, professorListId) {
        const professorList = document.getElementById(professorListId);
        if (!professorList) return;
        
        let html = '<div class="mb-3"><label class="form-label">选择学院（可多选）</label><div class="border rounded p-3">';
        
        departments.forEach(department => {
            const profCount = professors.filter(prof => prof.department === department).length;
            html += `
                <div class="form-check">
                    <input class="form-check-input department-checkbox" type="checkbox" value="${department}" id="dept-${department.replace(/\s+/g, '-')}">
                    <label class="form-check-label" for="dept-${department.replace(/\s+/g, '-')}">
                        ${department} (${profCount}位教授)
                    </label>
                </div>
            `;
        });
        
        html += '</div><button type="button" class="btn btn-primary btn-sm mt-2" onclick="window.ProfessorManager.loadSelectedDepartments()">加载选中学院的教授</button></div>';
        html += '<div id="selected-professors-container"></div>';
        
        professorList.innerHTML = html;
        professorList.style.display = 'block';
        
        // 存储教授数据和容器ID供后续使用
        this.currentProfessors = professors;
        this.currentProfessorListId = professorListId;
    }

    // 加载选中学院的教授
    loadSelectedDepartments() {
        const selectedDepartments = Array.from(document.querySelectorAll('.department-checkbox:checked')).map(cb => cb.value);
        if (selectedDepartments.length === 0) {
            Utils.showToast('请至少选择一个学院', 'warning');
            return;
        }
        
        // 使用存储的容器ID，确保在正确的模式下显示教授列表
        const professorListId = this.currentProfessorListId || 'ai-batch-professors-list';
        this.showProfessorsByDepartment(this.currentProfessors, selectedDepartments, professorListId);
    }

    // 显示指定学院的教授列表
    showProfessorsByDepartment(professors, departments, professorListId) {
        const professorList = document.getElementById(professorListId);
        if (!professorList) return;
        
        let filteredProfessors = professors.filter(prof => departments.includes(prof.department));
        
        // 过滤教授按学院
        
        if (filteredProfessors.length === 0) {
            professorList.innerHTML = '<p class="text-muted">该学院暂无教授数据</p>';
            professorList.style.display = 'block';
            return;
        }
        
        let html = '<div class="mb-3"><label class="form-label">选中的教授（可取消勾选排除）</label><div class="border rounded p-3" style="max-height: 300px; overflow-y: auto;">';
        
        // 按学院分组显示
        departments.forEach(department => {
            const deptProfessors = filteredProfessors.filter(prof => prof.department === department);
            if (deptProfessors.length > 0) {
                html += `<div class="mb-3"><h6 class="text-primary">${department}</h6>`;
                
                deptProfessors.forEach(prof => {
                    html += `
                        <div class="professor-selection-container">
                            <div class="form-check">
                                <input class="form-check-input professor-checkbox" type="checkbox" value="${prof.id}" 
                                       id="prof-${prof.id}" checked 
                                       data-name="${prof.name}" data-email="${prof.email}" data-university="${prof.university}" data-department="${prof.department || ''}">
                                <label class="form-check-label" for="prof-${prof.id}">
                                    <strong>${prof.name}</strong><br>
                                    <small class="text-muted">${prof.email}</small>
                                </label>
                            </div>
                        </div>
                    `;
                });
                
                html += '</div>';
            }
        });
        
        html += '</div><small class="text-muted">已选择 <span id="ai-selected-count">' + filteredProfessors.length + '</span> 位教授</small></div>';
        
        professorList.innerHTML = html;
        professorList.style.display = 'block';
        
        // 监听复选框变化
        document.querySelectorAll('.professor-checkbox').forEach(checkbox => {
            checkbox.onchange = this.updateSelectedCount;
        });
    }

    // 更新选中教授数量
    updateSelectedCount() {
        const selectedCount = document.querySelectorAll('.professor-checkbox:checked').length;
        const countElement = document.getElementById('ai-selected-count');
        if (countElement) {
            countElement.textContent = selectedCount;
        }
    }

    // 编辑教授
    async editProfessor(professorId) {
        try {
            const professor = await Utils.apiRequest(`/api/professors/${professorId}`);
            
            // 填充编辑表单
            document.getElementById('edit-prof-id').value = professor.id;
            document.getElementById('edit-prof-name').value = professor.name;
            document.getElementById('edit-prof-email').value = professor.email;
            document.getElementById('edit-prof-university').value = professor.university;
            document.getElementById('edit-prof-department').value = professor.department || '';
            document.getElementById('edit-prof-research').value = professor.research_area || '';
            document.getElementById('edit-prof-introduction').value = professor.introduction || '';
            document.getElementById('edit-prof-website').value = professor.website || '';
            
            // 显示编辑模态框
            const modal = new bootstrap.Modal(document.getElementById('editProfessorModal'));
            modal.show();
        } catch (error) {
            Utils.showToast('获取教授信息失败: ' + error.message, 'error');
        }
    }

    // 更新教授信息
    async updateProfessor() {
        const professorId = document.getElementById('edit-prof-id').value;
        const formData = {
            name: document.getElementById('edit-prof-name').value.trim(),
            email: document.getElementById('edit-prof-email').value.trim(),
            university: document.getElementById('edit-prof-university').value.trim(),
            department: document.getElementById('edit-prof-department').value.trim(),
            research_areas: document.getElementById('edit-prof-research').value.trim(),
            introduction: document.getElementById('edit-prof-introduction').value.trim(),
            website: document.getElementById('edit-prof-website').value.trim()
        };
        
        // 验证必填字段
        if (!formData.name || !formData.email || !formData.university) {
            Utils.showToast('请填写所有必填字段', 'error');
            return;
        }
        
        // 验证邮箱格式
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            Utils.showToast('请输入有效的邮箱地址', 'error');
            return;
        }
        
        try {
            const data = await Utils.apiRequest(`/api/professors/${professorId}`, {
                method: 'PUT',
                body: JSON.stringify(formData)
            });
            
            if (data.success) {
                Utils.showToast('教授信息更新成功', 'success');
                
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('editProfessorModal'));
                modal.hide();
                
                // 重新加载教授列表
                this.loadProfessors();
            } else {
                Utils.showToast('更新失败: ' + (data.message || '未知错误'), 'error');
            }
        } catch (error) {
            Utils.showToast('更新失败: ' + error.message, 'error');
        }
    }

    // 删除教授
    async deleteProfessor(professorId) {
        if (!confirm('确定要删除这个教授信息吗？')) {
            return;
        }
        
        try {
            await Utils.apiRequest(`/api/professors/${professorId}`, {
                method: 'DELETE'
            });
            
            Utils.showToast('教授信息删除成功', 'success');
            this.loadProfessors();
        } catch (error) {
            Utils.showToast('删除失败: ' + error.message, 'error');
        }
    }

    // 学校选择变化时的处理
    onUniversityChange() {
        this.updateDepartmentFilterByUniversity();
        this.filterProfessors();
    }

    // 根据选择的学校更新院系筛选选项
    updateDepartmentFilterByUniversity() {
        const universityFilter = document.getElementById('universityFilter')?.value || '';
        const departmentSelect = document.getElementById('departmentFilter');
        
        if (!departmentSelect) return;
        
        // 清空当前选择
        departmentSelect.value = '';
        
        if (!universityFilter) {
            // 如果没有选择学校，显示所有院系
            this.updateDepartmentFilter();
            return;
        }
        
        // 获取选定学校的所有院系
        const departments = [...new Set(window.AppGlobals.allProfessors
            .filter(p => p.university === universityFilter)
            .map(p => p.department)
            .filter(d => d && d.trim() !== '')
        )].sort();
        
        departmentSelect.innerHTML = '<option value="">所有院系</option>';
        
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            departmentSelect.appendChild(option);
        });
    }

    // 搜索和筛选教授
    filterProfessors() {
        const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
        const universityFilter = document.getElementById('universityFilter')?.value || '';
        const departmentFilter = document.getElementById('departmentFilter')?.value || '';
        
        let filtered = window.AppGlobals.allProfessors.filter(professor => {
            const matchesSearch = !searchTerm || 
                professor.name.toLowerCase().includes(searchTerm) ||
                professor.email.toLowerCase().includes(searchTerm);
            
            const matchesUniversity = !universityFilter || professor.university === universityFilter;
            const matchesDepartment = !departmentFilter || professor.department === departmentFilter;
            
            return matchesSearch && matchesUniversity && matchesDepartment;
        });
        
        window.AppGlobals.filteredProfessors = filtered;
        this.displayProfessors(filtered);
    }

    // 清除筛选
    clearFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('universityFilter').value = '';
        document.getElementById('departmentFilter').value = '';
        // 重置院系选项为所有院系
        this.updateDepartmentFilter();
        this.displayProfessors(window.AppGlobals.allProfessors);
    }

    // 更新学校筛选选项
    updateUniversityFilter() {
        const universities = [...new Set(window.AppGlobals.allProfessors.map(p => p.university))];
        const select = document.getElementById('universityFilter');
        
        if (select) {
            const currentValue = select.value;
            select.innerHTML = '<option value="">所有学校</option>';
            
            universities.forEach(uni => {
                const option = document.createElement('option');
                option.value = uni;
                option.textContent = uni;
                select.appendChild(option);
            });
            
            select.value = currentValue;
        }
    }

    // 更新院系筛选选项
    updateDepartmentFilter() {
        const departments = [...new Set(window.AppGlobals.allProfessors
            .map(p => p.department)
            .filter(d => d && d.trim() !== '')
        )];
        
        const select = document.getElementById('departmentFilter');
        
        if (select) {
            const currentValue = select.value;
            select.innerHTML = '<option value="">所有院系</option>';
            
            departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept;
                option.textContent = dept;
                select.appendChild(option);
            });
            
            select.value = currentValue;
        }
    }

    // 显示教授列表
    displayProfessors(professors) {
        const professorsList = document.getElementById('professors-list');
        
        if (!professorsList) return;
        
        if (professors.length === 0) {
            professorsList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-person-x" style="font-size: 3rem;"></i>
                    <p class="mt-2">没有找到匹配的教授信息</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        professors.forEach(professor => {
            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <h6 class="card-title">
                                    <i class="bi bi-person"></i> ${professor.name}
                                    <small class="text-muted">(${professor.university})</small>
                                </h6>
                                <p class="card-text">
                                    <i class="bi bi-envelope"></i> ${professor.email}<br>
                                    <i class="bi bi-building"></i> ${professor.department || '未指定院系'}<br>
                                    <i class="bi bi-lightbulb"></i> ${professor.research_area || '未指定研究领域'}
                                </p>
                                ${professor.introduction ? `<p class="card-text"><small class="text-muted">${professor.introduction}</small></p>` : ''}
                            </div>
                            <div class="col-md-4 d-flex align-items-center justify-content-end">
                                <div class="btn-group-vertical" role="group">
                                    <button class="btn btn-outline-primary btn-sm" onclick="window.ProfessorManager.editProfessor(${professor.id})">
                                        <i class="bi bi-pencil"></i> 编辑
                                    </button>
                                    <button class="btn btn-outline-danger btn-sm" onclick="window.ProfessorManager.deleteProfessor(${professor.id})">
                                        <i class="bi bi-trash"></i> 删除
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        professorsList.innerHTML = html;
    }

    // 导出教授信息
    async exportProfessors() {
        try {
            const universityFilter = document.getElementById('universityFilter')?.value || '';
            let url = '/api/export/professors';
            
            if (universityFilter) {
                url += `?university=${encodeURIComponent(universityFilter)}`;
            }
            
            // 使用fetch获取文件数据
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('导出失败');
            }
            
            // 获取文件名（从响应头或生成默认名称）
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'professors_export.csv';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            } else {
                // 生成带时间戳的文件名
                const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_');
                filename = `professors_export_${timestamp}.csv`;
            }
            
            // 创建blob和下载链接
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            // 创建临时下载链接并触发下载
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            
            // 清理
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);
            
            Utils.showToast('导出成功', 'success');
            
        } catch (error) {
            console.error('导出失败:', error);
            Utils.showToast('导出失败: ' + error.message, 'error');
        }
    }

    // 下载CSV模板
    downloadTemplate() {
        const csvContent = 'name,email,university,department,research_area,introduction\n# 必填字段：name(姓名), email(邮箱), university(大学), department(院系)\n# 可选字段：research_area(研究领域), introduction(教授介绍)\n张教授,zhang@university.edu,清华大学,计算机科学与技术学院,机器学习,专注于机器学习算法研究';
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'professor_template.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // 显示导入模态框
    showImportModal() {
        const modal = new bootstrap.Modal(document.getElementById('importModal'));
        modal.show();
        
        // 重置表单
        document.getElementById('csv-file').value = '';
        document.getElementById('csv-preview').innerHTML = '';
        document.getElementById('import-options').style.display = 'none';
    }

    // 预览CSV文件
    async previewCSV() {
        const fileInput = document.getElementById('csv-file');
        const file = fileInput.files[0];
        
        if (!file) {
            return;
        }
        
        if (!file.name.toLowerCase().endsWith('.csv')) {
            Utils.showToast('请选择CSV文件', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/preview/professors', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.displayCSVPreview(result);
                document.getElementById('import-options').style.display = 'block';
            } else {
                Utils.showToast('预览失败: ' + result.error, 'error');
            }
        } catch (error) {
            Utils.showToast('预览失败: ' + error.message, 'error');
        }
    }

    // 显示CSV预览
    displayCSVPreview(data) {
        const previewContainer = document.getElementById('csv-preview');
        
        if (data.errors && data.errors.length > 0) {
            let errorHtml = '<div class="alert alert-warning"><h6>发现以下问题：</h6><ul>';
            data.errors.forEach(error => {
                errorHtml += `<li>${error}</li>`;
            });
            errorHtml += '</ul></div>';
            previewContainer.innerHTML = errorHtml;
        }
        
        if (data.preview && data.preview.length > 0) {
            let tableHtml = '<h6>数据预览（前5行）：</h6><div class="table-responsive"><table class="table table-sm table-bordered">';
            
            // 表头
            tableHtml += '<thead class="table-light"><tr>';
            tableHtml += '<th>姓名</th><th>邮箱</th><th>大学</th><th>院系</th><th>研究领域</th><th>介绍</th>';
            tableHtml += '</tr></thead><tbody>';
            
            // 数据行
            data.preview.forEach(row => {
                tableHtml += '<tr>';
                tableHtml += `<td>${row.name || ''}</td>`;
                tableHtml += `<td>${row.email || ''}</td>`;
                tableHtml += `<td>${row.university || ''}</td>`;
                tableHtml += `<td>${row.department || ''}</td>`;
                tableHtml += `<td>${row.research_area || ''}</td>`;
                tableHtml += `<td>${(row.introduction || '').substring(0, 50)}${row.introduction && row.introduction.length > 50 ? '...' : ''}</td>`;
                tableHtml += '</tr>';
            });
            
            tableHtml += '</tbody></table></div>';
            tableHtml += `<p class="text-muted">共 ${data.total_rows} 行数据，有效数据 ${data.valid_rows} 行</p>`;
            
            previewContainer.innerHTML += tableHtml;
        }
    }

    // 导入CSV
    async importCSV() {
        const fileInput = document.getElementById('csv-file');
        const file = fileInput.files[0];
        
        if (!file) {
            Utils.showToast('请选择文件', 'error');
            return;
        }
        
        const skipDuplicates = document.getElementById('skip-duplicates').checked;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('skip_duplicates', skipDuplicates);
        
        try {
            const response = await fetch('/api/import/professors', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.displayImportResult(result);
                this.loadProfessors(); // 重新加载列表
            } else {
                Utils.showToast('导入失败: ' + result.error, 'error');
            }
        } catch (error) {
            Utils.showToast('导入失败: ' + error.message, 'error');
        }
    }

    // 显示导入结果
    displayImportResult(result) {
        let message = `导入完成！\n成功导入: ${result.success_count} 条\n跳过重复: ${result.duplicate_count} 条`;
        
        if (result.error_count > 0) {
            message += `\n错误: ${result.error_count} 条`;
        }
        
        if (result.errors && result.errors.length > 0) {
            message += '\n\n错误详情:\n' + result.errors.join('\n');
        }
        
        Utils.showAlert(message, result.error_count > 0 ? 'warning' : 'success');
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('importModal'));
        if (modal) {
            modal.hide();
        }
    }

    // 跳转到邮件生成页面

}

// 创建全局实例
window.ProfessorManager = new ProfessorManager();

// 导出全局函数供HTML调用
window.loadProfessors = () => window.ProfessorManager.loadProfessors();
window.loadProfessorsForSelect = () => window.ProfessorManager.loadProfessorsForSelect();
window.loadProfessorsForSelection = (professorSelectId, universitySelectId) => window.ProfessorManager.loadProfessorsForSelection(professorSelectId, universitySelectId);
window.loadProfessorsByDepartment = (universitySelectId, departmentSelectId, professorListId) => window.ProfessorManager.loadProfessorsByDepartment(universitySelectId, departmentSelectId, professorListId);
window.updateDepartmentsByUniversity = (professors, selectedUniversity, departmentSelectId, professorListId) => window.ProfessorManager.updateDepartmentsByUniversity(professors, selectedUniversity, departmentSelectId, professorListId);
window.showMultipleDepartmentSelection = (professors, departments, professorListId) => window.ProfessorManager.showMultipleDepartmentSelection(professors, departments, professorListId);
window.loadSelectedDepartments = () => window.ProfessorManager.loadSelectedDepartments();
window.showProfessorsByDepartment = (professors, departments, professorListId) => window.ProfessorManager.showProfessorsByDepartment(professors, departments, professorListId);
window.updateSelectedCount = () => window.ProfessorManager.updateSelectedCount();
window.editProfessor = (id) => window.ProfessorManager.editProfessor(id);
window.updateProfessor = () => window.ProfessorManager.updateProfessor();
window.deleteProfessor = (id) => window.ProfessorManager.deleteProfessor(id);
window.exportProfessors = () => window.ProfessorManager.exportProfessors();
window.downloadTemplate = () => window.ProfessorManager.downloadTemplate();
window.showImportModal = () => window.ProfessorManager.showImportModal();
window.importProfessors = () => window.ProfessorManager.importCSV();
window.filterProfessors = () => window.ProfessorManager.filterProfessors();
window.clearFilters = () => window.ProfessorManager.clearFilters();