/**
 * 虚拟滚动列表组件
 *
 * 用于高效渲染大量数据的列表
 */

import React, { useRef, useState, useEffect, useMemo } from 'react';
import './VirtualList.css';

/**
 * 虚拟滚动列表组件
 *
 * @param {Object} props - 组件属性
 * @param {Array} props.items - 数据项数组
 * @param {Function} props.renderItem - 渲染单个项目的函数
 * @param {number} props.itemHeight - 每个项目的高度
 * @param {number} props.visibleCount - 可见项目数量
 * @param {string} props.emptyText - 空状态文本
 * @param {string} props.loadingText - 加载状态文本
 * @param {boolean} props.loading - 加载状态
 * @param {Function} props.onScroll - 滚动回调
 * @returns {JSX.Element} 虚拟滚动列表
 */
const VirtualList = ({ 
  items = [], 
  renderItem, 
  itemHeight = 50, 
  visibleCount = 20, 
  emptyText = '暂无数据', 
  loadingText = '加载中...',
  loading = false,
  onScroll
}) => {
  const containerRef = useRef(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(visibleCount * itemHeight);

  // 计算可见项目的范围
  const visibleRange = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + visibleCount + 2, // 额外渲染2个项目以避免空白
      items.length
    );
    return { start: startIndex, end: endIndex };
  }, [scrollTop, itemHeight, visibleCount, items.length]);

  // 计算偏移量
  const offsetY = useMemo(() => {
    return visibleRange.start * itemHeight;
  }, [visibleRange.start, itemHeight]);

  // 处理滚动事件
  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
    if (onScroll) {
      onScroll(e);
    }
  };

  // 调整容器高度
  useEffect(() => {
    setContainerHeight(visibleCount * itemHeight);
  }, [visibleCount, itemHeight]);

  // 处理窗口 resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setContainerHeight(containerRef.current.clientHeight);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 渲染加载状态
  if (loading) {
    return (
      <div className="virtual-list-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>{loadingText}</p>
        </div>
      </div>
    );
  }

  // 渲染空状态
  if (items.length === 0) {
    return (
      <div className="virtual-list-container">
        <div className="empty-state">
          <span className="empty-icon">📋</span>
          <p>{emptyText}</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="virtual-list-container"
      onScroll={handleScroll}
      style={{
        height: containerHeight,
        overflowY: 'auto'
      }}
    >
      {/* 占位元素，用于创建滚动空间 */}
      <div 
        className="virtual-list-placeholder"
        style={{ 
          height: items.length * itemHeight,
          position: 'relative'
        }}
      >
        {/* 实际渲染的项目 */}
        <div 
          className="virtual-list-content"
          style={{ 
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0
          }}
        >
          {items.slice(visibleRange.start, visibleRange.end).map((item, index) => {
            const actualIndex = visibleRange.start + index;
            return renderItem(item, actualIndex);
          })}
        </div>
      </div>
    </div>
  );
};

export default VirtualList;
