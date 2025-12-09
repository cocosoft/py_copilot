import React, { useState, useEffect } from 'react';
import '../../styles/SupplierModal.css';

const SupplierModal = ({ isOpen, onClose, onSave, supplier = null, mode = 'add' }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    logo: '',
    website: '',
    api_endpoint: '',
    api_key: '',
    api_docs: ''
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
        website: supplier.website || '',
        api_endpoint: supplier.api_endpoint || supplier.apiUrl || '',
        api_key: supplier.api_key || '',
        api_docs: supplier.api_docs || ''
      });
      // 重置文件和预览
      setFile(null);
      // 处理logo预览URL，现在后端直接返回前端可访问的路径格式
        const logoUrl = supplier.logo || '';
        // 对于/logo/providers/开头的路径或其他相对路径，前端可以直接访问
        // 对于只有文件名的logo值，添加完整路径前缀
        let finalPreviewUrl = '';
        if (logoUrl && logoUrl.trim()) {
          if (logoUrl.startsWith('/')) {
            // 已经是完整路径，直接使用
            finalPreviewUrl = logoUrl;
          } else {
            // 只有文件名，添加完整路径前缀
            finalPreviewUrl = `/logos/providers/${logoUrl}`;
          }
        }
        setPreviewUrl(finalPreviewUrl);
        // 设置表单中的logo值（保持原始值，不包含完整路径前缀）
        setFormData(prev => ({
          ...prev,
          logo: logoUrl
        }));
    } else if (mode === 'add') {
      // 重置表单数据
      setFormData({
        name: '',
        description: '',
        logo: '',
        website: '',
        api_endpoint: '',
        api_key: '',
        api_docs: ''
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
      // 后端需要display_name字段，使用name作为display_name
      formDataToSubmit.append('display_name', formData.name);
      formDataToSubmit.append('description', formData.description);
      formDataToSubmit.append('website', formData.website);
      formDataToSubmit.append('api_endpoint', formData.api_endpoint || '');
      formDataToSubmit.append('api_key', formData.api_key || '');
      formDataToSubmit.append('api_docs', formData.api_docs || '');
      // 后端需要api_key_required字段，如果提供了api_key则设置为true
      formDataToSubmit.append('api_key_required', formData.api_key ? 'true' : 'false');
      
      // 如果有文件上传，添加文件
      if (file) {
        formDataToSubmit.append('logo', file);
      } else if (mode === 'edit') {
        // 编辑模式下，添加其他字段，logo由后端处理
        // 不要将字符串logo添加到FormData中，这会导致后端无法识别文件
        formDataToSubmit.append('existing_logo', formData.logo);
      }
      
      
      // 调用父组件的保存函数，传递FormData
      await onSave(formDataToSubmit);
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
              <label htmlFor="api_endpoint">API地址</label>
              <input 
                type="url" 
                id="api_endpoint"
                name="api_endpoint"
                value={formData.api_endpoint}
                onChange={handleChange}
                placeholder="https://api.example.com/v1"
                disabled={saving}
              />
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="api_key">API密钥</label>
              <input 
                type="password" 
                id="api_key"
                name="api_key"
                value={formData.api_key}
                onChange={handleChange}
                placeholder="API密钥"
                disabled={saving}
                autoComplete="off"
              />
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="api_docs">API文档地址</label>
              <input 
                type="url" 
                id="api_docs"
                name="api_docs"
                value={formData.api_docs}
                onChange={handleChange}
                placeholder="https://docs.example.com/api"
                disabled={saving}
              />
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

export default SupplierModal;