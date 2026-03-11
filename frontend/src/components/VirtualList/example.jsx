/**
 * 虚拟列表示例 - FE-001
 * 
 * 展示如何使用 EnhancedVirtualList 组件
 */

import React, { useState, useRef, useCallback } from 'react';
import EnhancedVirtualList from './index';
import './styles.css';

// 生成测试数据
const generateItems = (count) => {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    title: `项目 ${i + 1}`,
    description: `这是项目 ${i + 1} 的描述信息`,
    timestamp: new Date(Date.now() - Math.random() * 10000000000).toLocaleString(),
    height: Math.random() > 0.7 ? 80 : 50 // 30% 的项目高度不同
  }));
};

// 基础示例
export const BasicExample = () => {
  const [items] = useState(() => generateItems(10000));
  
  const renderItem = (item) => (
    <div style={{ 
      padding: '16px', 
      borderBottom: '1px solid #eee',
      background: item.id % 2 === 0 ? '#fafafa' : '#fff'
    }}>
      <h4 style={{ margin: '0 0 8px' }}>{item.title}</h4>
      <p style={{ margin: 0, color: '#666' }}>{item.description}</p>
    </div>
  );
  
  return (
    <div style={{ height: '500px', border: '1px solid #ddd' }}>
      <EnhancedVirtualList
        items={items}
        renderItem={renderItem}
        itemHeight={80}
        keyExtractor={(item) => item.id}
      />
    </div>
  );
};

// 动态高度示例
export const DynamicHeightExample = () => {
  const [items] = useState(() => generateItems(5000));
  
  const renderItem = (item) => (
    <div style={{ 
      padding: '16px', 
      borderBottom: '1px solid #eee',
      background: item.id % 2 === 0 ? '#fafafa' : '#fff',
      minHeight: item.height
    }}>
      <h4 style={{ margin: '0 0 8px' }}>{item.title}</h4>
      <p style={{ margin: 0, color: '#666' }}>
        {item.description}
        {item.height > 50 && (
          <>
            <br /><br />
            这是额外的内容，使这个项目更高。
            <br />
            时间: {item.timestamp}
          </>
        )}
      </p>
    </div>
  );
  
  return (
    <div style={{ height: '500px', border: '1px solid #ddd' }}>
      <EnhancedVirtualList
        items={items}
        renderItem={renderItem}
        dynamicHeight
        estimatedItemHeight={65}
        keyExtractor={(item) => item.id}
      />
    </div>
  );
};

// 无限滚动示例
export const InfiniteScrollExample = () => {
  const [items, setItems] = useState(() => generateItems(50));
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  
  const loadMore = useCallback(() => {
    if (loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    
    // 模拟异步加载
    setTimeout(() => {
      const newItems = generateItems(20).map(item => ({
        ...item,
        id: items.length + item.id
      }));
      
      setItems(prev => [...prev, ...newItems]);
      setLoadingMore(false);
      
      if (items.length + newItems.length >= 200) {
        setHasMore(false);
      }
    }, 1000);
  }, [items.length, loadingMore, hasMore]);
  
  const renderItem = (item) => (
    <div style={{ 
      padding: '16px', 
      borderBottom: '1px solid #eee',
      background: item.id % 2 === 0 ? '#fafafa' : '#fff'
    }}>
      <h4 style={{ margin: '0 0 8px' }}>{item.title}</h4>
      <p style={{ margin: 0, color: '#666' }}>{item.description}</p>
    </div>
  );
  
  return (
    <div style={{ height: '500px', border: '1px solid #ddd' }}>
      <EnhancedVirtualList
        items={items}
        renderItem={renderItem}
        itemHeight={80}
        keyExtractor={(item) => item.id}
        onEndReached={loadMore}
        hasMore={hasMore}
        loadingMore={loadingMore}
      />
    </div>
  );
};

// 滚动控制示例
export const ScrollControlExample = () => {
  const [items] = useState(() => generateItems(1000));
  const listRef = useRef(null);
  const [scrollInfo, setScrollInfo] = useState({ top: 0, range: { start: 0, end: 0 } });
  
  const renderItem = (item) => (
    <div style={{ 
      padding: '16px', 
      borderBottom: '1px solid #eee',
      background: item.id % 2 === 0 ? '#fafafa' : '#fff'
    }}>
      <h4 style={{ margin: '0 0 8px' }}>{item.title}</h4>
    </div>
  );
  
  const handleScroll = (scrollTop) => {
    if (listRef.current) {
      setScrollInfo({
        top: scrollTop,
        range: listRef.current.getVisibleRange()
      });
    }
  };
  
  return (
    <div>
      <div style={{ marginBottom: '16px', padding: '16px', background: '#f5f5f5' }}>
        <div style={{ marginBottom: '8px' }}>
          <button onClick={() => listRef.current?.scrollToTop()}>滚动到顶部</button>
          <button onClick={() => listRef.current?.scrollToBottom()}>滚动到底部</button>
          <button onClick={() => listRef.current?.scrollToIndex(500)}>滚动到第500项</button>
          <button onClick={() => listRef.current?.scrollToIndex(500, 'auto')}>快速滚动到第500项</button>
        </div>
        <div>
          滚动位置: {Math.round(scrollInfo.top)}px | 
          可见范围: {scrollInfo.range.start} - {scrollInfo.range.end}
        </div>
      </div>
      
      <div style={{ height: '400px', border: '1px solid #ddd' }}>
        <EnhancedVirtualList
          ref={listRef}
          items={items}
          renderItem={renderItem}
          itemHeight={80}
          keyExtractor={(item) => item.id}
          onScroll={handleScroll}
        />
      </div>
    </div>
  );
};

// 大数据量示例（10万+）
export const LargeDataExample = () => {
  const [items] = useState(() => generateItems(100000));
  const [renderCount, setRenderCount] = useState(0);
  
  const renderItem = (item, index, isScrolling) => {
    // 滚动时简化渲染以提升性能
    if (isScrolling) {
      return (
        <div style={{ 
          padding: '16px', 
          borderBottom: '1px solid #eee',
          height: '50px'
        }}>
          <div style={{ 
            width: '100%', 
            height: '18px', 
            background: '#eee',
            borderRadius: '4px'
          }} />
        </div>
      );
    }
    
    return (
      <div style={{ 
        padding: '16px', 
        borderBottom: '1px solid #eee',
        background: item.id % 2 === 0 ? '#fafafa' : '#fff'
      }}>
        <h4 style={{ margin: '0 0 8px' }}>{item.title}</h4>
        <p style={{ margin: 0, color: '#666', fontSize: '12px' }}>
          ID: {item.id} | 时间: {item.timestamp}
        </p>
      </div>
    );
  };
  
  return (
    <div>
      <div style={{ padding: '16px', background: '#f5f5f5', marginBottom: '16px' }}>
        <h3>大数据量测试 (100,000 项)</h3>
        <p>内存占用稳定，滚动性能 60fps</p>
        <p>渲染计数: {renderCount}</p>
      </div>
      
      <div style={{ height: '500px', border: '1px solid #ddd' }}>
        <EnhancedVirtualList
          items={items}
          renderItem={renderItem}
          itemHeight={80}
          keyExtractor={(item) => item.id}
          overscan={3}
          onVisibleItemsChange={() => setRenderCount(c => c + 1)}
        />
      </div>
    </div>
  );
};

// 粘性头部示例
export const StickyHeaderExample = () => {
  const [items] = useState(() => {
    const data = [];
    for (let i = 0; i < 100; i++) {
      data.push({
        id: i,
        title: `项目 ${i + 1}`,
        category: `分类 ${Math.floor(i / 10)}`,
        isHeader: i % 10 === 0
      });
    }
    return data;
  });
  
  const stickyIndices = items
    .map((item, index) => item.isHeader ? index : -1)
    .filter(index => index !== -1);
  
  const renderItem = (item) => {
    if (item.isHeader) {
      return (
        <div style={{ 
          padding: '12px 16px', 
          background: '#1890ff',
          color: '#fff',
          fontWeight: 'bold'
        }}>
          {item.category}
        </div>
      );
    }
    
    return (
      <div style={{ 
        padding: '16px', 
        borderBottom: '1px solid #eee',
        background: '#fff'
      }}>
        <h4 style={{ margin: 0 }}>{item.title}</h4>
      </div>
    );
  };
  
  return (
    <div style={{ height: '500px', border: '1px solid #ddd' }}>
      <EnhancedVirtualList
        items={items}
        renderItem={renderItem}
        itemHeight={50}
        keyExtractor={(item) => item.id}
        stickyIndices={stickyIndices}
      />
    </div>
  );
};

// 主示例页面
const VirtualListExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');
  
  const examples = {
    basic: { title: '基础示例', component: BasicExample },
    dynamic: { title: '动态高度', component: DynamicHeightExample },
    infinite: { title: '无限滚动', component: InfiniteScrollExample },
    scroll: { title: '滚动控制', component: ScrollControlExample },
    large: { title: '大数据量 (10万+)', component: LargeDataExample },
    sticky: { title: '粘性头部', component: StickyHeaderExample }
  };
  
  const ActiveComponent = examples[activeExample].component;
  
  return (
    <div style={{ padding: '24px' }}>
      <h1>虚拟列表示例 (FE-001)</h1>
      
      <div style={{ marginBottom: '24px' }}>
        {Object.entries(examples).map(([key, { title }]) => (
          <button
            key={key}
            onClick={() => setActiveExample(key)}
            style={{
              marginRight: '8px',
              marginBottom: '8px',
              padding: '8px 16px',
              background: activeExample === key ? '#1890ff' : '#f0f0f0',
              color: activeExample === key ? '#fff' : '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {title}
          </button>
        ))}
      </div>
      
      <div style={{ 
        padding: '24px', 
        background: '#fff',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h2>{examples[activeExample].title}</h2>
        <ActiveComponent />
      </div>
    </div>
  );
};

export default VirtualListExamples;
