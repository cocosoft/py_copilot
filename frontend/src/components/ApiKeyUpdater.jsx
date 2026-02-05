import React, { useState, useEffect } from 'react';
import { getImageUrl } from '../config/imageConfig';
import api from '../utils/api';

const ApiKeyUpdater = () => {
  useEffect(() => {
    // 从API获取供应商数据并缓存到localStorage
    const ensureLocalStorageSuppliers = async () => {
      try {
        // 从API获取所有供应商
        const suppliers = await api.supplierApi.getAll();
        
        // 确保suppliers是数组格式
        const suppliersArray = Array.isArray(suppliers) ? suppliers : [];
        
        // 如果API调用成功，将供应商数据保存到localStorage作为缓存
        const STORAGE_PREFIX = 'model_management_';
        const suppliersKey = `${STORAGE_PREFIX}suppliers`;
        localStorage.setItem(suppliersKey, JSON.stringify(suppliersArray));
        console.log('✅ 供应商数据已从API更新到localStorage');
      } catch (error) {
        console.error('❌ 获取供应商数据失败:', error.message);
        console.error('请检查后端服务是否正常运行');
      }
    };
    
    // 添加防抖，避免与其他组件的请求冲突
    const timer = setTimeout(ensureLocalStorageSuppliers, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  // 这个组件不会渲染任何内容
  return null;
};

export default ApiKeyUpdater;