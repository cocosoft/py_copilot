import React, { useState } from 'react';

const TemplatePreviewModal = ({ 
  isOpen, 
  onClose, 
  template, 
  onApplyTemplate,
  onEditTemplate 
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  if (!isOpen || !template) return null;

  // 处理模态窗口外部点击关闭
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // 处理ESC键关闭
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  // 处理应用模板
  const handleApplyTemplate = () => {
    onApplyTemplate(template);
    onClose();
  };

  // 渲染参数列表
  const renderParameters = () => {
    if (!template.parameters || Object.keys(template.parameters).length === 0) {
      return <div className="no-parameters">此模板没有定义参数</div>;
    }

    const basicParams = {};
    const advancedParams = {};

    // 分离基础参数和高级参数
    Object.entries(template.parameters).forEach(([key, value]) => {
      const isAdvanced = key.includes('advanced') || key.includes('experimental') || 
                        key.includes('custom') || key.includes('debug');
      
      if (isAdvanced && !showAdvanced) {
        advancedParams[key] = value;
      } else {
        basicParams[key] = value;
      }
    });

    return (
      <div className="parameters-list">
        {/* 基础参数 */}
        {Object.keys(basicParams).length > 0 && (
          <div className="parameter-section">
            <h4>基础参数</h4>
            <div className="parameter-grid">
              {Object.entries(basicParams).map(([key, value]) => (
                <div key={key} className="parameter-item">
                  <span className="parameter-name">{key}</span>
                  <span className="parameter-value">{JSON.stringify(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 高级参数 */}
        {Object.keys(advancedParams).length > 0 && (
          <div className="parameter-section">
            <div className="advanced-header">
              <h4>高级参数</h4>
              <button 
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="toggle-advanced"
              >
                {showAdvanced ? '隐藏' : '显示'} ({Object.keys(advancedParams).length}个)
              </button>
            </div>
            
            {showAdvanced && (
              <div className="parameter-grid advanced">
                {Object.entries(advancedParams).map(([key, value]) => (
                  <div key={key} className="parameter-item">
                    <span className="parameter-name">{key}</span>
                    <span className="parameter-value">{JSON.stringify(value)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div 
      className="modal-overlay template-preview-overlay" 
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      <div className="modal-container template-preview-modal">
        <div className="modal-header">
          <h3>模板预览: {template.name}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-content">
          {/* 模板基本信息 */}
          <div className="template-info">
            <div className="info-row">
              <label>模板名称:</label>
              <span>{template.name}</span>
            </div>
            
            {template.description && (
              <div className="info-row">
                <label>描述:</label>
                <span>{template.description}</span>
              </div>
            )}
            
            {template.dimension && (
              <div className="info-row">
                <label>适用维度:</label>
                <span className="dimension-tag">{template.dimension}</span>
              </div>
            )}
            
            {template.model_type && (
              <div className="info-row">
                <label>适用模型类型:</label>
                <span>{template.model_type}</span>
              </div>
            )}
            
            <div className="info-row">
              <label>参数数量:</label>
              <span>{template.parameters ? Object.keys(template.parameters).length : 0}</span>
            </div>
            
            {template.created_at && (
              <div className="info-row">
                <label>创建时间:</label>
                <span>{new Date(template.created_at).toLocaleDateString()}</span>
              </div>
            )}
          </div>

          {/* 参数预览 */}
          <div className="parameters-preview">
            <h4>参数配置</h4>
            {renderParameters()}
          </div>

          {/* 使用统计（如果有） */}
          {template.usage_count !== undefined && (
            <div className="usage-stats">
              <div className="stat-item">
                <span className="stat-label">使用次数:</span>
                <span className="stat-value">{template.usage_count}</span>
              </div>
              
              {template.last_used && (
                <div className="stat-item">
                  <span className="stat-label">最后使用:</span>
                  <span className="stat-value">{new Date(template.last_used).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="modal-actions">
          {onEditTemplate && (
            <button 
              type="button" 
              onClick={() => onEditTemplate(template)}
              className="btn btn-outline"
            >
              编辑模板
            </button>
          )}
          
          <button 
            type="button" 
            onClick={onClose}
            className="btn btn-secondary"
          >
            取消
          </button>
          
          <button 
            type="button" 
            onClick={handleApplyTemplate}
            className="btn btn-primary"
          >
            应用模板
          </button>
        </div>
      </div>
    </div>
  );
};

export default TemplatePreviewModal;