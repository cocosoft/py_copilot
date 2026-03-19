import React, { useEffect, useState } from 'react';
import DataVisualization from '../../../components/DataVisualization';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { getKnowledgeBases, getDocumentStats, getEntityStats } from '../../../utils/api/knowledgeApi';
import './styles.css';

/**
 * 数据可视化仪表盘页面
 * 展示知识库系统的各种统计数据和趋势
 */
const DataDashboard = () => {
  const { currentKnowledgeBase, setCurrentKnowledgeBase } = useKnowledgeStore();
  const [stats, setStats] = useState({
    documentStats: [],
    entityStats: [],
    trendData: [],
    entityTypeData: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, [currentKnowledgeBase]);

  /**
   * 获取仪表盘数据
   */
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 获取知识库列表
      const knowledgeBases = await getKnowledgeBases();
      if (knowledgeBases && knowledgeBases.length > 0 && !currentKnowledgeBase) {
        setCurrentKnowledgeBase(knowledgeBases[0]);
      }

      if (currentKnowledgeBase) {
        // 获取文档统计数据
        const documentStats = await getDocumentStats(currentKnowledgeBase.id);
        // 获取实体统计数据
        const entityStats = await getEntityStats(currentKnowledgeBase.id);

        // 模拟趋势数据
        const trendData = generateTrendData();
        // 模拟实体类型分布数据
        const entityTypeData = generateEntityTypeData(entityStats);

        setStats({
          documentStats,
          entityStats,
          trendData,
          entityTypeData
        });
      }
    } catch (err) {
      setError(`获取数据失败: ${err.message}`);
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 生成模拟趋势数据
   */
  const generateTrendData = () => {
    const today = new Date();
    const data = [];
    
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.floor(Math.random() * 50) + 10
      });
    }
    
    return data;
  };

  /**
   * 生成实体类型分布数据
   */
  const generateEntityTypeData = (entityStats) => {
    if (!entityStats || entityStats.length === 0) {
      return [
        { name: '人物', value: 30 },
        { name: '组织', value: 25 },
        { name: '地点', value: 20 },
        { name: '事件', value: 15 },
        { name: '其他', value: 10 }
      ];
    }
    
    return entityStats.map(stat => ({
      name: stat.type,
      value: stat.count
    }));
  };

  if (loading) {
    return (
      <div className="data-dashboard loading">
        <div className="loading-spinner">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="data-dashboard error">
        <div className="error-message">{error}</div>
        <button className="retry-button" onClick={fetchDashboardData}>
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="data-dashboard">
      <div className="dashboard-header">
        <h2>数据可视化仪表盘</h2>
        <p>知识库系统运行状态和统计数据</p>
      </div>

      <div className="dashboard-grid">
        {/* 文档数量趋势 */}
        <div className="dashboard-card">
          <h3>文档数量趋势</h3>
          <DataVisualization
            data={stats.trendData}
            chartType="line"
            title="每日文档处理量"
            height={300}
          />
        </div>

        {/* 实体类型分布 */}
        <div className="dashboard-card">
          <h3>实体类型分布</h3>
          <DataVisualization
            data={stats.entityTypeData}
            chartType="pie"
            title="实体类型占比"
            height={300}
          />
        </div>

        {/* 文档处理状态 */}
        <div className="dashboard-card">
          <h3>文档处理状态</h3>
          <DataVisualization
            data={[
              { name: '已处理', value: 120 },
              { name: '处理中', value: 30 },
              { name: '待处理', value: 15 },
              { name: '失败', value: 5 }
            ]}
            chartType="bar"
            title="文档状态分布"
            height={300}
          />
        </div>

        {/* 系统性能指标 */}
        <div className="dashboard-card">
          <h3>系统性能指标</h3>
          <DataVisualization
            data={[
              { name: '响应时间', 平均值: 120, 最大值: 300, 最小值: 50 },
              { name: '吞吐量', 平均值: 85, 最大值: 120, 最小值: 40 },
              { name: '准确率', 平均值: 92, 最大值: 98, 最小值: 85 },
              { name: '召回率', 平均值: 88, 最大值: 95, 最小值: 80 }
            ]}
            chartType="radar"
            title="系统性能雷达图"
            height={300}
          />
        </div>
      </div>

      <div className="dashboard-summary">
        <div className="summary-card">
          <div className="summary-value">{stats.documentStats.length || 0}</div>
          <div className="summary-label">总文档数</div>
        </div>
        <div className="summary-card">
          <div className="summary-value">{stats.entityStats.reduce((sum, stat) => sum + (stat.count || 0), 0)}</div>
          <div className="summary-label">总实体数</div>
        </div>
        <div className="summary-card">
          <div className="summary-value">{Math.floor(Math.random() * 1000) + 500}</div>
          <div className="summary-label">总关系数</div>
        </div>
        <div className="summary-card">
          <div className="summary-value">{Math.floor(Math.random() * 90) + 90}%</div>
          <div className="summary-label">处理成功率</div>
        </div>
      </div>
    </div>
  );
};

export default DataDashboard;