import React from 'react';

/**
 * 调试信息面板组件
 * 显示组件的运行状态和调试信息
 */
const DebugPanel = ({ 
  models, 
  sceneModels, 
  isLoading, 
  localModels 
}) => {
  return (
    <div className="debug-panel" style={{ 
      background: '#f5f5f5', 
      border: '1px solid #ddd', 
      padding: '10px', 
      marginBottom: '20px',
      borderRadius: '4px',
      fontSize: '12px'
    }}>
      <h4 style={{ margin: '0 0 10px 0', color: '#666' }}>调试信息</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div>
          <strong>数据状态:</strong>
          <ul style={{ margin: '5px 0', paddingLeft: '15px' }}>
            <li>所有模型数量: {models.length}</li>
            <li>本地模型数量: {localModels.length}</li>
            {Object.entries(sceneModels).map(([scene, sceneModelList]) => (
              <li key={scene}>{scene}场景模型: {sceneModelList.length}</li>
            ))}
            <li>加载状态: {isLoading ? '加载中...' : '完成'}</li>
          </ul>
        </div>
        <div>
          <strong>API端点:</strong>
          <ul style={{ margin: '5px 0', paddingLeft: '15px' }}>
            <li>/api/v1/models: {models.length > 0 ? '✅ 有数据' : '❌ 无数据'}</li>
            <li>/api/v1/models/local: {localModels.length > 0 ? '✅ 有数据' : '❌ 无数据'}</li>
            {Object.entries(sceneModels).map(([scene, sceneModelList]) => (
              <li key={scene}>/api/v1/models/by-scene/{scene}: {sceneModelList.length > 0 ? '✅ 有数据' : '❌ 无数据'}</li>
            ))}
          </ul>
        </div>
      </div>
      <div>
        <strong>问题分析:</strong>
        <p style={{ margin: '5px 0', fontSize: '11px', color: '#d63384' }}>
          {Object.values(sceneModels).every(models => models.length === 0) 
            ? '⚠️ 场景模型为空：可能原因 - 1. 数据库能力关联数据不足 2. 能力强度要求过高 3. API路径错误' 
            : '✅ 数据正常'}
        </p>
      </div>
    </div>
  );
};

export default DebugPanel;