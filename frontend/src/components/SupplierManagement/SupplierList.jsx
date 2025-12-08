import React, { useState } from 'react';
import { useSupplier } from '../contexts/SupplierContext';
import { supplierApi } from '../../utils/api/supplierApi';

const SupplierList = () => {
  const { suppliers, selectedSupplier, selectSupplier, loadSuppliers } = useSupplier();
  const [imageErrors, setImageErrors] = useState({}); // 跟踪哪些图片加载失败

  // 按名称排序供应商
  const sortedSuppliers = [...suppliers]
    .filter(supplier => supplier && supplier.id !== undefined && supplier.name) // 确保只显示有效的供应商
    .sort((a, b) => {
      return a.name.localeCompare(b.name);
    });

  // 生成供应商首字母作为回退logo
  const renderFallbackLogo = (supplier) => {
    const initial = supplier.name?.[0]?.toUpperCase() || '?';
    // 为不同的供应商生成不同的背景色，增强视觉区分度
    const colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e'];
    const colorIndex = (supplier.id || 0) % colors.length;
    const bgColor = colors[colorIndex];
    
    return (
      <div 
        style={{
          width: '18px', 
          height: '18px', 
          backgroundColor: bgColor,
          borderRadius: '2px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: '10px'
        }}
      >
        {initial}
      </div>
    );
  };

  // 处理图片加载错误
  const handleImageError = (supplierId) => {
    setImageErrors(prev => ({ ...prev, [supplierId]: true }));
  };

  // 切换供应商状态
  const toggleSupplierStatus = async (supplierId, isActive) => {
    try {
      
      // 创建FormData对象，因为后端期望Form参数
      const formData = new FormData();
      formData.append('is_active', isActive);
      
      // 发送PUT请求更新状态
      const response = await fetch(`/model-management/suppliers/${supplierId}`, {
        method: 'PUT',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`状态更新失败: ${response.status}`);
      }
     
      // 重新加载供应商数据以更新UI
      loadSuppliers();
    } catch (error) {
      console.error('切换供应商状态失败:', error);
      alert(`切换供应商状态失败: ${error.message}`);
    }
  };

  return (
    <div className="supplier-list">
      {sortedSuppliers.length === 0 ? (
        <div className="no-suppliers">
          <p>暂无可用供应商</p>
        </div>
      ) : (
        sortedSuppliers.map(supplier => (
          <div 
            key={`${supplier.id}-${supplier.name}`} // 使用更唯一的key避免渲染问题
            className={`supplier-item ${selectedSupplier && selectedSupplier.id === supplier.id ? 'selected' : ''}`}
            onClick={() => selectSupplier(supplier)}
          >
            <div className="supplier-info">
              <div className="supplier-logo">
                {/* 检查logo是否存在且未发生错误 */}
                {supplier.logo && !imageErrors[supplier.id] ? (
                  // 如果是完整URL直接使用，否则添加前缀路径
                  <img 
                    src={supplier.logo.startsWith('http') ? supplier.logo : `/logos/providers/${supplier.logo}`} 
                    alt={`${supplier.name} logo`} 
                    onError={() => handleImageError(supplier.id)}
                  />
                ) : (
                  // logo不存在或图片加载失败时使用回退logo
                  renderFallbackLogo(supplier)
                )}
              </div>
              <div className="supplier-name">
                {supplier.name}
              </div>
              <div className="supplier-tag">
                {supplier.is_active ? (
                  <button 
                    className="supplier-status-btn active" 
                    title="点击停用" 
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSupplierStatus(supplier.id, false);
                    }}
                  >
                    🟢 ON
                  </button>
                ) : (
                  <button 
                    className="supplier-status-btn inactive" 
                    title="点击启用" 
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSupplierStatus(supplier.id, true);
                    }}
                  >
                    🔴 OFF
                  </button>
                )}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default SupplierList;