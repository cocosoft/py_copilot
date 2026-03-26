import React, { useEffect, useState } from 'react';
import DataVisualization from '../../../components/DataVisualization';
import HierarchyNavigator from '../../../components/Hierarchy/HierarchyNavigator';
import HierarchyViewContainer from '../../../components/Hierarchy/HierarchyViewContainer';
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
      <div className="page-header">
        <h1>数据可视化仪表盘</h1>
        <p>知识库系统运行状态和统计数据</p>
      </div>
      
      <HierarchyNavigator />
      
      <div className="hierarchy-content">
        <HierarchyViewContainer knowledgeBaseId={currentKnowledgeBase?.id} />
      </div>
    </div>
  );
};

export default DataDashboard;