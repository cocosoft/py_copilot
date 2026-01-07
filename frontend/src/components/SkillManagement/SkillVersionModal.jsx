import React, { useState, useEffect } from 'react';
import { useSkills } from '../../hooks/useSkills';
import './SkillManagement.css';

function SkillVersionModal({ skill, onClose }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedVersion1, setSelectedVersion1] = useState(null);
  const [selectedVersion2, setSelectedVersion2] = useState(null);
  const [showCompare, setShowCompare] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [showRollbackConfirm, setShowRollbackConfirm] = useState(false);
  const [rollbackVersion, setRollbackVersion] = useState(null);
  
  const { getVersions, rollbackVersion: performRollback, compareVersions } = useSkills();

  useEffect(() => {
    loadVersions();
  }, [skill]);

  const loadVersions = async () => {
    setLoading(true);
    setError('');
    try {
      const versionsData = await getVersions(skill.id);
      setVersions(versionsData);
    } catch (err) {
      setError('加载版本失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleRollback = async (version) => {
    setLoading(true);
    setError('');
    try {
      await performRollback(skill.id, version.id);
      await loadVersions();
      setShowRollbackConfirm(false);
      setRollbackVersion(null);
    } catch (err) {
      setError('回滚失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!selectedVersion1 || !selectedVersion2) {
      setError('请选择两个版本进行比较');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const result = await compareVersions(selectedVersion1.id, selectedVersion2.id);
      setComparisonResult(result);
      setShowCompare(true);
    } catch (err) {
      setError('比较失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderDiff = (diffKey, diffValue) => {
    const getFieldLabel = (key) => {
      const labels = {
        version: '版本号',
        description: '描述',
        content: '内容',
        parameters_schema: '参数模式',
        requirements: '依赖',
        tags: '标签'
      };
      return labels[key] || key;
    };

    const formatValue = (value) => {
      if (typeof value === 'object' && value !== null) {
        return JSON.stringify(value, null, 2);
      }
      return value || '';
    };

    return (
      <div key={diffKey} className="version-diff-item">
        <h4>{getFieldLabel(diffKey)}</h4>
        <div className="version-diff-content">
          <div className="version-diff-column">
            <div className="version-diff-header">{comparisonResult.version1}</div>
            <pre className="version-diff-value">{formatValue(diffValue.version1)}</pre>
          </div>
          <div className="version-diff-column">
            <div className="version-diff-header">{comparisonResult.version2}</div>
            <pre className="version-diff-value">{formatValue(diffValue.version2)}</pre>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="skill-modal-backdrop" onClick={handleBackdropClick}>
      <div className="skill-modal skill-version-modal">
        <div className="skill-modal-header">
          <h2>{skill.name} - 版本管理</h2>
          <button className="close-btn" onClick={onClose}>
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        
        <div className="skill-modal-body">
          {error && <div className="error-message">{error}</div>}
          
          {loading ? (
            <div className="loading-indicator">加载中...</div>
          ) : (
            <>
              {!showCompare ? (
                <>
                  <div className="version-list-header">
                    <h3>版本历史</h3>
                    <div className="version-compare-controls">
                      <select 
                        value={selectedVersion1?.id || ''} 
                        onChange={(e) => setSelectedVersion1(versions.find(v => v.id === parseInt(e.target.value)))}
                        className="version-select"
                      >
                        <option value="">选择版本1</option>
                        {versions.map(v => (
                          <option key={v.id} value={v.id}>{v.version}</option>
                        ))}
                      </select>
                      <select 
                        value={selectedVersion2?.id || ''} 
                        onChange={(e) => setSelectedVersion2(versions.find(v => v.id === parseInt(e.target.value)))}
                        className="version-select"
                      >
                        <option value="">选择版本2</option>
                        {versions.map(v => (
                          <option key={v.id} value={v.id}>{v.version}</option>
                        ))}
                      </select>
                      <button 
                        className="compare-btn" 
                        onClick={handleCompare}
                        disabled={!selectedVersion1 || !selectedVersion2}
                      >
                        比较
                      </button>
                    </div>
                  </div>
                  
                  <div className="version-list">
                    {versions.map(version => (
                      <div key={version.id} className={`version-item ${version.is_current ? 'current-version' : ''}`}>
                        <div className="version-info">
                          <div className="version-header">
                            <span className="version-number">{version.version}</span>
                            {version.is_current && <span className="current-badge">当前版本</span>}
                          </div>
                          <div className="version-meta">
                            <span className="version-date">
                              {new Date(version.created_at).toLocaleString()}
                            </span>
                          </div>
                          <div className="version-changelog">
                            {version.change_log || '无变更日志'}
                          </div>
                        </div>
                        <div className="version-actions">
                          {!version.is_current && (
                            <button 
                              className="rollback-btn"
                              onClick={() => {
                                setRollbackVersion(version);
                                setShowRollbackConfirm(true);
                              }}
                            >
                              回滚
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="version-compare-section">
                  <div className="compare-header">
                    <h3>版本比较: {comparisonResult.version1} vs {comparisonResult.version2}</h3>
                    <button className="back-btn" onClick={() => {
                      setShowCompare(false);
                      setComparisonResult(null);
                    }}>
                      返回版本列表
                    </button>
                  </div>
                  
                  <div className="version-diff-result">
                    {Object.keys(comparisonResult.diffs).length === 0 ? (
                      <p>两个版本没有差异</p>
                    ) : (
                      Object.entries(comparisonResult.diffs).map(([key, value]) => renderDiff(key, value))
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
        
        {showRollbackConfirm && rollbackVersion && (
          <div className="modal-overlay">
            <div className="confirm-modal">
              <h3>确认回滚</h3>
              <p>确定要将技能 "{skill.name}" 回滚到版本 {rollbackVersion.version} 吗？</p>
              <p className="warning">此操作会创建一个新的版本记录，并将当前版本替换为所选版本。</p>
              <div className="confirm-modal-actions">
                <button 
                  className="cancel-btn" 
                  onClick={() => {
                    setShowRollbackConfirm(false);
                    setRollbackVersion(null);
                  }}
                >
                  取消
                </button>
                <button 
                  className="confirm-btn"
                  onClick={() => handleRollback(rollbackVersion)}
                  disabled={loading}
                >
                  {loading ? '回滚中...' : '确认回滚'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SkillVersionModal;
