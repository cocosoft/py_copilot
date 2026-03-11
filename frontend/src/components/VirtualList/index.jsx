/**
 * 增强版虚拟列表组件 - 向量化管理模块优化 FE-001
 * 
 * 特性：
 * - 支持大数据量流畅滚动
 * - 内存占用稳定
 * - 滚动性能优化
 * 
 * @task FE-001
 * @phase 前端界面优化
 */

import React, { 
  useRef, 
  useState, 
  useEffect, 
  useMemo, 
  useCallback,
  forwardRef
} from 'react';
import PropTypes from 'prop-types';
import './styles.css';

/**
 * 增强版虚拟列表组件
 */
const EnhancedVirtualList = forwardRef(({
  items = [],
  renderItem,
  keyExtractor,
  itemHeight = 80,
  overscan = 5,
  className = '',
  style = {},
  loading = false,
  emptyText = '暂无数据',
  loadingText = '加载中...',
  header,
  footer
}, ref) => {
  const containerRef = useRef(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);
  
  // 计算总高度
  const totalHeight = useMemo(() => {
    return items.length * itemHeight;
  }, [items.length, itemHeight]);
  
  // 计算可见范围
  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    return { start: startIndex, end: endIndex };
  }, [scrollTop, containerHeight, itemHeight, items.length, overscan]);
  
  // 可见项目
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end).map((item, index) => ({
      item,
      index: visibleRange.start + index,
      style: {
        position: 'absolute',
        top: (visibleRange.start + index) * itemHeight,
        left: 0,
        right: 0,
        height: itemHeight
      }
    }));
  }, [items, visibleRange, itemHeight]);
  
  // 处理滚动
  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);
  
  // 初始化容器高度
  useEffect(() => {
    if (containerRef.current) {
      setContainerHeight(containerRef.current.clientHeight);
    }
  }, []);
  
  // 渲染加载状态
  if (loading) {
    return (
      <div className="enhanced-virtual-list-container" style={style}>
        <div className="virtual-list-loading">
          <div className="virtual-list-spinner"></div>
          <p>{loadingText}</p>
        </div>
      </div>
    );
  }
  
  // 渲染空状态
  if (items.length === 0) {
    return (
      <div className="enhanced-virtual-list-container" style={style}>
        <div className="virtual-list-empty">
          <span className="virtual-list-empty-icon">📋</span>
          <p>{emptyText}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div
      ref={containerRef}
      className={`enhanced-virtual-list-container ${className}`}
      style={{
        ...style,
        overflow: 'auto',
        position: 'relative'
      }}
      onScroll={handleScroll}
    >
      {/* Header */}
      {header && (
        <div className="virtual-list-header">
          {header}
        </div>
      )}
      
      {/* 内容区域 */}
      <div
        className="virtual-list-content"
        style={{
          height: totalHeight,
          position: 'relative'
        }}
      >
        <div className="virtual-list-items">
          {visibleItems.map(({ item, index, style: itemStyle }) => (
            <div
              key={keyExtractor ? keyExtractor(item, index) : index}
              className="virtual-list-item"
              style={itemStyle}
            >
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
      
      {/* Footer */}
      {footer && (
        <div className="virtual-list-footer">
          {footer}
        </div>
      )}
    </div>
  );
});

EnhancedVirtualList.displayName = 'EnhancedVirtualList';

EnhancedVirtualList.propTypes = {
  items: PropTypes.array.isRequired,
  renderItem: PropTypes.func.isRequired,
  keyExtractor: PropTypes.func,
  itemHeight: PropTypes.number,
  overscan: PropTypes.number,
  className: PropTypes.string,
  style: PropTypes.object,
  loading: PropTypes.bool,
  emptyText: PropTypes.string,
  loadingText: PropTypes.string,
  header: PropTypes.node,
  footer: PropTypes.node
};

export default EnhancedVirtualList;
