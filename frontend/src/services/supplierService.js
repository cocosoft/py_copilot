import api from '../utils/api';

export const supplierService = {
  // 获取所有供应商
  getAll: async () => {
    try {
      const data = await api.supplierApi.getAll();
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error('获取供应商列表失败:', err);
      return [];
    }
  },

  // 获取单个供应商
  getById: async (id) => {
    try {
      return await api.supplierApi.getById(id);
    } catch (err) {
      console.error(`获取供应商 ${id} 失败:`, err);
      return null;
    }
  },

  // 创建供应商
  create: async (supplierData) => {
    try {
      return await api.supplierApi.create(supplierData);
    } catch (err) {
      console.error('创建供应商失败:', err);
      throw err;
    }
  },

  // 更新供应商
  update: async (id, supplierData) => {
    try {
      return await api.supplierApi.update(id, supplierData);
    } catch (err) {
      console.error(`更新供应商 ${id} 失败:`, err);
      throw err;
    }
  },

  // 删除供应商
  delete: async (id) => {
    try {
      return await api.supplierApi.delete(id);
    } catch (err) {
      console.error(`删除供应商 ${id} 失败:`, err);
      throw err;
    }
  }
};