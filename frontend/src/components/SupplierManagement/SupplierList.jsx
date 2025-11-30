import React, { useState } from 'react';
import { useSupplier } from '../contexts/SupplierContext';

const SupplierList = () => {
  const { suppliers, selectedSupplier, selectSupplier } = useSupplier();
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
          width: '30px', 
          height: '30px', 
          backgroundColor: bgColor,
          borderRadius: '4px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: '14px'
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
            style={{ display: 'flex', alignItems: 'center' }}
          >
            <div className="supplier-info" style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%' }}>
              <div className="supplier-logo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {/* 首先检查logo是否为完整URL且未发生错误 */}
                {supplier.logo && supplier.logo.startsWith('http') && !imageErrors[supplier.id] ? (
                  <img 
                    src={supplier.logo} 
                    alt={`${supplier.name} logo`} 
                    style={{ width: '30px', height: '30px', borderRadius: '4px', objectFit: 'contain' }} 
                    onError={() => handleImageError(supplier.id)}
                  />
                ) : (
                  // 不是URL或图片加载失败时使用回退logo
                  renderFallbackLogo(supplier)
                )}
              </div>
              <div className="supplier-name" style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
                {supplier.name}
              </div>
              <div className="supplier-tag" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {supplier.is_active === false ? (
                  <div className="supplier-tag inactive" title="已禁用" style={{  padding: '2px 8px', borderRadius: '12px', fontSize: '12px', minWidth: '60px', textAlign: 'center' }}>🔴 OFF</div>
                ) : (
                  <div className="supplier-tag active" title="已启用" style={{  padding: '2px 8px', borderRadius: '12px', fontSize: '12px', minWidth: '60px', textAlign: 'center' }}>🟢 ON</div>
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