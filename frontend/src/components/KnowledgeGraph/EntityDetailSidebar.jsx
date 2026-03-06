/**
 * 实体详情侧边栏组件
 *
 * 展示实体的详细信息，包括基本信息、属性、来源文档、关系图谱等
 */

import React, { useState, useEffect } from 'react';
import './EntityDetailSidebar.css';

/**
 * 实体详情侧边栏组件
 *
 * @param {Object} props - 组件属性
 * @param {Object} props.entity - 实体数据
 * @param {boolean} props.isOpen - 是否打开
 * @param {Function} props.onClose - 关闭回调
 * @param {Function} props.onEdit - 编辑回调
 * @param {Function} props.onDelete - 删除回调
 * @param {number} props.knowledgeBaseId - 知识库ID
 * @returns {JSX.Element} 实体详情侧边栏
 */
const EntityDetailSidebar = ({ entity, isOpen, onClose, onEdit, onDelete, knowledgeBaseId }) => {
  // 当前激活的标签页
  const [activeTab, setActiveTab] = useState('info');
  // 实体详情数据
  const [entityDetail, setEntityDetail] = useState(null);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 关系数据
  const [relations, setRelations] = useState([]);
  // 来源文档
  const [sourceDocuments, setSourceDocuments] = useState([]);

  // 加载实体详情
  useEffect(() => {
    if (!entity || !isOpen) return;

    setLoading(true);
    // TODO: 调用API获取实体详情
    // Mock数据
    setTimeout(() => {
      setEntityDetail({
        ...entity,
        description: `${entity.name}是一个重要的${entity.type === 'PERSON' ? '人物' : 
          entity.type === 'ORG' ? '组织' : 
          entity.type === 'LOCATION' ? '地点' : '概念'}，在知识库中具有较高的关联度。`,
        properties: {
          '创建时间': new Date(entity.created_at).toLocaleString('zh-CN'),
          '更新时间': new Date(entity.updated_at).toLocaleString('zh-CN'),
          '置信度': `${(entity.confidence * 100).toFixed(1)}%`,
          '出现次数': entity.occurrence_count || 1,
          '关联文档数': entity.document_count || 1
        },
        aliases: entity.aliases || []
      });

      // Mock关系数据
      setRelations([
        { target: 'ABC公司', type: '就职于', direction: 'outgoing' },
        { target: '张三', type: '同事', direction: 'outgoing' },
        { target: '北京', type: '位于', direction: 'incoming' },
        { target: 'XYZ项目', type: '负责', direction: 'outgoing' }
      ]);

      // Mock来源文档
      setSourceDocuments([
        { id: 1, title: '公司组织架构文档', snippet: `...${entity.name}担任重要职务...`, page: 5 },
        { id: 2, title: '项目报告2024', snippet: `...由${entity.name}负责的项目...`, page: 12 },
        { id: 3, title: '会议纪要', snippet: `...${entity.name}提出了重要建议...`, page: 3 }
      ]);

      setLoading(false);
    }, 500);
  }, [entity, isOpen]);

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

  // 获取置信度颜色
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return '#10b981';
    if (confidence >= 0.7) return '#f59e0b';
    return '#ef4444';
  };

  if (!isOpen || !entity) return null;

  return (
    <div className={`entity-detail-sidebar ${isOpen ? 'open' : ''}`}>
      {/* 头部 */}
      <div className="sidebar-header">
        <div className="header-title">
          <h3>实体详情</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        {entityDetail && (
          <div className="entity-header-info">
            <div className="entity-name">{entityDetail.name}</div>
            <div className="entity-meta">
              <span 
                className="entity-type-badge"
                style={{ backgroundColor: entityDetail.color || '#3b82f6' }}
              >
                {getEntityTypeLabel(entityDetail.type)}
              </span>
              <span 
                className="confidence-badge"
                style={{ color: getConfidenceColor(entityDetail.confidence) }}
              >
                置信度: {(entityDetail.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 标签页导航 */}
      <div className="sidebar-tabs">
        <button 
          className={`tab-btn ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          基本信息
        </button>
        <button 
          className={`tab-btn ${activeTab === 'relations' ? 'active' : ''}`}
          onClick={() => setActiveTab('relations')}
        >
          关系 ({relations.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
          onClick={() => setActiveTab('sources')}
        >
          来源 ({sourceDocuments.length})
        </button>
      </div>

      {/* 内容区域 */}
      <div className="sidebar-content">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>加载中...</p>
          </div>
        ) : (
          <>
            {/* 基本信息标签页 */}
            {activeTab === 'info' && entityDetail && (
              <div className="info-tab">
                {/* 描述 */}
                <div className="info-section">
                  <h4>描述</h4>
                  <p className="entity-description">{entityDetail.description}</p>
                </div>

                {/* 属性列表 */}
                <div className="info-section">
                  <h4>属性</h4>
                  <div className="properties-list">
                    {Object.entries(entityDetail.properties).map(([key, value]) => (
                      <div key={key} className="property-item">
                        <span className="property-key">{key}</span>
                        <span className="property-value">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 别名 */}
                {entityDetail.aliases && entityDetail.aliases.length > 0 && (
                  <div className="info-section">
                    <h4>别名</h4>
                    <div className="aliases-list">
                      {entityDetail.aliases.map((alias, index) => (
                        <span key={index} className="alias-tag">{alias}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 迷你关系图谱 */}
                <div className="info-section">
                  <h4>关系概览</h4>
                  <div className="mini-graph">
                    <div className="center-node">{entityDetail.name}</div>
                    <div className="relation-nodes">
                      {relations.slice(0, 5).map((rel, index) => (
                        <div key={index} className="relation-node">
                          <span className="relation-target">{rel.target}</span>
                          <span className="relation-type">{rel.type}</span>
                        </div>
                      ))}
                      {relations.length > 5 && (
                        <div className="more-relations">+{relations.length - 5} 更多</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 关系标签页 */}
            {activeTab === 'relations' && (
              <div className="relations-tab">
                {relations.length > 0 ? (
                  <div className="relations-list">
                    {relations.map((rel, index) => (
                      <div key={index} className="relation-item">
                        <div className="relation-direction">
                          {rel.direction === 'outgoing' ? '→' : '←'}
                        </div>
                        <div className="relation-info">
                          <div className="relation-target-name">{rel.target}</div>
                          <div className="relation-type-label">{rel.type}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <span className="empty-icon">🔗</span>
                    <p>暂无关系数据</p>
                  </div>
                )}
              </div>
            )}

            {/* 来源标签页 */}
            {activeTab === 'sources' && (
              <div className="sources-tab">
                {sourceDocuments.length > 0 ? (
                  <div className="sources-list">
                    {sourceDocuments.map((doc) => (
                      <div key={doc.id} className="source-item">
                        <div className="source-header">
                          <span className="source-title">{doc.title}</span>
                          <span className="source-page">第{doc.page}页</span>
                        </div>
                        <p className="source-snippet">{doc.snippet}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <span className="empty-icon">📄</span>
                    <p>暂无来源文档</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* 底部操作按钮 */}
      <div className="sidebar-footer">
        <button className="btn-edit" onClick={() => onEdit && onEdit(entity)}>
          ✏️ 编辑
        </button>
        <button className="btn-delete" onClick={() => onDelete && onDelete(entity)}>
          🗑️ 删除
        </button>
      </div>
    </div>
  );
};

export default EntityDetailSidebar;
