import React, { useState, useEffect } from 'react';
import { getImageUrl } from '../../config/imageConfig';
import { categoryApi, modelApi, dimensionHierarchyApi, parameterTemplatesApi } from '../../utils/api';
import SimplifiedCategorySelector from './SimplifiedCategorySelector';
import TemplatePreviewModal from './TemplatePreviewModal';
import '../../styles/ModelModal.css';

const ModelModalV2 = ({ isOpen, onClose, onSave, model = null, mode = 'add', isFirstModel = false }) => {
  // 表单状态管理
  const [formData, setFormData] = useState({
    model_id: '',
    model_name: '',
    description: '',
    contextWindow: 8000,
    max_tokens: 1000,
    isDefault: false,
    is_active: true
  });
  
  // 维度配置状态
  const [dimensionConfigs, setDimensionConfigs] = useState({});
  const [activeDimension, setActiveDimension] = useState('');
  const [useSimplifiedSelector, setUseSimplifiedSelector] = useState(true);
  const [categorySelections, setCategorySelections] = useState({});
  
  // UI状态
  const [logo, setLogo] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // 模板预览状态
  const [templatePreview, setTemplatePreview] = useState({
    isOpen: false,
    template: null
  });
  
  // 数据状态
  const [dimensions, setDimensions] = useState([]);
  const [categoriesByDimension, setCategoriesByDimension] = useState({});
  const [parameterTemplates, setParameterTemplates] = useState([]);

  // 初始化数据
  useEffect(() => {
    if (isOpen) {
      initializeData();
    }
  }, [isOpen, mode, model]); // 添加依赖以确保编辑模式下模型数据正确加载

  // 初始化所有数据
  const initializeData = async () => {
    try {
      setLoading(true);
      
      // 并行加载所有必要数据
      const [hierarchyData, templatesData, categoriesApiData] = await Promise.all([
        dimensionHierarchyApi.getHierarchy(),
        parameterTemplatesApi.getTemplates(),
        categoryApi.getCategoriesByDimension()
      ]);
      
      // 调试：输出各API响应数据
      console.log('层次结构数据:', hierarchyData);
      console.log('分类API数据:', categoriesApiData);
      console.log('分类API数据类型:', typeof categoriesApiData);
      console.log('分类API数据键:', categoriesApiData ? Object.keys(categoriesApiData) : '无数据');
      // 输出每个维度的分类数量
      if (categoriesApiData && typeof categoriesApiData === 'object') {
        Object.keys(categoriesApiData).forEach(dimension => {
          const categoryCount = Array.isArray(categoriesApiData[dimension]) ? categoriesApiData[dimension].length : 0;
          console.log(`维度 ${dimension} 的分类数量: ${categoryCount}`);
        });
      }
      
      // 从分类API数据中提取维度信息（优先使用分类API数据）
      let dimensionsData = [];
      let categoriesData = {};
      
      // 首先检查分类API数据，如果有数据，优先使用它来构建维度和分类信息
      if (categoriesApiData && typeof categoriesApiData === 'object' && Object.keys(categoriesApiData).length > 0) {
        console.log('优先使用分类API数据构建维度信息');
        dimensionsData = Object.keys(categoriesApiData);
        
        // 构建按维度组织的分类数据
        dimensionsData.forEach(dimension => {
          categoriesData[dimension] = Array.isArray(categoriesApiData[dimension]) ? categoriesApiData[dimension] : [];
        });
      } 
      // 如果分类API数据为空，再尝试使用层次结构数据
      else if (hierarchyData && hierarchyData.dimensions && typeof hierarchyData.dimensions === 'object') {
        console.log('使用层次结构数据构建维度信息');
        dimensionsData = Object.keys(hierarchyData.dimensions);
        
        // 构建按维度组织的分类数据
        dimensionsData.forEach(dimension => {
          const dimData = hierarchyData.dimensions[dimension];
          categoriesData[dimension] = dimData && dimData.categories ? dimData.categories : [];
        });
      } else {
        console.warn('维度层次结构数据格式不正确，使用默认维度:', hierarchyData);
        // 使用默认维度
        dimensionsData = ['tasks', 'languages', 'licenses', 'technologies'];
        dimensionsData.forEach(dimension => {
          categoriesData[dimension] = [];
        });
      }
      
      // 如果通过层次结构API获取的分类数据为空，尝试使用分类API的直接数据
      let hasEmptyCategories = false;
      dimensionsData.forEach(dimension => {
        if (!categoriesData[dimension] || categoriesData[dimension].length === 0) {
          hasEmptyCategories = true;
        }
      });
      
      if (hasEmptyCategories && categoriesApiData && typeof categoriesApiData === 'object') {
        console.log('使用分类API数据补充空维度分类');
        // 合并分类API数据到现有分类数据中
        for (const dimension in categoriesApiData) {
          if (categoriesApiData[dimension] && Array.isArray(categoriesApiData[dimension])) {
            if (!categoriesData[dimension] || categoriesData[dimension].length === 0) {
              categoriesData[dimension] = categoriesApiData[dimension];
            } else {
              // 合并分类数据，避免重复
              const existingIds = new Set(categoriesData[dimension].map(cat => cat.id));
              categoriesData[dimension] = [
                ...categoriesData[dimension],
                ...categoriesApiData[dimension].filter(cat => !existingIds.has(cat.id))
              ];
            }
          }
        }
      }
      
      // 如果分类API数据也没有，尝试直接从分类API获取所有分类并按维度分组
      let stillHasEmptyCategories = false;
      dimensionsData.forEach(dimension => {
        if (!categoriesData[dimension] || categoriesData[dimension].length === 0) {
          stillHasEmptyCategories = true;
        }
      });
      
      if (stillHasEmptyCategories) {
        console.log('尝试从分类API获取所有分类并按维度分组');
        try {
          const allCategories = await categoryApi.getAll();
          
          // 将所有分类按维度分组
          const groupedCategories = {};
          dimensionsData.forEach(dimension => {
            groupedCategories[dimension] = [];
          });
          
          // 遍历所有分类，按维度分组
          if (Array.isArray(allCategories)) {
            allCategories.forEach(category => {
              // 假设分类数据中有dimension字段或可以推断出维度
              if (category.dimension && dimensionsData.includes(category.dimension)) {
                groupedCategories[category.dimension].push(category);
              } else {
                // 如果没有维度信息，尝试根据分类名称推断
                const categoryName = category.name.toLowerCase();
                if (categoryName.includes('task') || categoryName.includes('任务')) {
                  groupedCategories.tasks.push(category);
                } else if (categoryName.includes('lang') || categoryName.includes('语言')) {
                  groupedCategories.languages.push(category);
                } else if (categoryName.includes('licen') || categoryName.includes('协议')) {
                  groupedCategories.licenses.push(category);
                } else if (categoryName.includes('tech') || categoryName.includes('技术')) {
                  groupedCategories.technologies.push(category);
                }
              }
            });
          }
          
          // 使用分组后的分类数据
          for (const dimension in groupedCategories) {
            if (groupedCategories[dimension].length > 0) {
              categoriesData[dimension] = groupedCategories[dimension];
            }
          }
        } catch (error) {
          console.error('获取所有分类失败:', error);
        }
      }
      
      // 调试：输出维度和分类数据
      console.log('维度数据:', dimensionsData);
      console.log('分类数据:', categoriesData);
      
      setDimensions(dimensionsData);
      setCategoriesByDimension(categoriesData);
      
      // 处理参数模板数据
      let processedTemplates = [];
      if (templatesData) {
        if (Array.isArray(templatesData)) {
          processedTemplates = templatesData;
        } else if (templatesData.templates && Array.isArray(templatesData.templates)) {
          processedTemplates = templatesData.templates;
        } else if (templatesData.data && Array.isArray(templatesData.data)) {
          processedTemplates = templatesData.data;
        }
      }
      console.log('处理后的参数模板:', processedTemplates);
      setParameterTemplates(processedTemplates);
      
      // 初始化维度配置并获取配置对象
      const initialConfigs = initializeDimensionConfigs(dimensionsData, categoriesData);
      
      // 设置默认激活维度
      if (dimensionsData.length > 0) {
        setActiveDimension(dimensionsData[0]);
      }
      
      // 如果是编辑模式，加载模型数据
      if (mode === 'edit' && model) {
        // 确保维度配置已初始化后再加载模型数据
        console.log('在编辑模式下加载模型数据:', model);
        await loadModelData(model, initialConfigs);
      }
      
    } catch (error) {
      console.error('初始化数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始化维度配置
  const initializeDimensionConfigs = (dimensionsData, categoriesData) => {
    const configs = {};
    
    // 确保dimensionsData是有效的数组
    const validDimensions = Array.isArray(dimensionsData) ? dimensionsData : [];
    
    validDimensions.forEach(dimension => {
      // 确保维度名称是有效的字符串
      if (typeof dimension === 'string' && dimension.trim()) {
        configs[dimension] = {
          selectedCategory: '',
          selectedTemplate: '',
          parameters: {},
          isActive: true
        };
      }
    });
    
    // 记录维度配置初始化状态
    console.log(`初始化维度配置: ${Object.keys(configs).length} 个维度`);
    
    setDimensionConfigs(configs);
    return configs; // 返回配置对象用于后续处理
  };

  // 加载模型数据
  const loadModelData = async (modelData, initialConfigs = null) => {
    try {
      // 设置基础表单数据
      const formData = {
        model_id: '',
        model_name: '',
        description: '',
        contextWindow: 8000,
        max_tokens: 1000,
        isDefault: false,
        is_active: true
      };
      
      // 调试：输出接收到的模型数据
      console.log('接收到的模型数据:', modelData);
      
      // 确保模型数据是一个对象
      if (modelData && typeof modelData === 'object') {
        // 尝试多种可能的字段名映射，确保正确获取模型ID和名称
        formData.model_id = modelData.model_id || modelData.id || modelData.modelId || '';
        formData.model_name = modelData.model_name || modelData.name || modelData.modelName || '';
        formData.description = modelData.description || '';
        formData.contextWindow = modelData.context_window || modelData.contextWindow || 8000;
        formData.max_tokens = modelData.max_tokens || modelData.maxTokens || 1000;
        formData.isDefault = modelData.is_default || modelData.isDefault || false;
        formData.is_active = modelData.is_active || modelData.isActive || true;
        
        console.log('从模型数据中提取的字段:');
        console.log('model_id:', modelData.model_id, modelData.id, modelData.modelId);
        console.log('model_name:', modelData.model_name, modelData.name, modelData.modelName);
      }
      
      // 调试：输出设置到表单的数据
      console.log('设置到表单的数据:', formData);
      
      setFormData(formData);

      // 设置LOGO预览
      let logoPath = modelData.logo || null;
      if (logoPath && !logoPath.startsWith('http')) {
        logoPath = getImageUrl('models', logoPath);
      }
      setLogoPreview(logoPath);

      // 获取模型ID用于加载维度配置
      const modelId = modelData.model_id || modelData.id || modelData.modelId;
      console.log('用于加载维度配置的模型ID:', modelId);
      
      // 加载模型的维度配置
      if (modelId) {
        await loadModelDimensionConfigs(modelId, initialConfigs);
      } else {
        console.warn('没有可用的模型ID，跳过维度配置加载');
      }
      
    } catch (error) {
      console.error('加载模型数据失败:', error);
    }
  };

  // 加载模型的维度配置
  const loadModelDimensionConfigs = async (modelId, initialConfigs = null) => {
    try {
      // 使用初始配置或当前配置
      let configs = initialConfigs ? { ...initialConfigs } : { ...dimensionConfigs };
      const selections = {};
      
      // 确保configs是有效的对象
      if (!configs || typeof configs !== 'object') {
        console.warn('维度配置无效，使用空配置');
        configs = {};
      }
      
      try {
        // 获取模型的维度信息
        const modelDimensions = await dimensionHierarchyApi.getModelDimensions(modelId);
        console.log('模型维度信息:', modelDimensions);
        
        // 处理每个维度的配置
        for (const dimension of Object.keys(configs)) {
          // 确保维度配置存在
          if (!configs[dimension]) {
            configs[dimension] = {
              selectedCategory: '',
              selectedTemplate: '',
              parameters: {},
              isActive: true
            };
          }
          
          // 获取该维度下的模型分类关联
          const dimensionAssociations = modelDimensions.dimensions?.[dimension] || [];
          
          if (dimensionAssociations.length > 0) {
            // 使用第一个关联的分类（支持多分类时可根据权重选择）
            const primaryAssociation = dimensionAssociations[0];
            configs[dimension].selectedCategory = primaryAssociation.category_id;
            configs[dimension].isActive = true; // 有分类关联的维度自动激活
            
            // 同时更新简化选择器状态
            const category = categoriesByDimension[dimension]?.find(c => c.id === primaryAssociation.category_id);
            if (category) {
              selections[dimension] = {
                categoryId: category.id,
                categoryName: category.display_name || category.name
              };
            }
            
            // 获取该维度下的参数配置
            try {
              const dimensionParameters = await modelApi.getModelParameters(modelId, dimension);
              const paramsObj = {};
              if (Array.isArray(dimensionParameters)) {
                dimensionParameters.forEach(param => {
                  if (param && param.parameter_name) {
                    paramsObj[param.parameter_name] = param.parameter_value || '';
                  }
                });
              }
              configs[dimension].parameters = paramsObj;
            } catch (paramError) {
              console.warn(`获取维度 ${dimension} 参数失败:`, paramError);
              configs[dimension].parameters = {};
            }
          } else {
            // 没有分类关联的维度，清空选择并停用
            configs[dimension].selectedCategory = '';
            configs[dimension].isActive = false;
          }
        }
      } catch (modelDimensionsError) {
        console.error('获取模型维度信息失败:', modelDimensionsError);
        // 如果获取模型维度信息失败，尝试从模型数据本身获取
        if (model && model.dimensionConfigs) {
          console.log('尝试从模型数据中获取维度配置:', model.dimensionConfigs);
          Object.keys(model.dimensionConfigs).forEach(dimension => {
            if (configs[dimension]) {
              configs[dimension] = {
                ...configs[dimension],
                ...model.dimensionConfigs[dimension]
              };
            }
          });
        }
      }
      
      // 记录维度配置加载状态
      const activeDimensions = Object.values(configs).filter(config => config.isActive).length;
      console.log(`维度配置加载完成: ${Object.keys(configs).length} 个维度，${activeDimensions} 个已激活`);
      
      setDimensionConfigs(configs);
      setCategorySelections(selections);
      
    } catch (error) {
      console.error('加载模型维度配置失败:', error);
      // 在错误情况下确保维度配置状态一致
      setDimensionConfigs(initialConfigs || {});
    }
  };

  // 处理基础表单变化
  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) || 0 : value
    }));
  };

  // 处理维度配置变化
  const handleDimensionConfigChange = (dimension, field, value) => {
    setDimensionConfigs(prev => ({
      ...prev,
      [dimension]: {
        ...prev[dimension],
        [field]: value
      }
    }));
  };

  // 打开模板预览
  const openTemplatePreview = (templateId) => {
    const template = parameterTemplates.find(t => t.id === templateId);
    if (template) {
      setTemplatePreview({
        isOpen: true,
        template: template
      });
    }
  };

  // 关闭模板预览
  const closeTemplatePreview = () => {
    setTemplatePreview({
      isOpen: false,
      template: null
    });
  };

  // 应用模板参数
  const applyTemplateParameters = (template) => {
    if (activeDimension) {
      setDimensionConfigs(prev => ({
        ...prev,
        [activeDimension]: {
          ...prev[activeDimension],
          selectedTemplate: template.id,
          parameters: { ...template.parameters }
        }
      }));
    }
  };

  // 编辑模板（跳转到模板管理页面）
  const editTemplate = (template) => {
    // 这里可以跳转到模板编辑页面
    console.log('编辑模板:', template);
    // window.location.href = `/template-management/${template.id}`;
  };

  // 处理简化分类选择器变化
  const handleCategorySelectionsChange = (selections) => {
    setCategorySelections(selections);
    
    // 同步更新维度配置
    const newConfigs = { ...dimensionConfigs };
    
    // 根据简化选择器设置分类，同时保持其他配置不变
    Object.keys(newConfigs).forEach(dimension => {
      if (selections[dimension]) {
        // 如果简化选择器中有该维度的选择，更新分类
        newConfigs[dimension].selectedCategory = selections[dimension].categoryId;
        newConfigs[dimension].isActive = true; // 自动激活有选择的维度
      } else {
        // 如果简化选择器中没有该维度的选择，清空分类并停用
        newConfigs[dimension].selectedCategory = '';
        newConfigs[dimension].isActive = false;
      }
    });
    
    setDimensionConfigs(newConfigs);
  };

  // 处理参数变化
  const handleParameterChange = (dimension, paramName, value) => {
    setDimensionConfigs(prev => ({
      ...prev,
      [dimension]: {
        ...prev[dimension],
        parameters: {
          ...prev[dimension].parameters,
          [paramName]: value
        }
      }
    }));
  };

  // 处理LOGO文件选择
  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLogo(file);
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
    if (!formData.model_id || !formData.model_name) {
      alert('请填写模型ID和模型名称');
      return;
    }
    

    // 验证至少有一个维度配置
    const activeDimensions = Object.entries(dimensionConfigs)
      .filter(([dimension, config]) => config.selectedCategory && config.isActive);
    
    if (activeDimensions.length === 0) {
      alert('请至少配置一个维度的分类');
      return;
    }
    
    try {
      setSaving(true);
      
      // 准备提交数据
      const submitData = {
        // 基础信息
        ...formData,
        contextWindow: parseInt(formData.contextWindow) || 8000,
        maxTokens: parseInt(formData.max_tokens) || 1000,
        
        // 维度配置
        dimensionConfigs: dimensionConfigs,
        
        // 分类关联（从维度配置中提取）
        categoryAssociations: activeDimensions
          .map(([dimension, config]) => ({
            category_id: config.selectedCategory,
            dimension: dimension
          }))
      };
      
      // 确保logo字段不是空对象
      if (submitData.logo && typeof submitData.logo === 'object') {
        delete submitData.logo;
      }
      
      // 调用父组件的保存函数
      await onSave(submitData, logo);
      onClose();
      
    } catch (error) {
      console.error('保存模型失败:', error);
      alert('保存失败：' + (error.message || '未知错误'));
    } finally {
      setSaving(false);
    }
  };

  // 渲染维度配置表单
  const renderDimensionConfig = (dimension) => {
    // 确保维度配置存在
    if (!dimensionConfigs[dimension]) {
      console.warn(`维度 ${dimension} 的配置不存在，使用默认配置`);
      handleDimensionConfigChange(dimension, 'isActive', true);
    }
    
    const config = dimensionConfigs[dimension] || {
      selectedCategory: '',
      selectedTemplate: '',
      parameters: {},
      isActive: true
    };
    
    const categories = categoriesByDimension[dimension] || [];
    const isActive = config.isActive !== false;
    
    // 维度显示名称映射
    const dimensionDisplayNames = {
      'tasks': '任务维度',
      'languages': '语言维度', 
      'licenses': '协议维度',
      'technologies': '技术维度'
    };
    
    const displayName = dimensionDisplayNames[dimension] || dimension;
    
    return (
      <div key={dimension} className={`dimension-config ${isActive ? 'active' : 'inactive'}`}>
        <div className="dimension-header">
          <div className="dimension-title">
            <h4>{displayName}</h4>
            <div className="dimension-badge">
              {isActive ? (
                <span className="badge active">已启用</span>
              ) : (
                <span className="badge inactive">已禁用</span>
              )}
            </div>
          </div>
          <div className="dimension-status">
            <label className={`activation-toggle ${isActive ? 'active' : ''}`}>
              <input 
                type="checkbox"
                checked={isActive}
                onChange={(e) => handleDimensionConfigChange(dimension, 'isActive', e.target.checked)}
              />
              <span className="status-label">
                {isActive ? '已启用' : '已禁用'}
              </span>
            </label>
          </div>
        </div>
        
        {config.isActive !== false && (
          <>
            {/* 分类选择 */}
            <div className="form-group">
              <label className="form-label-with-count">
                选择分类
                {categories.length > 0 && (
                  <span className="count-badge">{categories.length} 个分类</span>
                )}
              </label>
              <select 
                value={config.selectedCategory || ''}
                onChange={(e) => handleDimensionConfigChange(dimension, 'selectedCategory', e.target.value)}
                disabled={categories.length === 0}
                className={config.selectedCategory ? 'has-selection' : ''}
              >
                <option value="">
                  {categories.length === 0 ? '暂无分类' : '请选择分类'}
                </option>
                {categories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.display_name || category.name}
                  </option>
                ))}
              </select>
              {categories.length === 0 && (
                <div className="field-hint">该维度下暂无可用分类</div>
              )}
              {config.selectedCategory && (
                <div className="selection-hint">
                  ✓ 已选择分类
                </div>
              )}
            </div>
            
            {/* 参数模板选择 */}
            <div className="form-group">
              <label>参数模板:</label>
              <div className="template-selector">
                <select 
                  value={config.selectedTemplate || ''}
                  onChange={(e) => handleDimensionConfigChange(dimension, 'selectedTemplate', e.target.value)}
                  disabled={parameterTemplates.length === 0}
                >
                  <option value="">
                    {parameterTemplates.length === 0 ? '暂无模板' : '请选择模板'}
                  </option>
                  {parameterTemplates.map(template => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
                {config.selectedTemplate && (
                  <button 
                    type="button"
                    className="btn-preview"
                    onClick={() => openTemplatePreview(config.selectedTemplate)}
                    title="预览模板参数"
                  >
                    预览
                  </button>
                )}
              </div>
            </div>
            
            {/* 参数配置 */}
            {Object.keys(config.parameters || {}).length > 0 && (
              <div className="parameters-section">
                <h5>参数配置</h5>
                <div className="parameter-group">
                  {Object.entries(config.parameters).map(([paramName, paramValue]) => (
                    <div key={paramName} className="parameter-item">
                      <label>{paramName}:</label>
                      <input 
                        type="text"
                        value={paramValue}
                        onChange={(e) => handleParameterChange(dimension, paramName, e.target.value)}
                        placeholder="参数值"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* 当前配置状态 */}
            <div className="config-status">
              <div className="status-item">
                <span className="status-label">分类:</span>
                <span className="status-value">
                  {config.selectedCategory ? 
                    categories.find(c => c.id === config.selectedCategory)?.display_name || 
                    categories.find(c => c.id === config.selectedCategory)?.name || 
                    '未知分类' : 
                    '未选择'
                  }
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">模板:</span>
                <span className="status-value">
                  {config.selectedTemplate ? 
                    parameterTemplates.find(t => t.id === config.selectedTemplate)?.name || 
                    '未知模板' : 
                    '未选择'
                  }
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">参数:</span>
                <span className="status-value">
                  {Object.keys(config.parameters || {}).length} 个
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    );
  };

  // 处理模态窗口外部点击关闭
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // 渲染维度配置选择器
  const renderDimensionSelector = () => {
    if (useSimplifiedSelector) {
      return (
        <div className="simplified-selector-section">
          <SimplifiedCategorySelector
            dimensions={dimensions}
            categoriesByDimension={categoriesByDimension}
            onSelectionChange={handleCategorySelectionsChange}
            initialSelections={categorySelections}
          />
        </div>
      );
    }

    // 原有的维度选项卡方式
    return (
      <div>
        {/* 维度切换标签 */}
        <div className="dimension-tabs">
          {dimensions.map(dimension => (
            <button
              key={dimension}
              type="button"
              className={`tab-button ${activeDimension === dimension ? 'active' : ''}`}
              onClick={() => setActiveDimension(dimension)}
            >
              {dimension}
            </button>
          ))}
        </div>
        
        {/* 当前激活维度的配置 */}
        {activeDimension && renderDimensionConfig(activeDimension)}
      </div>
    );
  };

  // 处理ESC键关闭
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
          <h3>{mode === 'add' ? '添加模型（多维度配置）' : '编辑模型（多维度配置）'}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <form onSubmit={handleSubmit} className="modal-form">
            
            {/* 基础信息 */}
            <div className="form-section">
              <h4>基础信息</h4>
              
              <div className="form-row">
                <div className="form-group">
                  <label>模型ID: <span className="required">*</span></label>
                  <input 
                    type="text"
                    name="model_id"
                    value={formData.model_id}
                    onChange={handleFormChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>模型名称: <span className="required">*</span></label>
                  <input 
                    type="text"
                    name="model_name"
                    value={formData.model_name}
                    onChange={handleFormChange}
                    required
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>描述:</label>
                <textarea 
                  name="description"
                  value={formData.description}
                  onChange={handleFormChange}
                  rows="3"
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>上下文窗口:</label>
                  <input 
                    type="number"
                    name="contextWindow"
                    value={formData.contextWindow}
                    onChange={handleFormChange}
                  />
                </div>
                
                <div className="form-group">
                  <label>最大Token数:</label>
                  <input 
                    type="number"
                    name="max_tokens"
                    value={formData.max_tokens}
                    onChange={handleFormChange}
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>
                    <input 
                      type="checkbox"
                      name="isDefault"
                      checked={formData.isDefault}
                      onChange={handleFormChange}
                    />
                    设为默认模型
                  </label>
                </div>
                
                <div className="form-group">
                  <label>
                    <input 
                      type="checkbox"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleFormChange}
                    />
                    激活模型
                  </label>
                </div>
              </div>
              
              {/* LOGO上传 */}
              <div className="form-group">
                <label>模型LOGO:</label>
                <div className="logo-upload">
                  {logoPreview && (
                    <div className="logo-preview">
                      <img src={logoPreview} alt="LOGO预览" />
                      <button type="button" onClick={handleRemoveLogo}>移除</button>
                    </div>
                  )}
                  <input 
                    type="file"
                    accept="image/*"
                    onChange={handleLogoChange}
                  />
                </div>
              </div>
            </div>
            
            {/* 维度配置 */}
            <div className="form-section">
              <div className="dimension-config-header">
                <h4>维度配置</h4>
                <div className="selector-toggle">
                  <label>
                    <input
                      type="checkbox"
                      checked={useSimplifiedSelector}
                      onChange={(e) => setUseSimplifiedSelector(e.target.checked)}
                    />
                    使用简化分类选择器
                  </label>
                </div>
              </div>
              
              {renderDimensionSelector()}
            </div>
            
            {/* 操作按钮 */}
            <div className="modal-actions">
              <button type="button" onClick={onClose} disabled={saving}>
                取消
              </button>
              <button type="submit" disabled={saving}>
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        )}
      </div>
      
      {/* 模板预览模态框 */}
      <TemplatePreviewModal
        isOpen={templatePreview.isOpen}
        onClose={closeTemplatePreview}
        template={templatePreview.template}
        onApplyTemplate={applyTemplateParameters}
        onEditTemplate={editTemplate}
      />
    </div>
  );
};

export default ModelModalV2;