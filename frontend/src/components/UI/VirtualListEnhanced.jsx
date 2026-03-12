/**
 * 增强版虚拟列表组件
 * 
 * 基于 @tanstack/react-virtual 实现，支持动态高度和无限滚动
 */

import React, { useRef, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import './VirtualList.css';

/**
 * 增强版虚拟列表组件
 * 
 * @param {Object} props - 组件属性
 * @param {Array} props.items - 数据项数组
 * @param {Function} props.renderItem - 渲染单个项目的函数 (item, index) => ReactNode
 * @param {number} props.estimateSize - 预估每项高度
 * @param {number} props.overscan - 预渲染数量
 * @param {Function} props.onEndReached - 滚动到底部回调
 * @param {number} props.endReachedThreshold - 触发加载更多的阈值
 * @param {string} props.className - 自定义类名
 * @param {boolean} props.loading - 加载状态
 * @param {boolean} props.hasMore - 是否还有更多数据
 * @param {string} props.emptyText - 空状态文本
 * @returns {JSX.Element} 虚拟列表
 */
const VirtualListEnhanced = ({
  items = [],
  renderItem,
  estimateSize = 100,
  overscan = 5,
  onEndReached,
  endReachedThreshold = 200,
  className = '',
  loading = false,
  hasMore = false,
  emptyText = '暂无数据',
}) => {
  const parentRef = useRef(null);
  const endReachedCalledRef = useRef(false);

  // 使用 tanstack virtual
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan,
    measureElement: (el) => el.getBoundingClientRect().height,
  });

  // 监听滚动，触发加载更多
  const handleScroll = useCallback(() => {
    if (!onEndReached || !parentRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = parentRef.current;
    const scrollBottom = scrollHeight - scrollTop - clientHeight;

    if (scrollBottom < endReachedThreshold && !endReachedCalledRef.current && hasMore && !loading) {
      endReachedCalledRef.current = true;
      onEndReached();
    } else if (scrollBottom >= endReachedThreshold) {
      endReachedCalledRef.current = false;
    }
  }, [onEndReached, endReachedThreshold, hasMore, loading]);

  const virtualItems = virtualizer.getVirtualItems();

  // 渲染空状态
  if (items.length === 0 && !loading) {
    return (
      <div className={`virtual-list-container ${className}`}>
        <div className="virtual-list-empty">
          <span className="virtual-list-empty-icon">📋</span>
          <div className="virtual-list-empty-content">{emptyText}</div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      className={`virtual-list-container ${className}`}
      onScroll={handleScroll}
      style={{
        height: '100%',
        overflow: 'auto',
      }}
    >
      <div
        className="virtual-list-content"
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualItem) => (
          <div
            key={virtualItem.key}
            ref={virtualizer.measureElement}
            data-index={virtualItem.index}
            className="virtual-list-item"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem(items[virtualItem.index], virtualItem.index)}
          </div>
        ))}
      </div>

      {/* 加载更多指示器 */}
      {loading && (
        <div className="virtual-list-loading">
          <div className="virtual-list-spinner"></div>
          <span>加载中...</span>
        </div>
      )}

      {/* 没有更多数据 */}
      {!hasMore && items.length > 0 && !loading && (
        <div className="virtual-list-no-more">
          <span>没有更多数据了</span>
        </div>
      )}
    </div>
  );
};

export default VirtualListEnhanced;
