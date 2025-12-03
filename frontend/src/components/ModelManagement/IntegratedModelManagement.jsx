import { useState, useEffect } from 'react';
import SupplierManagement from '../SupplierManagement/SupplierManagement';
import ModelManagement from './ModelManagement';
import ModelCategoryManagement from '../CapabilityManagement/ModelCategoryManagement';
import CapabilityManagementTabs from '../CapabilityManagement/CapabilityManagementTabs';
import { useSupplier } from '../../contexts/SupplierContext';
import api from '../../utils/api';
import '../../styles/IntegratedModelManagement.css';

const IntegratedModelManagement = () => {
  const supplierContext = useSupplier();
  const { selectedSupplier, selectSupplier, suppliers: contextSuppliers, loading: contextLoading } = supplierContext;
  const [activeTab, setActiveTab] = useState('models'); // 'models', 'categories', 'capabilities'
  // 直接使用context中的suppliers，不再维护自己的状态
  const [loading, setLoading] = useState(true);

  // 加载模型分类列表
  const loadCategories = async () => {
    try {
      const response = await api.categoryApi.getAll();
    } catch (error) {
      console.error('❌ 加载模型分类失败:', error);
    }
  };
  
  // 加载能力信息列表
  const loadCapabilities = async () => {
    try {
      const response = await api.capabilityApi.getAll();
    } catch (error) {
      console.error('❌ 加载能力信息失败:', error);
    }
  };

  // 加载供应商列表 - 已移除，直接使用context中的数据
  
  // 在组件挂载时，加载必要的数据
  useEffect(() => {
    // 并行加载分类和能力数据
    Promise.all([
      loadCategories(),
      loadCapabilities()
      // 不再加载自己的供应商列表，直接使用context中的数据
    ]).then(() => {
      setLoading(false);
    }).catch(err => {
      console.error('❌ 数据加载过程中发生错误:', err);
      setLoading(false);
    });
  }, []);

  // 处理供应商选择
  const handleSupplierSelect = (supplier) => {
    selectSupplier(supplier);
  };

  // 处理供应商更新
  const handleSupplierUpdate = async () => {
    // 使用SupplierContext中的loadSuppliers方法重新加载数据
    if (supplierContext.loadSuppliers) {
      await supplierContext.loadSuppliers();
    }
  };

  return (
      <div className="integrated-model-management">
        <div className="content-section">
            <div className="tab-navigation">
              <button 
                className={`tab-button ${activeTab === 'models' ? 'active' : ''}`}
                onClick={() => setActiveTab('models')}
              >
                模型
              </button>
              <button 
                className={`tab-button ${activeTab === 'categories' ? 'active' : ''}`}
                onClick={() => setActiveTab('categories')}
              >
                分类
              </button>
              <button 
                className={`tab-button ${activeTab === 'capabilities' ? 'active' : ''}`}
                onClick={() => setActiveTab('capabilities')}
              >
                能力
              </button>
            </div>
            <div className="tab-content">
              {activeTab === 'models' && (
                <div className="management-layout">
                  <div className="models-content">
                    {/* 供应商管理容器 */}
                    <div className="supplier-management-container">
                      <SupplierManagement 
                        onSupplierSelect={handleSupplierSelect}
                        selectedSupplier={selectedSupplier}
                        initialSuppliers={contextSuppliers}
                        onSupplierUpdate={handleSupplierUpdate}
                      />
                    </div>
                    
                    {/* 供应商详情容器 */}
                    <div className="model-details-container">
                      {loading ? (
                        <div className="loading">加载中...</div>
                      ) : selectedSupplier ? (
                        <ModelManagement 
                          selectedSupplier={selectedSupplier} 
                          onSupplierUpdate={handleSupplierUpdate}
                        />
                      ) : (
                        <div className="no-selection">请先选择一个供应商</div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {activeTab === 'categories' && (
                <div className="categories-content">
                  <ModelCategoryManagement />
                </div>
              )}
              {activeTab === 'capabilities' && (
                <div className="capabilities-content">
                  <CapabilityManagementTabs />
                </div>
              )}
            </div>
          </div>
        </div>
    );
};

export default IntegratedModelManagement;