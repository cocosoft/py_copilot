import React, { useState, useEffect } from 'react';
import './SkillManagement.css';

function SkillFormModal({ skill, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    version: '1.0.0',
    license: '',
    tags: [],
    source: 'local',
    source_url: '',
    content: '',
    parameters_schema: {},
    icon: '',
    author: '',
    documentation_url: '',
    requirements: [],
    config: {},
  });
  
  const [newTag, setNewTag] = useState('');
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (skill) {
      setFormData({
        name: skill.name || '',
        display_name: skill.display_name || '',
        description: skill.description || '',
        version: skill.version || '1.0.0',
        license: skill.license || '',
        tags: Array.isArray(skill.tags) ? [...skill.tags] : [],
        source: skill.source || 'local',
        source_url: skill.source_url || '',
        content: skill.content || '',
        parameters_schema: skill.parameters_schema || {},
        icon: skill.icon || '',
        author: skill.author || '',
        documentation_url: skill.documentation_url || '',
        requirements: Array.isArray(skill.requirements) ? [...skill.requirements] : [],
        config: skill.config || {},
      });
    }
  }, [skill]);

  const validateForm = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = '技能名称不能为空';
    } else if (formData.name.length > 100) {
      newErrors.name = '技能名称不能超过100个字符';
    }
    if (!formData.version.trim()) {
      newErrors.version = '版本号不能为空';
    } else if (!/^\d+\.\d+\.\d+$/.test(formData.version)) {
      newErrors.version = '版本号格式不正确，应为X.Y.Z格式';
    } else if (formData.version.length > 50) {
      newErrors.version = '版本号不能超过50个字符';
    }
    if (!formData.source.trim()) {
      newErrors.source = '技能来源不能为空';
    }
    if (formData.display_name && formData.display_name.length > 100) {
      newErrors.display_name = '显示名称不能超过100个字符';
    }
    if (formData.license && formData.license.length > 100) {
      newErrors.license = '许可证名称不能超过100个字符';
    }
    if (formData.tags.length > 10) {
      newErrors.tags = '标签数量不能超过10个';
    }
    if (formData.source_url && formData.source_url.length > 500) {
      newErrors.source_url = '来源URL不能超过500个字符';
    }
    if (formData.author && formData.author.length > 100) {
      newErrors.author = '作者名称不能超过100个字符';
    }
    if (formData.documentation_url && formData.documentation_url.length > 500) {
      newErrors.documentation_url = '文档URL不能超过500个字符';
    }
    if (formData.icon && formData.icon.length > 200) {
      newErrors.icon = '图标URL不能超过200个字符';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      onClose();
    } catch (error) {
      setErrors({
        submit: error.message || '提交失败，请重试'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="skill-modal-backdrop" onClick={handleBackdropClick}>
      <div className="skill-modal skill-form-modal">
        <div className="skill-modal-header">
          <h2>{skill ? '编辑技能' : '创建技能'}</h2>
          <button className="close-btn" onClick={onClose}>
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="skill-form">
          {errors.submit && (
            <div className="form-error submit-error">{errors.submit}</div>
          )}
          
          <div className="form-group">
            <label htmlFor="name">技能名称 *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              className={errors.name ? 'input-error' : ''}
              placeholder="输入技能名称"
            />
            {errors.name && <div className="form-error">{errors.name}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="description">技能描述 *</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              className={errors.description ? 'input-error' : ''}
              placeholder="输入技能描述"
              rows="4"
            />
            {errors.description && <div className="form-error">{errors.description}</div>}
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="version">版本号 *</label>
              <input
                type="text"
                id="version"
                name="version"
                value={formData.version}
                onChange={handleInputChange}
                className={errors.version ? 'input-error' : ''}
                placeholder="例如：1.0.0"
              />
              {errors.version && <div className="form-error">{errors.version}</div>}
            </div>
            
            <div className="form-group">
              <label htmlFor="license">许可证</label>
              <input
                type="text"
                id="license"
                name="license"
                value={formData.license}
                onChange={handleInputChange}
                placeholder="例如：MIT"
              />
            </div>
          </div>
          
          <div className="form-group">
            <label>标签</label>
            <div className="tag-input-container">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                placeholder="添加标签"
              />
              <button
                type="button"
                className="add-tag-btn"
                onClick={handleAddTag}
                disabled={!newTag.trim()}
              >
                添加
              </button>
            </div>
            
            <div className="tags-list">
              {formData.tags.map(tag => (
                <span key={tag} className="tag-item">
                  {tag}
                  <button
                    type="button"
                    className="remove-tag-btn"
                    onClick={() => handleRemoveTag(tag)}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            {errors.tags && <div className="form-error">{errors.tags}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="display_name">显示名称</label>
            <input
              type="text"
              id="display_name"
              name="display_name"
              value={formData.display_name}
              onChange={handleInputChange}
              className={errors.display_name ? 'input-error' : ''}
              placeholder="输入技能显示名称"
            />
            {errors.display_name && <div className="form-error">{errors.display_name}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="source">技能来源 *</label>
            <select
              id="source"
              name="source"
              value={formData.source}
              onChange={handleInputChange}
              className={errors.source ? 'input-error' : ''}
            >
              <option value="local">本地</option>
              <option value="remote">远程</option>
              <option value="built-in">内置</option>
            </select>
            {errors.source && <div className="form-error">{errors.source}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="source_url">来源URL</label>
            <input
              type="url"
              id="source_url"
              name="source_url"
              value={formData.source_url}
              onChange={handleInputChange}
              className={errors.source_url ? 'input-error' : ''}
              placeholder="输入技能来源URL"
            />
            {errors.source_url && <div className="form-error">{errors.source_url}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="content">技能内容 *</label>
            <textarea
              id="content"
              name="content"
              value={formData.content}
              onChange={handleInputChange}
              className="code-editor"
              placeholder="输入技能代码内容"
              rows="10"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="author">作者</label>
            <input
              type="text"
              id="author"
              name="author"
              value={formData.author}
              onChange={handleInputChange}
              className={errors.author ? 'input-error' : ''}
              placeholder="输入作者名称"
            />
            {errors.author && <div className="form-error">{errors.author}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="documentation_url">文档URL</label>
            <input
              type="url"
              id="documentation_url"
              name="documentation_url"
              value={formData.documentation_url}
              onChange={handleInputChange}
              className={errors.documentation_url ? 'input-error' : ''}
              placeholder="输入文档URL"
            />
            {errors.documentation_url && <div className="form-error">{errors.documentation_url}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="icon">图标URL</label>
            <input
              type="text"
              id="icon"
              name="icon"
              value={formData.icon}
              onChange={handleInputChange}
              className={errors.icon ? 'input-error' : ''}
              placeholder="输入图标URL"
            />
            {errors.icon && <div className="form-error">{errors.icon}</div>}
          </div>
          
          <div className="form-group">
            <label htmlFor="parameters_schema">参数模式 (JSON)</label>
            <textarea
              id="parameters_schema"
              name="parameters_schema"
              value={JSON.stringify(formData.parameters_schema, null, 2)}
              onChange={(e) => {
                try {
                  setFormData(prev => ({
                    ...prev,
                    parameters_schema: JSON.parse(e.target.value || '{}')
                  }));
                } catch (error) {
                  // 忽略JSON解析错误
                }
              }}
              className="code-editor"
              placeholder="输入JSON格式的参数模式"
              rows="5"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="requirements">依赖要求 (JSON)</label>
            <textarea
              id="requirements"
              name="requirements"
              value={JSON.stringify(formData.requirements, null, 2)}
              onChange={(e) => {
                try {
                  setFormData(prev => ({
                    ...prev,
                    requirements: JSON.parse(e.target.value || '[]')
                  }));
                } catch (error) {
                  // 忽略JSON解析错误
                }
              }}
              className="code-editor"
              placeholder="输入JSON格式的依赖要求"
              rows="5"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="config">配置信息 (JSON)</label>
            <textarea
              id="config"
              name="config"
              value={JSON.stringify(formData.config, null, 2)}
              onChange={(e) => {
                try {
                  setFormData(prev => ({
                    ...prev,
                    config: JSON.parse(e.target.value || '{}')
                  }));
                } catch (error) {
                  // 忽略JSON解析错误
                }
              }}
              className="code-editor"
              placeholder="输入JSON格式的配置信息"
              rows="5"
            />
          </div>
          
          <div className="skill-modal-footer">
            <button type="button" className="cancel-btn" onClick={onClose} disabled={isSubmitting}>
              取消
            </button>
            <button type="submit" className="submit-btn" disabled={isSubmitting}>
              {isSubmitting ? '提交中...' : (skill ? '保存修改' : '创建技能')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SkillFormModal;
