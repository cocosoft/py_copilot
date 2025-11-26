import React, { useEffect } from 'react';
import api from '../utils/api';

const ApiKeyUpdater = () => {
  useEffect(() => {
    // 检查并更新DeepSeek供应商的API密钥
    const updateDeepseekApiKey = async () => {
      try {
        // 获取所有供应商
        const suppliers = await api.supplierApi.getAll();
        
        // 确保suppliers是数组格式
        const suppliersArray = Array.isArray(suppliers) ? suppliers : [];
        
        // 查找DeepSeek供应商
        const deepseekSupplier = suppliersArray.find(s => s.id === 'deepseek');
        
        // 如果找到DeepSeek供应商但API密钥为空或不正确，则更新
        if (deepseekSupplier && deepseekSupplier.apiKey !== 'sk-e532f4d835044ee595b38e25db741999') {
          await api.supplierApi.update('deepseek', {
            ...deepseekSupplier,
            apiKey: 'sk-e532f4d835044ee595b38e25db741999'
          });
          console.log('DeepSeek API密钥已更新');
        }
      } catch (error) {
        console.error('更新API密钥时出错:', error);
        // 直接使用localStorage进行降级更新
        const STORAGE_PREFIX = 'model_management_';
        const suppliersKey = `${STORAGE_PREFIX}suppliers`;
        let suppliers = [];
        
        try {
          const stored = localStorage.getItem(suppliersKey);
          if (stored) {
            suppliers = JSON.parse(stored);
          }
          
          const deepseekIndex = suppliers.findIndex(s => s.id === 'deepseek');
          if (deepseekIndex !== -1) {
            suppliers[deepseekIndex].apiKey = 'sk-e532f4d835044ee595b38e25db741999';
            localStorage.setItem(suppliersKey, JSON.stringify(suppliers));
            console.log('通过localStorage更新了DeepSeek API密钥');
          }
        } catch (localError) {
          console.error('localStorage更新失败:', localError);
        }
      }
    };
    
    updateDeepseekApiKey();
  }, []);

  // 这个组件不会渲染任何内容
  return null;
};

export default ApiKeyUpdater;