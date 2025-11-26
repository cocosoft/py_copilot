import React, { useState, useEffect } from 'react';
import SupplierManagement from './SupplierManagement';
import ModelManagement from './ModelManagement';
import ModelCategoryManagement from './ModelCategoryManagement';
import CapabilityManagementTabs from './CapabilityManagementTabs';
import api from '../utils/api';
import '../styles/IntegratedModelManagement.css';

const IntegratedModelManagement = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [models, setModels] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('models'); // 'models', 'categories', 'capabilities'
  const [categories, setCategories] = useState([]);
  
  const STORAGE_PREFIX = 'model_management_';
  
  // 加载模型分类列表
  const loadCategories = async () => {
    try {
      console.log('🔄 加载模型分类列表...');
      const response = await api.categoryApi.getAll();
      console.log('✅ 模型分类列表响应:', response);
      
      // 统一处理不同的响应格式
      let categories = [];
      if (Array.isArray(response)) {
        categories = response;
      } else if (response && Array.isArray(response.categories)) {
        categories = response.categories;
      } else if (response && Array.isArray(response.data)) {
        categories = response.data;
      }
      
      // 确保所有分类都有必要的属性
      const normalizedCategories = categories.map(category => ({
        ...category,
        id: category.id || Date.now() + Math.random(),
        name: category.name || '未命名分类',
        description: category.description || '暂无描述'
      }));
      
      console.log(`✅ 标准化后的模型分类列表，数量: ${normalizedCategories.length}`, normalizedCategories);
      setCategories(normalizedCategories);
    } catch (error) {
      console.error('❌ 加载模型分类失败:', error);
      
      // 降级处理：直接设置空数组，因为api.categoryApi.getAll应该已经处理了降级
      setCategories([]);
    }
  };
  
  // 加载能力信息列表
  const loadCapabilities = async () => {
    try {
      console.log('🔄 加载能力信息列表...');
      const response = await api.capabilityApi.getAll();
      console.log('✅ 能力信息列表响应:', response);
      
      // 统一处理不同的响应格式
      let capabilities = [];
      if (Array.isArray(response)) {
        capabilities = response;
      } else if (response && Array.isArray(response.capabilities)) {
        capabilities = response.capabilities;
      } else if (response && Array.isArray(response.data)) {
        capabilities = response.data;
      }
      
      // 确保所有能力信息都有必要的属性
      const normalizedCapabilities = capabilities.map(capability => ({
        ...capability,
        id: capability.id || Date.now() + Math.random(),
        name: capability.name || '未命名能力',
        description: capability.description || '暂无描述',
        category_id: capability.category_id || null,
        model_id: capability.model_id || null
      }));
      
      console.log(`✅ 标准化后的能力信息列表，数量: ${normalizedCapabilities.length}`, normalizedCapabilities);
      setCapabilities(normalizedCapabilities);
    } catch (error) {
      console.error('❌ 加载能力信息失败:', error);
      
      // 降级处理：创建默认能力数据
      const defaultCapabilities = [
        { id: 1, name: '文本生成', description: '生成各种类型的文本内容', category_id: 1, model_id: 1 },
        { id: 2, name: '代码生成', description: '生成各种编程语言的代码', category_id: 2, model_id: 1 },
        { id: 3, name: '问答', description: '回答各种领域的问题', category_id: 1, model_id: 1 },
        { id: 4, name: '摘要生成', description: '生成文本摘要', category_id: 1, model_id: 1 }
      ];
      console.log('⚠️ 使用默认能力数据:', defaultCapabilities);
      setCapabilities(defaultCapabilities);
    }
  };
  
  // 在组件挂载时，加载所有必要的数据
  useEffect(() => {
    // 并行加载供应商、分类和能力数据
    console.log('🔄 开始加载所有数据...');
    Promise.all([
      loadSuppliers(),
      loadCategories(),
      loadCapabilities()
    ]).then(() => {
      console.log('✅ 所有数据加载完成');
    }).catch(err => {
      console.error('❌ 数据加载过程中发生错误:', err);
    });
  }, []);
  
  // 当suppliers数据加载后，设置默认选中的供应商
  useEffect(() => {
    console.log('供应商数据更新:', suppliers);
    if (suppliers && suppliers.length > 0) {
      // 先尝试从本地存储获取之前选择的供应商
      const savedSupplierId = localStorage.getItem(`${STORAGE_PREFIX}selected_supplier`);
      let targetSupplier = null;
      
      if (savedSupplierId) {
        // 尝试通过ID查找（处理数字和字符串类型）
        targetSupplier = suppliers.find(s => String(s.id) === savedSupplierId);
        console.log('从本地存储获取的供应商ID:', savedSupplierId, '找到:', !!targetSupplier);
      }
      
      // 如果没有保存的选择，尝试通过key字段选择deepseek供应商
      if (!targetSupplier) {
        targetSupplier = suppliers.find(s => s.key === 'deepseek');
        console.log('尝试通过key选择deepseek供应商:', !!targetSupplier);
      }
      
      // 如果还没有找到，则选择第一个供应商
      if (!targetSupplier && suppliers.length > 0) {
        targetSupplier = suppliers[0];
        console.log('选择第一个供应商:', targetSupplier.name);
      }
      
      if (targetSupplier) {
        setSelectedSupplier(targetSupplier);
        // 存储ID为字符串以保持一致性
        localStorage.setItem(`${STORAGE_PREFIX}selected_supplier`, String(targetSupplier.id));
        console.log('已设置选中的供应商:', targetSupplier.name);
      }
    }
  }, [suppliers]);
  
  // 加载供应商数据
  const loadSuppliers = async () => {
    try {
      setLoading(true);
      console.log('🔄 调用api.supplierApi.getAll() 获取供应商列表');
      const data = await api.supplierApi.getAll();
      console.log('✅ 获取到供应商数据:', data);
      
      // 确保数据是数组格式并添加关键修复：将display_name映射到name字段
      const suppliersArray = Array.isArray(data) ? 
        data.map(supplier => ({
          ...supplier,
          // 优先使用display_name作为name显示，确保所有组件都能正确显示供应商名称
          name: supplier.display_name || supplier.name
        })) : [];
      
      console.log('✅ 处理后的供应商数据（添加name字段）:', suppliersArray);
      setSuppliers(suppliersArray);
      setError(null); // 清除错误状态
      
      if (suppliersArray.length === 0) {
        console.warn('⚠️ 获取到的供应商列表为空');
      }
      
      return suppliersArray; // 返回规范化的数据，以便后续处理
    } catch (err) {
      console.error('❌ 加载供应商失败:', err);
      
      // 降级处理：使用默认供应商数据，不再显示错误，确保页面能正常显示
      // 调用api.supplierApi.getAll()会自动降级到本地存储
      try {
        console.log('🔄 尝试降级获取供应商数据...');
        const defaultSuppliers = await api.supplierApi.getAll();
        console.log('✅ 降级获取到的供应商数据:', defaultSuppliers);
        
        // 关键修复：即使在降级情况下也进行display_name到name的映射
        const processedDefaultSuppliers = Array.isArray(defaultSuppliers) ? 
          defaultSuppliers.map(supplier => ({
            ...supplier,
            name: supplier.display_name || supplier.name
          })) : [];
        
        console.log('✅ 处理后的默认供应商数据:', processedDefaultSuppliers);
        setSuppliers(processedDefaultSuppliers);
      } catch (fallbackErr) {
        console.error('❌ 降级获取供应商数据也失败:', fallbackErr);
        setSuppliers([]);
      }
      
      // 清除错误状态，确保页面能正常显示
      setError(null);
      return []; // 返回空数组，确保后续处理的一致性
    } finally {
      setLoading(false);
      console.log('✅ 供应商数据加载流程完成');
    }
  };

  // 加载模型列表
  const loadModels = async (supplierId) => {
    if (!supplierId) {
      console.warn('⚠️ loadModels: 供应商ID为空');
      return;
    }
    
    try {
      console.log(`🔄 加载模型列表，供应商ID: ${supplierId}`);
      const response = await api.modelApi.getBySupplier(supplierId);
      console.log('✅ 模型列表响应:', response);
      
      // 统一处理不同的响应格式
      let models = [];
      if (Array.isArray(response)) {
        models = response;
      } else if (response && Array.isArray(response.models)) {
        models = response.models;
      } else if (response && Array.isArray(response.data)) {
        models = response.data;
      }
      
      // 确保所有模型都有id和key属性
      const normalizedModels = models.map(model => ({
        ...model,
        key: model.key || String(model.id),
        name: model.name || '未知模型',
        description: model.description || '暂无描述'
      }));
      
      console.log(`✅ 标准化后的模型列表，数量: ${normalizedModels.length}`, normalizedModels);
      setModels(normalizedModels);
      
      // 检查是否需要创建默认模型（针对DeepSeek供应商）
      if (normalizedModels.length === 0 && (String(supplierId) === '3' || String(supplierId).toLowerCase() === 'deepseek')) {
        console.log('⚠️ 未找到模型数据，为DeepSeek创建默认模型');
        // 注意：不再尝试创建，因为api.modelApi.getBySupplier已确保返回默认数据
      }
    } catch (error) {
      console.error('❌ 加载模型失败:', error);
      
      // 降级处理：直接设置空数组，因为api.modelApi.getBySupplier应该已经处理了降级
      setModels([]);
    }
  };

  // 处理供应商选择变化
  const handleSupplierSelect = (supplier) => {
    if (supplier) {
      setSelectedSupplier(supplier);
      // 保存选择到本地存储
      localStorage.setItem(`${STORAGE_PREFIX}selected_supplier`, supplier.id);
    }
  };

  // 处理供应商更新
  const handleSupplierUpdate = () => {
    // 重新加载供应商列表
    loadSuppliers();
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
                        initialSuppliers={suppliers}
                        onSupplierUpdate={loadSuppliers}
                      />
                    </div>
                    
                    {/* 供应商详情容器 */}
                    <div className="model-details-container">
                      {loading ? (
                        <div className="loading">加载中...</div>
                      ) : error ? (
                        <div className="error">{error}</div>
                      ) : selectedSupplier ? (
                        <ModelManagement 
                          selectedSupplier={selectedSupplier} 
                          onSupplierSelect={handleSupplierSelect}
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