import React, { useState, useEffect } from 'react';
import { capabilityApi } from '../../utils/api/capabilityApi';
import '../../styles/CapabilityManagement.css';

const CapabilityVersionManagement = () => {
  const [capabilities, setCapabilities] = useState([]);
  const [selectedCapability, setSelectedCapability] = useState(null);
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newVersionData, setNewVersionData] = useState({
    version: '',
    version_description: '',
    is_current: false,
    is_stable: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // 加载能力列表
  useEffect(() => {
    loadCapabilities();
  }, []);

  const loadCapabilities = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await capabilityApi.getAll();
      const capabilitiesData = Array.isArray(response?.capabilities)
        ? response.capabilities
        : Array.isArray(response) ? response : [];
      
      setCapabilities(capabilitiesData);
      
      // 默认选择第一个能力
      if (capabilitiesData.length > 0) {
        handleCapabilitySelect(capabilitiesData[0].id);
      }
    } catch (err) {
      console.error('加载能力列表失败:', err);
      setError('加载能力列表失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理能力选择
  const handleCapabilitySelect = async (capabilityId) => {
    try {
      setLoading(true);
      setError(null);
      setSelectedCapability(capabilityId);
      
      // 获取该能力的所有版本
      const versionsResponse = await capabilityApi.getCapabilityVersions(capabilityId);
      const processedVersions = Array.isArray(versionsResponse?.data)
        ? versionsResponse.data
        : Array.isArray(versionsResponse) ? versionsResponse : [];
      
      setVersions(processedVersions);
      setSelectedVersion(null);
    } catch (err) {
      console.error(`获取能力 ${capabilityId} 的版本列表失败:`, err);
      setError('获取版本列表失败，请重试');
      setVersions([]);
    } finally {
      setLoading(false);
    }
  };

  // 处理版本选择
  const handleVersionSelect = (version) => {
    setSelectedVersion(version);
  };

  // 打开创建版本模态框
  const openCreateModal = () => {
    // 自动生成版本号
    if (versions.length > 0) {
      const currentVersion = versions.find(v => v.is_current) || versions[0];
      const versionParts = currentVersion.version.split('.').map(Number);
      versionParts[2] += 1;
      const newVersion = versionParts.join('.');
      
      setNewVersionData({
        version: newVersion,
        version_description: '',
        is_current: false,
        is_stable: false
      });
    } else {
      setNewVersionData({
        version: '1.0.0',
        version_description: '',
        is_current: true,
        is_stable: true
      });
    }
    
    setShowCreateModal(true);
  };

  // 关闭创建版本模态框
  const closeCreateModal = () => {
    setShowCreateModal(false);
  };

  // 处理新版本数据变化
  const handleNewVersionChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewVersionData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // 创建新版本
  const handleCreateVersion = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!selectedCapability) return;
      
      // 调用API创建版本
      const response = await capabilityApi.createCapabilityVersion(
        selectedCapability,
        newVersionData
      );
      
      setSuccess('创建版本成功');
      closeCreateModal();
      
      // 重新加载版本列表
      handleCapabilitySelect(selectedCapability);
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('创建版本失败:', err);
      setError('创建版本失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 设置当前版本
  const handleSetCurrentVersion = async (versionId) => {
    try {
      setLoading(true);
      setError(null);
      
      if (!selectedCapability) return;
      
      await capabilityApi.setCurrentVersion(selectedCapability, versionId);
      
      setSuccess('设置当前版本成功');
      
      // 重新加载版本列表
      handleCapabilitySelect(selectedCapability);
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('设置当前版本失败:', err);
      setError('设置当前版本失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 设置稳定版本
  const handleSetStableVersion = async (versionId) => {
    try {
      setLoading(true);
      setError(null);
      
      if (!selectedCapability) return;
      
      await capabilityApi.setStableVersion(selectedCapability, versionId);
      
      setSuccess('设置稳定版本成功');
      
      // 重新加载版本列表
      handleCapabilitySelect(selectedCapability);
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('设置稳定版本失败:', err);
      setError('设置稳定版本失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !capabilities.length) {
    return <div className="loading-state">加载中...</div>;
  }

  const selectedCapabilityObj = capabilities.find(cap => cap.id === selectedCapability);

  return (
    <div className="capability-version-management">
      <div className="section-header">
        <h3>能力版本管理</h3>
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

      {/* 能力选择器 */}
      <div className="capability-selector">
        <label htmlFor="capability-select">选择能力:</label>
        <select
          id="capability-select"
          value={selectedCapability || ''}
          onChange={(e) => handleCapabilitySelect(parseInt(e.target.value))}
        >
          <option value="">请选择能力</option>
          {capabilities.map(capability => (
            <option key={capability.id} value={capability.id}>
              {capability.display_name || capability.name}
            </option>
          ))}
        </select>
      </div>

      {selectedCapability && (
        <div className="version-management">
          <div className="management-header">
            <h4>
              {selectedCapabilityObj?.display_name || selectedCapabilityObj?.name} 的版本
            </h4>
            <button
              className="btn btn-primary"
              onClick={openCreateModal}
              disabled={loading}
            >
              创建新版本
            </button>
          </div>

          {/* 版本列表 */}
          <div className="versions-list">
            {versions.length === 0 ? (
              <div className="empty-state">该能力暂无版本</div>
            ) : (
              versions.map(version => (
                <div
                  key={version.id}
                  className={`version-item ${selectedVersion?.id === version.id ? 'selected' : ''} ${version.is_current ? 'current' : ''} ${version.is_stable ? 'stable' : ''}`}
                  onClick={() => handleVersionSelect(version)}
                >
                  <div className="version-header">
                    <div className="version-info">
                      <span className="version-number">v{version.version}</span>
                      <span className="version-date">{new Date(version.created_at).toLocaleString()}</span>
                    </div>
                    <div className="version-badges">
                      {version.is_current && <span className="badge current-badge">当前版本</span>}
                      {version.is_stable && <span className="badge stable-badge">稳定版本</span>}
                    </div>
                  </div>
                  {version.version_description && (
                    <div className="version-description">
                      {version.version_description}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* 版本详情 */}
          {selectedVersion && (
            <div className="version-details">
              <h5>版本详情</h5>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">版本号:</span>
                  <span className="detail-value">{selectedVersion.version}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">创建时间:</span>
                  <span className="detail-value">{new Date(selectedVersion.created_at).toLocaleString()}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">当前版本:</span>
                  <span className="detail-value">{selectedVersion.is_current ? '是' : '否'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">稳定版本:</span>
                  <span className="detail-value">{selectedVersion.is_stable ? '是' : '否'}</span>
                </div>
                <div className="detail-item full-width">
                  <span className="detail-label">版本描述:</span>
                  <span className="detail-value">{selectedVersion.version_description || '无'}</span>
                </div>
              </div>

              <div className="version-actions">
                {!selectedVersion.is_current && (
                  <button
                    className="btn btn-primary"
                    onClick={() => handleSetCurrentVersion(selectedVersion.id)}
                    disabled={loading}
                  >
                    设置为当前版本
                  </button>
                )}
                {!selectedVersion.is_stable && (
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleSetStableVersion(selectedVersion.id)}
                    disabled={loading}
                  >
                    设置为稳定版本
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 创建版本模态框 */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>创建新版本</h3>
              <button className="btn-close" onClick={closeCreateModal}>×</button>
            </div>
            <form className="modal-form">
              <div className="form-group">
                <label>版本号 *</label>
                <input
                  type="text"
                  name="version"
                  value={newVersionData.version}
                  onChange={handleNewVersionChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>版本描述</label>
                <textarea
                  name="version_description"
                  value={newVersionData.version_description}
                  onChange={handleNewVersionChange}
                  rows="3"
                  placeholder="描述此版本的主要变化..."
                />
              </div>
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_current"
                  name="is_current"
                  checked={newVersionData.is_current}
                  onChange={handleNewVersionChange}
                />
                <label htmlFor="is_current">设为当前版本</label>
              </div>
              <div className="form-group form-check">
                <input
                  type="checkbox"
                  id="is_stable"
                  name="is_stable"
                  checked={newVersionData.is_stable}
                  onChange={handleNewVersionChange}
                />
                <label htmlFor="is_stable">设为稳定版本</label>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeCreateModal}>
                  取消
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleCreateVersion}
                  disabled={loading}
                >
                  {loading ? '创建中...' : '创建版本'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CapabilityVersionManagement;