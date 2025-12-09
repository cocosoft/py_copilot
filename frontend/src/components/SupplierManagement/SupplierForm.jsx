import { useState, useEffect } from 'react';
import '../styles/SupplierModal.css';

const SupplierForm = ({ formData, setFormData, onSubmit, saving, mode = 'add' }) => {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');

  // 当表单数据变化时，更新预览URL
  useEffect(() => {
    if (mode === 'edit' && formData.logo) {
      // 处理logo预览URL，现在后端直接返回前端可访问的路径格式
      const logoUrl = formData.logo || '';
      // 对于/logo/providers/开头的路径或其他相对路径，前端可以直接访问
      // 对于空值或不合法的URL，不设置预览
      const finalPreviewUrl = logoUrl && logoUrl.trim() 
        ? logoUrl 
        : '';
      setPreviewUrl(finalPreviewUrl);
    } else if (mode === 'add') {
      // 重置预览
      setPreviewUrl('');
    }
  }, [formData.logo, mode]);

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
      // 创建FormData对象用于文件上传
      const formDataToSubmit = new FormData();
      
      // 添加所有表单字段
      formDataToSubmit.append('name', formData.name);
      formDataToSubmit.append('description', formData.description);
      formDataToSubmit.append('website', formData.website);
      formDataToSubmit.append('api_endpoint', formData.api_endpoint || '');
      formDataToSubmit.append('api_key', formData.api_key || '');
      formDataToSubmit.append('api_docs', formData.api_docs || '');
      formDataToSubmit.append('category', formData.category || '');
      formDataToSubmit.append('is_active', formData.is_active || true);
      formDataToSubmit.append('api_key_required', formData.api_key ? 'true' : 'false');
      
      // 如果有文件上传，添加文件
      if (file) {
        formDataToSubmit.append('logo', file);
      } else if (mode === 'edit' && formData.logo) {
        // 编辑模式下，如果没有新文件但有旧logo，保持logo字段
        formDataToSubmit.append('logo', formData.logo);
      }
      
      // 调用父组件的提交函数
      await onSubmit(formDataToSubmit);
    } catch (error) {
      console.error('保存供应商失败:', error);
      alert('保存失败，请重试');
    }
  };

  return (
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
          <label htmlFor="category">分类</label>
          <input 
            type="text" 
            id="category"
            name="category"
            value={formData.category || ''}
            onChange={handleChange}
            placeholder="分类（如：国内、国外）"
            disabled={saving}
          />
        </div>
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
          <label htmlFor="api_endpoint">API 端点</label>
          <input 
            type="url" 
            id="api_endpoint"
            name="api_endpoint"
            value={formData.api_endpoint || ''}
            onChange={handleChange}
            placeholder="https://api.example.com/v1"
            disabled={saving}
          />
        </div>
      </div>
      
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="api_key">API 密钥</label>
          <input 
            type="password" 
            id="api_key"
            name="api_key"
            value={formData.api_key || ''}
            onChange={handleChange}
            placeholder="API密钥"
            disabled={saving}
            autoComplete="off"
          />
        </div>
      </div>
      
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="api_docs">API 文档</label>
          <input 
            type="url" 
            id="api_docs"
            name="api_docs"
            value={formData.api_docs || ''}
            onChange={handleChange}
            placeholder="https://docs.example.com/api"
            disabled={saving}
          />
        </div>
      </div>
      
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="is_active">状态</label>
          <select
            id="is_active"
            name="is_active"
            value={formData.is_active ? 'true' : 'false'}
            onChange={(e) => {
              setFormData(prev => ({
                ...prev,
                is_active: e.target.value === 'true'
              }));
            }}
            disabled={saving}
          >
            <option value="true">启用</option>
            <option value="false">禁用</option>
          </select>
        </div>
      </div>
      
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? (mode === 'add' ? '添加中...' : '保存中...') : (mode === 'add' ? '添加' : '保存')}
        </button>
      </div>
    </form>
  );
};

export default SupplierForm;