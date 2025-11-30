import React, { useState, useEffect } from 'react';
import '../../styles/ModelModal.css';

const ModelModal = ({ isOpen, onClose, onSave, model = null, mode = 'add', isFirstModel = false }) => {
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    contextWindow: 8000,
    isDefault: false
  });
  const [saving, setSaving] = useState(false);

  // 当传入的model变化时，更新表单数据
  useEffect(() => {
    if (mode === 'edit' && model) {
      setFormData({
        id: model.id || model.model_id || '',
        name: model.name || '',
        description: model.description || '',
        contextWindow: model.contextWindow || model.context_window || 8000,
        isDefault: model.isDefault || model.is_default || false
      });
    } else if (mode === 'add') {
      // 重置表单数据
      setFormData({
        id: '',
        name: '',
        description: '',
        contextWindow: 8000,
        isDefault: isFirstModel // 如果是第一个模型，默认设为默认模型
      });
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

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 验证必填字段
    if (!formData.id || !formData.name) {
      alert('请填写模型ID和模型名称');
      return;
    }
    
    try {
      setSaving(true);
      
      // 准备传递给父组件的数据
      const modelData = {
        ...formData,
        // 确保包含后端需要的model_id字段
        model_id: formData.id,
        // 确保字段命名一致性和类型转换
        contextWindow: parseInt(formData.contextWindow) || 8000,
        isDefault: formData.isDefault || false
      };
      
      console.log('ModelModal: 准备调用onSave，提交的数据:', modelData);
      
      // 调用父组件的保存函数
      await onSave(modelData);
      console.log('ModelModal: onSave调用成功，准备关闭模态窗口');
      onClose();
    } catch (error) {
      console.error('ModelModal: 保存模型失败:', error);
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
              <label htmlFor="id">模型ID: {mode === 'add' && <span className="required">*</span>}</label>
              <input 
                type="text" 
                id="id"
                name="id"
                value={formData.id}
                onChange={handleChange}
                placeholder="模型ID"
                disabled={mode === 'edit' || saving}
                required={mode === 'add'}
              />
            </div>
            <div className="form-group">
              <label htmlFor="name">模型名称: <span className="required">*</span></label>
              <input 
                type="text" 
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="模型名称"
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
              placeholder="模型描述"
              rows="3"
              disabled={saving}
            />
          </div>
          
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
              disabled={saving}
            />
          </div>
          
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