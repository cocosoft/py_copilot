import React, { useState, useEffect } from 'react';
import '../styles/SupplierModal.css';

const SupplierModal = ({ isOpen, onClose, onSave, supplier = null, mode = 'add' }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    logo: '',
    category: '',
    website: '',
    apiUrl: '',
    apiDocs: '',
    apiKey: '',
    isActive: true,
    isDomestic: false
  });
  const [saving, setSaving] = useState(false);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');

  // 当传入的supplier变化时，更新表单数据
  useEffect(() => {
    if (mode === 'edit' && supplier) {
      setFormData({
        name: supplier.name || '',
        description: supplier.description || '',
        logo: supplier.logo || '',
        category: supplier.category || '',
        website: supplier.website || '',
        apiUrl: supplier.api_endpoint || supplier.apiUrl || '',
        apiDocs: supplier.api_docs || supplier.apiDocs || '',
        apiKey: supplier.api_key || supplier.apiKey || '',
        isActive: supplier.is_active !== undefined ? supplier.is_active : true,
        isDomestic: supplier.is_domestic !== undefined ? supplier.is_domestic : false
      });
      // 重置文件和预览
      setFile(null);
      setPreviewUrl(supplier.logo || '');
    } else if (mode === 'add') {
      // 重置表单数据
      setFormData({
        name: '',
        description: '',
        logo: '',
        category: '',
        website: '',
        apiUrl: '',
        apiDocs: '',
        apiKey: '',
        isActive: true,
        isDomestic: false
      });
      setFile(null);
      setPreviewUrl('');
    }
  }, [supplier, mode]);

  // 处理表单输入变化
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // 处理文件上传变化
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      // 创建预览URL
      const objectUrl = URL.createObjectURL(selectedFile);
      setPreviewUrl(objectUrl);
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



  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (mode === 'add' && !formData.name) {
      alert('供应商名称为必填项');
      return;
    }
    
    try {
      setSaving(true);
      
      // 创建FormData对象用于文件上传
      const formDataToSubmit = new FormData();
      
      // 添加所有表单字段
      formDataToSubmit.append('name', formData.name);
      formDataToSubmit.append('description', formData.description);
      formDataToSubmit.append('category', formData.category);
      formDataToSubmit.append('website', formData.website);
      formDataToSubmit.append('api_endpoint', formData.apiUrl);
      formDataToSubmit.append('api_docs', formData.apiDocs);
      formDataToSubmit.append('api_key', formData.apiKey);
      formDataToSubmit.append('api_key_required', formData.apiKey ? 'true' : 'false');
      formDataToSubmit.append('is_active', formData.isActive ? 'true' : 'false');
      
      // 如果有文件上传，添加文件
      if (file) {
        formDataToSubmit.append('logo', file);
      }
      
      // 为了前端UI显示，创建一个包含所有前端数据的对象
      const frontendData = {
        ...formData,
        // 如果有新上传的文件，使用预览URL作为临时logo显示
        logo: file ? previewUrl : formData.logo
      };
      
      console.log('SupplierModal: 准备调用onSave，提交的数据:', formDataToSubmit);
      console.log('SupplierModal: 提交的前端数据:', frontendData);
      
      // 调用父组件的保存函数，传递FormData和前端数据
      await onSave(formDataToSubmit, frontendData);
      console.log('SupplierModal: onSave调用成功，准备关闭模态窗口');
      onClose();
    } catch (error) {
      console.error('SupplierModal: 保存供应商失败:', error);
      alert('保存失败，请重试');
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
          <h3>{mode === 'add' ? '添加供应商' : '编辑供应商'}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name">供应商名称 *</label>
              <input 
                type="text" 
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="供应商名称"
                required
                disabled={saving}
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="description">描述</label>
            <textarea 
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="供应商描述"
              rows="3"
              disabled={saving}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="logo">Logo 图片</label>
            {previewUrl && (
              <div className="logo-preview" style={{
                marginBottom: '10px',
                display: 'flex',
                justifyContent: 'center'
              }}>
                <img 
                  src={previewUrl} 
                  alt="Logo预览" 
                  style={{
                    maxWidth: '150px',
                    maxHeight: '150px',
                    objectFit: 'contain',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    padding: '5px'
                  }}
                />
              </div>
            )}
            <input 
              type="file" 
              id="logo"
              accept="image/*"
              onChange={handleFileChange}
              disabled={saving}
              style={{ marginTop: '5px' }}
            />
            <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
              支持JPG、PNG、GIF等图片格式，建议尺寸不超过500KB
            </small>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="category">供应商类别</label>
              <input 
                type="text" 
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                placeholder="如：AI模型、云服务等"
                disabled={saving}
              />
            </div>
            <div className="form-group">
              <label htmlFor="website">官网</label>
              <input 
                type="url" 
                id="website"
                name="website"
                value={formData.website}
                onChange={handleChange}
                placeholder="https://"
                disabled={saving}
              />
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="apiUrl">API地址</label>
              <input 
                type="url" 
                id="apiUrl"
                name="apiUrl"
                value={formData.apiUrl}
                onChange={handleChange}
                placeholder="https://"
                disabled={saving}
              />
            </div>
            <div className="form-group">
              <label htmlFor="apiDocs">API文档</label>
              <input 
                type="url" 
                id="apiDocs"
                name="apiDocs"
                value={formData.apiDocs}
                onChange={handleChange}
                placeholder="https://"
                disabled={saving}
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="apiKey">API密钥</label>
            <input 
              type="password" 
              id="apiKey"
              name="apiKey"
              value={formData.apiKey}
              onChange={handleChange}
              placeholder="API Key"
              disabled={saving}
            />
          </div>
          
          <div className="form-group">
            <label>
              <input 
                type="checkbox" 
                name="isActive"
                checked={formData.isActive}
                onChange={handleChange}
                disabled={saving}
              />
              启用此供应商
            </label>
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

export default SupplierModal;