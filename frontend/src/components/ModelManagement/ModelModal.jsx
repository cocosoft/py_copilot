import React, { useState, useEffect } from 'react';
import { getImageUrl } from '../../config/imageConfig';
import categoryApi from '../../utils/api/categoryApi';
import api from '../../utils/api';
import '../../styles/ModelModal.css';

const ModelModal = ({ isOpen, onClose, onSave, model = null, mode = 'add', isFirstModel = false }) => {
  const [formData, setFormData] = useState({
    model_id: '',
    model_name: '',
    description: '',
    contextWindow: 8000,
    max_tokens: 1000,
    model_type: '',
    parameter_template_id: '',
    isDefault: false,
    is_active: true
  });
  const [logo, setLogo] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [parameterTemplates, setParameterTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  // 获取模型分类树形结构
  useEffect(() => {
    if (isOpen) {
      fetchCategories();
      fetchParameterTemplates();
    }
  }, [isOpen]);

  const fetchCategories = async () => {
    try {
      setLoadingCategories(true);
      
      // 1. 首先直接调用后端API获取原始数据（使用正确的/api前缀）

      const response = await fetch('/api/model/categories');
      const rawData = await response.json();

      
      // 检查原始数据结构
      if (rawData && (Array.isArray(rawData) || rawData.categories || rawData.data)) {
        const categoriesArray = Array.isArray(rawData) ? rawData : 
                               rawData.categories ? rawData.categories : rawData.data;

        // 检查是否有子分类（parent_id不为null的分类）
        const hasChildCategories = categoriesArray.some(category => category.parent_id !== null);

        if (hasChildCategories) {
          const childCategories = categoriesArray.filter(category => category.parent_id !== null);
        }
      }
      

      const treeData = await categoryApi.getTree();
      
      // 检查返回的分类树是否包含子分类
      let hasChildren = false;
      const checkChildren = (categories) => {
        for (const category of categories) {
          if (category.children && category.children.length > 0) {
            hasChildren = true;
            break;
          }
          if (category.children) {
            checkChildren(category.children);
          }
        }
      };
      
      if (treeData && treeData.length > 0) {
        checkChildren(treeData);
        setCategories(treeData);
        return;
      }
      
      // 3. 如果getTree失败或返回空，尝试使用getAll方法
      const categoryTree = await categoryApi.getAll();

      checkChildren(categoryTree);

      setCategories(categoryTree);
      
    } catch (error) {
      console.error('ModelModal: 获取模型分类失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      console.error('❌ 错误详情:', error.message);
      console.error('❌ 错误栈:', error.stack);
      
    } finally {
      setLoadingCategories(false);
    }
  };

  // 获取参数模板列表
  const fetchParameterTemplates = async () => {
    try {
      setLoadingTemplates(true);
      const templates = await api.modelApi.getParameterTemplates();
      setParameterTemplates(templates);
    } catch (error) {
      console.error('获取参数模板失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      setParameterTemplates([]);
    } finally {
      setLoadingTemplates(false);
    }
  };

  // 递归渲染分类树形结构（包含所有层级）
  const renderCategoryTree = (categoryList, level = 0) => {
    return categoryList.map(category => (
      <React.Fragment key={category.id}>
        <option value={category.id} style={{ 
          paddingLeft: `${level * 20}px`,
          fontWeight: level === 0 ? 'bold' : 'normal',
          color: level === 0 ? '#333' : '#666'
        }}>
          {`${category.name} (${category.display_name || category.name})`}
        </option>
        {category.children && category.children.length > 0 && 
          renderCategoryTree(category.children, level + 1)
        }
      </React.Fragment>
    ));
  };

  // 当传入的model变化时，更新表单数据
  useEffect(() => {
    if (mode === 'edit' && model) {
      setFormData({
        model_id: model.modelId || model.model_id || '',
        model_name: model.modelName || model.model_name || '', // 确保模型名称字段正确设置
        description: model.description || '',
        contextWindow: model.contextWindow || model.context_window || 8000,
        max_tokens: model.maxTokens || model.max_tokens || 1000,
        model_type: model.modelType?.toString() || model.model_type?.toString() || '',
        parameter_template_id: model.parameter_template_id?.toString() || '',
        isDefault: model.isDefault || model.is_default || false,
        is_active: model.isActive || model.is_active || true
      });
      // 调试：打印设置的表单数据
      console.log('设置的表单数据:', JSON.stringify({
        model_id: model.modelId || model.model_id || '',
        model_name: model.modelName || model.model_name || '',
        description: model.description || '',
        contextWindow: model.contextWindow || model.context_window || 8000,
        max_tokens: model.maxTokens || model.max_tokens || 1000,
        model_type: model.modelType?.toString() || model.model_type?.toString() || '',
        parameter_template_id: model.parameter_template_id?.toString() || '',
        isDefault: model.isDefault || model.is_default || false,
        is_active: model.isActive || model.is_active || true
      }, null, 2));
      // 确保模型LOGO预览使用正确的路径
      let logoPath = model.logo || null;
      if (logoPath && !logoPath.startsWith('http')) {
        logoPath = getImageUrl('models', logoPath);
      }
      setLogoPreview(logoPath);
      setLogo(null);
    } else if (mode === 'add') {
      // 重置表单数据
      setFormData({
        model_id: '',
        model_name: '',
        description: '',
        contextWindow: 8000,
        max_tokens: 1000,
        model_type: '',
        parameter_template_id: '',
        isDefault: isFirstModel, // 如果是第一个模型，默认设为默认模型
        is_active: true
      });
      setLogo(null);
      setLogoPreview(null);
    }
  }, [model, mode, isFirstModel]);

  // 处理表单输入变化
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) || 8000 : value
    }));
  };

  // 处理LOGO文件选择
  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLogo(file);
      // 创建预览
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // 处理移除LOGO
  const handleRemoveLogo = () => {
    setLogo(null);
    setLogoPreview(null);
  };

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 验证必填字段
    if (!formData.model_id) {
      alert('请填写模型ID');
      return;
    }
    
    try {
      setSaving(true);
      
      // 准备传递给父组件的数据
      const modelData = {
        ...formData,
        // 确保字段命名一致性和类型转换
        contextWindow: parseInt(formData.contextWindow) || 8000,
        maxTokens: parseInt(formData.max_tokens) || 1000,
        modelType: formData.model_type || '',
        parameterTemplateId: formData.parameter_template_id || '',
        isDefault: formData.isDefault || false,
        isActive: formData.is_active || true
      };
      
      // 调试：打印提交的模型数据
      console.log('提交的模型数据:', JSON.stringify(modelData, null, 2));
      
      // 调用父组件的保存函数
      await onSave(modelData, logo);
      onClose();
    } catch (error) {
      console.error('ModelModal: 保存模型失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      alert('保存失败：' + (error.message || '未知错误'));
    } finally {
      setSaving(false);
    }
  };

  // 处理模态窗口外部点击关闭
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // 处理ESC键关闭模态窗口
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-container">
        <div className="modal-header">
          <h3>{mode === 'add' ? '添加模型' : '编辑模型'}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="model_id">模型ID: <span className="required">*</span></label>
              <input 
                type="text" 
                id="model_id"
                name="model_id"
                value={formData.model_id}
                onChange={handleChange}
                placeholder="模型ID（同一供应商下唯一）"
                required
                disabled={saving}
              />
              <div className="field-hint">
                该ID是模型正确调用的唯一ID，请确保与供应商提供的模型名称（ID）保持一致。否则可能会导致模型调用失败。
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="model_name">模型名称: <span className="required">*</span></label>
              <input 
                type="text" 
                id="model_name"
                name="model_name"
                value={formData.model_name}
                onChange={handleChange}
                placeholder="模型显示名称"
                required
                disabled={saving}
              />
              <div className="field-hint">
                模型在界面上显示的名称，方便用户识别
              </div>
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="model_type">模型类型</label>
              <select 
                id="model_type"
                name="model_type"
                value={formData.model_type}
                onChange={handleChange}
                disabled={loadingCategories || saving}
              >
                <option value="">请选择模型类型</option>
                {renderCategoryTree(categories)}
              </select>
              {loadingCategories && <span className="loading">加载中...</span>}
            </div>
            <div className="form-group">
              <label htmlFor="parameter_template_id">参数模板</label>
              <select 
                id="parameter_template_id"
                name="parameter_template_id"
                value={formData.parameter_template_id}
                onChange={handleChange}
                disabled={loadingTemplates || saving}
              >
                <option value="">请选择参数模板</option>
                {parameterTemplates.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.name || `模板 ${template.id}`}
                  </option>
                ))}
              </select>
              {loadingTemplates && <span className="loading">加载中...</span>}
              <div className="field-hint">
                选择一个参数模板，系统将自动为模型应用模板中的参数
              </div>
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="contextWindow">上下文窗口</label>
              <input 
                type="number" 
                id="contextWindow"
                name="contextWindow"
                value={formData.contextWindow}
                onChange={handleChange}
                min="1000"
                step="1000"
                placeholder="上下文窗口大小"
                disabled={saving}
              />
            </div>
            <div className="form-group">
              <label htmlFor="max_tokens">最大Token数</label>
              <input 
                type="number" 
                id="max_tokens"
                name="max_tokens"
                value={formData.max_tokens}
                onChange={handleChange}
                min="100"
                step="100"
                placeholder="最大生成Token数"
                disabled={saving}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="logo">模型LOGO</label>
            <div className="logo-upload-container">
              {logoPreview ? (
                <div className="logo-preview">
                  <img src={logoPreview} alt="Logo Preview" />
                  <button type="button" className="remove-logo-btn" onClick={handleRemoveLogo}>
                    ×
                  </button>
                </div>
              ) : (
                <div className="logo-upload-placeholder">
                  <span>点击上传LOGO或拖拽文件到此处</span>
                </div>
              )}
              <input 
                type="file" 
                id="logo"
                accept="image/*"
                onChange={handleLogoChange}
                style={{ display: 'none' }}
                disabled={saving}
              />
              <label htmlFor="logo" className="btn btn-secondary" style={{ marginTop: '10px' }}>
                选择LOGO
              </label>
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="description">描述</label>
            <textarea 
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="模型描述"
              rows="3"
              disabled={saving}
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>
                <input 
                  type="checkbox" 
                  name="isDefault"
                  checked={formData.isDefault}
                  onChange={handleChange}
                  disabled={saving}
                />
                设置为默认模型
              </label>
            </div>
            <div className="form-group">
              <label>
                <input 
                  type="checkbox" 
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  disabled={saving}
                />
                启用模型
              </label>
            </div>
          </div>
          
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? (mode === 'add' ? '添加中...' : '保存中...') : (mode === 'add' ? '添加' : '保存')}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ModelModal;