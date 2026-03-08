import React, { useState, useEffect } from 'react';
import { getImageUrl, DEFAULT_IMAGES } from '../../config/imageConfig';
import api from '../../utils/api';
import SupplierModal from './SupplierModal';
import '../../styles/ModelManagement.css';
// Adding additional logging for debugging logo field issues

const SupplierManagement = ({ onSupplierSelect, selectedSupplier, initialSuppliers, onSupplierUpdate }) => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 优先使用传入的初始供应商数据（来自父组件）
  useEffect(() => {
    if (initialSuppliers && Array.isArray(initialSuppliers) && initialSuppliers.length > 0) {
      // initialSuppliers 已经由 getAll 格式化，直接使用
      setSuppliers(initialSuppliers);
      setLoading(false);
    } else {
      // 如果没有初始数据，再加载
      loadSuppliers();
    }
  }, [initialSuppliers]);

  const loadSuppliers = async () => {
    try {
      setLoading(true);
      const data = await api.supplierApi.getAll();
      
      // 处理供应商数据，确保字段命名一致
      // getAll 已经返回格式化后的数据，使用 apiUrl 而不是 api_endpoint
      const processedSuppliers = Array.isArray(data) ? data : [];
      
      setSuppliers(processedSuppliers);
      setError(null); // 清除错误状态
    } catch (err) {
      console.error('Failed to load suppliers:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
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
  const [success, setSuccess] = useState(null); // 成功消息状态

  // 从SupplierDetail.jsx中提取的getSupplierLogo函数
  const getSupplierLogo = (supplier) => {
    if (!supplier) return '';

    try {
      // 如果有logo
      if (supplier.logo) {
        // 检测是否为外部URL
        if (supplier.logo.startsWith('http')) {
          // 使用后端代理端点处理外部URL，避免ORB安全限制
          const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(supplier.logo)}`;
          return proxyUrl;
        } else {
          // 使用配置的图片路径生成函数
          return getImageUrl('providers', supplier.logo);
        }
      }
      // 没有logo时返回空字符串
      return '';
    } catch (error) {
      console.error('获取供应商logo失败:', JSON.stringify({ message: error.message, stack: error.stack }, null, 2));
      return '';
    }
  };

  // 处理供应商选择
  const handleSupplierSelect = (supplier) => {
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

  // 处理保存供应商（添加或更新） - 支持FormData文件上传
  const handleSaveSupplier = async (apiData) => {
    try {
      setSaving(true);
      
      // 检查是否是FormData对象（用于文件上传）
      const isFormData = apiData instanceof FormData;
      
      if (modalMode === 'edit' && currentSupplier) {
        // 直接使用已经格式化好的apiData进行API调用（支持FormData和普通对象）
        await api.supplierApi.update(currentSupplier.id, apiData);
      } else if (modalMode === 'add') {
        // 添加新供应商 - 直接使用已经格式化好的apiData（支持FormData和普通对象）
        await api.supplierApi.create(apiData);
      }
      
      // 关键点：保存成功后直接重新加载供应商列表
      // 这样可以确保前端显示的是后端的最新数据，避免任何字段映射问题
      await loadSuppliers();
      
      // 强制刷新页面数据，确保所有组件都更新
      if (onSupplierUpdate) {
        await onSupplierUpdate();
      }
      
      // 关闭模态窗口
      handleCloseModal();
      
      // 显示成功消息
      setSuccess(modalMode === 'add' ? '供应商创建成功' : '供应商更新成功');
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
      
      // 返回成功信息
      return { success: true };
      
    } catch (err) {
      setError(modalMode === 'add' ? '添加供应商失败' : '更新供应商失败');
      console.error(`${modalMode === 'add' ? '添加' : '更新'}供应商失败:`, JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
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
      console.error('Failed to delete supplier:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setSaving(false);
    }
  };

  // 现在添加供应商的功能通过模态窗口实现，这个函数已经被handleSaveSupplier替代

  // 按状态（启用在前）和名称排序供应商
  const sortedSuppliers = (Array.isArray(suppliers) ? [...suppliers] : []).sort((a, b) => {
    // 首先按激活状态排序（启用在前）
    if (a.is_active && !b.is_active) return -1;
    if (!a.is_active && b.is_active) return 1;
    // 如果状态相同，则按名称排序
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
      ) : success ? (
        <div className="success">{success}</div>
      ) : (
        <div className="supplier-list">
          {sortedSuppliers.map(supplier => (
          <div 
            key={supplier.id} 
            className={`supplier-item ${selectedSupplier && selectedSupplier.id === supplier.id ? 'selected' : ''}`}
            style={{ display: 'flex', alignItems: 'center' }}
            onClick={() => handleSupplierSelect(supplier)}
          >
            <div className="supplier-info" style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%' }}>
              <div className="supplier-logo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px' }}>
                <div style={{ position: 'relative', width: '36px', height: '36px' }}>
                  <img 
                    src={getSupplierLogo(supplier)} 
                    alt={`${supplier.name} Logo`} 
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      borderRadius: '4px',
                      objectFit: 'contain',
                      backgroundColor: '#f5f5f5'
                    }} 
                    onError={(e) => {
                        // 图片加载失败时隐藏图片
                        e.target.style.display = 'none';
                      }}
                  />
                </div>
              </div>
              <div className="supplier-name" style={{ flex: 1, display: 'flex', alignItems: 'center', fontSize: '14px', fontWeight: 'bold' }}>
                {supplier.name}
              </div>
              <div className="supplier-tag" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {supplier.is_active === false ? (
                  <div></div>
                ) : (
                  <div className="supplier-tag active" title="已启用" style={{  padding: '2px 8px', borderRadius: '12px', fontSize: '12px', minWidth: '48px', textAlign: 'center' }}>🟢 ON</div>
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