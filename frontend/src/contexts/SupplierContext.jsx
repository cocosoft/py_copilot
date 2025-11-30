import { createContext, useState, useEffect, useContext } from 'react';
import api from '../utils/api';

const SupplierContext = createContext();

export const SupplierProvider = ({ children }) => {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 加载供应商数据 - 从API获取真实数据库数据
  const loadSuppliers = async () => {
    try {
      setLoading(true);
      console.log('🔍 开始加载供应商数据，当前时间:', new Date().toLocaleTimeString());
      
      // 尝试从API获取真实数据
      console.log('🔄 准备调用API.supplierApi.getAll()获取真实数据库数据');
      const data = await api.supplierApi.getAll();
      console.log('✅ API返回的供应商数据数量:', Array.isArray(data) ? data.length : 0);
      
      // 统一处理数据格式，确保字段命名一致
      const processedSuppliers = Array.isArray(data) ? 
        data.map(supplier => ({
          ...supplier,
          name: supplier.name,
          is_active: supplier.is_active ?? true
        })) : [];
        
      console.log('🔄 处理后的供应商数据数量:', processedSuppliers.length);
      
      // 确保只返回有效的供应商数据
      const finalSuppliers = processedSuppliers.filter(supplier => supplier.id && supplier.name);
      
      console.log('✅ 最终使用的供应商数据数量:', finalSuppliers.length);
      setSuppliers(finalSuppliers);
      setError(null);
      return finalSuppliers;
    } catch (err) {
      console.error('❌ 加载供应商失败:', err.message, err.stack);
      setError('加载供应商失败');
      setSuppliers([]);
      return [];
    } finally {
      setLoading(false);
      console.log('🔚 供应商数据加载完成');
    }
  };

  // 保存供应商
  const saveSupplier = async (supplierData, supplierId = null) => {
    try {
      setLoading(true);
      if (supplierId) {
        await api.supplierApi.update(supplierId, supplierData);
      } else {
        await api.supplierApi.create(supplierData);
      }
      // 重新加载供应商数据
      await loadSuppliers();
      setError(null);
      return true;
    } catch (err) {
      setError('保存供应商失败');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // 删除供应商
  const deleteSupplier = async (supplierId) => {
    try {
      setLoading(true);
      await api.supplierApi.delete(supplierId);
      // 重新加载供应商数据
      await loadSuppliers();
      setError(null);
      return true;
    } catch (err) {
      setError('删除供应商失败');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // 选择供应商
  const selectSupplier = (supplier) => {
    setSelectedSupplier(supplier);
    // 保存到本地存储
    if (supplier) {
      localStorage.setItem('selected_supplier', String(supplier.id));
    }
  };

  // 初始化加载供应商数据
  useEffect(() => {
    loadSuppliers();
  }, []);

  // 当供应商数据加载后，设置默认选中的供应商
  useEffect(() => {
    if (suppliers.length > 0) {
      const savedSupplierId = localStorage.getItem('selected_supplier');
      if (savedSupplierId) {
        const targetSupplier = suppliers.find(s => String(s.id) === savedSupplierId);
        if (targetSupplier) {
          selectSupplier(targetSupplier);
        }
      } else if (suppliers.length > 0) {
        selectSupplier(suppliers[0]);
      }
    }
  }, [suppliers]);

  return (
    <SupplierContext.Provider value={{
      suppliers,
      selectedSupplier,
      loading,
      error,
      loadSuppliers,
      saveSupplier,
      deleteSupplier,
      selectSupplier
    }}>
      {children}
    </SupplierContext.Provider>
  );
};

// 确保一致的导出格式，修复Fast Refresh警告
export function useSupplier() {
  const context = useContext(SupplierContext);
  if (!context) {
    throw new Error('useSupplier must be used within a SupplierProvider');
  }
  return context;
}

// SupplierProvider已经在定义时导出，不需要重复导出