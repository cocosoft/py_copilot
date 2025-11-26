// API模块整合文件
// 从共享工具导入通用函数和常量
import { API_BASE_URL, STORAGE_PREFIX, request } from './apiUtils';

// 从独立模块导入供应商API
import { supplierApi } from './api/supplierApi';
export { supplierApi };

// 从独立模块导入模型API
import { modelApi } from './api/modelApi';
export { modelApi };

// 临时简化的其他API
// 从分类API模块导入
import { categoryApi } from './api/categoryApi';
export { categoryApi };

// 从能力API模块导入
import { capabilityApi } from './api/capabilityApi';
export { capabilityApi };

// 从对话API模块导入
import { conversationApi } from './api/conversationApi';
export { conversationApi };

// 添加调试日志包装函数
const withDebugLog = (apiModule, moduleName) => {
  const wrapped = {};
  for (const key in apiModule) {
    if (typeof apiModule[key] === 'function') {
      wrapped[key] = async (...args) => {
        console.log(`🔍 ${moduleName}.${key} 调用开始`, args);
        try {
          const result = await apiModule[key](...args);
          console.log(`✅ ${moduleName}.${key} 调用成功，结果:`, result);
          return result;
        } catch (error) {
          console.error(`❌ ${moduleName}.${key} 调用失败:`, error);
          throw error;
        }
      };
    } else {
      wrapped[key] = apiModule[key];
    }
  }
  return wrapped;
};

// 便捷方法
export const getDefaultModel = async () => {
  try {
    const models = await modelApi.getAll();
    return models.find(model => model.is_default) || models[0] || null;
  } catch (error) {
    console.error('获取默认模型失败:', error);
    return null;
  }
};

// 导出所有API（已单独导出，此处省略以避免重复）

// 默认导出（带调试日志）
export default {
  supplierApi: withDebugLog(supplierApi, 'supplierApi'),
  modelApi: withDebugLog(modelApi, 'modelApi'),
  categoryApi: withDebugLog(categoryApi, 'categoryApi'),
  capabilityApi: withDebugLog(capabilityApi, 'capabilityApi'),
  conversationApi: withDebugLog(conversationApi, 'conversationApi'),
  getDefaultModel
};

// 为兼容性保留临时函数
export const fetchSuppliers = async () => {
  return supplierApi.getAll();
};

export const createSupplier = async (supplierData) => {
  return supplierApi.create(supplierData);
};

export const updateSupplier = async (supplierId, updatedData) => {
  return supplierApi.update(supplierId, updatedData);
};

export const deleteSupplier = async (supplierId) => {
  return supplierApi.delete(supplierId);
};

// 分类相关兼容性函数
export const fetchCategories = async () => {
  return categoryApi.getAll();
};

export const createCategory = async (categoryData) => {
  return categoryApi.create(categoryData);
};

export const updateCategory = async (categoryId, updatedData) => {
  return categoryApi.update(categoryId, updatedData);
};

export const deleteCategory = async (categoryId) => {
  return categoryApi.delete(categoryId);
};

// 能力相关兼容性函数
export const fetchCapabilities = async (params = {}) => {
  return capabilityApi.getAll(params);
};

export const createCapability = async (capabilityData) => {
  return capabilityApi.create(capabilityData);
};

export const updateCapability = async (capabilityId, updatedData) => {
  return capabilityApi.update(capabilityId, updatedData);
};

export const deleteCapability = async (capabilityId) => {
  return capabilityApi.delete(capabilityId);
};

// 本地处理函数导出（为兼容性保留）
export const handleLocalSupplierGetAll = async () => {
  return supplierApi.getAll();
};