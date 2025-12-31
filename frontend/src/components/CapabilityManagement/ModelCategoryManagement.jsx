import React, { useState, useEffect } from 'react';
import { getImageUrl, DEFAULT_IMAGES } from '../../config/imageConfig';
import { categoryApi } from '../../utils/api/categoryApi';
import { API_BASE_URL } from '../../utils/apiUtils';
import '../../styles/ModelCategoryManagement.css';

// 按层级排序分类数据，确保父子分类相邻显示
const getHierarchicalCategories = (categories) => {
  // 首先构建树状结构
  const treeStructure = buildCategoryTree(categories);
  
  // 然后扁平化，确保层级顺序正确
  return flattenCategoryTree(treeStructure);
};

// 将扁平的分类数据转换为树状结构
const buildCategoryTree = (categories) => {
  const categoryMap = new Map();
  const rootCategories = [];
  
  // 首先创建所有分类的映射
  categories.forEach(category => {
    categoryMap.set(category.id, {
      ...category,
      children: []
    });
  });
  
  // 然后构建树状结构
  categories.forEach(category => {
    const currentNode = categoryMap.get(category.id);
    
    if (category.parent_id === null || category.parent_id === undefined) {
      // 根分类
      rootCategories.push(currentNode);
    } else {
      // 子分类，添加到父分类的children数组中
      const parentNode = categoryMap.get(category.parent_id);
      if (parentNode) {
        parentNode.children.push(currentNode);
      } else {
        // 如果父分类不存在，将其作为根分类
        rootCategories.push(currentNode);
      }
    }
  });
  
  // 按权重排序子分类（权重越大，排序越靠前）
  const sortChildrenByWeight = (node) => {
    if (node.children && node.children.length > 0) {
      // 先对当前节点的子节点按权重排序
      node.children.sort((a, b) => {
        // 如果权重相同，按显示名称排序
        if ((a.weight || 0) === (b.weight || 0)) {
          return (a.display_name || a.name).localeCompare(b.display_name || b.name);
        }
        // 权重越大，排序越靠前
        return (b.weight || 0) - (a.weight || 0);
      });
      
      // 递归排序子节点的子节点
      node.children.forEach(child => sortChildrenByWeight(child));
    }
  };
  
  // 对所有根节点及其子节点进行排序
  rootCategories.forEach(root => sortChildrenByWeight(root));
  
  // 对根节点也按权重排序
  rootCategories.sort((a, b) => {
    if ((a.weight || 0) === (b.weight || 0)) {
      return (a.display_name || a.name).localeCompare(b.display_name || b.name);
    }
    return (b.weight || 0) - (a.weight || 0);
  });
  
  return rootCategories;
};

// 将树形结构的分类数据扁平化为数组
const flattenCategoryTree = (categories) => {
  const result = [];
  
  
  const traverse = (category) => {
    if (!category) return;
    
    // 添加当前分类
    const flatCategory = {
      ...category,
      // 移除children数组，避免重复处理
      children: undefined
    };
    result.push(flatCategory);
    
    // 递归处理子分类
    if (Array.isArray(category.children) && category.children.length > 0) {
      category.children.forEach(child => traverse(child));
    }
  };
  
  // 处理顶层分类
  if (Array.isArray(categories)) {
    categories.forEach(category => traverse(category));
  }
  
  return result;
};

const ModelCategoryManagement = () => {
  const [categories, setCategories] = useState([]);
  const [dimensions, setDimensions] = useState([]);
  const [categoriesByDimension, setCategoriesByDimension] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null); // 添加成功状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentCategory, setCurrentCategory] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // 添加当前选中标签的状态
  const [viewMode, setViewMode] = useState('table'); // 添加视图模式状态：'table' 或 'tagCloud'
  
  // 统计仪表板相关状态
  const [statistics, setStatistics] = useState(null);
  const [loadingStatistics, setLoadingStatistics] = useState(false);
  const [searchParams, setSearchParams] = useState({}); // 搜索参数状态
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    dimension: 'tasks', // 默认维度
    parent_id: null,
    is_active: true,
    logo: ''
  });
  
  // LOGO选择相关状态
  const [previewUrl, setPreviewUrl] = useState('');
  
  // 硬编码的分类图片列表，从public/logos/categories/目录获取
  const [categoryImages, setCategoryImages] = useState([
    'Diffusers.png',
    'LoRA.png',
    'default.png',
    'gguf.png',
    'llama.png',
    'mlx.png',
    'onnx.png',
    'openvino.png',
    'pytorch.png',
    'safetensors.png',
    'sentence-transformers.png',
    'tensorflow.png',
    'transformers.png',
    'vdr.png',
    'xinference.png'
  ]);
  
  // 参数配置相关状态
  const [selectedCategoryForParams, setSelectedCategoryForParams] = useState(null);
  const [categoryParameters, setCategoryParameters] = useState({}); // 存储每个分类的参数
  const [showParameterModal, setShowParameterModal] = useState(false);
  const [parameterModalMode, setParameterModalMode] = useState('add'); // add or edit
  const [editingParameter, setEditingParameter] = useState(null);
  const [parameterFormData, setParameterFormData] = useState({
    parameter_name: '',
    parameter_value: '',
    parameter_type: 'string',
    description: ''
  });
  const [parameterLoading, setParameterLoading] = useState(false);
  const [parameterError, setParameterError] = useState(null);
  const [showParameterPanelModal, setShowParameterPanelModal] = useState(false); // 控制参数配置面板模态框
  
  // 获取所有分类
  const loadCategories = async () => {
    try {
      setLoading(true);
      
      // 并行加载分类数据、维度数据和统计数据
      const [categoriesData, dimensionsData, categoriesByDimensionData, statsData] = await Promise.all([
        categoryApi.getAll(),
        categoryApi.getAllDimensions(),
        categoryApi.getCategoriesByDimension(),
        loadStatistics() // 加载统计数据
      ]);
      
      // 确保categoriesData是一个数组
      const flattenedData = Array.isArray(categoriesData) ? categoriesData : [];
      
      // 然后标准化分类数据，确保每个分类都有必要的属性
      const normalizedCategories = flattenedData.map(category => ({
        id: category.id ?? `category_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: category.name ?? `未命名分类_${category.id || 'unknown'}`,
        display_name: category.display_name ?? category.name ?? '未命名分类',
        description: category.description || '',
        dimension: category.dimension || 'tasks', // 修改默认维度为'tasks'
        parent_id: category.parent_id || null,
        is_active: category.is_active ?? true,
        is_system: category.is_system ?? false,
        logo: category.logo || null,
        ...category
      }));
      setCategories(normalizedCategories);
      setDimensions(dimensionsData);
      setCategoriesByDimension(categoriesByDimensionData);
      setError(null);
    } catch (err) {
      console.error('❌ 获取分类失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      setError('获取分类列表失败，请稍后重试');
      
    } finally {
      setLoading(false);
    }
  };

  // 加载统计数据
  const loadStatistics = async () => {
    try {
      setLoadingStatistics(true);
      const stats = await categoryApi.getStatistics();
      setStatistics(stats);
    } catch (err) {
      console.error('❌ 获取统计数据失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoadingStatistics(false);
    }
  };

  // 处理搜索
  const handleSearch = async (params) => {
    try {
      setSearchParams(params);
      const result = await categoryApi.search(params);
      // 处理搜索结果
      let searchResult = [];
      if (result && Array.isArray(result.categories)) {
        searchResult = result.categories;
      } else if (result && Array.isArray(result)) {
        searchResult = result;
      }
      
      // 标准化搜索结果，确保与原始数据格式一致
      const normalizedResults = searchResult.map(category => ({
        id: category.id ?? `category_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: category.name ?? `未命名分类_${category.id || 'unknown'}`,
        display_name: category.display_name ?? category.name ?? '未命名分类',
        description: category.description || '',
        dimension: category.dimension || 'tasks', // 修改默认维度为'tasks'
        parent_id: category.parent_id || null,
        is_active: category.is_active ?? true,
        is_system: category.is_system ?? false,
        logo: category.logo || null,
        ...category
      }));
      
      setCategories(normalizedResults);
    } catch (err) {
      console.error('❌ 搜索分类失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    }
  };
  
  // 初始化加载
  useEffect(() => {
    loadCategories();
  }, []);
  
  // 处理输入变化
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    let processedValue;
    if (name === 'parent_id') {
      processedValue = value === '' ? null : parseInt(value);
      console.log('父级分类选择变化:', value, '→', processedValue);
    } else {
      processedValue = value;
    }
    setFormData(prev => ({
      ...prev,
      [name]: processedValue
    }));
  };
  
  // 重置表单
  const resetForm = () => {
    setFormData({
      name: '',
      display_name: '',
      description: '',
      dimension: 'tasks', // 重置维度字段
      parent_id: null,
      is_active: true,
      logo: ''
    });
    setCurrentCategory(null);
    // 重置LOGO相关状态
    setPreviewUrl('');
  };
  
  // 处理图片选择变化
  const handleImageSelect = (e) => {
    const selectedImage = e.target.value;
    setFormData(prev => ({ ...prev, logo: selectedImage }));
    // 更新预览URL
    setPreviewUrl(getImageUrl('categories', selectedImage));
  };
  

  
  // 清理预览URL
  useEffect(() => {
    return () => {
      // 不再需要清理blob URL，因为现在使用的是静态文件URL
    };
  }, [previewUrl]);
  
  // 打开创建模态框
  const handleCreateModalOpen = () => {
    resetForm();
    setShowCreateModal(true);
  };
  
  // 打开编辑模态框
  const handleEditModalOpen = (category) => {
    setCurrentCategory(category);
    setFormData({
      name: category.name,
      display_name: category.display_name,
      description: category.description || '',
      dimension: category.dimension || 'task_type', // 添加维度字段
      parent_id: category.parent_id !== null ? category.parent_id : null,
      is_active: category.is_active,
      logo: category.logo || ''
    });
    
    // 处理logo预览URL
    const logoUrl = category.logo || '';
    let finalPreviewUrl = '';
    if (logoUrl && logoUrl.trim() && !logoUrl.startsWith('fa-')) {
      if (logoUrl.startsWith('/')) {
        // 已经是完整路径，直接使用
        finalPreviewUrl = logoUrl;
      } else {
        // 只有文件名，添加完整路径前缀
        finalPreviewUrl = getImageUrl('categories', logoUrl);
      }
    }
    setPreviewUrl(finalPreviewUrl);
    
    setShowEditModal(true);
  };
  
  // 关闭模态框
  const handleModalClose = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    resetForm();
  };
  
  // 提交创建表单
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      // 创建FormData对象用于文件上传
      const formDataToSubmit = new FormData();
      
      // 添加所有表单字段，包括维度
      formDataToSubmit.append('name', formData.name);
      formDataToSubmit.append('display_name', formData.display_name);
      formDataToSubmit.append('description', formData.description);
      formDataToSubmit.append('dimension', formData.dimension); // 添加维度字段
      // 当parent_id为null或undefined时，使用空字符串表示"无父级分类"
      const parentIdValue = formData.parent_id === null || formData.parent_id === undefined ? '' : formData.parent_id;
      formDataToSubmit.append('parent_id', parentIdValue);
      console.log('提交的父级分类ID:', parentIdValue);
      formDataToSubmit.append('is_active', formData.is_active.toString());
      
      // 处理LOGO
      if (formData.logo && !formData.logo.startsWith('fa-')) {
        // 直接发送选中的图片文件名
        formDataToSubmit.append('logo', formData.logo);
      }
      
      await categoryApi.create(formDataToSubmit);
      setShowCreateModal(false);
      loadCategories(); // 重新加载列表
      setSuccess('分类创建成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('创建分类失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      // 显示更具体的错误消息
      const errorMsg = err.response?.data?.detail || err.message || '创建分类失败，请检查输入并重试';
      setError(errorMsg);
    }
  };
  
  // 提交编辑表单
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!currentCategory) return;
    
    try {
      // 创建FormData对象用于文件上传
      const formDataToSubmit = new FormData();
      
      // 添加所有表单字段，包括维度
      formDataToSubmit.append('name', formData.name);
      formDataToSubmit.append('display_name', formData.display_name);
      formDataToSubmit.append('description', formData.description);
      formDataToSubmit.append('dimension', formData.dimension); // 添加维度字段
      // 当parent_id为null或undefined时，使用空字符串表示"无父级分类"
      const parentIdValue = formData.parent_id === null || formData.parent_id === undefined ? '' : formData.parent_id;
      formDataToSubmit.append('parent_id', parentIdValue);
      console.log('提交的父级分类ID:', parentIdValue);
      formDataToSubmit.append('is_active', formData.is_active.toString());
      
      // 处理LOGO
      if (formData.logo && !formData.logo.startsWith('fa-')) {
        // 直接发送选中的图片文件名
        formDataToSubmit.append('logo', formData.logo);
      }
      
      await categoryApi.update(currentCategory.id, formDataToSubmit);
      setShowEditModal(false);
      loadCategories(); // 重新加载列表
      setSuccess('分类更新成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('更新分类失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      // 显示更具体的错误消息
      const errorMsg = err.response?.data?.detail || err.message || '更新分类失败，请检查输入并重试';
      setError(errorMsg);
    }
  };
  
  // 处理删除
  const handleDelete = async (categoryId) => {
    if (window.confirm('确定要删除这个分类吗？删除前请确保该分类没有子分类和关联的模型。')) {
      try {
        const result = await categoryApi.delete(categoryId);
        loadCategories(); // 重新加载列表
        // 清除该分类的参数数据
        setCategoryParameters(prev => {
          const newParams = { ...prev };
          delete newParams[categoryId];
          return newParams;
        });
        setSuccess('分类删除成功');
        // 3秒后自动清除成功消息
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error('❌ 删除分类失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
        // 显示更具体的错误消息
        const errorMsg = err.response?.data?.detail || err.message || '删除分类失败，可能是因为该分类下有子分类或关联的模型';
        setError(errorMsg);
      }
    }
  };
  
  // 加载分类参数
  const loadCategoryParameters = async (categoryId) => {
    try {
      setParameterLoading(true);
      const parameters = await categoryApi.getParameters(categoryId);
      // 确保parameters始终是数组，将后端返回的字典转换为数组
      let safeParameters;
      if (Array.isArray(parameters)) {
        safeParameters = parameters;
      } else if (parameters && typeof parameters === 'object') {
        // 将后端返回的字典格式转换为前端需要的数组格式
        safeParameters = Object.entries(parameters).map(([name, valueObj]) => ({
          parameter_name: name,
          parameter_value: valueObj.value,
          parameter_type: valueObj.type,
          description: valueObj.description
        }));
      } else {
        safeParameters = [];
      }
      setCategoryParameters(prev => ({
        ...prev,
        [categoryId]: safeParameters
      }));
      setParameterError(null);
    } catch (err) {
      setParameterError('加载分类参数失败，请稍后重试');
    } finally {
      setParameterLoading(false);
    }
  };
  
  // 打开参数配置模态框
  const handleOpenParameterModal = (category, mode, parameter = null) => {
    setSelectedCategoryForParams(category);
    setParameterModalMode(mode);
    
    if (mode === 'edit' && parameter) {
      setEditingParameter(parameter);
      setParameterFormData({
        parameter_name: parameter.parameter_name,
        parameter_value: parameter.parameter_value,
        parameter_type: parameter.parameter_type || 'string',
        description: parameter.description || ''
      });
    } else {
      setEditingParameter(null);
      setParameterFormData({
        parameter_name: '',
        parameter_value: '',
        parameter_type: 'string',
        description: ''
      });
    }
    
    // 关闭参数配置面板模态框，打开参数编辑模态框
    setShowParameterPanelModal(false);
    setShowParameterModal(true);
  };
  
  // 关闭参数配置模态框
  const handleCloseParameterModal = () => {
    setShowParameterModal(false);
    setEditingParameter(null);
    setParameterFormData({
      parameter_name: '',
      parameter_value: '',
      parameter_type: 'string',
      description: ''
    });
    
    // 重新打开参数配置面板模态框
    if (selectedCategoryForParams) {
      setShowParameterPanelModal(true);
    }
  };
  
  // 处理参数表单输入变化
  const handleParameterInputChange = (e) => {
    const { name, value } = e.target;
    setParameterFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // 提交参数表单
  const handleParameterSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCategoryForParams) return;
    
    try {
      setParameterLoading(true);
      
      const parameterData = {
        parameter_name: parameterFormData.parameter_name,
        parameter_value: parameterFormData.parameter_value,
        parameter_type: parameterFormData.parameter_type,
        description: parameterFormData.description
      };
      
      if (parameterModalMode === 'add') {
        // 对于添加操作，我们需要获取当前参数列表并添加新参数
        const currentParams = Array.isArray(categoryParameters[selectedCategoryForParams.id]) ? categoryParameters[selectedCategoryForParams.id] : [];
        const updatedParamsArray = [...currentParams, parameterData];
        // 将数组转换为后端期望的字典格式
        const updatedParamsDict = updatedParamsArray.reduce((dict, param) => {
          dict[param.parameter_name] = {
            value: param.parameter_value,
            type: param.parameter_type,
            description: param.description
          };
          return dict;
        }, {});
        await categoryApi.setParameters(selectedCategoryForParams.id, updatedParamsDict);
      } else if (parameterModalMode === 'edit' && editingParameter) {
        // 对于编辑操作，我们需要更新指定参数
        const currentParams = Array.isArray(categoryParameters[selectedCategoryForParams.id]) ? categoryParameters[selectedCategoryForParams.id] : [];
        const updatedParamsArray = currentParams.map(p => 
          p.parameter_name === editingParameter.parameter_name ? parameterData : p
        );
        // 将数组转换为后端期望的字典格式
        const updatedParamsDict = updatedParamsArray.reduce((dict, param) => {
          dict[param.parameter_name] = {
            value: param.parameter_value,
            type: param.parameter_type,
            description: param.description
          };
          return dict;
        }, {});
        await categoryApi.setParameters(selectedCategoryForParams.id, updatedParamsDict);
      }
      
      // 重新加载参数列表
      await loadCategoryParameters(selectedCategoryForParams.id);
      
      // 关闭模态框并重新打开参数配置面板模态框
      setShowParameterModal(false);
      setEditingParameter(null);
      setParameterFormData({
        parameter_name: '',
        parameter_value: '',
        parameter_type: 'string',
        description: ''
      });
      setShowParameterPanelModal(true);
      
      setSuccess('参数配置成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('❌ 参数配置失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      setParameterError('参数配置失败，请稍后重试');
    } finally {
      setParameterLoading(false);
    }
  };
  
  // 处理删除参数
  const handleDeleteParameter = async (categoryId, parameterName) => {
    if (window.confirm(`确定要删除参数 ${parameterName} 吗？`)) {
      try {
        setParameterLoading(true);
        await categoryApi.deleteParameter(categoryId, parameterName);
        // 重新加载参数列表
        await loadCategoryParameters(categoryId);
        setSuccess('参数删除成功');
        // 3秒后自动清除成功消息
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error('❌ 删除参数失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
        setParameterError('删除参数失败，请稍后重试');
      } finally {
        setParameterLoading(false);
      }
    }
  };
  
  // 处理分类参数配置点击
  const handleConfigureParameters = (category) => {
    setSelectedCategoryForParams(category);
    // 加载分类参数
    loadCategoryParameters(category.id);
    // 显示参数配置模态框
    setShowParameterPanelModal(true);
  };

  // 关闭参数配置面板模态框
  const handleCloseParameterPanelModal = () => {
    setShowParameterPanelModal(false);
    setSelectedCategoryForParams(null);
  };

  // 监听selectedCategoryForParams状态变化
  useEffect(() => {
    if (selectedCategoryForParams) {
      // 参数加载逻辑已移至handleConfigureParameters中
    }
  }, [selectedCategoryForParams]);
  
  // 获取所有分类列表（用于父分类选择）
  const mainCategories = categories;
  
  // 处理标签点击
  const handleTabClick = (tabType) => {
    setActiveTab(tabType);
  };

  // 根据当前选中的维度选项卡过滤分类
  const filteredCategories = activeTab === 'all' 
    ? categories 
    : categories.filter(cat => {
        // 确保维度值是字符串类型且去除空格，以避免匹配问题
        const categoryDimension = String(cat.dimension).trim().toLowerCase();
        const tabDimension = String(activeTab).trim().toLowerCase();
        return categoryDimension === tabDimension;
      }).sort((a, b) => {
        // 按权重排序，权重越大，排序越靠前
        if ((a.weight || 0) === (b.weight || 0)) {
          return (a.display_name || a.name).localeCompare(b.display_name || b.name);
        }
        return (b.weight || 0) - (a.weight || 0);
      });
  

  
  if (loading) {
    return <div className="category-management-loading">加载中...</div>;
  }
  
  return (
    <div className="model-category-management">
      <div className="category-header">
        <button 
          className="btn btn-primary" 
          onClick={handleCreateModalOpen}
        >
          创建分类
        </button>
      </div>
      
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      {/* 统计仪表板 */}
      <div className="statistics-dashboard">
        <div className="dashboard-header">
          <h3>分类使用统计</h3>
          <button 
            className="btn btn-small btn-info" 
            onClick={loadStatistics}
            disabled={loadingStatistics}
          >
            {loadingStatistics ? '刷新中...' : '刷新统计'}
          </button>
        </div>
        <div className="dashboard-cards">
          {statistics ? (
            <>
              <div className="stat-card">
                <div className="stat-value">{statistics.total_categories}</div>
                <div className="stat-label">总分类数</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{statistics.total_models}</div>
                <div className="stat-label">关联模型数</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{statistics.total_active_categories}</div>
                <div className="stat-label">激活分类数</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{statistics.total_system_categories}</div>
                <div className="stat-label">系统分类数</div>
              </div>
            </>
          ) : (
            <div className="loading-stats">加载统计数据中...</div>
          )}
        </div>
        
        {/* 维度统计详情 */}
        {statistics && statistics.dimension_stats && Object.keys(statistics.dimension_stats).length > 0 && (
          <div className="dimension-stats">
            <h4>各维度统计</h4>
            <div className="dimension-stats-grid">
              {Object.entries(statistics.dimension_stats).map(([dimension, stats]) => (
                <div key={dimension} className="dimension-stat-card">
                  <div className="dimension-name">{dimension}</div>
                  <div className="dimension-stats-list">
                    <div>分类数: {stats.total_categories}</div>
                    <div>关联模型数: {stats.total_models}</div>
                    <div>激活分类数: {stats.active_categories}</div>
                    <div>系统分类数: {stats.system_categories}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 搜索和筛选区域 */}
      <div className="search-filter-section">
        <div className="search-input-group">
          <input
            type="text"
            placeholder="搜索分类（名称、显示名称、描述）"
            onChange={(e) => handleSearch({ ...searchParams, keyword: e.target.value })}
            className="search-input"
          />
          <select
            onChange={(e) => handleSearch({ ...searchParams, dimension: e.target.value || undefined })}
            className="filter-select"
          >
            <option value="">所有维度</option>
            {dimensions.map(dimension => (
              <option key={dimension} value={dimension}>{dimension}</option>
            ))}
          </select>
          <select
            onChange={(e) => handleSearch({ ...searchParams, isActive: e.target.value === 'active' ? true : e.target.value === 'inactive' ? false : undefined })}
            className="filter-select"
          >
            <option value="">所有状态</option>
            <option value="active">激活</option>
            <option value="inactive">禁用</option>
          </select>
          <button 
            className="btn btn-small btn-secondary"
            onClick={() => handleSearch({})}
          >
            重置筛选
          </button>
        </div>
      </div>

      <div className="category-content">
        {categories.length === 0 ? (
          <div className="empty-state">暂无分类数据</div>
        ) : (
          <div>
            {/* 维度选项卡 */}
            <div className="category-tabs">
              <div 
                className={`tab ${activeTab === 'all' ? 'active' : ''}`} 
                data-type="all"
                onClick={() => handleTabClick('all')}
              >所有分类</div>
              {dimensions.map(dimension => (
                <div 
                  key={dimension}
                  className={`tab ${activeTab === dimension ? 'active' : ''}`} 
                  data-type={dimension}
                  onClick={() => handleTabClick(dimension)}
                >{dimension}</div>
              ))}
            </div>
            
            {/* 视图切换按钮 */}
            <div className="view-toggle-buttons">
              <button 
                className={`btn btn-secondary ${viewMode === 'table' ? 'active' : ''}`}
                onClick={() => setViewMode('table')}
              >
                表格视图
              </button>
              <button 
                className={`btn btn-secondary ${viewMode === 'tagCloud' ? 'active' : ''}`}
                onClick={() => setViewMode('tagCloud')}
              >
                标签云视图
              </button>

            </div>
            
            {/* 表格视图 */}
            {viewMode === 'table' && (
              <div className="category-table-container">
                <table className="category-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>LOGO</th>
                      <th>名称</th>
                      <th>显示名称</th>
                      <th>维度</th>
                      <th>父分类</th>
                      <th>状态</th>
                      <th>是否系统分类</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getHierarchicalCategories(filteredCategories).map(category => {
                      const parentCategory = category.parent_id 
                        ? categories.find(cat => cat.id === category.parent_id)
                        : null;
                      
                      // 判断是否为主分类（没有父分类的分类）
                      const isPrimaryCategory = category.parent_id === null;
                      
                      return (
                        <tr 
                          key={category.id} 
                          className={`
                            ${category.is_system ? 'system-category-row' : ''}
                            ${isPrimaryCategory ? 'primary-category' : 'sub-category'}
                          `}
                        >
                          <td>{category.id}</td>
                          <td>
                            {category.logo ? (
                              <div className="category-logo">
                                {category.logo.startsWith('<i class=') ? (
                                  <div 
                                    dangerouslySetInnerHTML={{ __html: category.logo }}
                                    className="fa-icon"
                                    title={`${category.display_name} logo`}
                                  />
                                ) : category.logo.includes('fa-') ? (
                                  <div className="fa-icon">
                                    <i className={category.logo} title={`${category.display_name} logo`}></i>
                                  </div>
                                ) : (
                                  <img 
                                    src={getImageUrl('categories', category.logo)} 
                                    alt={`${category.display_name} logo`} 
                                    title={`${category.display_name} logo`}
                                    onError={(e) => {
                                      e.target.src = DEFAULT_IMAGES.category;
                                      console.error('图片加载失败，使用默认图片:', e.target.src);
                                    }}
                                  />
                                )}
                              </div>
                            ) : (
                              <div className="category-logo placeholder">
                                无LOGO
                              </div>
                            )}
                          </td>
                          <td className={isPrimaryCategory ? 'primary-category-name' : ''}>
                            {category.name}
                          </td>
                          <td>{category.display_name}</td>
                          <td>{category.dimension}</td>
                          <td>{parentCategory ? parentCategory.display_name : '-'}</td>
                          <td>
                            <span className={`status-badge ${category.is_active ? 'active' : 'inactive'}`}>
                              {category.is_active ? '启用' : '禁用'}
                            </span>
                          </td>
                          <td>
                            <span className={`system-badge ${category.is_system ? 'system' : 'custom'}`}>
                              {category.is_system ? '是' : '否'}
                            </span>
                          </td>
                          <td className="action-buttons">
                            <button 
                                className={`btn btn-small btn-info ${category.is_system ? 'disabled' : ''}`}
                                onClick={() => handleEditModalOpen(category)}
                                disabled={category.is_system}
                                title={category.is_system ? '系统分类不允许编辑' : '编辑分类'}
                              >
                                编辑
                              </button>
                            <button 
                              className={`btn btn-small btn-info ${category.is_system ? 'disabled' : ''}`}
                              onClick={(e) => {
                                e.stopPropagation(); // 阻止事件冒泡
                                handleConfigureParameters(category);
                              }}
                              disabled={category.is_system}
                              title={category.is_system ? '系统分类不允许配置参数' : '参数配置'}
                            >
                              参数配置
                            </button>
                            <button 
                              className={`btn btn-small btn-danger ${category.is_system ? 'disabled' : ''}`}
                              onClick={() => handleDelete(category.id)}
                              disabled={category.is_system}
                              title={category.is_system ? '系统分类不允许删除' : '删除分类'}
                            >
                              删除
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
            
            {/* 标签云视图 */}
            {viewMode === 'tagCloud' && (
              <div className="category-tag-cloud">
                {filteredCategories.sort((a, b) => {
                  // 按权重排序，权重越大，排序越靠前
                  if ((a.weight || 0) === (b.weight || 0)) {
                    return (a.display_name || a.name).localeCompare(b.display_name || b.name);
                  }
                  return (b.weight || 0) - (a.weight || 0);
                }).map(category => {
                  // 计算标签的大小，基于分类的权重或其他属性
                  const fontSize = Math.max(14, Math.min(24, 14 + category.weight * 2));
                  const opacity = category.is_active ? 1 : 0.5;
                  
                  return (
                    <div 
                      key={category.id} 
                      className={`category-tag ${category.is_system ? 'system-tag' : ''}`}
                      style={{ 
                        fontSize: `${fontSize}px`,
                        opacity: opacity
                      }}
                      onMouseEnter={() => console.log(category)} // 可以添加悬停效果
                    >
                      {category.display_name}
                      <span className="tag-dimension">({category.dimension})</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* 创建分类模态框 */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>创建新分类</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-form">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入分类名称（英文）"
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入分类显示名称（中文）"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入分类描述"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>维度 *</label>
                <select
                  name="dimension"
                  value={formData.dimension}
                  onChange={handleInputChange}
                  required
                >
                  {dimensions.map(dimension => (
                    <option key={dimension} value={dimension}>{dimension}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>父分类</label>
                <select
                  name="parent_id"
                  value={formData.parent_id || ''}
                  onChange={handleInputChange}
                >
                  <option value="">无</option>
                  {mainCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.display_name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>LOGO</label>
                
                {/* 图片选择 */}
                <div className="logo-upload-section">
                  {previewUrl && (
                    <div className="logo-preview">
                      <h4>预览</h4>
                      <div className="category-logo">
                        <img src={previewUrl} alt="Logo预览" className="logo-image" />
                      </div>
                    </div>
                  )}
                  <select 
                    id="logo-select"
                    value={formData.logo || ''}
                    onChange={handleImageSelect}
                    style={{ marginTop: '10px', width: '100%', padding: '8px' }}
                  >
                    <option value="">请选择图片</option>
                    {categoryImages.map(image => (
                      <option key={image} value={image}>{image}</option>
                    ))}
                  </select>
                  <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
                    从前端已有的图片中选择分类LOGO
                  </small>
                </div>
              </div>
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                />
                <label htmlFor="is_active">启用</label>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  创建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* 编辑分类模态框 */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>编辑分类</h3>
              <button className="btn-close" onClick={handleModalClose}>×</button>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-form">
              <div className="form-group">
                <label>名称 *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入分类名称（英文）"
                />
              </div>
              <div className="form-group">
                <label>显示名称 *</label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleInputChange}
                  required
                  placeholder="输入分类显示名称（中文）"
                />
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="输入分类描述"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>维度 *</label>
                <select
                  name="dimension"
                  value={formData.dimension}
                  onChange={handleInputChange}
                  required
                >
                  {dimensions.map(dimension => (
                    <option key={dimension} value={dimension}>{dimension}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>父分类</label>
                <select
                  name="parent_id"
                  value={formData.parent_id || ''}
                  onChange={handleInputChange}
                >
                  <option value="">无</option>
                  {mainCategories.filter(cat => cat.id !== currentCategory?.id).map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.display_name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>LOGO</label>
                
                {/* 图片选择 */}
                <div className="logo-upload-section">
                  {previewUrl && (
                    <div className="logo-preview">
                      <h4>预览</h4>
                      <div className="category-logo">
                        <img src={previewUrl} alt="Logo预览" className="logo-image" />
                      </div>
                    </div>
                  )}
                  <select 
                    id="logo-select-edit"
                    value={formData.logo || ''}
                    onChange={handleImageSelect}
                    style={{ marginTop: '10px', width: '100%', padding: '8px' }}
                  >
                    <option value="">请选择图片</option>
                    {categoryImages.map(image => (
                      <option key={image} value={image}>{image}</option>
                    ))}
                  </select>
                  <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
                    从前端已有的图片中选择分类LOGO
                  </small>
                </div>
              </div>
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_active_edit"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                />
                <label htmlFor="is_active_edit">启用</label>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={handleModalClose}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  更新
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      

      
      {/* 参数配置模态框 */}
      {showParameterModal && selectedCategoryForParams && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>
                {parameterModalMode === 'add' ? '添加参数' : '编辑参数'} - {selectedCategoryForParams.display_name}
              </h3>
              <button className="btn-close" onClick={handleCloseParameterModal}>×</button>
            </div>
            <form onSubmit={handleParameterSubmit} className="modal-form">
              <div className="form-group">
                <label>参数名称 *</label>
                <input
                  type="text"
                  name="parameter_name"
                  value={parameterFormData.parameter_name}
                  onChange={handleParameterInputChange}
                  required
                  placeholder="输入参数名称"
                  disabled={parameterModalMode === 'edit'}
                />
              </div>
              <div className="form-group">
                <label>参数值 *</label>
                <input
                  type="text"
                  name="parameter_value"
                  value={parameterFormData.parameter_value}
                  onChange={handleParameterInputChange}
                  required
                  placeholder="输入参数值"
                />
              </div>
              <div className="form-group">
                <label>参数类型 *</label>
                <select
                  name="parameter_type"
                  value={parameterFormData.parameter_type}
                  onChange={handleParameterInputChange}
                  required
                >
                  <option value="string">字符串 (string)</option>
                  <option value="number">数字 (number)</option>
                  <option value="boolean">布尔值 (boolean)</option>
                  <option value="array">数组 (array)</option>
                  <option value="object">对象 (object)</option>
                </select>
              </div>
              <div className="form-group">
                <label>描述</label>
                <textarea
                  name="description"
                  value={parameterFormData.description}
                  onChange={handleParameterInputChange}
                  placeholder="输入参数描述"
                  rows="3"
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={handleCloseParameterModal}>
                  取消
                </button>
                <button type="submit" className="btn btn-primary">
                  {parameterModalMode === 'add' ? '添加' : '更新'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 参数配置面板模态框 */}
      {showParameterPanelModal && selectedCategoryForParams && (
        <div className="modal-overlay">
          <div className="modal" style={{ width: '90%', maxWidth: '1200px', maxHeight: '80vh' }}>
            <div className="modal-header">
              <h3>{selectedCategoryForParams.display_name} - 参数配置</h3>
              <button className="btn-close" onClick={handleCloseParameterPanelModal}>×</button>
            </div>
            <div className="modal-content" style={{ overflow: 'auto' }}>
              <div className="parameter-panel-header" style={{ marginBottom: '20px' }}>
                <button 
                  className="btn btn-primary btn-small"
                  onClick={() => handleOpenParameterModal(selectedCategoryForParams, 'add')}
                >
                  添加参数
                </button>
              </div>
              
              {parameterLoading ? (
                <div className="loading">加载中...</div>
              ) : parameterError ? (
                <div className="error-message">{parameterError}</div>
              ) : (
                <div className="parameter-table-container">
                  <table className="parameter-table">
                    <thead>
                      <tr>
                        <th>参数名称</th>
                        <th>参数值</th>
                        <th>参数类型</th>
                        <th>描述</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {categoryParameters[selectedCategoryForParams.id]?.length > 0 ? (
                        categoryParameters[selectedCategoryForParams.id].map((param, index) => (
                          <tr key={index}>
                            <td>{param.parameter_name}</td>
                            <td>{param.parameter_value}</td>
                            <td>{param.parameter_type}</td>
                            <td>{param.description || '-'}</td>
                            <td>
                              <button 
                                className="btn btn-small btn-warning mr-1"
                                onClick={() => handleOpenParameterModal(selectedCategoryForParams, 'edit', param)}
                              >
                                编辑
                              </button>
                              <button 
                                className="btn btn-small btn-danger"
                                onClick={() => handleDeleteParameter(selectedCategoryForParams.id, param.parameter_name)}
                              >
                                删除
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" style={{ textAlign: 'center' }}>暂无参数配置</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelCategoryManagement;