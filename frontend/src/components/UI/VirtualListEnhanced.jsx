/**
 * 增强版虚拟列表组件
 * 
 * 基于 @tanstack/react-virtual 实现，支持动态高度和无限滚动
 */

import React, { useRef, useCallback, useEffect } from 'react';
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
  const measureElementsRef = useRef(new Map());

  // 使用 tanstack virtual
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan,
  });

  /**
   * 创建安全的测量 ref 回调
   * 使用 requestAnimationFrame 延迟测量，避免在渲染过程中调用 flushSync
   *
   * @param {number} index - 元素索引
   * @returns {Function} ref 回调函数
   */
  const createMeasureRef = useCallback((index) => {
    return (element) => {
      if (!element) {
        // 元素卸载时清理
        const prevElement = measureElementsRef.current.get(index);
        if (prevElement) {
          measureElementsRef.current.delete(index);
        }
        return;
      }

      // 存储元素引用
      measureElementsRef.current.set(index, element);

      // 使用 requestAnimationFrame 延迟测量，避免 flushSync 警告
      requestAnimationFrame(() => {
        if (element && virtualizer.measureElement) {
          virtualizer.measureElement(element);
        }
      });
    };
  }, [virtualizer]);

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

  /**
   * 当数据变化时，清理不再需要的元素引用
   */
  useEffect(() => {
    // 清理不在当前虚拟列表中的元素引用
    const currentIndices = new Set(virtualItems.map(item => item.index));
    for (const index of measureElementsRef.current.keys()) {
      if (!currentIndices.has(index)) {
        measureElementsRef.current.delete(index);
      }
    }
  }, [virtualItems]);

  /**
   * 当 items 完全替换时（如切换知识库），重置滚动位置到顶部
   * 解决切换知识库时文档列表不显示的问题
   */
  useEffect(() => {
    // 使用 requestAnimationFrame 延迟滚动操作，避免在 React 渲染过程中执行
    if (parentRef.current) {
      requestAnimationFrame(() => {
        if (parentRef.current) {
          parentRef.current.scrollTop = 0;
        }
      });
    }
    // 重置加载更多标记
    endReachedCalledRef.current = false;
    // 清理测量缓存
    measureElementsRef.current.clear();
  }, [items.length === 0 ? 'empty' : items[0]?.id]);

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
        {virtualItems.map((virtualItem) => {
          const item = items[virtualItem.index];
          // 使用 item.id 作为 key，确保列表项正确更新
          const itemKey = item?.id !== undefined ? `item-${item.id}` : virtualItem.key;
          
          return (
            <div
              key={itemKey}
              ref={createMeasureRef(virtualItem.index)}
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
              {renderItem(item, virtualItem.index)}
            </div>
          );
        })}
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
