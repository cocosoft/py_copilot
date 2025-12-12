import React, { useState, useEffect } from 'react';
import { getImageUrl } from '../config/imageConfig';
import api from '../utils/api';

const ApiKeyUpdater = () => {
  useEffect(() => {
    // 此组件不再自动更新API密钥，API密钥应通过供应商管理界面手动设置
    // 仅保留localStorage降级功能，确保前端应用能正常工作
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
      } catch (error) {
        console.error('获取供应商数据时出错:', error);
        // API调用失败时，确保localStorage中有基本的供应商数据结构
        const STORAGE_PREFIX = 'model_management_';
        const suppliersKey = `${STORAGE_PREFIX}suppliers`;
        let suppliers = [];
        
        try {
          const stored = localStorage.getItem(suppliersKey);
          if (stored) {
            suppliers = JSON.parse(stored);
          }
          
          // 确保至少有一个基本的供应商结构
          if (suppliers.length === 0) {
            suppliers = [
              {
                id: 'deepseek',
                name: 'DeepSeek',
                key: 'deepseek',
                logo: getImageUrl('providers', 'deepseek.png'),
                category: 'llm',
                website: 'https://deepseek.com',
                api_endpoint: 'https://api.deepseek.com/v1',
                api_docs: 'https://platform.deepseek.com/api-docs/v1',
                api_key_required: true,
                is_active: true
                // 注意：不再硬编码API密钥
              }
            ];
            localStorage.setItem(suppliersKey, JSON.stringify(suppliers));
          }
        } catch (localError) {
          console.error('localStorage操作失败:', localError);
        }
      }
    };
    
    ensureLocalStorageSuppliers();
  }, []);

  // 这个组件不会渲染任何内容
  return null;
};

export default ApiKeyUpdater;