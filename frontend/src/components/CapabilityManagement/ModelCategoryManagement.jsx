import React, { useState, useEffect } from 'react';
import { getImageUrl, DEFAULT_IMAGES } from '../../config/imageConfig';
import { categoryApi } from '../../utils/api/categoryApi';
import { API_BASE_URL } from '../../utils/apiUtils';
import '../../styles/ModelCategoryManagement.css';

// 将树形结构的分类数据扁平化为数组
const flattenCategoryTree = (categories) => {
  const result = [];
  
  
  const traverse = (category) => {
    if (!category) return;
    
    // 添加当前分类
    const flatCategory = {
      ...category,
      // 移除children数组，避免重复处理
      children: undefined
    };
    result.push(flatCategory);
    
    // 递归处理子分类
    if (Array.isArray(category.children) && category.children.length > 0) {
      category.children.forEach(child => traverse(child));
    }
  };
  
  // 处理顶层分类
  if (Array.isArray(categories)) {
    categories.forEach(category => traverse(category));
  }
  
  return result;
};

const ModelCategoryManagement = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null); // 添加成功状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentCategory, setCurrentCategory] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // 添加当前选中标签的状态
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category_type: 'main',
    parent_id: null,
    is_active: true,
    logo: ''
  });
  
  // LOGO选择相关状态
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  
  // 参数配置相关状态
  const [selectedCategoryForParams, setSelectedCategoryForParams] = useState(null);
  const [categoryParameters, setCategoryParameters] = useState({}); // 存储每个分类的参数
  const [showParameterModal, setShowParameterModal] = useState(false);
  const [parameterModalMode, setParameterModalMode] = useState('add'); // add or edit
  const [editingParameter, setEditingParameter] = useState(null);
  const [parameterFormData, setParameterFormData] = useState({
    parameter_name: '',
    parameter_value: '',
    parameter_type: 'string',
    description: ''
  });
  const [parameterLoading, setParameterLoading] = useState(false);
  const [parameterError, setParameterError] = useState(null);
  
  // 获取所有分类
  const loadCategories = async () => {
    try {
      setLoading(true);
      
      // 使用categoryApi获取所有分类
      const categoriesData = await categoryApi.getAll();
      
      // 标准化分类数据，确保每个分类都有必要的属性
      const normalizedCategories = categoriesData.map(category => ({
        id: category.id ?? `category_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: category.name ?? `未命名分类_${category.id || 'unknown'}`,
        display_name: category.display_name ?? category.name ?? '未命名分类',
        description: category.description || '',
        category_type: category.category_type || 'main',
        parent_id: category.parent_id || null,
        is_active: category.is_active ?? true,
        is_system: category.is_system ?? false,
        logo: category.logo || null,
        ...category
      }));
      
      
      // 使用扁平化处理确保所有分类（包括嵌套的次要分类）都能正确显示
      const flattenedCategories = flattenCategoryTree(normalizedCategories);
      
      setCategories(flattenedCategories);
      setError(null);
    } catch (err) {
      console.error('❌ 获取分类失败:', err);
      console.error('❌ 错误详情:', err.message, err.stack);
      setError('获取分类列表失败，请稍后重试');
      
    } finally {
      setLoading(false);
    }
  };
  
  // 初始化加载
  useEffect(() => {
    loadCategories();
  }, []);
  
  // 处理输入变化
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'parent_id' ? (value === '' ? null : parseInt(value)) : value
    }));
  };
  
  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      description: '',
      category_type: 'main',
      parent_id: null,
      is_active: true,
      logo: ''
    });
    setCurrentCategory(null);
    // 重置LOGO相关状态
    setFile(null);
    setPreviewUrl('');
  };
  
  // 处理文件上传变化
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      // 创建预览URL
      const objectUrl = URL.createObjectURL(selectedFile);
      setPreviewUrl(objectUrl);
      // 清除之前的Font Awesome图标选择
      setFormData(prev => ({ ...prev, logo: '' }));
    }
  };
  

  
  // 清理预览URL
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);
  
  // 打开创建模态框
  const handleCreateModalOpen = () => {
    resetForm();
    setShowCreateModal(true);
  };
  
  // 打开编辑模态框
  const handleEditModalOpen = (category) => {
    setCurrentCategory(category);
    setFormData({
      name: category.name,
      display_name: category.display_name,
      description: category.description || '',
      category_type: category.category_type,
      parent_id: category.parent_id !== null ? category.parent_id : null,
      is_active: category.is_active,
      logo: category.logo || ''
    });
    
    // 重置LOGO相关状态
    setFile(null);
    // 处理logo预览URL
    const logoUrl = category.logo || '';
    let finalPreviewUrl = '';
    if (logoUrl && logoUrl.trim() && !logoUrl.startsWith('fa-')) {
      if (logoUrl.startsWith('/')) {
        // 已经是完整路径，直接使用
        finalPreviewUrl = logoUrl;
      } else {
        // 只有文件名，添加完整路径前缀
        finalPreviewUrl = getImageUrl('categories', logoUrl);
      }
    }
    setPreviewUrl(finalPreviewUrl);
    
    setShowEditModal(true);
  };
  
  // 关闭模态框
  const handleModalClose = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    resetForm();
  };
  
  // 提交创建表单
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      // 创建FormData对象用于文件上传
      const formDataToSubmit = new FormData();
      
      // 添加所有表单字段
      formDataToSubmit.append('name', formData.name);
      formDataToSubmit.append('display_name', formData.display_name);
      formDataToSubmit.append('description', formData.description);
      formDataToSubmit.append('category_type', formData.category_type);
      formDataToSubmit.append('parent_id', formData.parent_id || '');
      formDataToSubmit.append('is_active', formData.is_active.toString());
      
      // 处理LOGO
      if (file) {
        formDataToSubmit.append('logo_file', file);
      } else if (formData.logo && !formData.logo.startsWith('fa-')) {
        // 编辑模式下，如果没有上传新文件但有现有logo，保留现有logo
        formDataToSubmit.append('logo', formData.logo);
      }
      
      await categoryApi.create(formDataToSubmit);
      setShowCreateModal(false);
      loadCategories(); // 重新加载列表
      setSuccess('分类创建成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('创建分类失败:', err);
      setError('创建分类失败，请检查输入并重试');
    }
  };
  
  // 提交编辑表单
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!currentCategory) return;
    
    try {
      // 创建FormData对象用于文件上传
      const formDataToSubmit = new FormData();
      
      // 添加所有表单字段
      formDataToSubmit.append('name', formData.name);
      formDataToSubmit.append('display_name', formData.display_name);
      formDataToSubmit.append('description', formData.description);
      formDataToSubmit.append('category_type', formData.category_type);
      formDataToSubmit.append('parent_id', formData.parent_id || '');
      formDataToSubmit.append('is_active', formData.is_active.toString());
      
      // 处理LOGO
      if (file) {
        formDataToSubmit.append('logo_file', file);
      } else if (formData.logo && !formData.logo.startsWith('fa-')) {
        // 编辑模式下，如果没有上传新文件但有现有logo，保留现有logo
        formDataToSubmit.append('logo', formData.logo);
      }
      
      await categoryApi.update(currentCategory.id, formDataToSubmit);
      setShowEditModal(false);
      loadCategories(); // 重新加载列表
      setSuccess('分类更新成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('更新分类失败:', err);
      setError('更新分类失败，请检查输入并重试');
    }
  };
  
  // 处理删除
  const handleDelete = async (categoryId) => {
    if (window.confirm('确定要删除这个分类吗？删除前请确保该分类没有子分类和关联的模型。')) {
      try {
        const result = await categoryApi.delete(categoryId);
        loadCategories(); // 重新加载列表
        // 清除该分类的参数数据
        setCategoryParameters(prev => {
          const newParams = { ...prev };
          delete newParams[categoryId];
          return newParams;
        });
        setSuccess('分类删除成功');
        // 3秒后自动清除成功消息
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error('❌ 删除分类失败:', err);
        console.error('❌ 错误详情:', err.message, err.stack);
        setError('删除分类失败，可能是因为该分类下有子分类或关联的模型');
      }
    }
  };
  
  // 加载分类参数
  const loadCategoryParameters = async (categoryId) => {
    try {
      setParameterLoading(true);
      const parameters = await categoryApi.getParameters(categoryId);
      setCategoryParameters(prev => ({
        ...prev,
        [categoryId]: parameters
      }));
      setParameterError(null);
    } catch (err) {
      setParameterError('加载分类参数失败，请稍后重试');
    } finally {
      setParameterLoading(false);
    }
  };
  
  // 打开参数配置模态框
  const handleOpenParameterModal = (category, mode, parameter = null) => {
    setSelectedCategoryForParams(category);
    setParameterModalMode(mode);
    
    if (mode === 'edit' && parameter) {
      setEditingParameter(parameter);
      setParameterFormData({
        parameter_name: parameter.parameter_name,
        parameter_value: parameter.parameter_value,
        parameter_type: parameter.parameter_type || 'string',
        description: parameter.description || ''
      });
    } else {
      setEditingParameter(null);
      setParameterFormData({
        parameter_name: '',
        parameter_value: '',
        parameter_type: 'string',
        description: ''
      });
    }
    
    setShowParameterModal(true);
  };
  
  // 关闭参数配置模态框
  const handleCloseParameterModal = () => {
    setShowParameterModal(false);
    setEditingParameter(null);
    setParameterFormData({
      parameter_name: '',
      parameter_value: '',
      parameter_type: 'string',
      description: ''
    });
  };
  
  // 处理参数表单输入变化
  const handleParameterInputChange = (e) => {
    const { name, value } = e.target;
    setParameterFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // 提交参数表单
  const handleParameterSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCategoryForParams) return;
    
    try {
      setParameterLoading(true);
      
      const parameterData = {
        parameter_name: parameterFormData.parameter_name,
        parameter_value: parameterFormData.parameter_value,
        parameter_type: parameterFormData.parameter_type,
        description: parameterFormData.description
      };
      
      if (parameterModalMode === 'add') {
        // 对于添加操作，我们需要获取当前参数列表并添加新参数
        const currentParams = categoryParameters[selectedCategoryForParams.id] || [];
        const updatedParams = [...currentParams, parameterData];
        await categoryApi.setParameters(selectedCategoryForParams.id, updatedParams);
      } else if (parameterModalMode === 'edit' && editingParameter) {
        // 对于编辑操作，我们需要更新指定参数
        const currentParams = categoryParameters[selectedCategoryForParams.id] || [];
        const updatedParams = currentParams.map(p => 
          p.parameter_name === editingParameter.parameter_name ? parameterData : p
        );
        await categoryApi.setParameters(selectedCategoryForParams.id, updatedParams);
      }
      
      // 重新加载参数列表
      await loadCategoryParameters(selectedCategoryForParams.id);
      setShowParameterModal(false);
      setSuccess('参数配置成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('❌ 参数配置失败:', err);
      setParameterError('参数配置失败，请稍后重试');
    } finally {
      setParameterLoading(false);
    }
  };
  
  // 处理删除参数
  const handleDeleteParameter = async (categoryId, parameterName) => {
    if (window.confirm(`确定要删除参数 ${parameterName} 吗？`)) {
      try {
        setParameterLoading(true);
        await categoryApi.deleteParameter(categoryId, parameterName);
        // 重新加载参数列表
        await loadCategoryParameters(categoryId);
        setSuccess('参数删除成功');
        // 3秒后自动清除成功消息
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error('❌ 删除参数失败:', err);
        setParameterError('删除参数失败，请稍后重试');
      } finally {
        setParameterLoading(false);
      }
    }
  };
  
  // 处理分类参数配置点击
  const handleConfigureParameters = (category) => {
    setSelectedCategoryForParams(category);
    // 加载分类参数
    loadCategoryParameters(category.id);
  };

  // 监听selectedCategoryForParams状态变化
  useEffect(() => {
    if (selectedCategoryForParams) {
      // 参数加载逻辑已移至handleConfigureParameters中
    }
  }, [selectedCategoryForParams]);
  
  // 获取主分类列表（用于父分类选择）
  const mainCategories = categories.filter(cat => cat.category_type === 'main');
  
  // 处理标签点击
  const handleTabClick = (tabType) => {
    setActiveTab(tabType);
  };
  
  // 根据当前选中的标签过滤分类
  const filteredCategories = activeTab === 'all' 
    ? categories 
    : categories.filter(cat => cat.category_type === activeTab);
  
  if (loading) {
    return <div className="category-management-loading">加载中...</div>;
  }
  
  return (
    <div className="model-category-management">
      <div className="category-header">
        <button 
          className="btn btn-primary" 
          onClick={handleCreateModalOpen}
        >
          创建分类
        </button>
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
      
      <div className="category-content">
        {categories.length === 0 ? (
          <div className="empty-state">暂无分类数据</div>
        ) : (
          <div className="category-tabs">
            <div 
              className={`tab ${activeTab === 'all' ? 'active' : ''}`} 
              data-type="all"
              onClick={() => handleTabClick('all')}
            >所有分类</div>
            <div 
              className={`tab ${activeTab === 'main' ? 'active' : ''}`} 
              data-type="main"
              onClick={() => handleTabClick('main')}
            >主要分类</div>
            <div 
              className={`tab ${activeTab === 'secondary' ? 'active' : ''}`} 
              data-type="secondary"
              onClick={() => handleTabClick('secondary')}
            >次要分类</div>
          </div>
        )}
        
        <div className="category-table-container">
          <table className="category-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>LOGO</th>
                <th>名称</th>
                <th>显示名称</th>
                <th>类型</th>
                <th>父分类</th>
                <th>状态</th>
                <th>是否系统分类</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredCategories.map(category => {
                const parentCategory = category.parent_id 
                  ? categories.find(cat => cat.id === category.parent_id)
                  : null;
                
                return (
                  <tr key={category.id}>
                    <td>{category.id}</td>
                    <td>
                      {category.logo ? (
                        <div className="category-logo">
                          {category.logo.startsWith('<i class=') ? (
                            <div 
                              dangerouslySetInnerHTML={{ __html: category.logo }}
                              className="fa-icon"
                              title={`${category.display_name} logo`}
                            />
                          ) : category.logo.includes('fa-') ? (
                            <div className="fa-icon">
                              <i className={category.logo} title={`${category.display_name} logo`}></i>
                            </div>
                          ) : (
                            <img 
                              src={getImageUrl('categories', category.logo)} 
                              alt={`${category.display_name} logo`} 
                              title={`${category.display_name} logo`}
                              onError={(e) => {
                                e.target.src = DEFAULT_IMAGES.category;
                                console.error('图片加载失败，使用默认图片:', e.target.src);
                              }}
                            />
                          )}
                        </div>
                      ) : (
                        <div className="category-logo placeholder">
                          无LOGO
                        </div>
                      )}
                    </td>
                    <td>{category.name}</td>
                    <td>{category.display_name}</td>
                    <td>
                      <span className={`category-type-badge ${category.category_type}`}>
                        {category.category_type === 'main' ? '主要' : '次要'}
                      </span>
                    </td>
                    <td>{parentCategory ? parentCategory.display_name : '-'}</td>
                    <td>
                      <span className={`status-badge ${category.is_active ? 'active' : 'inactive'}`}>
                        {category.is_active ? '启用' : '禁用'}
                      </span>
                    </td>
                    <td>
                      <span className={`system-badge ${category.is_system ? 'system' : 'custom'}`}>
                        {category.is_system ? '是' : '否'}
                      </span>
                    </td>
                    <td className="action-buttons">
                      <button 
                          className={`btn btn-small btn-info ${category.is_system ? 'disabled' : ''}`}
                          onClick={() => handleEditModalOpen(category)}
                          disabled={category.is_system}
                          title={category.is_system ? '系统分类不允许编辑' : '编辑分类'}
                        >
                          编辑
                        </button>
                      <button 
                        className={`btn btn-small btn-info ${category.is_system ? 'disabled' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation(); // 阻止事件冒泡
                          handleConfigureParameters(category);
                        }}
                        disabled={category.is_system}
                        title={category.is_system ? '系统分类不允许配置参数' : '参数配置'}
                      >
                        参数配置
                      </button>
                      <button 
                        className={`btn btn-small btn-danger ${category.is_system ? 'disabled' : ''}`}
                        onClick={() => handleDelete(category.id)}
                        disabled={category.is_system}
                        title={category.is_system ? '系统分类不允许删除' : '删除分类'}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* 创建分类模态框 */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>创建新分类</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-form">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入分类名称（英文）"
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
                  placeholder="输入分类显示名称（中文）"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入分类描述"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>类型 *</label>
                <select
                  name="category_type"
                  value={formData.category_type}
                  onChange={handleInputChange}
                  required
                >
                  <option value="main">主要分类</option>
                  <option value="secondary">次要分类</option>
                </select>
              </div>
              <div className="form-group">
                <label>父分类</label>
                <select
                  name="parent_id"
                  value={formData.parent_id || ''}
                  onChange={handleInputChange}
                >
                  <option value="">无</option>
                  {mainCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.display_name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>LOGO</label>
                
                {/* 图片上传 */}
                <div className="logo-upload-section">
                  {previewUrl && (
                    <div className="logo-preview">
                      <h4>预览</h4>
                      <div className="category-logo">
                        <img src={previewUrl} alt="Logo预览" className="logo-image" />
                      </div>
                    </div>
                  )}
                  <input 
                    type="file" 
                    id="logo-upload"
                    accept="image/*"
                    onChange={handleFileChange}
                    style={{ marginTop: '10px' }}
                  />
                  <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
                    支持JPG、PNG、GIF等图片格式，建议尺寸不超过500KB
                  </small>
                </div>
              </div>
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                />
                <label htmlFor="is_active">启用</label>
              </div>
              <div className="modal-footer">
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
      
      {/* 编辑分类模态框 */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>编辑分类</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-form">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入分类名称（英文）"
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
                  placeholder="输入分类显示名称（中文）"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入分类描述"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>类型 *</label>
                <select
                  name="category_type"
                  value={formData.category_type}
                  onChange={handleInputChange}
                  required
                >
                  <option value="main">主要分类</option>
                  <option value="secondary">次要分类</option>
                </select>
              </div>
              <div className="form-group">
                <label>父分类</label>
                <select
                  name="parent_id"
                  value={formData.parent_id || ''}
                  onChange={handleInputChange}
                >
                  <option value="">无</option>
                  {mainCategories.filter(cat => cat.id !== currentCategory?.id).map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.display_name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>LOGO</label>
                
                {/* 图片上传 */}
                <div className="logo-upload-section">
                  {previewUrl && (
                    <div className="logo-preview">
                      <h4>预览</h4>
                      <div className="category-logo">
                        <img src={previewUrl} alt="Logo预览" className="logo-image" />
                      </div>
                    </div>
                  )}
                  <input 
                    type="file" 
                    id="logo-upload-edit"
                    accept="image/*"
                    onChange={handleFileChange}
                    style={{ marginTop: '10px' }}
                  />
                  <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
                    支持JPG、PNG、GIF等图片格式，建议尺寸不超过500KB
                  </small>
                </div>
              </div>
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_active_edit"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                />
                <label htmlFor="is_active_edit">启用</label>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  更新
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* 参数配置面板 */}
      {selectedCategoryForParams && (
        <div className="category-parameter-panel" style={{ border: '2px solid red', marginTop: '20px', padding: '20px' }}>
          <div className="parameter-panel-header">
            <h3>{selectedCategoryForParams.display_name} - 参数配置</h3>
            <p>测试参数配置面板是否显示</p>
            <button 
              className="btn btn-primary btn-small"
              onClick={() => handleOpenParameterModal(selectedCategoryForParams, 'add')}
            >
              添加参数
            </button>
          </div>
          
          {parameterLoading ? (
            <div className="loading">加载中...</div>
          ) : parameterError ? (
            <div className="error-message">{parameterError}</div>
          ) : (
            <div className="parameter-table-container">
              <table className="parameter-table">
                <thead>
                  <tr>
                    <th>参数名称</th>
                    <th>参数值</th>
                    <th>参数类型</th>
                    <th>描述</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {categoryParameters[selectedCategoryForParams.id]?.length > 0 ? (
                    categoryParameters[selectedCategoryForParams.id].map((param, index) => (
                      <tr key={index}>
                        <td>{param.parameter_name}</td>
                        <td>{param.parameter_value}</td>
                        <td>{param.parameter_type}</td>
                        <td>{param.description || '-'}</td>
                        <td>
                          <button 
                            className="btn btn-small btn-warning mr-1"
                            onClick={() => handleOpenParameterModal(selectedCategoryForParams, 'edit', param)}
                          >
                            编辑
                          </button>
                          <button 
                            className="btn btn-small btn-danger"
                            onClick={() => handleDeleteParameter(selectedCategoryForParams.id, param.parameter_name)}
                          >
                            删除
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center' }}>暂无参数配置</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      
      {/* 参数配置模态框 */}
      {showParameterModal && selectedCategoryForParams && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>
                {parameterModalMode === 'add' ? '添加参数' : '编辑参数'} - {selectedCategoryForParams.display_name}
              </h3>
              <button className="btn-close" onClick={handleCloseParameterModal}>×</button>
            </div>
            <form onSubmit={handleParameterSubmit} className="modal-form">
              <div className="form-group">
                <label>参数名称 *</label>
                <input
                  type="text"
                  name="parameter_name"
                  value={parameterFormData.parameter_name}
                  onChange={handleParameterInputChange}
                  required
                  placeholder="输入参数名称"
                  disabled={parameterModalMode === 'edit'}
                />
              </div>
              <div className="form-group">
                <label>参数值 *</label>
                <input
                  type="text"
                  name="parameter_value"
                  value={parameterFormData.parameter_value}
                  onChange={handleParameterInputChange}
                  required
                  placeholder="输入参数值"
                />
              </div>
              <div className="form-group">
                <label>参数类型 *</label>
                <select
                  name="parameter_type"
                  value={parameterFormData.parameter_type}
                  onChange={handleParameterInputChange}
                  required
                >
                  <option value="string">字符串 (string)</option>
                  <option value="number">数字 (number)</option>
                  <option value="boolean">布尔值 (boolean)</option>
                  <option value="array">数组 (array)</option>
                  <option value="object">对象 (object)</option>
                </select>
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={parameterFormData.description}
                  onChange={handleParameterInputChange}
                  placeholder="输入参数描述"
                  rows="3"
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={handleCloseParameterModal}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  {parameterModalMode === 'add' ? '添加' : '更新'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelCategoryManagement;