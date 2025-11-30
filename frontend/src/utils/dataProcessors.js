// 处理供应商数据
export const processSupplierData = (supplier) => {
  if (!supplier) return null;
  
  return {
    ...supplier,
    name: supplier.display_name || supplier.name || '未知供应商',
    logo: supplier.logo || '',
    category: supplier.category || '未分类',
    website: supplier.website || '',
    api_endpoint: supplier.api_endpoint || '',
    api_docs: supplier.api_docs || '',
    api_key: supplier.api_key || '',
    is_active: supplier.is_active !== false
  };
};

// 批量处理供应商数据
export const processSuppliersData = (suppliers) => {
  if (!Array.isArray(suppliers)) return [];
  
  return suppliers.map(processSupplierData);
};

// 处理模型数据
export const processModelData = (model) => {
  if (!model) return null;
  
  return {
    ...model,
    key: model.key || String(model.id),
    name: model.name || '未知模型',
    description: model.description || '暂无描述'
  };
};

// 批量处理模型数据
export const processModelsData = (models) => {
  if (!Array.isArray(models)) return [];
  
  return models.map(processModelData);
};

// 处理分类数据
export const processCategoryData = (category) => {
  if (!category) return null;
  
  return {
    ...category,
    id: category.id || Date.now() + Math.random(),
    name: category.name || '未命名分类',
    display_name: category.display_name || category.name || '未命名分类',
    description: category.description || '暂无描述'
  };
};

// 批量处理分类数据
export const processCategoriesData = (categories) => {
  if (!Array.isArray(categories)) return [];
  
  return categories.map(processCategoryData);
};

// 处理能力数据
export const processCapabilityData = (capability) => {
  if (!capability) return null;
  
  return {
    ...capability,
    id: capability.id || Date.now() + Math.random(),
    name: capability.name || '未命名能力',
    description: capability.description || '暂无描述',
    category_id: capability.category_id || null,
    model_id: capability.model_id || null
  };
};

// 批量处理能力数据
export const processCapabilitiesData = (capabilities) => {
  if (!Array.isArray(capabilities)) return [];
  
  return capabilities.map(processCapabilityData);
};