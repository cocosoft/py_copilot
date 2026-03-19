/**
 * 增强版知识图谱页面
 * 
 * 基于用户体验分析结果，重构知识图谱可视化交互
 * 解决核心功能不突出、交互反馈延迟、视觉复杂度高等问题
 */

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { 
  FiRefreshCw, FiZoomIn, FiZoomOut, FiMaximize, FiFilter, 
  FiPlay, FiCpu, FiCheckCircle, FiAlertCircle, FiHelpCircle,
  FiSettings, FiDownload, FiUpload, FiSearch, FiX, FiPlus,
  FiMinus, FiEye, FiEyeOff, FiLayers, FiTarget, FiBarChart2
} from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { 
  Button, 
  Modal, 
  Loading, 
  ErrorBoundary,
  designTokens 
} from '../../../components/UnifiedComponentLibrary';
import { message } from '../../../components/UI/Message/Message';
import {
  getKnowledgeBaseGraphData,
  buildKnowledgeGraph,
  getDocumentProcessingProgress
} from '../../../utils/api/knowledgeApi';
import './enhanced-styles.css';

/**
 * 增强版知识图谱页面
 */
const EnhancedKnowledgeGraph = () => {
  const canvasRef = useRef(null);
  const graphContainerRef = useRef(null);
  const { currentKnowledgeBase } = useKnowledgeStore();
  
  // 本地状态 - 优化后的状态管理
  const [loading, setLoading] = useState(false);
  const [scale, setScale] = useState(1);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  // 视图状态
  const [viewMode, setViewMode] = useState('graph'); // 'graph' | 'hierarchy' | 'force'
  const [showFilters, setShowFilters] = useState(false);
  const [showNodeDetails, setShowNodeDetails] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  
  // 知识图谱构建状态
  const [buildingGraph, setBuildingGraph] = useState(false);
  const [buildProgress, setBuildProgress] = useState(0);
  const [buildStatus, setBuildStatus] = useState('idle'); // 'idle', 'extracting', 'building', 'completed', 'failed'
  const [buildError, setBuildError] = useState(null);
  const [lastBuildTime, setLastBuildTime] = useState(null);
  
  // 筛选条件
  const [filters, setFilters] = useState({
    entityTypes: [],
    relationshipTypes: [],
    minConnections: 1,
    showIsolated: false,
  });

  // 图谱分析状态
  const [analysisResults, setAnalysisResults] = useState({
    communities: [],
    centralNodes: [],
    paths: [],
  });

  /**
   * 获取图谱数据
   */
  const fetchGraphData = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setLoading(true);
    try {
      // 调用真实 API 获取知识图谱数据
      const response = await getKnowledgeBaseGraphData(currentKnowledgeBase.id);
      setGraphData(response);
      
      // 自动进行图谱分析
      analyzeGraph(response);
      
      message.success({ content: '知识图谱数据加载成功' });
    } catch (error) {
      message.error({ content: `获取知识图谱数据失败: ${error.message}` });
    } finally {
      setLoading(false);
    }
  }, [currentKnowledgeBase]);

  /**
   * 构建知识图谱
   */
  const handleBuildGraph = useCallback(async () => {
    if (!currentKnowledgeBase) {
      message.warning({ content: '请先选择知识库' });
      return;
    }

    setBuildingGraph(true);
    setBuildStatus('extracting');
    setBuildProgress(0);
    setBuildError(null);

    try {
      // 开始构建图谱
      await buildKnowledgeGraph(currentKnowledgeBase.id);
      
      // 模拟构建进度
      const progressInterval = setInterval(async () => {
        try {
          const progress = await getDocumentProcessingProgress(currentKnowledgeBase.id);
          setBuildProgress(progress.percentage || 0);
          
          if (progress.percentage >= 100) {
            clearInterval(progressInterval);
            setBuildStatus('completed');
            setLastBuildTime(new Date());
            
            // 构建完成后自动刷新数据
            setTimeout(fetchGraphData, 1000);
            
            message.success({ content: '知识图谱构建完成' });
          }
        } catch (error) {
          clearInterval(progressInterval);
          setBuildStatus('failed');
          setBuildError(error.message);
          message.error({ content: `构建进度获取失败: ${error.message}` });
        }
      }, 1000);
      
    } catch (error) {
      setBuildingGraph(false);
      setBuildStatus('failed');
      setBuildError(error.message);
      message.error({ content: `知识图谱构建失败: ${error.message}` });
    }
  }, [currentKnowledgeBase, fetchGraphData]);

  /**
   * 图谱分析功能
   */
  const analyzeGraph = useCallback((graphData) => {
    if (!graphData.nodes.length) return;

    // 社区检测（简化版）
    const communities = detectCommunities(graphData);
    
    // 中心性分析
    const centralNodes = findCentralNodes(graphData);
    
    // 路径发现
    const paths = findImportantPaths(graphData);
    
    setAnalysisResults({
      communities,
      centralNodes,
      paths,
    });
  }, []);

  /**
   * 社区检测算法（简化实现）
   */
  const detectCommunities = (graphData) => {
    // 简化版社区检测
    const visited = new Set();
    const communities = [];
    
    graphData.nodes.forEach(node => {
      if (!visited.has(node.id)) {
        const community = [node];
        visited.add(node.id);
        
        // 广度优先搜索找连通分量
        const queue = [node.id];
        while (queue.length > 0) {
          const currentId = queue.shift();
          const connectedEdges = graphData.edges.filter(edge => 
            edge.source === currentId || edge.target === currentId
          );
          
          connectedEdges.forEach(edge => {
            const neighborId = edge.source === currentId ? edge.target : edge.source;
            if (!visited.has(neighborId)) {
              const neighbor = graphData.nodes.find(n => n.id === neighborId);
              if (neighbor) {
                community.push(neighbor);
                visited.add(neighborId);
                queue.push(neighborId);
              }
            }
          });
        }
        
        communities.push({
          id: `community-${communities.length}`,
          nodes: community,
          size: community.length,
          color: getCommunityColor(communities.length)
        });
      }
    });
    
    return communities;
  };

  /**
   * 中心性分析
   */
  const findCentralNodes = (graphData) => {
    // 简化版度中心性计算
    const degreeMap = new Map();
    
    graphData.nodes.forEach(node => {
      degreeMap.set(node.id, 0);
    });
    
    graphData.edges.forEach(edge => {
      degreeMap.set(edge.source, (degreeMap.get(edge.source) || 0) + 1);
      degreeMap.set(edge.target, (degreeMap.get(edge.target) || 0) + 1);
    });
    
    return Array.from(degreeMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([nodeId, degree]) => ({
        node: graphData.nodes.find(n => n.id === nodeId),
        degree,
        centrality: degree / (graphData.nodes.length - 1)
      }));
  };

  /**
   * 重要路径发现
   */
  const findImportantPaths = (graphData) => {
    // 简化版路径发现
    if (graphData.nodes.length < 2) return [];
    
    const paths = [];
    
    // 找几个重要的起始节点
    const importantNodes = graphData.nodes.slice(0, Math.min(3, graphData.nodes.length));
    
    importantNodes.forEach((startNode, index) => {
      const endNodes = graphData.nodes.slice(index + 1, index + 4);
      endNodes.forEach(endNode => {
        if (startNode.id !== endNode.id) {
          paths.push({
            id: `path-${startNode.id}-${endNode.id}`,
            start: startNode,
            end: endNode,
            length: 2, // 简化版
            nodes: [startNode, endNode]
          });
        }
      });
    });
    
    return paths;
  };

  /**
   * 获取社区颜色
   */
  const getCommunityColor = (index) => {
    const colors = [
      designTokens.colors.primary[500],
      designTokens.colors.success[500],
      designTokens.colors.warning[500],
      designTokens.colors.danger[500],
      designTokens.colors.info[500],
      designTokens.colors.purple[500],
      designTokens.colors.cyan[500],
    ];
    return colors[index % colors.length];
  };

  /**
   * 缩放操作
   */
  const handleZoom = useCallback((direction) => {
    const newScale = direction === 'in' ? scale * 1.2 : scale / 1.2;
    setScale(Math.max(0.1, Math.min(5, newScale)));
  }, [scale]);

  /**
   * 重置视图
   */
  const handleResetView = useCallback(() => {
    setScale(1);
    setSelectedNode(null);
    setShowNodeDetails(false);
  }, []);

  /**
   * 导出图谱数据
   */
  const handleExportData = useCallback(() => {
    const dataStr = JSON.stringify(graphData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `knowledge-graph-${currentKnowledgeBase?.id || 'unknown'}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    message.success({ content: '图谱数据导出成功' });
  }, [graphData, currentKnowledgeBase]);

  /**
   * 渲染图谱可视化区域
   */
  const renderGraphVisualization = () => (
    <div className="graph-visualization">
      <div className="graph-header">
        <div className="header-left">
          <h2>知识图谱可视化</h2>
          <span className="graph-info">
            {graphData.nodes.length} 个节点, {graphData.edges.length} 条关系
          </span>
        </div>
        
        <div className="header-right">
          <div className="view-controls">
            <Button 
              variant={viewMode === 'graph' ? 'primary' : 'outline'}
              size="small"
              icon={FiLayers}
              onClick={() => setViewMode('graph')}
            >
              图谱视图
            </Button>
            <Button 
              variant={viewMode === 'hierarchy' ? 'primary' : 'outline'}
              size="small"
              icon={FiTarget}
              onClick={() => setViewMode('hierarchy')}
            >
              层次视图
            </Button>
            <Button 
              variant={viewMode === 'force' ? 'primary' : 'outline'}
              size="small"
              icon={FiBarChart2}
              onClick={() => setViewMode('force')}
            >
              力导向图
            </Button>
          </div>
        </div>
      </div>

      <div className="graph-container" ref={graphContainerRef}>
        <canvas 
          ref={canvasRef}
          className="graph-canvas"
          style={{ transform: `scale(${scale})` }}
        />
        
        {graphData.nodes.length === 0 && (
          <div className="empty-state">
            <div className="empty-content">
              <FiLayers className="empty-icon" />
              <h3>暂无图谱数据</h3>
              <p>请先构建知识图谱或选择包含数据的知识库</p>
              <Button 
                variant="primary"
                icon={FiPlay}
                onClick={handleBuildGraph}
              >
                开始构建图谱
              </Button>
            </div>
          </div>
        )}
        
        {/* 缩放控制 */}
        <div className="zoom-controls">
          <Button 
            variant="outline"
            size="small"
            icon={FiPlus}
            onClick={() => handleZoom('in')}
          />
          <span className="scale-display">{Math.round(scale * 100)}%</span>
          <Button 
            variant="outline"
            size="small"
            icon={FiMinus}
            onClick={() => handleZoom('out')}
          />
          <Button 
            variant="outline"
            size="small"
            icon={FiMaximize}
            onClick={handleResetView}
          />
        </div>
      </div>
    </div>
  );

  /**
   * 渲染构建状态面板
   */
  const renderBuildPanel = () => (
    <div className="build-panel">
      <div className="panel-header">
        <FiCpu className="icon" />
        <span>知识图谱构建</span>
      </div>
      
      <div className="build-content">
        {buildingGraph ? (
          <div className="build-progress">
            <div className="progress-header">
              <span className="status">
                {buildStatus === 'extracting' && '实体提取中...'}
                {buildStatus === 'building' && '图谱构建中...'}
                {buildStatus === 'completed' && '构建完成'}
                {buildStatus === 'failed' && '构建失败'}
              </span>
              <span className="progress">{Math.round(buildProgress)}%</span>
            </div>
            
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${buildProgress}%` }}
              />
            </div>
            
            {buildError && (
              <div className="error-message">
                <FiAlertCircle />
                <span>{buildError}</span>
              </div>
            )}
          </div>
        ) : (
          <div className="build-actions">
            <Button 
              variant="primary"
              icon={FiPlay}
              onClick={handleBuildGraph}
              disabled={!currentKnowledgeBase}
            >
              构建知识图谱
            </Button>
            
            {lastBuildTime && (
              <div className="last-build">
                上次构建: {lastBuildTime.toLocaleString()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  /**
   * 渲染分析结果面板
   */
  const renderAnalysisPanel = () => (
    <div className="analysis-panel">
      <div className="panel-header">
        <FiBarChart2 className="icon" />
        <span>图谱分析</span>
      </div>
      
      <div className="analysis-content">
        <div className="analysis-section">
          <h4>社区检测</h4>
          <div className="communities">
            {analysisResults.communities.map(community => (
              <div key={community.id} className="community-item">
                <div 
                  className="color-indicator"
                  style={{ backgroundColor: community.color }}
                />
                <span className="community-name">社区 {community.id}</span>
                <span className="community-size">{community.size} 个节点</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="analysis-section">
          <h4>中心节点</h4>
          <div className="central-nodes">
            {analysisResults.centralNodes.map((nodeInfo, index) => (
              <div key={nodeInfo.node.id} className="central-node">
                <span className="rank">{index + 1}</span>
                <span className="node-name">{nodeInfo.node.name}</span>
                <span className="degree">{nodeInfo.degree} 度</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="analysis-section">
          <h4>重要路径</h4>
          <div className="important-paths">
            {analysisResults.paths.slice(0, 3).map(path => (
              <div key={path.id} className="path-item">
                <span className="path-name">{path.start.name} → {path.end.name}</span>
                <span className="path-length">{path.length} 跳</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  /**
   * 渲染节点详情面板
   */
  const renderNodeDetails = () => (
    <div className={`node-details-panel ${showNodeDetails && selectedNode ? 'visible' : ''}`}>
      {selectedNode && (
        <>
          <div className="panel-header">
            <span>节点详情</span>
            <Button 
              variant="ghost"
              size="small"
              icon={FiX}
              onClick={() => setShowNodeDetails(false)}
            />
          </div>
          
          <div className="node-content">
            <div className="node-header">
              <h3>{selectedNode.name}</h3>
              <span className="node-type">{selectedNode.type}</span>
            </div>
            
            <div className="node-properties">
              <div className="property">
                <label>置信度</label>
                <span>{selectedNode.confidence || 'N/A'}</span>
              </div>
              <div className="property">
                <label>出现次数</label>
                <span>{selectedNode.frequency || 'N/A'}</span>
              </div>
              <div className="property">
                <label>来源文档</label>
                <span>{selectedNode.source || 'N/A'}</span>
              </div>
            </div>
            
            <div className="node-relations">
              <h4>关联关系</h4>
              {graphData.edges
                .filter(edge => edge.source === selectedNode.id || edge.target === selectedNode.id)
                .map(edge => {
                  const otherNodeId = edge.source === selectedNode.id ? edge.target : edge.source;
                  const otherNode = graphData.nodes.find(n => n.id === otherNodeId);
                  return (
                    <div key={edge.id} className="relation-item">
                      <span className="relation-type">{edge.type}</span>
                      <span className="relation-target">{otherNode?.name}</span>
                    </div>
                  );
                })}
            </div>
          </div>
        </>
      )}
    </div>
  );

  // 初始化数据
  useEffect(() => {
    if (currentKnowledgeBase) {
      fetchGraphData();
    }
  }, [currentKnowledgeBase, fetchGraphData]);

  return (
    <ErrorBoundary>
      <div className="enhanced-knowledge-graph">
        {/* 页面头部 */}
        <div className="page-header">
          <div className="header-content">
            <h1>知识图谱管理</h1>
            <div className="header-actions">
              <Button 
                variant="outline"
                icon={FiHelpCircle}
                onClick={() => setShowHelpModal(true)}
              >
                使用帮助
              </Button>
              <Button 
                variant="outline"
                icon={FiDownload}
                onClick={handleExportData}
                disabled={graphData.nodes.length === 0}
              >
                导出数据
              </Button>
              <Button 
                variant="outline"
                icon={FiFilter}
                onClick={() => setShowFilters(!showFilters)}
              >
                {showFilters ? '隐藏筛选' : '显示筛选'}
              </Button>
            </div>
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="main-content">
          {/* 左侧面板 */}
          <div className="sidebar">
            {renderBuildPanel()}
            {renderAnalysisPanel()}
          </div>

          {/* 中间图谱区域 */}
          <div className="graph-area">
            {renderGraphVisualization()}
          </div>
        </div>

        {/* 节点详情面板 */}
        {renderNodeDetails()}

        {/* 帮助模态框 */}
        <Modal
          isOpen={showHelpModal}
          onClose={() => setShowHelpModal(false)}
          title="知识图谱使用帮助"
          size="large"
        >
          <div className="help-content">
            <h3>操作指南</h3>
            <p>1. 点击"构建知识图谱"按钮开始构建过程</p>
            <p>2. 使用不同的视图模式查看图谱结构</p>
            <p>3. 点击节点查看详细信息</p>
            <p>4. 使用缩放工具调整视图大小</p>
            <p>5. 查看分析面板了解图谱特征</p>
          </div>
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default EnhancedKnowledgeGraph;