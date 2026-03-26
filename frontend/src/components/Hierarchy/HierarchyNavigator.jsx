import React from 'react';
import { FiLayers, FiFileText, FiDatabase, FiGlobe, FiArrowUp } from 'react-icons/fi';
import './HierarchyNavigator.css';

const HIERARCHY_LEVELS = [
  { 
    key: 'fragment', 
    label: '片段级', 
    icon: <FiFileText />, 
    description: '查看文本片段内的实体标注',
    color: '#1890ff'
  },
  { 
    key: 'document', 
    label: '文档级', 
    icon: <FiLayers />, 
    description: '查看文档内的实体关系',
    color: '#52c41a'
  },
  { 
    key: 'knowledge_base', 
    label: '知识库级', 
    icon: <FiDatabase />, 
    description: '查看跨文档的实体聚合',
    color: '#faad14'
  },
  { 
    key: 'global', 
    label: '全局级', 
    icon: <FiGlobe />, 
    description: '查看跨知识库的全局关系',
    color: '#722ed1'
  }
];

const HierarchyNavigator = ({ currentLevel, onLevelChange, levelStats }) => {
  // 实现返回上级功能
  const handleGoUp = () => {
    const currentIndex = HIERARCHY_LEVELS.findIndex(level => level.key === currentLevel);
    if (currentIndex > 0 && onLevelChange) {
      const previousLevel = HIERARCHY_LEVELS[currentIndex - 1];
      onLevelChange(previousLevel.key);
    }
  };

  return (
    <div className="hierarchy-navigator">
      <div className="hierarchy-title">
        <h3>数据层级</h3>
        <p className="hierarchy-subtitle">选择要查看的数据层级</p>
      </div>
      
      {/* 返回上级按钮 */}
      <div className="hierarchy-actions">
        <button 
          className="go-up-button"
          onClick={handleGoUp}
          disabled={HIERARCHY_LEVELS.findIndex(level => level.key === currentLevel) === 0}
          title="返回上级"
        >
          <FiArrowUp /> 返回上级
        </button>
      </div>
      
      <div className="hierarchy-levels">
        {HIERARCHY_LEVELS.map(level => (
          <div 
            key={level.key}
            className={`hierarchy-level ${currentLevel === level.key ? 'active' : ''}`}
            onClick={() => onLevelChange && onLevelChange(level.key)}
            style={{ '--level-color': level.color }}
          >
            <div className="level-icon">{level.icon}</div>
            <div className="level-info">
              <div className="level-label">{level.label}</div>
              <div className="level-description">{level.description}</div>
              {levelStats && levelStats[level.key] && (
                <div className="level-count">
                  {levelStats[level.key]} 个实体
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* 面包屑导航 */}
      <div className="hierarchy-breadcrumb">
        {HIERARCHY_LEVELS.map((level, index) => (
          <span key={level.key}>
            {index > 0 && <span className="breadcrumb-separator">/</span>}
            <span 
              className={`breadcrumb-item ${currentLevel === level.key ? 'active' : ''}`}
              onClick={() => onLevelChange && onLevelChange(level.key)}
            >
              {level.label}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
};

export default HierarchyNavigator;