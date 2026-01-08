import React, { useState, useEffect } from 'react';
import { skillApi } from '../../services/skillApi';
import ChartRenderer from './ChartRenderer';

function SkillArtifactsViewer({ skillId, executionLogId }) {
  const [artifacts, setArtifacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [previewArtifact, setPreviewArtifact] = useState(null);

  useEffect(() => {
    if (executionLogId) {
      loadArtifacts();
    }
  }, [skillId, executionLogId]);

  const loadArtifacts = async () => {
    try {
      setLoading(true);
      const data = await skillApi.getArtifacts(skillId, executionLogId);
      setArtifacts(data.artifacts || []);
    } catch (err) {
      setError('加载Artifacts失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (artifactId) => {
    try {
      const response = await skillApi.downloadArtifact(skillId, executionLogId, artifactId);
      // 这里需要处理下载逻辑，根据实际API返回格式调整
      console.log('下载Artifact:', response);
    } catch (err) {
      setError('下载失败: ' + err.message);
    }
  };

  const handlePreview = async (artifactId) => {
    try {
      const data = await skillApi.previewArtifact(skillId, executionLogId, artifactId);
      setPreviewArtifact(data);
    } catch (err) {
      setError('预览失败: ' + err.message);
    }
  };

  const getArtifactIcon = (type) => {
    const icons = {
      html: '🌐',
      js: '⚡',
      md: '📝',
      json: '📋',
      chart: '📊',
      image: '🖼️',
      file: '📁'
    };
    return icons[type] || '📄';
  };

  const renderArtifactContent = (artifact) => {
    switch (artifact.type) {
      case 'html':
        return (
          <div className="artifact-html">
            <iframe 
              srcDoc={artifact.content}
              title={artifact.name}
              className="html-preview"
              sandbox="allow-scripts"
            />
          </div>
        );
      
      case 'js':
        return (
          <div className="artifact-js">
            <pre className="code-preview">{artifact.content}</pre>
          </div>
        );
      
      case 'md':
        return (
          <div className="artifact-md">
            <div className="markdown-content">
              {artifact.content}
            </div>
          </div>
        );
      
      case 'json':
        return (
          <div className="artifact-json">
            <pre className="json-preview">
              {JSON.stringify(JSON.parse(artifact.content), null, 2)}
            </pre>
          </div>
        );
      
      case 'chart':
        return (
          <div className="artifact-chart">
            <div className="chart-container">
              <ChartRenderer 
                data={artifact.content} 
                name={artifact.name}
                metadata={artifact.metadata}
              />
            </div>
          </div>
        );
      
      default:
        return (
          <div className="artifact-default">
            <pre className="text-preview">{artifact.content}</pre>
          </div>
        );
    }
  };

  if (loading) {
    return <div className="artifacts-viewer loading">加载Artifacts中...</div>;
  }

  if (!executionLogId) {
    return <div className="artifacts-viewer no-log">请先执行技能以查看Artifacts</div>;
  }

  return (
    <div className="artifacts-viewer">
      <div className="artifacts-header">
        <h3>执行结果 Artifacts</h3>
        <div className="artifacts-count">
          {artifacts.length} 个Artifacts
        </div>
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {artifacts.length === 0 ? (
        <div className="no-artifacts">
          本次执行未生成任何Artifacts
        </div>
      ) : (
        <div className="artifacts-grid">
          {artifacts.map((artifact, index) => (
            <div key={artifact.id || index} className="artifact-card">
              <div className="artifact-header">
                <div className="artifact-icon">
                  {getArtifactIcon(artifact.type)}
                </div>
                <div className="artifact-info">
                  <div className="artifact-name">{artifact.name}</div>
                  <div className="artifact-type">{artifact.type.toUpperCase()}</div>
                </div>
                <div className="artifact-actions">
                  <button 
                    className="btn btn-primary btn-sm"
                    onClick={() => handlePreview(artifact.id)}
                    title="预览"
                  >
                    👁️
                  </button>
                  <button 
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleDownload(artifact.id)}
                    title="下载"
                  >
                    📥
                  </button>
                </div>
              </div>
              
              <div className="artifact-preview">
                {renderArtifactContent(artifact)}
              </div>
              
              {artifact.description && (
                <div className="artifact-description">
                  {artifact.description}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Artifact预览模态框 */}
      {previewArtifact && (
        <div className="artifact-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h4>{previewArtifact.name}</h4>
              <button 
                className="close-btn"
                onClick={() => setPreviewArtifact(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              {renderArtifactContent(previewArtifact)}
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-primary"
                onClick={() => handleDownload(previewArtifact.id)}
              >
                下载
              </button>
              <button 
                className="btn btn-secondary"
                onClick={() => setPreviewArtifact(null)}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SkillArtifactsViewer;