import React, { useState, useRef } from 'react';

/**
 * 模型选择下拉列表组件
 * @param {Object} props - 组件属性
 * @param {Array} props.models - 模型列表
 * @param {Object} props.selectedModel - 当前选中的模型
 * @param {Function} props.onModelSelect - 模型选择回调函数
 * @param {string} props.className - 自定义类名
 * @param {string} props.placeholder - 占位文本
 * @param {boolean} props.disabled - 是否禁用
 * @param {Function} props.getModelLogoUrl - 自定义获取模型LOGO URL的函数
 * @param {Function} props.getModelBadge - 自定义获取模型徽章的函数
 */
const ModelSelectDropdown = ({ 
  models = [], 
  selectedModel = null, 
  onModelSelect = () => {}, 
  className = '', 
  placeholder = '-- 请选择模型 --',
  disabled = false,
  getModelLogoUrl = null,
  getModelBadge = null
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const selectRef = useRef(null);
  
  // 默认的获取模型LOGO URL函数
  const defaultGetModelLogoUrl = (model) => {
    // 优先使用模型LOGO
    if (model.logo) {
      // 检查是否已经是完整URL
      if (model.logo.startsWith('http') || model.logo.startsWith('/')) {
        return model.logo;
      }
      // 否则添加完整路径
      return `/logos/models/${model.logo}`;
    }
    
    // 如果没有模型LOGO，使用供应商LOGO
    if (model.supplier_logo) {
      if (model.supplier_logo.startsWith('http') || model.supplier_logo.startsWith('/')) {
        return model.supplier_logo;
      }
      return `/logos/providers/${model.supplier_logo}`;
    }
    
    // 如果都没有，返回默认图标
    return '/logos/models/default.png';
  };
  
  // 使用传入的getModelLogoUrl函数，如果没有则使用默认函数
  const logoUrlFunction = getModelLogoUrl || defaultGetModelLogoUrl;
  
  // 处理点击外部关闭下拉列表
  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // 处理模型选择
  const handleSelectModel = (model) => {
    onModelSelect(model);
    setIsDropdownOpen(false);
  };
  
  return (
    <div className={`custom-select-container ${className}`} ref={selectRef}>
      <div 
        className={`custom-select ${isDropdownOpen ? 'open' : ''} ${disabled ? 'disabled' : ''}`}
        onClick={() => !disabled && setIsDropdownOpen(!isDropdownOpen)}
      >
        <div className="custom-select__selected">
          {selectedModel ? (
            <div className="model-info">
              <img 
                src={logoUrlFunction(selectedModel)} 
                alt={selectedModel.model_name || '模型LOGO'} 
                className="model-logo"
              />
              <div className="model-details">
                <span className="model-name">
                  {selectedModel.model_name || selectedModel.name || '未知模型'} 
                  ({selectedModel.model_id || selectedModel.id || '未知ID'})
                </span>
                <span className="supplier-name">
                  {selectedModel.supplier_display_name || selectedModel.supplier_name || 
                   (selectedModel.supplier && (selectedModel.supplier.display_name || selectedModel.supplier.name)) || 
                   selectedModel.supplierDisplayName || 
                   selectedModel.supplierName || 
                   '未知供应商'}
                </span>
              </div>
              {getModelBadge && getModelBadge(selectedModel)}
            </div>
          ) : (
            <span>{placeholder}</span>
          )}
        </div>
        <div className="custom-select__arrow">▼</div>
      </div>
      {isDropdownOpen && !disabled && (
        <div className="custom-select__dropdown">
          {models.length === 0 ? (
            <div className="custom-select__option">暂无模型数据</div>
          ) : (
            models.map(model => (
              <div 
                key={model.id} 
                className={`custom-select__option ${selectedModel?.id === model.id ? 'selected' : ''}`}
                onClick={() => handleSelectModel(model)}
              >
                <img 
                  src={logoUrlFunction(model)} 
                  alt={model.model_name || '模型LOGO'} 
                  className="model-logo"
                />
                <div className="option-content">
                  <span className="model-name">
                    {model.model_name || model.name || '未知模型'} 
                    ({model.model_id || model.id || '未知ID'})
                  </span>
                  <span className="supplier-name">
                    {model.supplier_display_name || model.supplier_name || 
                     (model.supplier && (model.supplier.display_name || model.supplier.name)) || 
                     model.supplierDisplayName || 
                     model.supplierName || 
                     '未知供应商'}
                  </span>
                </div>
                {getModelBadge && getModelBadge(model)}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default ModelSelectDropdown;