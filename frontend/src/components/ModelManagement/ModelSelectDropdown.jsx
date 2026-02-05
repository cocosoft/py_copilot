import React, { useState, useRef, useEffect, useMemo } from 'react';
import ModelDataManager from '../../services/modelDataManager';

// 组件样式
const styles = `
  /* 基础样式 */
  .custom-select-container {
    position: relative;
    display: inline-block;
  }
  
  .custom-select {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    background-color: #ffffff;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .custom-select:hover {
    border-color: #007bff;
  }
  
  .custom-select.open {
    border-color: #007bff;
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .custom-select.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .custom-select__selected {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
  }
  
  .model-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .model-logo {
    width: 32px;
    height: 32px;
    border-radius: 4px;
    object-fit: contain;
  }
  
  .model-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .model-name {
    font-size: 14px;
    font-weight: 500;
    color: #333333;
  }
  
  .supplier-name {
    font-size: 12px;
    color: #666666;
  }
  
  .custom-select__arrow {
    font-size: 10px;
    color: #666666;
    transition: transform 0.2s ease;
  }
  
  .custom-select.open .custom-select__arrow {
    transform: rotate(180deg);
  }
  
  .custom-select__dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #e0e0e0;
    border-top: none;
    border-radius: 0 0 6px 6px;
    background-color: #ffffff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
  }
  
  .custom-select__dropdown.dropdown-up {
    top: auto;
    bottom: 100%;
    border-top: 1px solid #e0e0e0;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
  }
  
  .custom-select__search {
    padding: 8px 12px;
    border-bottom: 1px solid #e0e0e0;
  }
  
  .search-input {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .custom-select__option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }
  
  .custom-select__option:hover {
    background-color: #f8f9fa;
  }
  
  .custom-select__option.selected {
    background-color: #e3f2fd;
    border-left: 3px solid #007bff;
  }
  
  .option-content {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
  }
  
  /* 单行显示样式 */
  .custom-select-container.single-line {
    max-width: 250px;
  }
  
  .custom-select.single-line {
    padding: 6px 10px;
  }
  
  .model-info.single-line {
    gap: 6px;
  }
  
  .model-logo.single-line {
    width: 24px;
    height: 24px;
  }
  
  .model-details.single-line {
    flex-direction: row;
    align-items: center;
    gap: 6px;
    flex: 1;
    overflow: hidden;
  }
  
  .model-name.single-line {
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 2;
    min-width: 0;
  }
  
  .supplier-name.single-line {
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
    min-width: 0;
    max-width: none;
  }
  
  /* 加载状态 */
  .custom-select__option.loading {
    justify-content: center;
    color: #666666;
    font-style: italic;
  }
  
  /* 深色模式 */
  [data-theme="dark"] .custom-select {
    border-color: #444444;
    background-color: #2d2d2d;
  }
  
  [data-theme="dark"] .custom-select:hover {
    border-color: #007bff;
  }
  
  [data-theme="dark"] .custom-select.open {
    border-color: #007bff;
  }
  
  [data-theme="dark"] .model-name {
    color: #e0e0e0;
  }
  
  [data-theme="dark"] .supplier-name {
    color: #999999;
  }
  
  [data-theme="dark"] .custom-select__arrow {
    color: #999999;
  }
  
  [data-theme="dark"] .custom-select__dropdown {
    border-color: #444444;
    background-color: #2d2d2d;
  }
  
  [data-theme="dark"] .custom-select__option:hover {
    background-color: #3d3d3d;
  }
  
  [data-theme="dark"] .custom-select__option.selected {
    background-color: #1a3a5c;
  }
  
  [data-theme="dark"] .search-input {
    border-color: #444444;
    background-color: #3d3d3d;
    color: #e0e0e0;
  }
`;

// 注入样式
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = styles;
  document.head.appendChild(styleElement);
}

/**
 * 模型选择下拉列表组件
 * @param {Object} props - 组件属性
 * @param {Array} props.models - 模型列表（如果传入则使用，否则自动从API加载）
 * @param {Object} props.selectedModel - 当前选中的模型
 * @param {Function} props.onModelSelect - 模型选择回调函数
 * @param {string} props.className - 自定义类名
 * @param {string} props.placeholder - 占位文本
 * @param {boolean} props.disabled - 是否禁用
 * @param {Function} props.getModelLogoUrl - 自定义获取模型LOGO URL的函数
 * @param {Function} props.getModelBadge - 自定义获取模型徽章的函数
 * @param {string} props.scene - 使用场景
 * @param {string} props.dropDirection - 下拉方向：'down' 或 'up'
 * @param {boolean} props.singleLine - 是否单行显示
 */
const ModelSelectDropdown = ({ 
  models = null, 
  selectedModel = null, 
  onModelSelect = () => {}, 
  className = '', 
  placeholder = '-- 请选择模型 --',
  disabled = false,
  getModelLogoUrl = null,
  getModelBadge = null,
  scene = 'chat',
  dropDirection = 'down',
  singleLine = false
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [allModels, setAllModels] = useState([]);
  const selectRef = useRef(null);
  
  // 加载模型数据
  useEffect(() => {
    const loadModels = async () => {
      if (models) {
        // 如果传入了models，直接使用
        setAllModels(models);
        return;
      }
      
      setIsLoading(true);
      try {
        // 从API加载数据
        const loadedModels = await ModelDataManager.loadModels(scene);
        setAllModels(loadedModels);
      } catch (error) {
        console.error('加载模型失败:', error);
        setAllModels([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadModels();
  }, [scene, models]);
  
  // 默认的获取模型LOGO URL函数
  const defaultGetModelLogoUrl = (model) => {
    // 优先使用模型LOGO，但排除默认值
    if (model.logo !== null && model.logo !== undefined && model.logo !== '' && model.logo !== 'logos/models/default.png' && model.logo !== '/logos/models/default.png' && model.logo !== 'default.png') {
      // 检查是否已经是完整URL
      if (model.logo.startsWith('http')) {
        return model.logo;
      }
      // 检查是否已经是完整路径
      if (model.logo.startsWith('/')) {
        return model.logo;
      }
      // 检查是否已经包含 logos/models/ 前缀
      if (model.logo.startsWith('logos/models/')) {
        return `/${model.logo}`;
      }
      // 否则添加完整路径
      return `/logos/models/${model.logo}`;
    }
    
    // 如果没有模型LOGO或模型LOGO是默认值，使用供应商LOGO（优先检查 supplier_logo 字段）
    if (model.supplier_logo !== null && model.supplier_logo !== undefined && model.supplier_logo !== '') {
      // 检查是否已经是完整URL
      if (model.supplier_logo.startsWith('http')) {
        return model.supplier_logo;
      }
      // 检查是否已经是完整路径
      if (model.supplier_logo.startsWith('/')) {
        return model.supplier_logo;
      }
      // 检查是否已经包含 logos/providers/ 前缀
      if (model.supplier_logo.startsWith('logos/providers/')) {
        return `/${model.supplier_logo}`;
      }
      // 否则添加完整路径
      return `/logos/providers/${model.supplier_logo}`;
    }
    
    // 如果 supplier_logo 不存在，检查 supplier.logo 字段
    if (model.supplier && model.supplier.logo !== null && model.supplier.logo !== undefined && model.supplier.logo !== '') {
      // 检查是否已经是完整URL
      if (model.supplier.logo.startsWith('http')) {
        return model.supplier.logo;
      }
      // 检查是否已经是完整路径
      if (model.supplier.logo.startsWith('/')) {
        return model.supplier.logo;
      }
      // 检查是否已经包含 logos/providers/ 前缀
      if (model.supplier.logo.startsWith('logos/providers/')) {
        return `/${model.supplier.logo}`;
      }
      // 否则添加完整路径
      return `/logos/providers/${model.supplier.logo}`;
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
  
  // 搜索过滤
  const filteredModels = useMemo(() => {
    if (!searchQuery) {
      return allModels;
    }
    
    const query = searchQuery.toLowerCase();
    return allModels.filter(model => {
      return (
        (model.model_name || '').toLowerCase().includes(query) ||
        (model.model_id || '').toLowerCase().includes(query) ||
        (model.supplier_name || '').toLowerCase().includes(query) ||
        (model.supplier_display_name || '').toLowerCase().includes(query) ||
        (model.description || '').toLowerCase().includes(query)
      );
    });
  }, [allModels, searchQuery]);
  
  // 按供应商分组
  const groupedModels = useMemo(() => {
    return ModelDataManager.groupModelsBySupplier(filteredModels);
  }, [filteredModels]);
  
  // 处理模型选择
  const handleSelectModel = (model) => {
    onModelSelect(model);
    setIsDropdownOpen(false);
  };
  
  return (
    <div className={`custom-select-container ${className} ${singleLine ? 'single-line' : ''}`} ref={selectRef}>
      <div 
        className={`custom-select ${isDropdownOpen ? 'open' : ''} ${disabled ? 'disabled' : ''} ${singleLine ? 'single-line' : ''}`}
        onClick={() => !disabled && setIsDropdownOpen(!isDropdownOpen)}
      >
        <div className="custom-select__selected">
          {selectedModel ? (
            <div className={`model-info horizontal ${singleLine ? 'single-line' : ''}`}>
              <img 
                src={logoUrlFunction(selectedModel)} 
                alt={selectedModel.model_name || '模型LOGO'} 
                className={`model-logo ${singleLine ? 'single-line' : ''}`}
                onError={(e) => {
                  // 模型LOGO加载失败时，尝试使用供应商LOGO
                  const supplierLogoUrl = () => {
                    if (selectedModel.supplier_logo) {
                      return selectedModel.supplier_logo.startsWith('http') || selectedModel.supplier_logo.startsWith('/') 
                        ? selectedModel.supplier_logo 
                        : `/logos/providers/${selectedModel.supplier_logo}`;
                    }
                    if (selectedModel.supplier && selectedModel.supplier.logo) {
                      return selectedModel.supplier.logo.startsWith('http') || selectedModel.supplier.logo.startsWith('/') 
                        ? selectedModel.supplier.logo 
                        : `/logos/providers/${selectedModel.supplier.logo}`;
                    }
                    return '/logos/models/default.png';
                  };
                  e.target.src = supplierLogoUrl();
                }}
              />
              <div className={`model-details ${singleLine ? 'single-line' : ''}`}>
                <span className={`model-name ${singleLine ? 'single-line' : ''}`}>
                  {selectedModel.model_name || selectedModel.name || '未知模型'}{!singleLine && ` (${selectedModel.model_id || selectedModel.id || '未知ID'})`}
                </span>
                <span className={`supplier-name ${singleLine ? 'single-line' : ''}`}>
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
        <div className={`custom-select__dropdown ${dropDirection === 'up' ? 'dropdown-up' : ''}`}>
          {/* 搜索框 */}
          <div className="custom-select__search">
            <input 
              type="text" 
              placeholder="搜索模型或供应商..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
          
          {isLoading ? (
            <div className="custom-select__option loading">加载中...</div>
          ) : filteredModels.length === 0 ? (
            <div className="custom-select__option">暂无模型数据</div>
          ) : (
            filteredModels.map(model => (
              <div 
                key={model.id} 
                className={`custom-select__option ${selectedModel?.id === model.id ? 'selected' : ''}`}
                onClick={() => handleSelectModel(model)}
              >
                <img 
                  src={logoUrlFunction(model)} 
                  alt={model.model_name || '模型LOGO'} 
                  className="model-logo"
                  onError={(e) => {
                    // 模型LOGO加载失败时，尝试使用供应商LOGO
                    const supplierLogoUrl = () => {
                      if (model.supplier_logo) {
                        if (model.supplier_logo.startsWith('http')) {
                          return model.supplier_logo;
                        }
                        if (model.supplier_logo.startsWith('/')) {
                          return model.supplier_logo;
                        }
                        if (model.supplier_logo.startsWith('logos/providers/')) {
                          return `/${model.supplier_logo}`;
                        }
                        return `/logos/providers/${model.supplier_logo}`;
                      }
                      if (model.supplier && model.supplier.logo) {
                        if (model.supplier.logo.startsWith('http')) {
                          return model.supplier.logo;
                        }
                        if (model.supplier.logo.startsWith('/')) {
                          return model.supplier.logo;
                        }
                        if (model.supplier.logo.startsWith('logos/providers/')) {
                          return `/${model.supplier.logo}`;
                        }
                        return `/logos/providers/${model.supplier.logo}`;
                      }
                      return '/logos/models/default.png';
                    };
                    e.target.src = supplierLogoUrl();
                  }}
                />
                <div className="option-content">
                  <span className="model-name">
                    {model.model_name || model.name || '未知模型'}{!singleLine && ` (${model.model_id || model.id || '未知ID'})`}
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