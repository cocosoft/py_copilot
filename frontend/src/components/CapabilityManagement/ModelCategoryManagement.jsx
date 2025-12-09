import React, { useState, useEffect } from 'react';
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
  
  // 获取所有分类
  const loadCategories = async () => {
    try {
      setLoading(true);
      
      // 直接调用API获取原始数据，避免在API层进行树形转换
      const rawResponse = await fetch(`${API_BASE_URL}/categories`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!rawResponse.ok) {
        throw new Error(`HTTP error! Status: ${rawResponse.status}`);
      }
      
      const response = await rawResponse.json();
      
      // 统一响应格式处理
      let categoriesData = [];
      if (Array.isArray(response)) {
        categoriesData = response;
      } else if (response?.categories) {
        categoriesData = response.categories;
      } else if (response?.data) {
        categoriesData = response.data;
      }      
     
      // 标准化分类数据，确保每个分类都有必要的属性
      const normalizedCategories = categoriesData.map(category => ({
        id: category.id ?? `category_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: category.name ?? `未命名分类_${category.id || 'unknown'}`,
        display_name: category.display_name ?? category.name ?? '未命名分类',
        description: category.description || '',
        category_type: category.category_type || 'main',
        parent_id: category.parent_id || null,
        is_active: category.is_active ?? true,
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
  };
  
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
      await categoryApi.create(formData);
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
      await categoryApi.update(currentCategory.id, formData);
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
                      {category.logo && (
                        <div className="category-logo">
                          <div 
                            dangerouslySetInnerHTML={{__html: category.logo}}
                            className="fa-icon"
                            title={`${category.display_name} logo`}
                          />
                        </div>
                      )}
                      {!category.logo && (
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
                    <td className="action-buttons">
                      <button 
                        className="btn btn-small btn-info" 
                        onClick={() => handleEditModalOpen(category)}
                      >
                        编辑
                      </button>
                      <button 
                        className="btn btn-small btn-danger" 
                        onClick={() => handleDelete(category.id)}
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
                <label>LOGO (SVG格式)</label>
                <textarea
                  name="logo"
                  value={formData.logo}
                  onChange={handleInputChange}
                  placeholder="输入SVG格式的LOGO代码"
                  rows="5"
                />
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
                <label>LOGO (SVG格式)</label>
                <textarea
                  name="logo"
                  value={formData.logo}
                  onChange={handleInputChange}
                  placeholder="输入SVG格式的LOGO代码"
                  rows="5"
                />
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
    </div>
  );
};

export default ModelCategoryManagement;