/**
 * 文本高亮组件
 *
 * 用于在片段级视图中高亮显示实体标注
 */

import React from 'react';
import './TextHighlighter.css';

const TextHighlighter = ({ text, entities, onEntityClick }) => {
  if (!text) return null;

  // 实体类型颜色映射
  const entityColors = {
    PERSON: '#FF6B6B',
    ORGANIZATION: '#4ECDC4',
    ORG: '#4ECDC4',
    LOCATION: '#45B7D1',
    LOC: '#45B7D1',
    DATE: '#96CEB4',
    MONEY: '#FECA57',
    TECH: '#A29BFE',
    PRODUCT: '#FD79A8',
    EVENT: '#FDCB6E',
    CONCEPT: '#6C5CE7',
    default: '#A29BFE'
  };

  // 实体类型标签映射
  const entityLabels = {
    PERSON: '人物',
    ORGANIZATION: '组织',
    ORG: '组织',
    LOCATION: '地点',
    LOC: '地点',
    DATE: '日期',
    MONEY: '金额',
    TECH: '技术',
    PRODUCT: '产品',
    EVENT: '事件',
    CONCEPT: '概念',
    default: '实体'
  };

  /**
   * 获取实体颜色
   * @param {string} type - 实体类型
   * @returns {string} 颜色值
   */
  const getEntityColor = (type) => {
    return entityColors[type] || entityColors.default;
  };

  /**
   * 获取实体标签
   * @param {string} type - 实体类型
   * @returns {string} 标签文本
   */
  const getEntityLabel = (type) => {
    return entityLabels[type] || entityLabels.default;
  };

  /**
   * 处理实体点击事件
   * @param {Object} entity - 实体数据
   */
  const handleEntityClick = (entity) => {
    if (onEntityClick) {
      onEntityClick(entity);
    }
  };

  // 构建高亮文本
  const buildHighlightedText = () => {
    if (!entities || entities.length === 0) {
      return <span>{text}</span>;
    }

    // 按实体在文本中的位置排序
    const sortedEntities = [...entities].sort((a, b) => {
      const startA = a.start || a.offset || 0;
      const startB = b.start || b.offset || 0;
      return startA - startB;
    });

    const parts = [];
    let lastIndex = 0;

    sortedEntities.forEach((entity, index) => {
      const start = entity.start || entity.offset || 0;
      const end = entity.end || (start + (entity.text || entity.name || '').length);
      const entityText = text.substring(start, end);
      const entityType = entity.type || 'default';

      // 添加实体前的文本
      if (start > lastIndex) {
        parts.push(
          <span key={`text-${index}`}>
            {text.substring(lastIndex, start)}
          </span>
        );
      }

      // 添加高亮的实体
      parts.push(
        <span
          key={`entity-${index}`}
          className="entity-highlight"
          style={{
            backgroundColor: getEntityColor(entityType) + '30', // 30% opacity
            borderBottom: `2px solid ${getEntityColor(entityType)}`,
            cursor: onEntityClick ? 'pointer' : 'default'
          }}
          onClick={() => handleEntityClick(entity)}
          title={`${getEntityLabel(entityType)}: ${entityText}`}
        >
          {entityText}
        </span>
      );

      lastIndex = end;
    });

    // 添加最后一个实体后的文本
    if (lastIndex < text.length) {
      parts.push(
        <span key="text-end">
          {text.substring(lastIndex)}
        </span>
      );
    }

    return parts;
  };

  return (
    <div className="text-highlighter">
      <div className="highlighted-text">
        {buildHighlightedText()}
      </div>
      
      {/* 实体类型图例 */}
      {entities && entities.length > 0 && (
        <div className="entity-legend">
          <h4>实体类型</h4>
          <div className="legend-items">
            {Array.from(new Set(entities.map(e => e.type || 'default'))).map((type, index) => (
              <div key={`th-legend-${type}-${index}`} className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: getEntityColor(type) }}
                ></span>
                <span className="legend-label">{getEntityLabel(type)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TextHighlighter;