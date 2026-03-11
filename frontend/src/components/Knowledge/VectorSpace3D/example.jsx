/**
 * 向量空间3D可视化使用示例 - FE-006
 *
 * 展示如何使用3D向量空间可视化组件
 *
 * @task FE-006
 * @phase 前端功能拓展
 */

import React, { useState, useCallback, useMemo } from 'react';
import VectorSpace3D, { VectorSpace3DWithControls, generateMockData, CLUSTER_COLORS } from './index';
import { Box, Layers, Search, MousePointer, Info, Settings } from 'lucide-react';

// ==================== 示例 1: 基础用法 ====================

/**
 * 基础3D可视化示例
 */
export const BasicExample = () => {
  const [selectedPoint, setSelectedPoint] = useState(null);

  const handlePointClick = useCallback((point) => {
    console.log('点击了点:', point);
    setSelectedPoint(point);
  }, []);

  const handlePointHover = useCallback((point) => {
    // 可以在这里更新外部状态
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>向量空间3D可视化 - 基础示例</h2>

      <VectorSpace3D
        width={800}
        height={600}
        onPointClick={handlePointClick}
        onPointHover={handlePointHover}
      />

      {selectedPoint && (
        <div
          style={{
            marginTop: '24px',
            padding: '16px',
            background: '#f6ffed',
            borderRadius: '8px',
            border: '1px solid #b7eb8f',
          }}
        >
          <h4>选中的点</h4>
          <p>ID: {selectedPoint.id}</p>
          <p>标签: {selectedPoint.label}</p>
          <p>聚类: {selectedPoint.cluster}</p>
          <p>
            坐标: ({selectedPoint.x.toFixed(2)}, {selectedPoint.y.toFixed(2)},{' '}
            {selectedPoint.z.toFixed(2)})
          </p>
        </div>
      )}
    </div>
  );
};

// ==================== 示例 2: 带控制面板 ====================

/**
 * 带控制面板的3D可视化示例
 */
export const WithControlsExample = () => {
  const [selectedPoint, setSelectedPoint] = useState(null);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>向量空间3D可视化 - 带控制面板</h2>

      <VectorSpace3DWithControls
        width={800}
        height={600}
        onPointClick={setSelectedPoint}
      />

      {selectedPoint && (
        <div style={{ marginTop: '24px', padding: '16px', background: '#f5f5f5', borderRadius: '8px' }}>
          <h4>选中的点详情</h4>
          <pre style={{ fontSize: '12px', overflow: 'auto' }}>
            {JSON.stringify(selectedPoint, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

// ==================== 示例 3: 自定义数据 ====================

/**
 * 使用自定义数据的示例
 */
export const CustomDataExample = () => {
  // 生成自定义数据（更多聚类、更多点）
  const customData = useMemo(() => {
    return generateMockData(1000, 6);
  }, []);

  const [highlightedPoints, setHighlightedPoints] = useState([]);

  // 随机高亮一些点
  const randomHighlight = () => {
    const randomIds = customData
      .slice(0, 50)
      .map((p) => p.id);
    setHighlightedPoints(randomIds);
  };

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>向量空间3D可视化 - 自定义数据</h2>

      <div style={{ marginBottom: '16px', display: 'flex', gap: '12px' }}>
        <button
          onClick={randomHighlight}
          style={{
            padding: '10px 20px',
            background: '#1890ff',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          随机高亮50个点
        </button>
        <button
          onClick={() => setHighlightedPoints([])}
          style={{
            padding: '10px 20px',
            background: '#f0f0f0',
            color: '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          清除高亮
        </button>
      </div>

      <VectorSpace3D
        data={customData}
        width={800}
        height={600}
        highlightedPoints={highlightedPoints}
      />

      <p style={{ marginTop: '16px', color: '#666' }}>
        数据点: {customData.length} | 聚类数: {new Set(customData.map((p) => p.cluster)).size}
      </p>
    </div>
  );
};

// ==================== 示例 4: 搜索高亮 ====================

/**
 * 搜索高亮示例
 */
export const SearchHighlightExample = () => {
  const data = useMemo(() => generateMockData(300, 3), []);
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>向量空间3D可视化 - 搜索高亮</h2>

      <div style={{ marginBottom: '16px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            background: '#fff',
            border: '1px solid #d9d9d9',
            borderRadius: '8px',
            maxWidth: '400px',
          }}
        >
          <Search size={20} color="#8c8c8c" />
          <input
            type="text"
            placeholder="输入向量标签搜索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              fontSize: '14px',
            }}
          />
        </div>
      </div>

      <VectorSpace3D
        data={data}
        width={800}
        height={600}
        searchQuery={searchQuery}
      />

      <p style={{ marginTop: '16px', color: '#666' }}>
        搜索 &quot;{searchQuery}&quot; 高亮匹配的向量
      </p>
    </div>
  );
};

// ==================== 示例 5: 多视图对比 ====================

/**
 * 多视图对比示例
 */
export const MultiViewExample = () => {
  const data1 = useMemo(() => generateMockData(200, 3), []);
  const data2 = useMemo(() => generateMockData(200, 4), []);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>向量空间3D可视化 - 多视图对比</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div>
          <h4 style={{ marginBottom: '12px' }}>数据集 A (3个聚类)</h4>
          <VectorSpace3D data={data1} width={400} height={350} />
        </div>
        <div>
          <h4 style={{ marginBottom: '12px' }}>数据集 B (4个聚类)</h4>
          <VectorSpace3D data={data2} width={400} height={350} />
        </div>
      </div>
    </div>
  );
};

// ==================== 示例 6: 聚类分析 ====================

/**
 * 聚类分析示例
 */
export const ClusterAnalysisExample = () => {
  const data = useMemo(() => generateMockData(500, 5), []);

  // 计算每个聚类的统计信息
  const clusterStats = useMemo(() => {
    const stats = {};
    data.forEach((point) => {
      if (!stats[point.cluster]) {
        stats[point.cluster] = {
          count: 0,
          color: point.color,
          points: [],
        };
      }
      stats[point.cluster].count++;
      stats[point.cluster].points.push(point);
    });
    return stats;
  }, [data]);

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginBottom: '24px' }}>向量空间3D可视化 - 聚类分析</h2>

      <div style={{ display: 'flex', gap: '24px' }}>
        <VectorSpace3D data={data} width={600} height={500} />

        <div style={{ width: '300px' }}>
          <h4 style={{ marginBottom: '16px' }}>聚类统计</h4>
          {Object.entries(clusterStats).map(([clusterId, stat]) => (
            <div
              key={clusterId}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px',
                marginBottom: '8px',
                background: '#f5f5f5',
                borderRadius: '8px',
              }}
            >
              <span
                style={{
                  width: '16px',
                  height: '16px',
                  background: stat.color,
                  borderRadius: '50%',
                }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500 }}>聚类 {clusterId}</div>
                <div style={{ fontSize: '13px', color: '#666' }}>{stat.count} 个点</div>
              </div>
              <div style={{ fontSize: '18px', fontWeight: 600 }}>
                {((stat.count / data.length) * 100).toFixed(1)}%
              </div>
            </div>
          ))}

          <div
            style={{
              marginTop: '24px',
              padding: '16px',
              background: '#e6f7ff',
              borderRadius: '8px',
              border: '1px solid #91d5ff',
            }}
          >
            <h5 style={{ margin: '0 0 8px 0' }}>分析说明</h5>
            <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
              每个聚类代表一组语义相似的向量。通过3D可视化可以直观地观察聚类的分布和边界。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== 主示例页面 ====================

const VectorSpace3DExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');

  const examples = {
    basic: { title: '基础用法', component: BasicExample, icon: Box },
    controls: { title: '控制面板', component: WithControlsExample, icon: Settings },
    custom: { title: '自定义数据', component: CustomDataExample, icon: Layers },
    search: { title: '搜索高亮', component: SearchHighlightExample, icon: Search },
    multi: { title: '多视图对比', component: MultiViewExample, icon: MousePointer },
    cluster: { title: '聚类分析', component: ClusterAnalysisExample, icon: Info },
  };

  const ActiveComponent = examples[activeExample].component;

  return (
    <div>
      <div
        style={{
          padding: '16px 24px',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <h1 style={{ margin: '0 0 16px 0' }}>向量空间3D可视化示例 (FE-006)</h1>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {Object.entries(examples).map(([key, { title, icon: Icon }]) => (
            <button
              key={key}
              onClick={() => setActiveExample(key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: activeExample === key ? '#1890ff' : '#f0f0f0',
                color: activeExample === key ? '#fff' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <Icon size={16} />
              {title}
            </button>
          ))}
        </div>
      </div>

      <ActiveComponent />
    </div>
  );
};

export default VectorSpace3DExamples;
