/**
 * 知识图谱页面
 *
 * 展示知识库的知识图谱可视化，支持实体识别和关系提取
 */

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { FiRefreshCw, FiZoomIn, FiZoomOut, FiMaximize, FiFilter, FiPlay, FiCpu, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { message } from '../../../components/UI/Message/Message';
import {
  getKnowledgeBaseGraphData,
  buildKnowledgeGraph,
  getDocumentProcessingProgress
} from '../../../utils/api/knowledgeApi';
import './styles.css';

/**
 * 知识图谱页面
 */
const KnowledgeGraph = () => {
  const canvasRef = useRef(null);
  const { currentKnowledgeBase } = useKnowledgeStore();
  
  // 本地状态
  const [loading, setLoading] = useState(false);
  const [scale, setScale] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  // 知识图谱构建状态
  const [buildingGraph, setBuildingGraph] = useState(false);
  const [buildProgress, setBuildProgress] = useState(0);
  const [buildStatus, setBuildStatus] = useState(''); // 'idle', 'extracting', 'building', 'completed', 'failed'
  const [buildError, setBuildError] = useState(null);
  const [lastBuildTime, setLastBuildTime] = useState(null);
  const progressIntervalRef = useRef(null);

  /**
   * 获取图谱数据
   */
  const fetchGraphData = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setLoading(true);
    try {
      // 调用真实 API 获取知识图谱数据
      const response = await getKnowledgeBaseGraphData(currentKnowledgeBase.id);

      // 转换后端数据为前端格式
      const nodes = (response.nodes || []).map((node, index) => ({
        id: node.id || `node-${index}`,
        label: node.name || node.label || `实体 ${index + 1}`,
        type: node.type || 'entity',
        x: Math.random() * 800,
        y: Math.random() * 600,
        size: 20 + (node.importance || 0.5) * 30,
      }));

      const edges = (response.edges || response.relationships || []).map((edge, index) => ({
        id: edge.id || `edge-${index}`,
        source: edge.source || edge.source_id,
        target: edge.target || edge.target_id,
        label: edge.label || edge.type || '关联',
      }));

      setGraphData({ nodes, edges });
    } catch (error) {
      message.error({ content: '获取知识图谱失败：' + error.message });
    } finally {
      setLoading(false);
    }
  }, [currentKnowledgeBase]);

  // 初始加载
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  // 清理进度轮询
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  /**
   * 构建知识图谱
   */
  const handleBuildKnowledgeGraph = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setBuildingGraph(true);
    setBuildStatus('extracting');
    setBuildProgress(0);
    setBuildError(null);

    try {
      // 启动知识图谱构建
      const response = await buildKnowledgeGraph(null, currentKnowledgeBase.id);

      if (response.task_id) {
        // 开始轮询进度
        startProgressPolling(response.task_id);
        message.success({ content: '知识图谱构建已启动' });
      } else {
        // 同步完成
        setBuildStatus('completed');
        setBuildProgress(100);
        setLastBuildTime(new Date());
        message.success({ content: '知识图谱构建完成' });
        fetchGraphData();
      }
    } catch (error) {
      setBuildStatus('failed');
      setBuildError(error.message);
      message.error({ content: '构建知识图谱失败：' + error.message });
    } finally {
      setBuildingGraph(false);
    }
  }, [currentKnowledgeBase, fetchGraphData]);

  /**
   * 开始进度轮询
   */
  const startProgressPolling = useCallback((taskId) => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    progressIntervalRef.current = setInterval(async () => {
      try {
        // 这里应该调用获取任务进度的 API
        // 暂时模拟进度增长
        setBuildProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressIntervalRef.current);
            setBuildStatus('completed');
            setLastBuildTime(new Date());
            fetchGraphData();
            return 100;
          }
          return prev + 5;
        });
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    }, 1000);
  }, [fetchGraphData]);

  /**
   * 绘制图谱
   */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || graphData.nodes.length === 0) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    // 设置画布尺寸
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    // 清空画布
    ctx.clearRect(0, 0, rect.width, rect.height);

    // 绘制边
    graphData.edges.forEach(edge => {
      const sourceNode = graphData.nodes.find(n => n.id === edge.source);
      const targetNode = graphData.nodes.find(n => n.id === edge.target);
      
      if (sourceNode && targetNode) {
        ctx.beginPath();
        ctx.moveTo(sourceNode.x * scale, sourceNode.y * scale);
        ctx.lineTo(targetNode.x * scale, targetNode.y * scale);
        ctx.strokeStyle = '#d9d9d9';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    });

    // 绘制节点
    graphData.nodes.forEach(node => {
      const x = node.x * scale;
      const y = node.y * scale;
      const radius = node.size * scale;

      // 节点圆形
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      
      // 根据类型设置颜色
      const colors = {
        concept: '#1890ff',
        entity: '#52c41a',
        relation: '#faad14',
      };
      ctx.fillStyle = colors[node.type] || '#8c8c8c';
      ctx.fill();

      // 选中状态
      if (selectedNode?.id === node.id) {
        ctx.beginPath();
        ctx.arc(x, y, radius + 4, 0, Math.PI * 2);
        ctx.strokeStyle = '#1890ff';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // 节点标签
      ctx.fillStyle = '#262626';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(node.label, x, y + radius + 16);
    });
  }, [graphData, scale, selectedNode]);

  /**
   * 处理画布点击
   */
  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;

    // 查找点击的节点
    const clickedNode = graphData.nodes.find(node => {
      const dx = x - node.x;
      const dy = y - node.y;
      return Math.sqrt(dx * dx + dy * dy) <= node.size;
    });

    setSelectedNode(clickedNode || null);
  };

  /**
   * 缩放操作
   */
  const handleZoomIn = () => setScale(prev => Math.min(prev * 1.2, 3));
  const handleZoomOut = () => setScale(prev => Math.max(prev / 1.2, 0.3));
  const handleReset = () => setScale(1);

  if (!currentKnowledgeBase) {
    return (
      <div className="knowledge-graph-empty">
        <div className="empty-icon">🕸️</div>
        <h3>请选择一个知识库</h3>
        <p>从左侧边栏选择一个知识库查看知识图谱</p>
      </div>
    );
  }

  return (
    <div className="knowledge-graph">
      {/* 工具栏 */}
      <div className="knowledge-graph-toolbar">
        <div className="toolbar-left">
          <h3>知识图谱</h3>
          <span className="graph-stats">
            {graphData.nodes.length} 个实体 · {graphData.edges.length} 个关系
          </span>
          {lastBuildTime && (
            <span className="last-build-time">
              上次构建: {lastBuildTime.toLocaleString('zh-CN')}
            </span>
          )}
        </div>

        <div className="toolbar-right">
          {/* 构建知识图谱按钮 */}
          <Button
            variant="primary"
            size="sm"
            icon={<FiCpu />}
            onClick={handleBuildKnowledgeGraph}
            loading={buildingGraph}
            disabled={buildingGraph}
          >
            {buildingGraph ? '构建中...' : '构建知识图谱'}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            icon={<FiFilter />}
            onClick={() => setShowFilters(!showFilters)}
          >
            筛选
          </Button>

          <div className="zoom-controls">
            <button onClick={handleZoomOut} title="缩小">
              <FiZoomOut size={16} />
            </button>
            <span className="zoom-level">{Math.round(scale * 100)}%</span>
            <button onClick={handleZoomIn} title="放大">
              <FiZoomIn size={16} />
            </button>
            <button onClick={handleReset} title="重置">
              <FiMaximize size={16} />
            </button>
          </div>

          <Button
            variant="secondary"
            size="sm"
            icon={<FiRefreshCw />}
            onClick={fetchGraphData}
            loading={loading}
          >
            刷新
          </Button>
        </div>
      </div>

      {/* 构建进度面板 */}
      {(buildingGraph || buildStatus === 'completed' || buildStatus === 'failed') && (
        <div className={`build-status-panel ${buildStatus}`}>
          <div className="build-status-header">
            {buildStatus === 'extracting' && <FiCpu className="status-icon" />}
            {buildStatus === 'building' && <FiPlay className="status-icon" />}
            {buildStatus === 'completed' && <FiCheckCircle className="status-icon" />}
            {buildStatus === 'failed' && <FiAlertCircle className="status-icon" />}
            <span className="status-text">
              {buildStatus === 'extracting' && '正在提取实体和关系...'}
              {buildStatus === 'building' && '正在构建知识图谱...'}
              {buildStatus === 'completed' && '知识图谱构建完成'}
              {buildStatus === 'failed' && '构建失败'}
            </span>
          </div>
          {buildingGraph && (
            <div className="build-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${buildProgress}%` }}
                />
              </div>
              <span className="progress-text">{buildProgress}%</span>
            </div>
          )}
          {buildError && (
            <div className="build-error">{buildError}</div>
          )}
        </div>
      )}

      {/* 主内容区 */}
      <div className="knowledge-graph-content">
        {/* 图谱画布 */}
        <div className="graph-canvas-wrapper">
          <canvas
            ref={canvasRef}
            className="graph-canvas"
            onClick={handleCanvasClick}
          />
          
          {loading && (
            <div className="graph-loading">
              <div className="loading-spinner" />
              <span>加载图谱中...</span>
            </div>
          )}
        </div>

        {/* 节点详情面板 */}
        {selectedNode && (
          <div className="node-detail-panel">
            <div className="node-detail-header">
              <h4>节点详情</h4>
              <button 
                className="close-detail"
                onClick={() => setSelectedNode(null)}
              >
                ×
              </button>
            </div>
            <div className="node-detail-content">
              <div className="detail-item">
                <label>ID</label>
                <span>{selectedNode.id}</span>
              </div>
              <div className="detail-item">
                <label>名称</label>
                <span>{selectedNode.label}</span>
              </div>
              <div className="detail-item">
                <label>类型</label>
                <span className={`type-badge ${selectedNode.type}`}>
                  {selectedNode.type === 'concept' && '概念'}
                  {selectedNode.type === 'entity' && '实体'}
                  {selectedNode.type === 'relation' && '关系'}
                </span>
              </div>
              <div className="detail-item">
                <label>关联数</label>
                <span>
                  {graphData.edges.filter(e => 
                    e.source === selectedNode.id || e.target === selectedNode.id
                  ).length}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraph;
