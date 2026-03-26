import React, { useState, useEffect } from 'react';
import { request } from '../../utils/api';
import { useI18n } from '../../hooks/useI18n';

const VectorStoreSettings = () => {
  const { t } = useI18n();
  const [config, setConfig] = useState({
    backend: 'sqlite',
    sqlite_db_path: '',
    chromadb_server_url: 'http://localhost:8008',
    chromadb_collection: 'documents'
  });
  const [status, setStatus] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadConfig();
    loadStatus();
  }, []);

  const loadConfig = async () => {
    try {
      setIsLoading(true);
      const result = await request('/v1/vector-store/config', {
        method: 'GET'
      });
      
      if (result) {
        setConfig(result);
      }
    } catch (error) {
      console.error('加载向量存储配置失败:', error);
      showMessage('error', '加载配置失败');
    } finally {
      setIsLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const result = await request('/v1/vector-store/status', {
        method: 'GET'
      });
      
      if (result) {
        setStatus(result);
      }
    } catch (error) {
      console.error('加载向量存储状态失败:', error);
    }
  };

  const saveConfig = async () => {
    try {
      setIsLoading(true);
      const result = await request('/v1/vector-store/config', {
        method: 'POST',
        data: config
      });
      
      if (result && result.success) {
        showMessage('success', '配置保存成功');
        loadStatus();
      } else {
        showMessage('error', result?.message || '保存失败');
      }
    } catch (error) {
      console.error('保存向量存储配置失败:', error);
      showMessage('error', '保存配置失败');
    } finally {
      setIsLoading(false);
    }
  };

  const switchBackend = async (backend) => {
    try {
      setIsLoading(true);
      const result = await request(`/v1/vector-store/switch/${backend}`, {
        method: 'POST'
      });
      
      if (result && result.success) {
        showMessage('success', `已切换到 ${backend} 后端`);
        setConfig(prev => ({ ...prev, backend }));
        loadStatus();
      } else {
        showMessage('error', result?.message || '切换失败');
      }
    } catch (error) {
      console.error('切换向量存储后端失败:', error);
      showMessage('error', '切换后端失败');
    } finally {
      setIsLoading(false);
    }
  };

  const performHealthCheck = async () => {
    try {
      setIsLoading(true);
      const result = await request('/v1/vector-store/health-check', {
        method: 'POST'
      });
      
      if (result && result.success) {
        setStatus(result.results);
        showMessage('success', '健康检查完成');
      } else {
        showMessage('error', '健康检查失败');
      }
    } catch (error) {
      console.error('健康检查失败:', error);
      showMessage('error', '健康检查失败');
    } finally {
      setIsLoading(false);
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  const handleInputChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getBackendStatus = (backend) => {
    const backendStatus = status[backend];
    if (!backendStatus) return { label: '未知', className: 'status-unknown' };
    
    if (backendStatus.healthy) {
      return { label: '运行中', className: 'status-healthy' };
    } else {
      return { label: '不可用', className: 'status-unhealthy' };
    }
  };

  return (
    <div className="vector-store-settings">
      <h3>向量存储配置</h3>
      
      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="settings-section">
        <h4>后端状态</h4>
        <div className="backend-status-list">
          <div className="backend-status-item">
            <span className="backend-name">SQLite</span>
            <span className={`status-badge ${getBackendStatus('sqlite').className}`}>
              {getBackendStatus('sqlite').label}
            </span>
            {status.sqlite?.details && (
              <span className="status-detail">
                文档数: {status.sqlite.details.total_documents || 0}
              </span>
            )}
          </div>
          <div className="backend-status-item">
            <span className="backend-name">ChromaDB</span>
            <span className={`status-badge ${getBackendStatus('chromadb').className}`}>
              {getBackendStatus('chromadb').label}
            </span>
            {status.chromadb?.details && (
              <span className="status-detail">
                {status.chromadb.details.server_url}
              </span>
            )}
          </div>
        </div>
        
        <button 
          className="btn btn-secondary"
          onClick={performHealthCheck}
          disabled={isLoading}
        >
          {isLoading ? '检查中...' : '执行健康检查'}
        </button>
      </div>

      <div className="settings-section">
        <h4>当前后端</h4>
        <div className="current-backend">
          <span className="backend-label">当前使用:</span>
          <span className="backend-value">{config.backend === 'sqlite' ? 'SQLite' : 'ChromaDB'}</span>
        </div>
        
        <div className="backend-switch">
          <button
            className={`btn ${config.backend === 'sqlite' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => switchBackend('sqlite')}
            disabled={isLoading || config.backend === 'sqlite'}
          >
            切换到 SQLite
          </button>
          <button
            className={`btn ${config.backend === 'chromadb' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => switchBackend('chromadb')}
            disabled={isLoading || config.backend === 'chromadb'}
          >
            切换到 ChromaDB
          </button>
        </div>
      </div>

      <div className="settings-section">
        <h4>配置参数</h4>
        
        <div className="form-group">
          <label>默认后端</label>
          <select
            value={config.backend}
            onChange={(e) => handleInputChange('backend', e.target.value)}
            disabled={isLoading}
          >
            <option value="sqlite">SQLite</option>
            <option value="chromadb">ChromaDB</option>
          </select>
          <small>选择默认的向量存储后端</small>
        </div>

        <div className="form-group">
          <label>SQLite 数据库路径</label>
          <input
            type="text"
            value={config.sqlite_db_path}
            onChange={(e) => handleInputChange('sqlite_db_path', e.target.value)}
            placeholder="./vector_store.db"
            disabled={isLoading}
          />
          <small>SQLite 数据库文件的存储路径</small>
        </div>

        <div className="form-group">
          <label>ChromaDB 服务地址</label>
          <input
            type="text"
            value={config.chromadb_server_url}
            onChange={(e) => handleInputChange('chromadb_server_url', e.target.value)}
            placeholder="http://localhost:8008"
            disabled={isLoading}
          />
          <small>ChromaDB 独立服务的 HTTP 地址</small>
        </div>

        <div className="form-group">
          <label>ChromaDB 集合名称</label>
          <input
            type="text"
            value={config.chromadb_collection}
            onChange={(e) => handleInputChange('chromadb_collection', e.target.value)}
            placeholder="documents"
            disabled={isLoading}
          />
          <small>ChromaDB 默认集合名称</small>
        </div>

        <button
          className="btn btn-primary"
          onClick={saveConfig}
          disabled={isLoading}
        >
          {isLoading ? '保存中...' : '保存配置'}
        </button>
      </div>

      <div className="settings-section">
        <h4>说明</h4>
        <div className="info-box">
          <p><strong>SQLite:</strong> 无需外部服务，内嵌在应用中，适合开发和中小规模数据。</p>
          <p><strong>ChromaDB:</strong> 专业向量数据库，支持高效的相似度搜索，适合大规模数据，需要启动外部服务。</p>
          <p><strong>注意:</strong> 切换后端后，新上传的文档将使用新的存储后端。已有文档的向量数据不会自动迁移。</p>
        </div>
      </div>
    </div>
  );
};

export default VectorStoreSettings;
