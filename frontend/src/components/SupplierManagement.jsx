import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import SupplierModal from './SupplierModal';
import '../styles/ModelManagement.css';

const SupplierManagement = ({ onSupplierSelect, selectedSupplier, initialSuppliers, onSupplierUpdate }) => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 优先使用传入的初始供应商数据（来自父组件）
  useEffect(() => {
    if (initialSuppliers && Array.isArray(initialSuppliers) && initialSuppliers.length > 0) {
      console.log('使用父组件传入的供应商数据:', initialSuppliers);
      // 处理初始供应商数据，确保字段命名一致
      const processedInitialSuppliers = initialSuppliers.map(supplier => ({
        ...supplier,
        // 前端字段映射
        name: supplier.name,
        logo: supplier.logo,
        category: supplier.category,
        website: supplier.website,
        api_endpoint: supplier.api_endpoint,
        api_docs: supplier.api_docs,
        api_key: supplier.api_key,
        is_active: supplier.is_active
      }));
      setSuppliers(processedInitialSuppliers);
      setLoading(false);
    } else {
      // 如果没有初始数据，再加载
      loadSuppliers();
    }
  }, [initialSuppliers]);

  const loadSuppliers = async () => {
    try {
      setLoading(true);
      console.log('正在加载供应商数据...');
      const data = await api.supplierApi.getAll();
      console.log('获取到的供应商原始数据:', data);
      
      // 处理供应商数据，确保字段命名一致
      const processedSuppliers = Array.isArray(data) ? 
        data.map(supplier => ({
          ...supplier,
          // 前端字段映射
          name: supplier.name,
          logo: supplier.logo,
          category: supplier.category,
          website: supplier.website,
          api_endpoint: supplier.api_endpoint,
          api_docs: supplier.api_docs,
          api_key: supplier.api_key,
          is_active: supplier.is_active
        })) : [];
      
      console.log('处理后用于UI显示的供应商数据:', processedSuppliers);
      setSuppliers(processedSuppliers);
      setError(null); // 清除错误状态
    } catch (err) {
      console.error('Failed to load suppliers:', err);
      // 即使出错，也要设置空数组，避免页面空白
      setSuppliers([]);
      // 暂时注释掉错误显示，避免页面显示错误
      // setError('加载供应商数据失败');
    } finally {
      setLoading(false);
    }
  };

  const [currentSupplier, setCurrentSupplier] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('add'); // 'add' 或 'edit'
  const [saving, setSaving] = useState(false);

  // 处理供应商选择
  const handleSupplierSelect = (supplier) => {
    console.log('SupplierManagement: 选择供应商:', supplier.name, supplier.id, supplier.key);
    setCurrentSupplier(supplier);
    if (onSupplierSelect) {
      onSupplierSelect(supplier);
    }
  };

  // 处理编辑供应商
  const handleEditSupplier = (supplier) => {
    setCurrentSupplier({ ...supplier });
    setModalMode('edit');
    setIsModalOpen(true);
  };

  // 处理打开添加供应商模态窗口
  const handleOpenAddModal = () => {
    setModalMode('add');
    setIsModalOpen(true);
  };

  // 处理关闭模态窗口
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentSupplier(null);
  };

  // 处理保存供应商（添加或更新） - 简化版本
  const handleSaveSupplier = async (apiData, frontendData) => {
    try {
      setSaving(true);
      
      if (modalMode === 'edit' && currentSupplier) {
        console.log('SupplierManagement: 编辑模式，准备更新供应商', currentSupplier.id);
        // 直接使用已经格式化好的apiData进行API调用
        await api.supplierApi.update(currentSupplier.id, apiData);
        console.log('SupplierManagement: 更新供应商成功');
      } else if (modalMode === 'add') {
        console.log('SupplierManagement: 添加模式，准备创建新供应商');
        // 添加新供应商 - 直接使用已经格式化好的apiData
        await api.supplierApi.create(apiData);
        console.log('SupplierManagement: 创建供应商成功');
      }
      
      // 关键点：保存成功后直接重新加载供应商列表
      // 这样可以确保前端显示的是后端的最新数据，避免任何字段映射问题
      console.log('SupplierManagement: 重新加载供应商列表以获取最新数据...');
      await loadSuppliers();
      
      // 强制刷新页面数据，确保所有组件都更新
      if (onSupplierUpdate) {
        await onSupplierUpdate();
      }
      
      // 关闭模态窗口
      handleCloseModal();
      
      // 返回成功信息
      return { success: true };
      
    } catch (err) {
      setError(modalMode === 'add' ? '添加供应商失败' : '更新供应商失败');
      console.error(`${modalMode === 'add' ? '添加' : '更新'}供应商失败:`, err);
      // 重新加载供应商数据以确保UI显示正确
      setTimeout(() => loadSuppliers(), 100);
      throw err; // 抛出错误让模态窗口处理
    } finally {
      setSaving(false);
    }
  };

  // 处理删除供应商
  const handleDeleteSupplier = async (supplier) => {
    if (!window.confirm(`确定要删除供应商 "${supplier.name}" 吗？删除后将无法恢复。`)) {
      return;
    }

    try {
      setSaving(true);
      await api.supplierApi.delete(supplier.id);
      setSuppliers(suppliers.filter(s => s.id !== supplier.id));
      // 如果删除的是当前选中的供应商，则清除选中状态
      if (selectedSupplier?.id === supplier.id) {
        handleSupplierSelect(null);
      }
    } catch (err) {
      setError('删除供应商失败');
      console.error('Failed to delete supplier:', err);
    } finally {
      setSaving(false);
    }
  };

  // 现在添加供应商的功能通过模态窗口实现，这个函数已经被handleSaveSupplier替代

  // 按名称排序供应商
  const sortedSuppliers = (Array.isArray(suppliers) ? [...suppliers] : []).sort((a, b) => {
    return (a.name || '').localeCompare(b.name || '');
  });

  return (
    <div className="supplier-management">
      <div className="supplier-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h3 style={{ margin: 0, color: '#2c3e50', fontSize: '16px' }}>供应商列表</h3>
        <button 
          className="btn btn-primary"
          onClick={handleOpenAddModal}
          disabled={saving}
        >
          + 添加供应商
        </button>
      </div>

      {/* 供应商模态窗口将在底部渲染 */}

      {/* 供应商列表 */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <div className="supplier-list">
          {sortedSuppliers.map(supplier => (
          <div 
            key={supplier.id} 
            className={`supplier-item ${selectedSupplier && selectedSupplier.id === supplier.id ? 'selected' : ''}`}
            onClick={() => handleSupplierSelect(supplier)}
          >
            <div className="supplier-info" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="supplier-logo">
                {supplier.logo ? (
                    <img src={supplier.logo} alt={`${supplier.name} logo`} style={{ width: '30px', height: '30px', borderRadius: '4px' }} />
                  ) : (
                  <div style={{ width: '30px', height: '30px', backgroundColor: '#e0e0e0', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {supplier.name?.[0] || '?'}
                  </div>
                )}
              </div>
              <div className="supplier-details">
                <div className="supplier-name">
                  {supplier.name}
                  {supplier.category && <span style={{ marginLeft: '8px', fontSize: '12px', color: '#666' }}>({supplier.category})</span>}
                </div>
                {supplier.is_active === false ? (
                  <div className="supplier-tag" title="OFF"></div>
                ) : (
                  <div className="supplier-tag active" title="已启用">🟢 ON</div>
                )}
              </div>
            </div>
          </div>
          ))}
        </div>
      )}

      {/* 供应商模态窗口 */}
      <SupplierModal 
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveSupplier}
        supplier={currentSupplier}
        mode={modalMode}
      />
    </div>
  );
};

export default SupplierManagement;