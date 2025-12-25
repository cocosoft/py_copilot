import React, { useState, useEffect } from 'react';
import { capabilityApi } from '../../utils/api/capabilityApi';
import modelApi from '../../utils/api/modelApi';
import ModelCapabilityManagement from '../CapabilityManagement/ModelCapabilityManagement';
import ModelCapabilityAssociation from '../CapabilityManagement/ModelCapabilityAssociation';
import '../../styles/CapabilityManagement.css';

const CapabilityManagementMain = ({ selectedSupplier, onBack, selectedModel }) => {
  const [activeTab, setActiveTab] = useState('capabilities'); // capabilities | associations | types
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [models, setModels] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [capabilityTypes, setCapabilityTypes] = useState([]);
  const [selectedLevel, setSelectedLevel] = useState('system');
  const [suppliers, setSuppliers] = useState([]);

  const levelOptions = [
    { value: 'system', label: '系统级别' },
    { value: 'supplier', label: '供应商级别' },
    { value: 'model_type', label: '模型类型级别' },
    { value: 'model_capability', label: '模型能力级别' },
    { value: 'model', label: '模型级别' }
  ];

  useEffect(() => {
    loadInitialData();
  }, [selectedSupplier]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      await Promise.all([
        loadModels(),
        loadCapabilities(),
        loadSuppliers()
      ]);
    } catch (err) {
      console.error('加载初始数据失败:', err);
      setError('加载数据失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const loadModels = async () => {
    try {
      const response = await modelApi.getAll();
      const modelsData = Array.isArray(response.models) ? response.models : [];
      setModels(modelsData);
    } catch (err) {
      console.error('加载模型列表失败:', err);
      setModels([]);
    }
  };

  const loadCapabilities = async () => {
    try {
      const data = await capabilityApi.getAll();
      setCapabilities(Array.isArray(data) ? data : []);

      const types = [...new Set(data.map(c => c.capability_type).filter(Boolean))];
      setCapabilityTypes(types);
    } catch (err) {
      console.error('加载能力列表失败:', err);
      setCapabilities([]);
    }
  };

  const loadSuppliers = async () => {
    try {
      const { supplierApi } = await import('../../utils/api');
      const response = await supplierApi.getAll();
      const suppliersData = Array.isArray(response) ? response : (response.suppliers || []);
      setSuppliers(suppliersData);
    } catch (err) {
      console.error('加载供应商列表失败:', err);
      setSuppliers([]);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const handleCapabilityUpdate = () => {
    loadCapabilities();
    setSuccess('能力更新成功');
    setTimeout(() => setSuccess(null), 3000);
  };

  const handleAssociationUpdate = () => {
    loadCapabilities();
    setSuccess('关联更新成功');
    setTimeout(() => setSuccess(null), 3000);
  };

  if (loading && capabilities.length === 0) {
    return (
      <div className="capability-management-main">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="capability-management-main">
      <div className="section-header">
        <div className="header-left">
          {onBack && (
            <button className="btn btn-secondary btn-back" onClick={onBack}>
              返回
            </button>
          )}
          <h2>能力管理</h2>
        </div>
        <div className="header-right">
          {selectedSupplier && (
            <span className="current-supplier">
              当前供应商: {selectedSupplier.name}
            </span>
          )}
        </div>
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

      <div className="capability-tabs">
        <button
          className={`tab-button ${activeTab === 'capabilities' ? 'active' : ''}`}
          onClick={() => handleTabChange('capabilities')}
        >
          能力定义
        </button>
        <button
          className={`tab-button ${activeTab === 'associations' ? 'active' : ''}`}
          onClick={() => handleTabChange('associations')}
        >
          模型能力关联
        </button>
        <button
          className={`tab-button ${activeTab === 'types' ? 'active' : ''}`}
          onClick={() => handleTabChange('types')}
        >
          能力类型
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'capabilities' && (
          <div className="capabilities-panel">
            <div className="panel-header">
              <h3>能力列表</h3>
              <div className="header-actions">
                <select
                  className="level-selector"
                  value={selectedLevel}
                  onChange={(e) => setSelectedLevel(e.target.value)}
                >
                  {levelOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <ModelCapabilityManagement />
          </div>
        )}

        {activeTab === 'associations' && (
          <div className="associations-panel">
            <div className="panel-header">
              <h3>模型能力关联管理</h3>
            </div>
            <ModelCapabilityAssociation
              models={models}
              capabilities={capabilities}
              onAssociationChange={handleAssociationUpdate}
            />
          </div>
        )}

        {activeTab === 'types' && (
          <div className="types-panel">
            <div className="panel-header">
              <h3>能力类型统计</h3>
            </div>
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
          </div>
        )}
      </div>
    </div>
  );
};

export default CapabilityManagementMain;
