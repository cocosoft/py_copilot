import React, { useState, useEffect } from 'react';
import ModelCapabilityManagement from './ModelCapabilityManagement';
import ModelCapabilityAssociation from './ModelCapabilityAssociation';
import CapabilityDimensionManagement from './CapabilityDimensionManagement';
import CapabilityParameterTemplateManagement from './CapabilityParameterTemplateManagement';
import CategoryDefaultCapabilityManagement from './CategoryDefaultCapabilityManagement';
import { capabilityApi } from '../../utils/api/capabilityApi';
import '../../styles/CapabilityManagementTabs.css';

const CapabilityManagementTabs = () => {
  const [activeSubTab, setActiveSubTab] = useState('management'); // 'management', 'association', 'types', 'dimensions'
  const [capabilityTypes, setCapabilityTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [capabilities, setCapabilities] = useState([]);

  const handleSubTabChange = (subTab) => {
    setActiveSubTab(subTab);
  };

  // 只在需要时加载能力类型数据（用于类型统计）
  useEffect(() => {
    if (activeSubTab === 'types') {
      const loadCapabilities = async () => {
        try {
          setLoading(true);
          const data = await capabilityApi.getAll();
          const capabilitiesData = Array.isArray(data) ? data : [];
          setCapabilities(capabilitiesData);
          
          // 提取能力类型
          const types = [...new Set(capabilitiesData.map(c => c.capability_type).filter(Boolean))];
          setCapabilityTypes(types);
        } catch (err) {
          console.error('加载能力列表失败:', err);
          setCapabilities([]);
          setCapabilityTypes([]);
        } finally {
          setLoading(false);
        }
      };

      loadCapabilities();
    }
  }, [activeSubTab]);

  return (
    <div className="capability-management-tabs">
      {/* 子Tab导航 */}
      <div className="sub-tab-navigation">
        <button 
          className={`sub-tab-button ${activeSubTab === 'management' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('management')}
        >
          能力管理
        </button>
        <button 
          className={`sub-tab-button ${activeSubTab === 'types' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('types')}
        >
          能力类型
        </button>
        <button 
          className={`sub-tab-button ${activeSubTab === 'association' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('association')}
        >
          模型能力关联
        </button>
        <button 
          className={`sub-tab-button ${activeSubTab === 'dimensions' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('dimensions')}
        >
          能力维度
        </button>
        <button 
          className={`sub-tab-button ${activeSubTab === 'templates' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('templates')}
        >
          参数模板
        </button>
        <button 
          className={`sub-tab-button ${activeSubTab === 'category-defaults' ? 'active' : ''}`}
          onClick={() => handleSubTabChange('category-defaults')}
        >
          分类默认能力
        </button>
      </div>
      
      {/* 子Tab内容区域 */}
      <div className="sub-tab-content">
        {activeSubTab === 'management' && (
          <ModelCapabilityManagement />
        )}
        {activeSubTab === 'types' && (
          <div className="types-panel">
            <div className="panel-header">
              <h3>能力类型统计</h3>
            </div>
            {loading ? (
              <div className="loading-state">加载中...</div>
            ) : (
              <div className="capability-types-grid">
                {capabilityTypes.length === 0 ? (
                  <div className="empty-state">暂无能力类型数据</div>
                ) : (
                  capabilityTypes.map(type => {
                    const typeCapabilities = capabilities.filter(c => c.capability_type === type);
                    return (
                      <div key={type} className="capability-type-card">
                        <div className="type-header">
                          <h4>{type}</h4>
                          <span className="type-count">{typeCapabilities.length} 个能力</span>
                        </div>
                        <ul className="type-capabilities">
                          {typeCapabilities.slice(0, 5).map(cap => (
                            <li key={cap.id}>
                              <span className="cap-name">{cap.display_name || cap.name}</span>
                              <span className={`cap-status ${cap.is_active ? 'active' : 'inactive'}`}>
                                {cap.is_active ? '启用' : '禁用'}
                              </span>
                            </li>
                          ))}
                          {typeCapabilities.length > 5 && (
                            <li className="more-items">
                              + 还有 {typeCapabilities.length - 5} 个能力
                            </li>
                          )}
                        </ul>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>
        )}
        {activeSubTab === 'association' && (
          <ModelCapabilityAssociation />
        )}
        {activeSubTab === 'dimensions' && (
          <CapabilityDimensionManagement />
        )}
        {activeSubTab === 'templates' && (
          <CapabilityParameterTemplateManagement />
        )}
        {activeSubTab === 'category-defaults' && (
          <CategoryDefaultCapabilityManagement />
        )}
      </div>
    </div>
  );
};

export default CapabilityManagementTabs;