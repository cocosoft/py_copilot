import React, { useState, useEffect, useRef } from 'react';
import { categoryApi } from '../../utils/api/categoryApi';
import '../../styles/CategoryTemplateManagement.css';

const CategoryTemplateManagement = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    template_data: {
      categories: []
    },
    is_active: true
  });
  
  const [applyFormData, setApplyFormData] = useState({
    category_name: '',
    dimension: 'task_type'
  });
  
  // 导入/导出相关状态
  const [selectedTemplates, setSelectedTemplates] = useState([]);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importOverwrite, setImportOverwrite] = useState(false);
  const fileInputRef = useRef(null);
  
  // 导出模板
  const handleExportTemplates = async () => {
    try {
      const data = await categoryApi.exportTemplates(selectedTemplates.length > 0 ? selectedTemplates : null);
      
      // 创建下载链接
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `category-templates-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setSuccess('模板导出成功');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('导出模板失败:', err);
      setError('导出模板失败，请稍后重试');
    }
  };
  
  // 处理文件选择
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = JSON.parse(event.target.result);
          if (Array.isArray(data)) {
            handleImportTemplates(data);
          } else {
            setError('导入文件格式错误，请确保文件包含模板数组');
          }
        } catch (err) {
          setError('导入文件解析失败，请检查JSON格式');
        }
      };
      reader.readAsText(file);
    }
  };
  
  // 导入模板
  const handleImportTemplates = async (templatesData) => {
    try {
      const result = await categoryApi.importTemplates(templatesData, importOverwrite);
      setShowImportModal(false);
      loadTemplates();
      setSuccess(`模板导入成功：导入${result.imported_count}个，更新${result.updated_count}个，跳过${result.skipped_count}个`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('导入模板失败:', err);
      setError('导入模板失败，请稍后重试');
    }
  };
  
  // 切换模板选择
  const toggleTemplateSelection = (templateId) => {
    setSelectedTemplates(prev => {
      if (prev.includes(templateId)) {
        return prev.filter(id => id !== templateId);
      } else {
        return [...prev, templateId];
      }
    });
  };
  
  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedTemplates.length === templates.length) {
      setSelectedTemplates([]);
    } else {
      setSelectedTemplates(templates.map(template => template.id));
    }
  };
  
  // 获取所有模板
  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await categoryApi.getTemplates();
      setTemplates(data);
      setError(null);
    } catch (err) {
      console.error('获取模板失败:', err);
      setError('获取模板列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };
  
  // 初始化加载
  useEffect(() => {
    loadTemplates();
  }, []);
  
  // 处理输入变化
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // 处理模板数据变化
  const handleTemplateDataChange = (e) => {
    try {
      const value = JSON.parse(e.target.value);
      setFormData(prev => ({
        ...prev,
        template_data: value
      }));
      setError(null);
    } catch (err) {
      setError('模板数据格式错误，请检查JSON语法');
    }
  };
  
  // 处理应用表单输入变化
  const handleApplyInputChange = (e) => {
    const { name, value } = e.target;
    setApplyFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      description: '',
      template_data: {
        categories: []
      },
      is_active: true
    });
    setCurrentTemplate(null);
  };
  
  // 打开创建模态框
  const handleCreateModalOpen = () => {
    resetForm();
    setShowCreateModal(true);
  };
  
  // 打开编辑模态框
  const handleEditModalOpen = (template) => {
    setCurrentTemplate(template);
    setFormData({
      name: template.name,
      display_name: template.display_name,
      description: template.description || '',
      template_data: template.template_data || { categories: [] },
      is_active: template.is_active
    });
    setShowEditModal(true);
  };
  
  // 打开应用模态框
  const handleApplyModalOpen = (template) => {
    setCurrentTemplate(template);
    setApplyFormData({
      category_name: '',
      dimension: 'task_type'
    });
    setShowApplyModal(true);
  };
  
  // 关闭模态框
  const handleModalClose = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setShowApplyModal(false);
    resetForm();
    setError(null);
  };
  
  // 提交创建表单
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      await categoryApi.createTemplate(formData);
      setShowCreateModal(false);
      loadTemplates();
      setSuccess('模板创建成功');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('创建模板失败:', err);
      setError(err.response?.data?.detail || err.message || '创建模板失败，请检查输入并重试');
    }
  };
  
  // 提交编辑表单
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!currentTemplate) return;
    
    try {
      await categoryApi.updateTemplate(currentTemplate.id, formData);
      setShowEditModal(false);
      loadTemplates();
      setSuccess('模板更新成功');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('更新模板失败:', err);
      setError(err.response?.data?.detail || err.message || '更新模板失败，请检查输入并重试');
    }
  };
  
  // 提交应用表单
  const handleApplySubmit = async (e) => {
    e.preventDefault();
    if (!currentTemplate) return;
    
    try {
      const result = await categoryApi.applyTemplate(
        currentTemplate.id,
        applyFormData
      );
      setShowApplyModal(false);
      setSuccess('模板应用成功');
      setTimeout(() => setSuccess(null), 3000);
      // 可以在这里使用result数据创建新分类
      console.log('模板应用结果:', result);
    } catch (err) {
      console.error('应用模板失败:', err);
      setError(err.response?.data?.detail || err.message || '应用模板失败，请稍后重试');
    }
  };
  
  // 处理删除模板
  const handleDelete = async (templateId) => {
    if (window.confirm('确定要删除这个模板吗？')) {
      try {
        await categoryApi.deleteTemplate(templateId);
        loadTemplates();
        setSuccess('模板删除成功');
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error('删除模板失败:', err);
        setError(err.response?.data?.detail || err.message || '删除模板失败，可能是因为该模板正在使用中');
      }
    }
  };
  
  if (loading) {
    return <div className="template-management-loading">加载中...</div>;
  }
  
  return (
    <div className="category-template-management">
      <div className="template-header">
        <h2>分类模板管理</h2>
        <div className="header-actions">
          <button 
            className="btn btn-success" 
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
          >
            导入模板
          </button>
          <button 
            className="btn btn-info" 
            onClick={handleExportTemplates}
            disabled={loading || templates.length === 0}
          >
            导出模板
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleCreateModalOpen}
            disabled={loading}
          >
            创建模板
          </button>
          {/* 隐藏的文件输入 */}
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".json"
            onChange={handleFileChange}
          />
        </div>
      </div>
      
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      <div className="template-content">
        {templates.length === 0 ? (
          <div className="empty-state">暂无模板数据</div>
        ) : (
          <table className="template-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedTemplates.length === templates.filter(t => !t.is_system).length && templates.length > 0}
                    onChange={toggleSelectAll}
                    disabled={loading || templates.length === 0}
                  />
                </th>
                <th>名称</th>
                <th>显示名称</th>
                <th>描述</th>
                <th>状态</th>
                <th>是否系统模板</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {templates.map(template => (
                <tr 
                  key={template.id} 
                  className={template.is_system ? 'system-template-row' : ''}
                >
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedTemplates.includes(template.id)}
                      onChange={() => toggleTemplateSelection(template.id)}
                      disabled={template.is_system}
                    />
                  </td>
                  <td>{template.name}</td>
                  <td>{template.display_name}</td>
                  <td>{template.description || '-'}</td>
                  <td>
                    <span className={`status-badge ${template.is_active ? 'active' : 'inactive'}`}>
                      {template.is_active ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td>
                    <span className={`system-badge ${template.is_system ? 'system' : 'custom'}`}>
                      {template.is_system ? '是' : '否'}
                    </span>
                  </td>
                  <td>{new Date(template.created_at).toLocaleString()}</td>
                  <td className="action-buttons">
                    <button 
                      className={`btn btn-small btn-info ${template.is_system ? 'disabled' : ''}`}
                      onClick={() => handleEditModalOpen(template)}
                      disabled={template.is_system}
                      title={template.is_system ? '系统模板不允许编辑' : '编辑模板'}
                    >
                      编辑
                    </button>
                    <button 
                      className="btn btn-small btn-success"
                      onClick={() => handleApplyModalOpen(template)}
                      title="应用模板"
                    >
                      应用
                    </button>
                    <button 
                      className={`btn btn-small btn-danger ${template.is_system ? 'disabled' : ''}`}
                      onClick={() => handleDelete(template.id)}
                      disabled={template.is_system}
                      title={template.is_system ? '系统模板不允许删除' : '删除模板'}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      
      {/* 创建模板模态框 */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>创建新模板</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-form">
              <div className="form-group">
                <label>模板名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入模板名称（英文）"
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入模板显示名称（中文）"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入模板描述"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>模板数据 JSON *</label>
                <textarea
                  name="template_data"
                  value={JSON.stringify(formData.template_data, null, 2)}
                  onChange={handleTemplateDataChange}
                  required
                  placeholder="输入模板数据（JSON格式）"
                  rows="10"
                  className="json-editor"
                />
                <small className="help-text">
                  模板数据格式示例：<br />
                  {`{"categories": [{"name": "example", "display_name": "示例分类", "dimension": "task_type", "parent_id": null}]}`}
                </small>
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      is_active: e.target.checked
                    }))}
                  />
                  启用模板
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  创建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* 编辑模板模态框 */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>编辑模板</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-form">
              <div className="form-group">
                <label>模板名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>模板数据 JSON *</label>
                <textarea
                  name="template_data"
                  value={JSON.stringify(formData.template_data, null, 2)}
                  onChange={handleTemplateDataChange}
                  required
                  rows="10"
                  className="json-editor"
                />
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      is_active: e.target.checked
                    }))}
                  />
                  启用模板
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  保存
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* 应用模板模态框 */}
      {showApplyModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>应用模板: {currentTemplate?.display_name}</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleApplySubmit} className="modal-form">
              <div className="form-group">
                <label>分类名称前缀</label>
                <input
                  type="text"
                  name="category_name"
                  value={applyFormData.category_name}
                  onChange={handleApplyInputChange}
                  placeholder="输入分类名称前缀（可选）"
                />
                <small className="help-text">
                  如果填写，将在模板分类名称前添加此前缀
                </small>
              </div>
              <div className="form-group">
                <label>维度</label>
                <select
                  name="dimension"
                  value={applyFormData.dimension}
                  onChange={handleApplyInputChange}
                >
                  <option value="task_type">任务类型</option>
                  <option value="model_size">模型大小</option>
                  <option value="application">应用场景</option>
                  <option value="framework">技术框架</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  应用
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryTemplateManagement;