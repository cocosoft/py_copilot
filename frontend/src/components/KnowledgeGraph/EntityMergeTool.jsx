/**
 * 实体合并工具组件
 *
 * 用于合并相似实体，提供相似实体列表、合并预览和确认合并功能
 */

import React, { useState, useEffect } from 'react';
import './EntityMergeTool.css';

/**
 * 实体合并工具组件
 *
 * @param {Object} props - 组件属性
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @param {Function} props.onMergeComplete - 合并完成回调
 * @param {Function} props.onCancel - 取消回调
 * @returns {JSX.Element} 实体合并工具界面
 */
const EntityMergeTool = ({ knowledgeBaseId, onMergeComplete, onCancel }) => {
  // 相似实体组列表
  const [similarGroups, setSimilarGroups] = useState([]);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 当前选中的组
  const [selectedGroup, setSelectedGroup] = useState(null);
  // 合并预览数据
  const [mergePreview, setMergePreview] = useState(null);
  // 合并中状态
  const [merging, setMerging] = useState(false);
  // 合并结果
  const [mergeResult, setMergeResult] = useState(null);
  // 搜索关键词
  const [searchKeyword, setSearchKeyword] = useState('');
  // 相似度阈值
  const [similarityThreshold, setSimilarityThreshold] = useState(0.8);

  // 加载相似实体组
  useEffect(() => {
    loadSimilarGroups();
  }, [knowledgeBaseId, similarityThreshold]);

  const loadSimilarGroups = async () => {
    setLoading(true);
    // TODO: 调用API获取相似实体组
    // Mock数据
    setTimeout(() => {
      const mockGroups = [
        {
          id: 1,
          entities: [
            { id: 101, name: '张三', type: 'PERSON', confidence: 0.95, document_count: 5 },
            { id: 102, name: '张三（工程师）', type: 'PERSON', confidence: 0.88, document_count: 3 },
            { id: 103, name: '张 三', type: 'PERSON', confidence: 0.82, document_count: 2 }
          ],
          similarity: 0.92,
          reason: '名称相似'
        },
        {
          id: 2,
          entities: [
            { id: 201, name: 'ABC公司', type: 'ORG', confidence: 0.96, document_count: 8 },
            { id: 202, name: 'ABC科技有限公司', type: 'ORG', confidence: 0.91, document_count: 4 }
          ],
          similarity: 0.85,
          reason: '名称相似'
        },
        {
          id: 3,
          entities: [
            { id: 301, name: '北京', type: 'LOCATION', confidence: 0.98, document_count: 12 },
            { id: 302, name: '北京市', type: 'LOCATION', confidence: 0.95, document_count: 6 },
            { id: 303, name: '北京城', type: 'LOCATION', confidence: 0.87, document_count: 3 }
          ],
          similarity: 0.88,
          reason: '地理位置相同'
        }
      ];
      setSimilarGroups(mockGroups);
      setLoading(false);
    }, 1000);
  };

  // 选择实体组进行合并预览
  const handleSelectGroup = (group) => {
    setSelectedGroup(group);
    // 生成合并预览
    const preview = generateMergePreview(group);
    setMergePreview(preview);
  };

  // 生成合并预览
  const generateMergePreview = (group) => {
    // 选择置信度最高的实体作为主实体
    const mainEntity = group.entities.reduce((prev, current) =>
      prev.confidence > current.confidence ? prev : current
    );

    // 合并所有别名
    const allAliases = new Set();
    group.entities.forEach(entity => {
      allAliases.add(entity.name);
    });
    allAliases.delete(mainEntity.name);

    // 合并文档计数
    const totalDocuments = group.entities.reduce((sum, entity) =>
      sum + (entity.document_count || 1), 0
    );

    return {
      mainEntity,
      aliases: Array.from(allAliases),
      totalDocuments,
      entityCount: group.entities.length,
      mergedProperties: {
        '主名称': mainEntity.name,
        '实体类型': mainEntity.type,
        '置信度': `${(mainEntity.confidence * 100).toFixed(1)}%`,
        '别名数量': allAliases.size,
        '关联文档': totalDocuments
      }
    };
  };

  // 执行合并
  const handleMerge = async () => {
    if (!selectedGroup || !mergePreview) return;

    setMerging(true);
    // TODO: 调用API执行合并
    setTimeout(() => {
      setMergeResult({
        success: true,
        message: `成功合并 ${mergePreview.entityCount} 个实体`,
        mergedEntityId: mergePreview.mainEntity.id,
        timestamp: new Date().toISOString()
      });
      setMerging(false);

      // 从列表中移除已合并的组
      setSimilarGroups(prev => prev.filter(g => g.id !== selectedGroup.id));
      setSelectedGroup(null);
      setMergePreview(null);

      // 通知父组件
      if (onMergeComplete) {
        onMergeComplete(mergeResult);
      }
    }, 1500);
  };

  // 忽略当前组
  const handleIgnore = () => {
    if (!selectedGroup) return;
    setSimilarGroups(prev => prev.filter(g => g.id !== selectedGroup.id));
    setSelectedGroup(null);
    setMergePreview(null);
  };

  // 过滤后的组列表
  const filteredGroups = similarGroups.filter(group =>
    group.entities.some(entity =>
      entity.name.toLowerCase().includes(searchKeyword.toLowerCase())
    )
  );

  // 获取实体类型标签
  const getEntityTypeLabel = (type) => {
    const typeMap = {
      'PERSON': '人物',
      'ORG': '组织',
      'LOCATION': '地点',
      'TIME': '时间',
      'EVENT': '事件',
      'CONCEPT': '概念',
      'PRODUCT': '产品'
    };
    return typeMap[type] || type;
  };

  return (
    <div className="entity-merge-tool">
      {/* 头部 */}
      <div className="merge-tool-header">
        <h3>🔄 实体合并工具</h3>
        <p className="header-desc">发现并合并知识库中的相似实体</p>
      </div>

      {/* 筛选工具栏 */}
      <div className="merge-tool-toolbar">
        <div className="search-box">
          <input
            type="text"
            placeholder="搜索实体名称..."
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
          />
        </div>
        <div className="threshold-control">
          <label>相似度阈值: {(similarityThreshold * 100).toFixed(0)}%</label>
          <input
            type="range"
            min="0.5"
            max="0.95"
            step="0.05"
            value={similarityThreshold}
            onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
          />
        </div>
        <button className="refresh-btn" onClick={loadSimilarGroups} disabled={loading}>
          {loading ? '⟳' : '🔄'} 刷新
        </button>
      </div>

      {/* 主内容区域 */}
      <div className="merge-tool-content">
        {/* 左侧：相似实体组列表 */}
        <div className="groups-panel">
          <div className="panel-header">
            <h4>相似实体组 ({filteredGroups.length})</h4>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>正在分析相似实体...</p>
            </div>
          ) : filteredGroups.length > 0 ? (
            <div className="groups-list">
              {filteredGroups.map(group => (
                <div
                  key={group.id}
                  className={`group-item ${selectedGroup?.id === group.id ? 'selected' : ''}`}
                  onClick={() => handleSelectGroup(group)}
                >
                  <div className="group-header">
                    <span className="similarity-badge">
                      相似度: {(group.similarity * 100).toFixed(0)}%
                    </span>
                    <span className="entity-count">{group.entities.length} 个实体</span>
                  </div>
                  <div className="group-reason">{group.reason}</div>
                  <div className="group-entities">
                    {group.entities.map((entity, index) => (
                      <span key={entity.id} className="entity-tag">
                        {entity.name}
                        {index < group.entities.length - 1 && '、'}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">✅</span>
              <p>未发现相似实体</p>
              <p className="empty-desc">知识库中的实体数据质量良好</p>
            </div>
          )}
        </div>

        {/* 右侧：合并预览 */}
        <div className="preview-panel">
          {mergePreview ? (
            <>
              <div className="panel-header">
                <h4>合并预览</h4>
              </div>

              <div className="preview-content">
                {/* 主实体信息 */}
                <div className="preview-section">
                  <h5>主实体</h5>
                  <div className="main-entity-card">
                    <div className="entity-name">{mergePreview.mainEntity.name}</div>
                    <div className="entity-type">
                      {getEntityTypeLabel(mergePreview.mainEntity.type)}
                    </div>
                    <div className="entity-confidence">
                      置信度: {(mergePreview.mainEntity.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* 将被合并的实体 */}
                <div className="preview-section">
                  <h5>将被合并的实体 ({mergePreview.entityCount - 1})</h5>
                  <div className="merged-entities-list">
                    {selectedGroup.entities
                      .filter(e => e.id !== mergePreview.mainEntity.id)
                      .map(entity => (
                        <div key={entity.id} className="merged-entity-item">
                          <span className="entity-name-sm">{entity.name}</span>
                          <span className="entity-confidence-sm">
                            {(entity.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                  </div>
                </div>

                {/* 合并后的属性 */}
                <div className="preview-section">
                  <h5>合并后属性</h5>
                  <div className="merged-properties">
                    {Object.entries(mergePreview.mergedProperties).map(([key, value]) => (
                      <div key={key} className="property-row">
                        <span className="property-label">{key}</span>
                        <span className="property-value">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 别名 */}
                {mergePreview.aliases.length > 0 && (
                  <div className="preview-section">
                    <h5>合并后的别名</h5>
                    <div className="aliases-tags">
                      {mergePreview.aliases.map((alias, index) => (
                        <span key={index} className="alias-tag">{alias}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 警告提示 */}
                <div className="warning-box">
                  <span className="warning-icon">⚠️</span>
                  <p>合并操作不可撤销，被合并的实体将被删除，其关系和属性将合并到主实体中。</p>
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="preview-actions">
                <button
                  className="btn-merge"
                  onClick={handleMerge}
                  disabled={merging}
                >
                  {merging ? '合并中...' : '✓ 确认合并'}
                </button>
                <button
                  className="btn-ignore"
                  onClick={handleIgnore}
                  disabled={merging}
                >
                  忽略此组
                </button>
              </div>
            </>
          ) : (
            <div className="empty-preview">
              <span className="empty-icon">👈</span>
              <p>请从左侧选择一个相似实体组</p>
              <p className="empty-desc">查看合并预览并执行合并操作</p>
            </div>
          )}
        </div>
      </div>

      {/* 底部操作 */}
      <div className="merge-tool-footer">
        <button className="btn-cancel" onClick={onCancel}>
          关闭
        </button>
        {mergeResult && (
          <div className="merge-result-message success">
            ✓ {mergeResult.message}
          </div>
        )}
      </div>
    </div>
  );
};

export default EntityMergeTool;
