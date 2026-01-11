import React, { useState, useEffect } from 'react';
import { capabilityApi } from '../../utils/api/capabilityApi';
import CapabilityModal from './CapabilityModal';
import '../../styles/ModelCapabilityManagement.css';

const ModelCapabilityManagement = () => {
  const [capabilities, setCapabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null); // 添加成功状态
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add'); // 'add' 或 'edit'
  const [currentCapability, setCurrentCapability] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // 当前激活的标签页
  // 分页相关状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  
  // 获取所有能力
  const loadCapabilities = async (current = currentPage, size = pageSize) => {
    try {
      setLoading(true);
      // 暂时移除分页参数，一次性获取所有数据
      const params = {};
      
      // 根据activeTab设置筛选条件
      if (activeTab !== 'all') {
        if (activeTab === 'active' || activeTab === 'inactive') {
          params.is_active = activeTab === 'active';
        } else {
          params.capability_type = activeTab;
        }
      }
      
      // 获取所有能力（包括激活和禁用的）
      const response = await capabilityApi.getAll(params);
      
      // 处理API响应
      let capabilitiesData = [];
      let totalCount = 0;
      
      // 检查API响应格式
      if (response && Array.isArray(response)) {
        capabilitiesData = response;
        totalCount = response.length;
      } else if (response && response.data && Array.isArray(response.data)) {
        capabilitiesData = response.data;
        totalCount = response.data.length;
      } else if (response && response.total !== undefined) {
        totalCount = response.total;
      }
      
      // 标准化能力数据，确保每个能力都有必要的属性
      const normalizedCapabilities = capabilitiesData
        .map(capability => ({
          id: capability.id ?? `capability_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          name: capability.name ?? `未命名能力_${capability.id || 'unknown'}`,
          display_name: capability.display_name ?? capability.name ?? '未命名能力',
          description: capability.description || '',
          capability_type: capability.capability_type || 'general',
          is_active: capability.is_active ?? true,
          is_system: capability.is_system ?? false,
          ...capability
        }));
      
      console.log('📊 能力数据处理完成', {
        response, 
        capabilitiesData: capabilitiesData.length, 
        totalCount, 
        normalizedCapabilities: normalizedCapabilities.length
      });
       
      setCapabilities(normalizedCapabilities);
      setTotal(totalCount);
      setError(null);
    } catch (err) {
      console.error('❌ 获取能力失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      setError('获取能力列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 筛选能力（基于完整数据进行客户端筛选）
  const filterCapabilities = () => {
    let filtered = capabilities;
    
    if (activeTab === 'all') {
      // 返回所有能力
    } else if (activeTab === 'active') {
      filtered = capabilities.filter(cap => cap.is_active);
    } else if (activeTab === 'inactive') {
      filtered = capabilities.filter(cap => !cap.is_active);
    } else {
      // 按能力类型筛选
      filtered = capabilities.filter(cap => cap.capability_type === activeTab);
    }
    
    return filtered;
  };

  // 获取筛选后的总数
  const getFilteredTotal = () => {
    const filtered = filterCapabilities();
    return filtered.length;
  };
  
  // 初始化加载
  useEffect(() => {
    loadCapabilities();
  }, []);
  
  // 打开创建模态框
  const handleCreateModalOpen = () => {
    setModalMode('add');
    setCurrentCapability(null);
    setShowModal(true);
  };
  
  // 打开编辑模态框
  const handleEditModalOpen = (capability) => {
    setModalMode('edit');
    setCurrentCapability(capability);
    setShowModal(true);
  };
  
  // 关闭模态框
  const handleModalClose = () => {
    setShowModal(false);
    setCurrentCapability(null);
  };
  
  // 提交表单
  const handleSubmit = async (formData) => {
    try {
      if (modalMode === 'add') {
        await capabilityApi.create(formData);
        setSuccess('能力创建成功');
      } else if (modalMode === 'edit' && currentCapability) {
        await capabilityApi.update(currentCapability.id, formData);
        setSuccess('能力更新成功');
      }
      
      // 关闭模态框
      setShowModal(false);
      // 重新加载列表
      loadCapabilities(currentPage, pageSize);
      // 3秒后自动清除成功消息
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error(`${modalMode === 'add' ? '创建' : '更新'}能力失败:`, JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      setError(`${modalMode === 'add' ? '创建' : '更新'}能力失败，请检查输入并重试`);
    }
  };
  
  // 处理删除
  const handleDelete = async (capabilityId) => {
    if (window.confirm('确定要删除这个能力吗？删除前请确保该能力没有关联的模型。')) {
      try {
        await capabilityApi.delete(capabilityId);
        loadCapabilities(); // 重新加载列表
        setSuccess('能力删除成功');
        // 3秒后自动清除成功消息
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        console.error('删除能力失败:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
        setError('删除能力失败，可能是因为该能力与模型存在关联');
      }
    }
  };
  
  // 获取不同类型的能力列表（用于筛选）
  const getCapabilityTypes = () => {
    const types = new Set(capabilities.map(cap => cap.capability_type).filter(Boolean));
    return Array.from(types);
  };
  
  const capabilityTypes = getCapabilityTypes();
  
  // 获取分页后的能力列表
  const getPagedCapabilities = () => {
    const filtered = filterCapabilities();
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const pagedData = filtered.slice(startIndex, endIndex);
    return pagedData;
  };
  
  // 获取总页数
  const getTotalPages = () => {
    const filteredTotal = getFilteredTotal();
    const totalPages = Math.ceil(filteredTotal / pageSize);
    console.log('🔍 总页数计算 - 筛选总数:', filteredTotal, '每页大小:', pageSize, '总页数:', totalPages);
    return totalPages;
  };
  
  // 处理标签页点击
  const handleTabClick = (type) => {
    setActiveTab(type);
    setCurrentPage(1); // 切换标签时重置到第一页
    loadCapabilities(1, pageSize);
    
    // 确保分页状态正确
    setTimeout(() => {
      const newTotalPages = getTotalPages();
      if (newTotalPages === 0 && currentPage !== 1) {
        setCurrentPage(1);
      }
    }, 0);
  };
  
  // 处理分页变化
  const handlePageChange = (page, size) => {
    setCurrentPage(page);
    setPageSize(size);
    loadCapabilities(page, size);
  };
  
  // 处理每页显示数量变化
  const handlePageSizeChange = (current, size) => {
    setPageSize(size);
    setCurrentPage(1); // 改变每页显示数量时重置到第一页
    loadCapabilities(1, size);
  };
  
  if (loading) {
    return <div className="capability-management-loading">加载中...</div>;
  }
  
  return (
    <div className="model-capability-management">
      <div className="capability-header">
        <button 
          className="btn btn-primary" 
          onClick={handleCreateModalOpen}
        >
          创建能力
        </button>
      </div>
      
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess(null)} className="btn btn-small">×</button>
        </div>
      )}
      
      <div className="capability-content">
        {capabilities.length === 0 ? (
          <div className="empty-state">暂无能力数据</div>
        ) : (
          <div className="capability-tabs">
            <div 
              className={`tab ${activeTab === 'all' ? 'active' : ''}`} 
              data-type="all"
              onClick={() => handleTabClick('all')}
            >
              所有能力
            </div>
            {capabilityTypes.map(type => (
              <div 
                key={type} 
                className={`tab ${activeTab === type ? 'active' : ''}`} 
                data-type={type}
                onClick={() => handleTabClick(type)}
              >
                {type}
              </div>
            ))}
            <div 
              className={`tab ${activeTab === 'active' ? 'active' : ''}`} 
              data-type="active"
              onClick={() => handleTabClick('active')}
            >
              启用
            </div>
            <div 
              className={`tab ${activeTab === 'inactive' ? 'active' : ''}`} 
              data-type="inactive"
              onClick={() => handleTabClick('inactive')}
            >
              禁用
            </div>
          </div>
        )}
        
        <div className="capability-table-container">
          <table className="capability-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>名称</th>
                <th>显示名称</th>
                <th>类型</th>
                <th>状态</th>
                <th>是否系统能力</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {getPagedCapabilities().map(capability => (
                <tr key={capability.id}>
                  <td>{capability.id}</td>
                  <td>{capability.name}</td>
                  <td>{capability.display_name}</td>
                  <td>
                    <span className={`capability-type-badge ${capability.capability_type}`}>
                      {capability.capability_type || '-'}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${capability.is_active ? 'active' : 'inactive'}`}>
                      {capability.is_active ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td>
                    <span className={`system-badge ${capability.is_system ? 'system' : 'user'}`}>
                      {capability.is_system ? '是' : '否'}
                    </span>
                  </td>
                  <td className="action-buttons">
                    <button 
                      className="btn btn-small btn-info" 
                      onClick={() => handleEditModalOpen(capability)}
                      title="编辑"
                      disabled={capability.is_system}
                    >
                      编辑
                    </button>
                    <button 
                      className="btn btn-small btn-danger" 
                      onClick={() => handleDelete(capability.id)}
                      title="删除"
                      disabled={capability.is_system}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* 分页组件 */}
        {getFilteredTotal() > 0 && (
          <div className="capability-pagination">
            <div className="pagination-info">
              显示第 {currentPage} 页，共 {getTotalPages()} 页，共 {getFilteredTotal()} 条记录
            </div>
            <div className="pagination-controls">
              <button 
                className="btn btn-small" 
                onClick={() => handlePageChange(currentPage - 1, pageSize)}
                disabled={currentPage === 1}
              >
                上一页
              </button>
              <span className="page-info">第 {currentPage} / {getTotalPages()} 页</span>
              <button 
                className="btn btn-small" 
                onClick={() => handlePageChange(currentPage + 1, pageSize)}
                disabled={currentPage >= getTotalPages()}
              >
                下一页
              </button>
              <select 
                className="page-size-select" 
                value={pageSize}
                onChange={(e) => handlePageSizeChange(currentPage, parseInt(e.target.value))}
              >
                <option value={10}>10条/页</option>
                <option value={20}>20条/页</option>
                <option value={50}>50条/页</option>
                <option value={100}>100条/页</option>
              </select>
            </div>
          </div>
        )}
      </div>
      
      {/* 能力管理模态框 */}
      <CapabilityModal
        visible={showModal}
        mode={modalMode}
        capability={currentCapability}
        onCancel={handleModalClose}
        onSubmit={handleSubmit}
      />
    </div>
  );
};

export default ModelCapabilityManagement;