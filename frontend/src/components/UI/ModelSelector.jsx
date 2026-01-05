import React, { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Button, 
  Input, 
  Select, 
  Modal, 
  Card, 
  Badge, 
  Icon,
  Toast,
  ToastContainer 
} from './index';

/**
 * 高级模型选择器组件
 * 支持搜索、过滤、分类、多选等高级功能
 */
const ModelSelector = ({
  models = [],
  selectedModels = [],
  onSelectionChange = () => {},
  mode = 'single', // 'single' | 'multiple'
  placeholder = '选择模型...',
  disabled = false,
  showSearch = true,
  showCategoryFilter = true,
  showSupplierFilter = true,
  showPreview = true,
  maxHeight = '400px',
  className = '',
  size = 'medium', // 'small' | 'medium' | 'large'
  enableFavorites = true,
  enableKeyboard = true,
  customFilter = null,
  // 回调函数
  onModelPreview = null,
  onModelFavorite = null,
  onCreateNew = null,
  // 显示选项
  showCreateButton = false,
  createButtonText = '创建新模型',
}) => {
  // 状态管理
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [favorites, setFavorites] = useState(new Set());
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'
  const [previewModel, setPreviewModel] = useState(null);
  const [keyboardIndex, setKeyboardIndex] = useState(0);
  
  // Refs
  const searchInputRef = useRef(null);
  const containerRef = useRef(null);
  
  // 获取所有分类和供应商选项
  const { categories, suppliers } = useMemo(() => {
    const cats = new Set();
    const sups = new Set();
    
    models.forEach(model => {
      if (model.category) cats.add(model.category);
      if (model.supplier) {
        const supplierName = typeof model.supplier === 'string' 
          ? model.supplier 
          : model.supplier.display_name || model.supplier.name;
        if (supplierName) sups.add(supplierName);
      }
    });
    
    return {
      categories: Array.from(cats).map(cat => ({ value: cat, label: cat })),
      suppliers: Array.from(sups).map(sup => ({ value: sup, label: sup }))
    };
  }, [models]);

  // 过滤模型
  const filteredModels = useMemo(() => {
    let filtered = models;
    
    // 搜索过滤
    if (searchTerm) {
      filtered = filtered.filter(model => 
        model.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.model_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.supplier?.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        model.supplier?.name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // 分类过滤
    if (selectedCategory) {
      filtered = filtered.filter(model => model.category === selectedCategory);
    }
    
    // 供应商过滤
    if (selectedSupplier) {
      filtered = filtered.filter(model => {
        const supplierName = typeof model.supplier === 'string' 
          ? model.supplier 
          : model.supplier.display_name || model.supplier.name;
        return supplierName === selectedSupplier;
      });
    }
    
    // 自定义过滤
    if (customFilter) {
      filtered = filtered.filter(customFilter);
    }
    
    // 收藏模型优先显示
    if (enableFavorites) {
      filtered = [...filtered].sort((a, b) => {
        const aIsFavorite = favorites.has(a.id);
        const bIsFavorite = favorites.has(b.id);
        if (aIsFavorite && !bIsFavorite) return -1;
        if (!aIsFavorite && bIsFavorite) return 1;
        return 0;
      });
    }
    
    return filtered;
  }, [models, searchTerm, selectedCategory, selectedSupplier, customFilter, favorites, enableFavorites]);

  // 处理键盘导航
  useEffect(() => {
    if (!enableKeyboard || !isOpen) return;
    
    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setKeyboardIndex(prev => 
            prev < filteredModels.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setKeyboardIndex(prev => prev > 0 ? prev - 1 : 0);
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          if (filteredModels[keyboardIndex]) {
            handleModelSelect(filteredModels[keyboardIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          setIsOpen(false);
          break;
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, keyboardIndex, filteredModels, enableKeyboard]);

  // 处理点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // 切换收藏状态
  const toggleFavorite = (modelId) => {
    if (!enableFavorites) return;
    
    const newFavorites = new Set(favorites);
    if (newFavorites.has(modelId)) {
      newFavorites.delete(modelId);
    } else {
      newFavorites.add(modelId);
    }
    setFavorites(newFavorites);
    onModelFavorite?.(modelId, newFavorites.has(modelId));
  };

  // 处理模型选择
  const handleModelSelect = (model) => {
    if (mode === 'single') {
      onSelectionChange([model]);
      setIsOpen(false);
    } else {
      const isSelected = selectedModels.some(m => m.id === model.id);
      if (isSelected) {
        onSelectionChange(selectedModels.filter(m => m.id !== model.id));
      } else {
        onSelectionChange([...selectedModels, model]);
      }
    }
  };

  // 清除选择
  const clearSelection = () => {
    onSelectionChange([]);
    setSearchTerm('');
    setSelectedCategory('');
    setSelectedSupplier('');
  };

  // 获取模型显示信息
  const getModelDisplayInfo = (model) => {
    const modelName = model.model_name || model.name || '未知模型';
    const modelId = model.model_id || model.id || '未知ID';
    const supplierName = typeof model.supplier === 'string' 
      ? model.supplier 
      : model.supplier?.display_name || model.supplier?.name || '未知供应商';
    
    return { modelName, modelId, supplierName };
  };

  // 获取模型LOGO
  const getModelLogoUrl = (model) => {
    if (model.logo) {
      return model.logo.startsWith('http') || model.logo.startsWith('/') 
        ? model.logo 
        : `/logos/models/${model.logo}`;
    }
    
    if (model.supplier && model.supplier.logo) {
      return model.supplier.logo.startsWith('http') || model.supplier.logo.startsWith('/')
        ? model.supplier.logo
        : `/logos/providers/${model.supplier.logo}`;
    }
    
    return '/logos/models/default.png';
  };

  // 获取尺寸样式
  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'px-3 py-2 text-sm';
      case 'large':
        return 'px-6 py-4 text-lg';
      default:
        return 'px-4 py-3 text-base';
    }
  };

  // 渲染模型卡片
  const renderModelCard = (model, index) => {
    const { modelName, modelId, supplierName } = getModelDisplayInfo(model);
    const isSelected = selectedModels.some(m => m.id === model.id);
    const isFavorite = favorites.has(model.id);
    const isKeyboardFocused = index === keyboardIndex;
    
    return (
      <motion.div
        key={model.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`
          model-card p-4 border rounded-lg cursor-pointer transition-all duration-200
          ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}
          ${isKeyboardFocused ? 'ring-2 ring-blue-400' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onClick={() => !disabled && handleModelSelect(model)}
        tabIndex={0}
      >
        <div className="flex items-start gap-3">
          <img 
            src={getModelLogoUrl(model)} 
            alt={modelName}
            className="w-12 h-12 rounded-lg object-cover border"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-medium text-gray-900 truncate">{modelName}</h4>
              {model.is_default && (
                <Badge variant="success" size="small">默认</Badge>
              )}
            </div>
            <p className="text-sm text-gray-600 truncate">{supplierName}</p>
            <p className="text-xs text-gray-500">ID: {modelId}</p>
            {model.description && (
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">{model.description}</p>
            )}
          </div>
          <div className="flex flex-col gap-1">
            {enableFavorites && (
              <button
                className={`p-1 rounded ${isFavorite ? 'text-yellow-500' : 'text-gray-400 hover:text-yellow-500'}`}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavorite(model.id);
                }}
              >
                <Icon name="star" size={16} fill={isFavorite} />
              </button>
            )}
            {showPreview && (
              <button
                className="p-1 rounded text-gray-400 hover:text-gray-600"
                onClick={(e) => {
                  e.stopPropagation();
                  setPreviewModel(model);
                }}
              >
                <Icon name="eye" size={16} />
              </button>
            )}
          </div>
        </div>
        
        {/* 模型标签 */}
        {model.category && (
          <div className="mt-3">
            <Badge variant="outline" size="small">{model.category}</Badge>
          </div>
        )}
      </motion.div>
    );
  };

  // 渲染选择指示器
  const renderSelectionIndicator = () => {
    if (mode === 'single') {
      const selectedModel = selectedModels[0];
      if (selectedModel) {
        const { modelName } = getModelDisplayInfo(selectedModel);
        return (
          <div className="flex items-center gap-2">
            <img 
              src={getModelLogoUrl(selectedModel)} 
              alt={modelName}
              className="w-5 h-5 rounded object-cover"
            />
            <span className="truncate">{modelName}</span>
          </div>
        );
      }
      return <span className="text-gray-500">{placeholder}</span>;
    } else {
      if (selectedModels.length === 0) {
        return <span className="text-gray-500">{placeholder}</span>;
      }
      return (
        <div className="flex items-center gap-2">
          <span>已选择 {selectedModels.length} 个模型</span>
          {selectedModels.length > 0 && (
            <button
              className="text-blue-500 hover:text-blue-700 text-sm"
              onClick={(e) => {
                e.stopPropagation();
                clearSelection();
              }}
            >
              清除
            </button>
          )}
        </div>
      );
    }
  };

  return (
    <div className={`model-selector ${className}`} ref={containerRef}>
      <ToastContainer />
      
      {/* 选择触发器 */}
      <div
        className={`
          selector-trigger border rounded-lg cursor-pointer flex items-center justify-between
          ${getSizeClasses()}
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white hover:bg-gray-50'}
          ${isOpen ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-300'}
        `}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <div className="flex-1 truncate">
          {renderSelectionIndicator()}
        </div>
        <Icon 
          name="chevron-down" 
          size={16} 
          className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </div>

      {/* 下拉面板 */}
      <AnimatePresence>
        {isOpen && !disabled && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
            style={{ maxHeight }}
          >
            {/* 搜索和过滤栏 */}
            {(showSearch || showCategoryFilter || showSupplierFilter || showCreateButton) && (
              <div className="p-4 border-b border-gray-100 space-y-3">
                {showSearch && (
                  <Input
                    ref={searchInputRef}
                    placeholder="搜索模型..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    icon={<Icon name="search" size={16} />}
                    size="small"
                  />
                )}
                
                <div className="flex gap-3">
                  {showCategoryFilter && categories.length > 0 && (
                    <div className="flex-1">
                      <Select
                        options={[
                          { value: '', label: '所有分类' },
                          ...categories
                        ]}
                        value={selectedCategory}
                        onChange={setSelectedCategory}
                        placeholder="选择分类"
                        size="small"
                      />
                    </div>
                  )}
                  
                  {showSupplierFilter && suppliers.length > 0 && (
                    <div className="flex-1">
                      <Select
                        options={[
                          { value: '', label: '所有供应商' },
                          ...suppliers
                        ]}
                        value={selectedSupplier}
                        onChange={setSelectedSupplier}
                        placeholder="选择供应商"
                        size="small"
                      />
                    </div>
                  )}
                </div>
                
                {showCreateButton && onCreateNew && (
                  <Button
                    variant="outline"
                    size="small"
                    onClick={onCreateNew}
                    className="w-full"
                  >
                    <Icon name="plus" size={16} />
                    {createButtonText}
                  </Button>
                )}
              </div>
            )}

            {/* 模型列表 */}
            <div className="overflow-y-auto" style={{ maxHeight: 'calc(100% - 120px)' }}>
              {filteredModels.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Icon name="inbox" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>没有找到匹配的模型</p>
                </div>
              ) : (
                <div className="p-2 space-y-2">
                  {filteredModels.map((model, index) => renderModelCard(model, index))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 模型预览模态框 */}
      {previewModel && (
        <Modal
          isOpen={!!previewModel}
          onClose={() => setPreviewModel(null)}
          title="模型详情"
          size="large"
        >
          <div className="space-y-6">
            {/* 模型基本信息 */}
            <div className="flex items-start gap-4">
              <img 
                src={getModelLogoUrl(previewModel)} 
                alt={previewModel.model_name || previewModel.name}
                className="w-16 h-16 rounded-lg object-cover border"
              />
              <div className="flex-1">
                <h3 className="text-xl font-semibold mb-2">
                  {previewModel.model_name || previewModel.name}
                </h3>
                <p className="text-gray-600 mb-2">
                  {typeof previewModel.supplier === 'string' 
                    ? previewModel.supplier 
                    : previewModel.supplier?.display_name || previewModel.supplier?.name}
                </p>
                <p className="text-sm text-gray-500">ID: {previewModel.model_id || previewModel.id}</p>
              </div>
            </div>

            {/* 模型描述 */}
            {previewModel.description && (
              <div>
                <h4 className="font-medium mb-2">模型描述</h4>
                <p className="text-gray-700">{previewModel.description}</p>
              </div>
            )}

            {/* 模型属性 */}
            <div className="grid grid-cols-2 gap-4">
              {previewModel.category && (
                <div>
                  <label className="text-sm font-medium text-gray-500">分类</label>
                  <p className="text-gray-900">{previewModel.category}</p>
                </div>
              )}
              {previewModel.model_type && (
                <div>
                  <label className="text-sm font-medium text-gray-500">类型</label>
                  <p className="text-gray-900">{previewModel.model_type}</p>
                </div>
              )}
              {previewModel.version && (
                <div>
                  <label className="text-sm font-medium text-gray-500">版本</label>
                  <p className="text-gray-900">{previewModel.version}</p>
                </div>
              )}
              {previewModel.max_tokens && (
                <div>
                  <label className="text-sm font-medium text-gray-500">最大Token</label>
                  <p className="text-gray-900">{previewModel.max_tokens.toLocaleString()}</p>
                </div>
              )}
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-3 pt-4 border-t">
              <Button
                onClick={() => {
                  handleModelSelect(previewModel);
                  setPreviewModel(null);
                }}
                disabled={disabled}
              >
                {mode === 'single' ? '选择此模型' : '添加到此选择'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setPreviewModel(null)}
              >
                关闭
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default ModelSelector;