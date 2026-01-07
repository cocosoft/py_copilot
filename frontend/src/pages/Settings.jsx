import React, { useState, useEffect, useRef } from 'react';
import { request } from '../utils/apiUtils';
import * as d3 from 'd3';
import './settings.css';
import IntegratedModelManagement from '../components/ModelManagement/IntegratedModelManagement';
import Agent from './Agent';
import Knowledge from './Knowledge';
import Workflow from './Workflow';
import Tool from './Tool';
import ModelSelectDropdown from '../components/ModelManagement/ModelSelectDropdown';


const Settings = () => {
  // 状态管理当前选中的二级菜单
  const [activeSection, setActiveSection] = useState('model');
  
  // 新增：控制侧边栏是否展开的状态
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  
  // 监听URL的hash变化，当hash为"#personal"或"#help"时，自动设置对应的activeSection
  useEffect(() => {
    const hash = window.location.hash;
    if (hash === '#personal') {
      setActiveSection('personal');
    } else if (hash === '#help') {
      setActiveSection('help');
    }
    
    // 监听hash变化事件
    const handleHashChange = () => {
      const newHash = window.location.hash;
      if (newHash === '#personal') {
        setActiveSection('personal');
      } else if (newHash === '#help') {
        setActiveSection('help');
      }
    };
    
    window.addEventListener('hashchange', handleHashChange);
    
    // 清理事件监听器
    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);
  
  // 搜索设置的状态（仅保留基础配置）
  const [defaultSearchEngine, setDefaultSearchEngine] = useState('google');
  const [safeSearch, setSafeSearch] = useState(true);
  const [isLoadingSearch, setIsLoadingSearch] = useState(false);
  const [isSavingSearch, setIsSavingSearch] = useState(false);

  // 默认模型管理的状态 - 移到组件顶层
  const [globalDefaultModel, setGlobalDefaultModel] = useState('');
  const [sceneDefaultModels, setSceneDefaultModels] = useState({
    chat: '',
    image: '',
    video: '',
    voice: '',
    translate: '',
    knowledge: '',
    workflow: '',
    tool: '',
    search: '',
    mcp: ''
  });
  const [isSavingDefaultModel, setIsSavingDefaultModel] = useState(false);
  const [models, setModels] = useState([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // 模拟模型数据 - 移到组件顶层
  useEffect(() => {
    setIsLoadingModels(true);
    // 模拟从API获取模型列表
    setTimeout(() => {
      const mockModels = [
        { id: 'model-123', name: '通用聊天模型', supplier: 'openai', type: 'chat' },
        { id: 'model-456', name: '高级推理模型', supplier: 'anthropic', type: 'chat' },
        { id: 'model-789', name: '图像生成模型', supplier: 'openai', type: 'image' },
        { id: 'model-101', name: '视频分析模型', supplier: 'google', type: 'video' },
        { id: 'model-102', name: '语音识别模型', supplier: 'baidu', type: 'voice' },
        { id: 'model-103', name: '多语言翻译模型', supplier: 'microsoft', type: 'translate' },
        { id: 'model-104', name: '知识库模型', supplier: 'openai', type: 'knowledge' },
        { id: 'model-105', name: '工作流模型', supplier: 'anthropic', type: 'workflow' },
        { id: 'model-106', name: '工具调用模型', supplier: 'openai', type: 'tool' },
        { id: 'model-107', name: '搜索增强模型', supplier: 'google', type: 'search' },
        { id: 'model-108', name: 'MCP上下文模型', supplier: 'openai', type: 'mcp' }
      ];
      setModels(mockModels);
      setIsLoadingModels(false);
    }, 500);
  }, []);

  // 全局记忆配置相关状态
  const [memoryConfig, setMemoryConfig] = useState({
    short_term_retention_days: 7,
    privacy_level: 'MEDIUM',
    auto_purge: true,
    retrieval_threshold: 0.7,
    max_retrieval_results: 20
  });
  const [isLoadingMemoryConfig, setIsLoadingMemoryConfig] = useState(false);
  const [isSavingMemoryConfig, setIsSavingMemoryConfig] = useState(false);

  // 加载记忆配置
  const loadMemoryConfig = async () => {
    setIsLoadingMemoryConfig(true);
    try {
      const data = await request('/v1/memory/memory-config', { method: 'GET' });
      setMemoryConfig(data);
    } catch (error) {
      console.error('加载记忆配置失败:', error);
      // 加载失败时使用默认值
      setMemoryConfig({
        short_term_retention_days: 7,
        privacy_level: 'MEDIUM',
        auto_purge: true,
        retrieval_threshold: 0.7,
        max_retrieval_results: 20
      });
    } finally {
      setIsLoadingMemoryConfig(false);
    }
  };

  // 保存记忆配置
  const saveMemoryConfig = async () => {
    setIsSavingMemoryConfig(true);
    try {
      await request('/v1/memory/memory-config', {
        method: 'PUT',
        data: memoryConfig
      });
      alert('记忆配置已保存');
    } catch (error) {
      console.error('保存记忆配置失败:', error);
      alert('保存失败，请重试');
    } finally {
      setIsSavingMemoryConfig(false);
    }
  };

  // 页面加载时获取记忆配置
  useEffect(() => {
    if (activeSection === 'globalMemory') {
      loadMemoryConfig();
      loadMemories();
      loadMemoryStats();
      loadMemoryPatterns();
      loadKnowledgeGraph();
    }
  }, [activeSection]);

  // 记忆列表相关状态
  const [memories, setMemories] = useState([]);
  const [isLoadingMemories, setIsLoadingMemories] = useState(false);
  const [memorySearchQuery, setMemorySearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [memoriesPerPage] = useState(10);
  const [totalMemories, setTotalMemories] = useState(0);
  const [isDeletingMemory, setIsDeletingMemory] = useState(false);
  
  // 记忆统计和分析相关状态
  const [memoryStats, setMemoryStats] = useState(null);
  const [memoryPatterns, setMemoryPatterns] = useState(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [isLoadingPatterns, setIsLoadingPatterns] = useState(false);
  const [isCleaningUpMemories, setIsCleaningUpMemories] = useState(false);
  const [isCompressingMemories, setIsCompressingMemories] = useState(false);
  
  // 知识图谱相关状态
  const [knowledgeGraph, setKnowledgeGraph] = useState(null);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [maxNodes, setMaxNodes] = useState(100);
  
  // 图表引用
  const memoryTypeChartRef = useRef(null);
  const importanceChartRef = useRef(null);
  const knowledgeGraphRef = useRef(null);
  
  // 渲染记忆类型分布饼图
  const renderMemoryTypeChart = () => {
    if (!memoryStats || !memoryTypeChartRef.current) return;
    
    const data = [
      { name: '短期记忆', value: memoryStats.by_type?.SHORT_TERM || 0 },
      { name: '长期记忆', value: memoryStats.by_type?.LONG_TERM || 0 }
    ];
    
    const width = memoryTypeChartRef.current.clientWidth;
    const height = 200;
    const radius = Math.min(width, height) / 2;
    
    // 清空图表
    d3.select(memoryTypeChartRef.current).selectAll('*').remove();
    
    const svg = d3.select(memoryTypeChartRef.current)
      .attr('width', width)
      .attr('height', height);
    
    const g = svg.append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2})`);
    
    const color = d3.scaleOrdinal()
      .domain(['短期记忆', '长期记忆'])
      .range(['#3498db', '#2ecc71']);
    
    const pie = d3.pie()
      .value(d => d.value)
      .sort(null);
    
    const arc = d3.arc()
      .innerRadius(0)
      .outerRadius(radius);
    
    const arcs = g.selectAll('.arc')
      .data(pie(data))
      .enter().append('g')
      .attr('class', 'arc');
    
    arcs.append('path')
      .attr('d', arc)
      .attr('fill', d => color(d.data.name))
      .style('stroke', '#fff')
      .style('stroke-width', '2px');
    
    // 添加标签
    arcs.append('text')
      .attr('transform', d => `translate(${arc.centroid(d)})`)
      .attr('dy', '.35em')
      .style('text-anchor', 'middle')
      .style('font-size', '14px')
      .text(d => `${d.data.name}: ${d.data.value}`);
  };
  
  // 渲染记忆重要性分布柱状图
  const renderImportanceChart = () => {
    if (!memoryStats || !importanceChartRef.current) return;
    
    // 模拟重要性分布数据（实际应该从memoryStats或memoryPatterns获取）
    const data = [
      { importance: '低', count: Math.floor((memoryStats.total_count || 0) * 0.3) },
      { importance: '中', count: Math.floor((memoryStats.total_count || 0) * 0.5) },
      { importance: '高', count: Math.floor((memoryStats.total_count || 0) * 0.2) }
    ];
    
    const width = importanceChartRef.current.clientWidth;
    const height = 200;
    const margin = { top: 20, right: 20, bottom: 30, left: 40 };
    
    // 清空图表
    d3.select(importanceChartRef.current).selectAll('*').remove();
    
    const svg = d3.select(importanceChartRef.current)
      .attr('width', width)
      .attr('height', height);
    
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const x = d3.scaleBand()
      .range([0, chartWidth])
      .padding(0.1)
      .domain(data.map(d => d.importance));
    
    const y = d3.scaleLinear()
      .range([chartHeight, 0])
      .domain([0, d3.max(data, d => d.count)]);
    
    // 添加x轴
    g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(x));
    
    // 添加y轴
    g.append('g')
      .call(d3.axisLeft(y));
    
    // 添加柱子
    g.selectAll('.bar')
      .data(data)
      .enter().append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.importance))
      .attr('width', x.bandwidth())
      .attr('y', d => y(d.count))
      .attr('height', d => chartHeight - y(d.count))
      .attr('fill', '#8e44ad');
    
    // 添加数值标签
    g.selectAll('.label')
      .data(data)
      .enter().append('text')
      .attr('class', 'label')
      .attr('x', d => x(d.importance) + x.bandwidth() / 2)
      .attr('y', d => y(d.count) - 5)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .text(d => d.count);
  };
  
  // 当记忆统计数据更新时渲染图表
  useEffect(() => {
    if (memoryStats) {
      renderMemoryTypeChart();
      renderImportanceChart();
    }
  }, [memoryStats]);
  
  // 渲染知识图谱
  const renderKnowledgeGraph = () => {
    if (!knowledgeGraph || !knowledgeGraphRef.current) return;
    
    const { nodes = [], edges = [] } = knowledgeGraph;
    
    const width = knowledgeGraphRef.current.clientWidth;
    const height = 500;
    
    // 清空图表
    d3.select(knowledgeGraphRef.current).selectAll('*').remove();
    
    const svg = d3.select(knowledgeGraphRef.current)
      .attr('width', width)
      .attr('height', height);
    
    // 创建力导向图布局
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => (d.centrality + 0.5) * 25));
    
    // 创建边
    const link = svg.append('g')
      .selectAll('line')
      .data(edges)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => d.strength * 2);
    
    // 创建节点
    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .enter().append('g');
    
    // 为节点添加圆形
    node.append('circle')
      .attr('r', d => (d.centrality + 0.5) * 25)
      .attr('fill', d => {
        // 根据记忆类型设置不同颜色
        const typeColors = {
          'SHORT_TERM': '#3498db',
          'LONG_TERM': '#2ecc71',
          'IMPORTANT': '#e74c3c'
        };
        return typeColors[d.type] || '#9b59b6';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));
    
    // 为节点添加文本标签
    node.append('text')
      .text(d => d.title || d.content_preview)
      .attr('x', 0)
      .attr('y', 0)
      .attr('dy', 5)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .attr('pointer-events', 'none');
    
    // 力导向图的事件处理函数
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    // 更新节点和边的位置
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  };
  
  // 窗口大小变化时重新渲染图表
  useEffect(() => {
    const handleResize = () => {
      renderMemoryTypeChart();
      renderImportanceChart();
      renderKnowledgeGraph();
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [memoryStats, knowledgeGraph]);
  
  // 知识图谱数据更新时重新渲染
  useEffect(() => {
    if (knowledgeGraph) {
      renderKnowledgeGraph();
    }
  }, [knowledgeGraph]);

  // 加载记忆列表
  const loadMemories = async () => {
    setIsLoadingMemories(true);
    try {
      const params = {
        page: currentPage,
        limit: memoriesPerPage
      };
      if (memorySearchQuery) {
        params.query = memorySearchQuery;
      }
      
      const data = await request('/v1/memory/memories', {
        method: 'GET',
        params: params
      });
      
      setMemories(data.memories || []);
      setTotalMemories(data.total || 0);
    } catch (error) {
      console.error('加载记忆列表失败:', error);
      alert('加载记忆列表失败，请重试');
    } finally {
      setIsLoadingMemories(false);
    }
  };

  // 删除单个记忆
  const deleteMemory = async (memoryId) => {
    if (!confirm('确定要删除这个记忆吗？')) {
      return;
    }
    
    setIsDeletingMemory(true);
    try {
      await request(`/v1/memory/memories/${memoryId}`, {
        method: 'DELETE'
      });
      // 重新加载记忆列表
      loadMemories();
      alert('记忆已删除');
    } catch (error) {
      console.error('删除记忆失败:', error);
      alert('删除记忆失败，请重试');
    } finally {
      setIsDeletingMemory(false);
    }
  };

  // 清空所有记忆
  const clearAllMemories = async () => {
    if (!confirm('确定要清空所有记忆吗？此操作不可恢复！')) {
      return;
    }
    
    setIsDeletingMemory(true);
    try {
      await request('/v1/memory/memories', {
        method: 'DELETE'
      });
      // 重新加载记忆列表
      loadMemories();
      alert('所有记忆已清空');
    } catch (error) {
      console.error('清空记忆失败:', error);
      alert('清空记忆失败，请重试');
    } finally {
      setIsDeletingMemory(false);
    }
  };

  // 加载记忆统计信息
  const loadMemoryStats = async () => {
    setIsLoadingStats(true);
    try {
      const data = await request('/v1/memory/memories/analytics/stats', { method: 'GET' });
      setMemoryStats(data);
    } catch (error) {
      console.error('加载记忆统计失败:', error);
      alert('加载记忆统计失败，请重试');
    } finally {
      setIsLoadingStats(false);
    }
  };

  // 加载记忆模式分析
  const loadMemoryPatterns = async () => {
    setIsLoadingPatterns(true);
    try {
      const data = await request('/v1/memory/memories/analytics/patterns', { method: 'GET' });
      setMemoryPatterns(data);
    } catch (error) {
      console.error('加载记忆模式分析失败:', error);
      // 设置默认值，避免渲染错误
      setMemoryPatterns({ top_topics: [], association_patterns: [] });
      alert('加载记忆模式分析失败，请重试');
    } finally {
      setIsLoadingPatterns(false);
    }
  };
  
  // 加载知识图谱
  const loadKnowledgeGraph = async () => {
    setIsLoadingGraph(true);
    try {
      const data = await request(`/v1/memory/memories/knowledge-graph?max_nodes=${maxNodes}`, { method: 'GET' });
      setKnowledgeGraph(data.graph_data);
    } catch (error) {
      console.error('加载知识图谱失败:', error);
      // 设置默认值，避免渲染错误
      setKnowledgeGraph({ nodes: [], edges: [] });
      alert('加载知识图谱失败，请重试');
    } finally {
      setIsLoadingGraph(false);
    }
  };

  // 清理过期记忆
  const cleanupExpiredMemories = async () => {
    if (!confirm('确定要清理过期的短期记忆吗？')) {
      return;
    }
    
    setIsCleaningUpMemories(true);
    try {
      const data = await request('/v1/memory/memories/cleanup', { method: 'POST' });
      alert(`成功清理${data.deleted_count}条过期记忆`);
      // 重新加载记忆列表和统计信息
      loadMemories();
      loadMemoryStats();
    } catch (error) {
      console.error('清理过期记忆失败:', error);
      alert('清理过期记忆失败，请重试');
    } finally {
      setIsCleaningUpMemories(false);
    }
  };

  // 压缩相似记忆
  const compressSimilarMemories = async () => {
    if (!confirm('确定要压缩相似的短期记忆为长期记忆吗？')) {
      return;
    }
    
    setIsCompressingMemories(true);
    try {
      const data = await request('/v1/memory/memories/compress', { method: 'POST' });
      const result = data.result;
      alert(`压缩完成：处理了${result.processed}条记忆，压缩了${result.compressed}条，创建了${result.created}条新的长期记忆`);
      // 重新加载记忆列表和统计信息
      loadMemories();
      loadMemoryStats();
    } catch (error) {
      console.error('压缩相似记忆失败:', error);
      alert('压缩相似记忆失败，请重试');
    } finally {
      setIsCompressingMemories(false);
    }
  };

  // 分页变化时重新加载数据
  useEffect(() => {
    if (activeSection === 'globalMemory') {
      loadMemories();
      loadMemoryStats();
      loadMemoryPatterns();
      loadKnowledgeGraph();
    }
  }, [currentPage, activeSection]);

  // 保存默认模型设置 - 移到组件顶层
  const handleSaveDefaultModel = () => {
    setIsSavingDefaultModel(true);
    // 模拟保存操作
    setTimeout(() => {
      alert('默认模型设置已保存');
      setIsSavingDefaultModel(false);
    }, 800);
  };

  // 根据场景类型过滤模型 - 移到组件顶层
  const getModelsByType = (type) => {
    return models.filter(model => model.type === type || model.type === 'chat');
  };

  // 切换侧边栏展开/收缩状态
  const toggleSidebar = () => {
    setSidebarExpanded(!sidebarExpanded);
  };

  // 加载搜索设置
  const loadSearchSettings = async () => {
    setIsLoadingSearch(true);
    try {
      // 这里只需要使用/v1/search/settings路径，因为request函数会自动添加API_BASE_URL（即/api）
      // 所以实际请求的URL是/api/v1/search/settings，与后端的路由匹配
      const data = await request('/v1/search/settings', { method: 'GET' });
      setDefaultSearchEngine(data.default_search_engine);
      setSafeSearch(data.safe_search);
    } catch (error) {
      console.error('加载搜索设置失败:', error);
      // 加载失败时使用默认值
      setDefaultSearchEngine('google');
      setSafeSearch(true);
    } finally {
      setIsLoadingSearch(false);
    }
  };

  // 保存搜索设置
  const saveSearchSettings = async () => {
    setIsSavingSearch(true);
    try {
      // 这里只需要使用/v1/search/settings路径，因为request函数会自动添加API_BASE_URL（即/api）
      // 所以实际请求的URL是/api/v1/search/settings，与后端的路由匹配
      await request('/v1/search/settings', {
        method: 'PUT',
        data: {
          default_search_engine: defaultSearchEngine,
          safe_search: safeSearch
        }
      });
      alert('搜索设置已保存');
    } catch (error) {
      console.error('保存搜索设置失败:', error);
      alert('保存失败，请重试');
    } finally {
      setIsSavingSearch(false);
    }
  };

  // 页面加载时获取搜索设置
  useEffect(() => {
    if (activeSection === 'search') {
      loadSearchSettings();
    }
  }, [activeSection]);

  // 根据选中的二级菜单渲染对应内容
  const renderContent = () => {
    switch (activeSection) {
      case 'model':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>模型管理</h2>
              <p>管理AI供应商和模型配置，含模型分类与模型能力管理。</p>
            </div>
            
            <div className="model-management-container">
              <IntegratedModelManagement />
            </div>
          </div>
        );
        
      case 'agents':
        return (
          <div className="settings-content">
            <Agent />
          </div>
        );
        
      case 'knowledge':
        return (
          <div className="settings-content">
            <Knowledge />
          </div>
        );
        
      case 'workflow':
        return (
          <div className="settings-content">
            <Workflow />
          </div>
        );
        
      case 'tool':
        return (
          <div className="settings-content">
            <Tool />
          </div>
        );
      
      case 'search':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>搜索管理</h2>
              <p>配置联网搜索的基础选项</p>
            </div>
            
            {isLoadingSearch ? (
              <div className="loading">加载中...</div>
            ) : (
              <div className="search-section">
                <div className="setting-card">
                  <div className="setting-item">
                    <label htmlFor="defaultSearchEngine">默认搜索引擎</label>
                    <select 
                      id="defaultSearchEngine"
                      className="search-select"
                      value={defaultSearchEngine}
                      onChange={(e) => setDefaultSearchEngine(e.target.value)}
                    >
                      <option value="google">Google</option>
                      <option value="bing">Bing</option>
                      <option value="baidu">百度</option>
                    </select>
                  </div>
                  
                  <div className="setting-item">
                    <label htmlFor="safeSearch">启用安全搜索</label>
                    <input 
                      type="checkbox" 
                      id="safeSearch" 
                      checked={safeSearch}
                      onChange={(e) => setSafeSearch(e.target.checked)}
                    />
                  </div>
                  
                  <div className="setting-actions">
                    <button 
                      className="save-btn" 
                      onClick={saveSearchSettings}
                      disabled={isSavingSearch}
                    >
                      {isSavingSearch ? '保存中...' : '保存设置'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
        
      case 'defaultModel':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>默认模型</h2>
              <p>设置系统默认使用的AI模型</p>
            </div>
            
            {/* 全局默认模型 */}
            <div className="setting-card">
              <div className="setting-header">
                <h3>全局默认模型</h3>
                <p>系统级别的默认AI模型，作为所有场景的基础默认值</p>
              </div>
              
              <div className="setting-item">
                <label htmlFor="globalDefaultModel">选择全局默认模型</label>
                <ModelSelectDropdown
                  models={models}
                  selectedModel={models.find(model => model.id === globalDefaultModel) || null}
                  onModelSelect={(model) => setGlobalDefaultModel(model.id)}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => {
                    // 根据供应商返回不同的LOGO URL
                    return `/logos/providers/${model.supplier || 'default'}.png`;
                  }}
                />
              </div>
            </div>
            
            {/* 场景默认模型 */}
            <div className="setting-card">
              <div className="setting-header">
                <h3>场景默认模型</h3>
                <p>为特定业务场景设置专属默认模型</p>
              </div>
              
              {/* 聊天场景 */}
              <div className="setting-item">
                <label htmlFor="chatModel">聊天场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('chat')}
                  selectedModel={getModelsByType('chat').find(model => model.id === sceneDefaultModels.chat) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, chat: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 图像场景 */}
              <div className="setting-item">
                <label htmlFor="imageModel">图像场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('image')}
                  selectedModel={getModelsByType('image').find(model => model.id === sceneDefaultModels.image) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, image: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 视频场景 */}
              <div className="setting-item">
                <label htmlFor="videoModel">视频场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('video')}
                  selectedModel={getModelsByType('video').find(model => model.id === sceneDefaultModels.video) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, video: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 语音场景 */}
              <div className="setting-item">
                <label htmlFor="voiceModel">语音场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('voice')}
                  selectedModel={getModelsByType('voice').find(model => model.id === sceneDefaultModels.voice) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, voice: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 翻译场景 */}
              <div className="setting-item">
                <label htmlFor="translateModel">翻译场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('translate')}
                  selectedModel={getModelsByType('translate').find(model => model.id === sceneDefaultModels.translate) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, translate: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 知识库场景 */}
              <div className="setting-item">
                <label htmlFor="knowledgeModel">知识库场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('knowledge')}
                  selectedModel={getModelsByType('knowledge').find(model => model.id === sceneDefaultModels.knowledge) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, knowledge: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 工作流场景 */}
              <div className="setting-item">
                <label htmlFor="workflowModel">工作流场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('workflow')}
                  selectedModel={getModelsByType('workflow').find(model => model.id === sceneDefaultModels.workflow) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, workflow: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 工具调用场景 */}
              <div className="setting-item">
                <label htmlFor="toolModel">工具调用场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('tool')}
                  selectedModel={getModelsByType('tool').find(model => model.id === sceneDefaultModels.tool) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, tool: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* 搜索场景 */}
              <div className="setting-item">
                <label htmlFor="searchModel">搜索场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('search')}
                  selectedModel={getModelsByType('search').find(model => model.id === sceneDefaultModels.search) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, search: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              {/* MCP场景 */}
              <div className="setting-item">
                <label htmlFor="mcpModel">MCP场景</label>
                <ModelSelectDropdown
                  models={getModelsByType('mcp')}
                  selectedModel={getModelsByType('mcp').find(model => model.id === sceneDefaultModels.mcp) || null}
                  onModelSelect={(model) => setSceneDefaultModels(prev => ({ ...prev, mcp: model.id }))}
                  placeholder="请选择模型"
                  disabled={isLoadingModels}
                  getModelLogoUrl={(model) => `/logos/providers/${model.supplier || 'default'}.png`}
                />
              </div>
              
              <div className="setting-actions">
                <button 
                  className="save-btn" 
                  onClick={handleSaveDefaultModel}
                  disabled={isSavingDefaultModel || isLoadingModels}
                >
                  {isSavingDefaultModel ? '保存中...' : '保存设置'}
                </button>
              </div>
            </div>
          </div>
        );
        
      case 'system':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>系统功能管理</h2>
              <p>管理系统功能和模块的启用状态</p>
            </div>
            
            <div className="system-management-container">
              <div className="coming-soon-placeholder">
                <div className="placeholder-icon">🚧</div>
                <h3>功能开发中</h3>
                <p>系统功能管理模块正在设计中，敬请期待...</p>
              </div>
            </div>
          </div>
        );
        
      case 'globalMemory':
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>全局记忆</h2>
              <p>管理系统全局记忆和上下文信息</p>
            </div>
            
            <div className="global-memory-container">
              {/* 全局记忆配置 */}
              <div className="setting-card">
                <div className="setting-header">
                  <h3>记忆配置</h3>
                  <p>配置全局记忆的存储和管理参数</p>
                </div>
                
                {isLoadingMemoryConfig ? (
                  <div className="loading">加载中...</div>
                ) : (
                  <div className="memory-config-section">
                    <div className="setting-item">
                      <label htmlFor="shortTermRetention">短期记忆保留天数</label>
                      <input 
                        type="number" 
                        id="shortTermRetention" 
                        className="form-input" 
                        min="1" 
                        max="30" 
                        value={memoryConfig.short_term_retention_days}
                        onChange={(e) => setMemoryConfig(prev => ({ ...prev, short_term_retention_days: parseInt(e.target.value) }))}
                      />
                    </div>
                    
                    <div className="setting-item">
                      <label htmlFor="privacyLevel">隐私级别</label>
                      <select 
                        id="privacyLevel" 
                        className="form-select"
                        value={memoryConfig.privacy_level}
                        onChange={(e) => setMemoryConfig(prev => ({ ...prev, privacy_level: e.target.value }))}
                      >
                        <option value="LOW">低（基本保护）</option>
                        <option value="MEDIUM">中（标准保护）</option>
                        <option value="HIGH">高（严格保护）</option>
                      </select>
                    </div>
                    
                    <div className="setting-item">
                      <label htmlFor="autoPurge">自动清理过期记忆</label>
                      <input 
                        type="checkbox" 
                        id="autoPurge" 
                        checked={memoryConfig.auto_purge}
                        onChange={(e) => setMemoryConfig(prev => ({ ...prev, auto_purge: e.target.checked }))}
                      />
                    </div>
                    
                    <div className="setting-item">
                      <label htmlFor="retrievalThreshold">检索相似度阈值</label>
                      <input 
                        type="number" 
                        id="retrievalThreshold" 
                        className="form-input" 
                        min="0.1" 
                        max="1.0" 
                        step="0.1"
                        value={memoryConfig.retrieval_threshold}
                        onChange={(e) => setMemoryConfig(prev => ({ ...prev, retrieval_threshold: parseFloat(e.target.value) }))}
                      />
                    </div>
                    
                    <div className="setting-item">
                      <label htmlFor="maxRetrievalResults">最大检索结果数</label>
                      <input 
                        type="number" 
                        id="maxRetrievalResults" 
                        className="form-input" 
                        min="1" 
                        max="100" 
                        value={memoryConfig.max_retrieval_results}
                        onChange={(e) => setMemoryConfig(prev => ({ ...prev, max_retrieval_results: parseInt(e.target.value) }))}
                      />
                    </div>
                    
                    <div className="setting-actions">
                      <button 
                        className="save-btn" 
                        onClick={saveMemoryConfig}
                        disabled={isSavingMemoryConfig}
                      >
                        {isSavingMemoryConfig ? '保存中...' : '保存配置'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
              
              {/* 记忆统计和分析 */}
              <div className="setting-card">
                <div className="setting-header">
                  <h3>记忆统计与分析</h3>
                  <p>查看记忆的统计信息和模式分析</p>
                </div>
                
                <div className="memory-analytics-section">
                  {/* 记忆统计 */}
                  <div className="analytics-row">
                    {isLoadingStats ? (
                      <div className="loading">加载中...</div>
                    ) : memoryStats ? (
                      <div className="stats-grid">
                        <div className="stat-card">
                          <div className="stat-value">{memoryStats?.total_count || 0}</div>
                          <div className="stat-label">总记忆数</div>
                        </div>
                        <div className="stat-card">
                          <div className="stat-value">{memoryStats.by_type?.SHORT_TERM || 0}</div>
                          <div className="stat-label">短期记忆</div>
                        </div>
                        <div className="stat-card">
                          <div className="stat-value">{memoryStats.by_type?.LONG_TERM || 0}</div>
                          <div className="stat-label">长期记忆</div>
                        </div>
                        <div className="stat-card">
                          <div className="stat-value">{memoryStats?.vector_db_count || 0}</div>
                          <div className="stat-label">向量存储数</div>
                        </div>
                        <div className="stat-card">
                          <div className="stat-value">{memoryStats?.average_importance ? memoryStats.average_importance.toFixed(2) : '0.00'}</div>
                          <div className="stat-label">平均重要性</div>
                        </div>
                        <div className="stat-card">
                          <div className="stat-value">0.00 MB</div>
                          <div className="stat-label">存储大小</div>
                        </div>
                      </div>
                    ) : (
                      <div className="empty-state">
                        <p>暂无统计数据</p>
                      </div>
                    )}
                  </div>
                  
                  {/* 可视化图表 */}
                  <div className="analytics-row">
                    <div className="chart-container">
                      <h4>记忆类型分布</h4>
                      <svg ref={memoryTypeChartRef} width="100%" height="200"></svg>
                    </div>
                    <div className="chart-container">
                      <h4>记忆重要性分布</h4>
                      <svg ref={importanceChartRef} width="100%" height="200"></svg>
                    </div>
                  </div>
                  
                  {/* 记忆模式分析 */}
                  <div className="analytics-row">
                    <div className="pattern-analysis">
                      <h4>记忆模式分析</h4>
                      {isLoadingPatterns ? (
                        <div className="loading">加载中...</div>
                      ) : memoryPatterns ? (
                        <div className="patterns-grid">
                          <div className="pattern-card">
                            <h5>高频主题</h5>
                            <div className="pattern-content">
                              <ul>
                                {memoryPatterns.top_topics?.map((topic, index) => (
                                  <li key={index}>{topic.topic}: {topic.frequency}次</li>
                                )) || []}
                              </ul>
                            </div>
                          </div>
                          <div className="pattern-card">
                            <h5>关联模式</h5>
                            <div className="pattern-content">
                              <ul>
                                {memoryPatterns.association_patterns?.map((pattern, index) => (
                                  <li key={index}>{pattern.concept1} → {pattern.concept2}: 相似度 {pattern.strength.toFixed(2)}</li>
                                )) || []}
                              </ul>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="empty-state">
                          <p>暂无模式数据</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* 记忆生命周期管理 */}
              <div className="setting-card">
                <div className="setting-header">
                  <h3>记忆生命周期管理</h3>
                  <p>管理记忆的自动清理和压缩</p>
                </div>
                
                <div className="lifecycle-management">
                  <div className="lifecycle-actions">
                    <button 
                      className="cleanup-btn" 
                      onClick={cleanupExpiredMemories}
                      disabled={isCleaningUpMemories}
                    >
                      {isCleaningUpMemories ? '清理中...' : '清理过期记忆'}
                    </button>
                    <button 
                      className="compress-btn" 
                      onClick={compressSimilarMemories}
                      disabled={isCompressingMemories}
                    >
                      {isCompressingMemories ? '压缩中...' : '压缩相似记忆'}
                    </button>
                  </div>
                  
                  <div className="lifecycle-info">
                    <p>• 清理过期记忆：移除超过保留天数的短期记忆</p>
                    <p>• 压缩相似记忆：将相似度超过阈值的短期记忆合并为长期记忆</p>
                  </div>
                </div>
              </div>
              
              {/* 知识图谱 */}
              <div className="setting-card">
                <div className="setting-header">
                  <h3>知识图谱</h3>
                  <p>可视化展示记忆之间的关联关系</p>
                </div>
                
                <div className="knowledge-graph-section">
                  <div className="graph-controls">
                    <div className="setting-item">
                      <label htmlFor="maxNodes">最大节点数</label>
                      <input 
                        type="number" 
                        id="maxNodes" 
                        className="form-input" 
                        min="10" 
                        max="500" 
                        value={maxNodes}
                        onChange={(e) => setMaxNodes(parseInt(e.target.value))}
                      />
                    </div>
                    <button 
                      className="load-graph-btn" 
                      onClick={loadKnowledgeGraph}
                      disabled={isLoadingGraph}
                    >
                      {isLoadingGraph ? '加载中...' : '刷新图谱'}
                    </button>
                  </div>
                  
                  <div className="graph-container">
                    {isLoadingGraph ? (
                      <div className="loading">加载中...</div>
                    ) : knowledgeGraph ? (
                      <div className="graph-info">
                        <p>节点数: {knowledgeGraph.nodes?.length || 0}, 边数: {knowledgeGraph.edges?.length || 0}</p>
                        <svg ref={knowledgeGraphRef} width="100%" height="500"></svg>
                      </div>
                    ) : (
                      <div className="empty-state">
                        <div className="empty-icon">🔗</div>
                        <h4>暂无知识图谱数据</h4>
                        <p>点击"刷新图谱"按钮加载知识图谱</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {/* 记忆列表 */}
              <div className="setting-card">
                <div className="setting-header">
                  <h3>记忆列表</h3>
                  <p>查看和管理系统中的全局记忆</p>
                </div>
                
                <div className="memory-list-section">
                  <div className="list-header">
                    <div className="search-box">
                      <input 
                        type="text" 
                        className="form-input" 
                        placeholder="搜索记忆内容..." 
                        value={memorySearchQuery}
                        onChange={(e) => setMemorySearchQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && loadMemories()}
                      />
                      <button className="search-btn" onClick={loadMemories}>搜索</button>
                    </div>
                    <div className="list-actions">
                      <button className="refresh-btn" onClick={loadMemories} disabled={isLoadingMemories}>
                        {isLoadingMemories ? '加载中...' : '刷新'}
                      </button>
                      <button className="clear-btn" onClick={clearAllMemories} disabled={isDeletingMemory}>
                        {isDeletingMemory ? '处理中...' : '清空所有'}
                      </button>
                    </div>
                  </div>
                  
                  {isLoadingMemories ? (
                    <div className="loading">加载中...</div>
                  ) : memories.length > 0 ? (
                    <div className="memory-list">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>ID</th>
                            <th>类型</th>
                            <th>分类</th>
                            <th>内容</th>
                            <th>重要性</th>
                            <th>创建时间</th>
                            <th>操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          {memories.map((memory) => (
                            <tr key={memory.id}>
                              <td>{memory.id}</td>
                              <td>{memory.memory_type}</td>
                              <td>{memory.memory_category || '未分类'}</td>
                              <td className="memory-content">{memory.content.length > 50 ? memory.content.substring(0, 50) + '...' : memory.content}</td>
                              <td>{memory.importance}</td>
                              <td>{new Date(memory.created_at).toLocaleString()}</td>
                              <td>
                                <button 
                                  className="delete-btn" 
                                  onClick={() => deleteMemory(memory.id)}
                                  disabled={isDeletingMemory}
                                >
                                  删除
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      
                      {/* 分页 */}
                      {totalMemories > memoriesPerPage && (
                        <div className="pagination">
                          <button 
                            className="page-btn" 
                            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                            disabled={currentPage === 1}
                          >
                            上一页
                          </button>
                          <span className="page-info">
                            第 {currentPage} 页，共 {Math.ceil(totalMemories / memoriesPerPage)} 页
                          </span>
                          <button 
                            className="page-btn" 
                            onClick={() => setCurrentPage(prev => Math.min(Math.ceil(totalMemories / memoriesPerPage), prev + 1))}
                            disabled={currentPage === Math.ceil(totalMemories / memoriesPerPage)}
                          >
                            下一页
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-icon">📭</div>
                      <h4>暂无记忆数据</h4>
                      <p>系统中尚未存储任何全局记忆</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
           
      default:
        return (
          <div className="settings-content">
            <div className="content-header">
              <h2>设置</h2>
              <p>选择左侧菜单查看相应设置选项</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>Py Copilot 设置</h1>
        <p>管理 Py Copilot 应用的各种配置选项</p>
      </div>
      
      <div className="settings-content-wrapper">
        {/* 左侧二级菜单 */}
        <div className={`settings-sidebar ${sidebarExpanded ? 'expanded' : 'collapsed'}`}>
          <nav className="settings-nav">
            <button 
              className={`nav-item ${activeSection === 'model' ? 'active' : ''}`}
              onClick={() => setActiveSection('model')}
            >
              <span className="nav-icon">🧠</span>
              <span className="nav-text">模型管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'agents' ? 'active' : ''}`}
              onClick={() => setActiveSection('agents')}
            >
              <span className="nav-icon">🤖</span>
              <span className="nav-text">智能体管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'knowledge' ? 'active' : ''}`}
              onClick={() => setActiveSection('knowledge')}
            >
              <span className="nav-icon">📚</span>
              <span className="nav-text">知识库管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'workflow' ? 'active' : ''}`}
              onClick={() => setActiveSection('workflow')}
            >
              <span className="nav-icon">🔄</span>
              <span className="nav-text">工作流管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'tool' ? 'active' : ''}`}
              onClick={() => setActiveSection('tool')}
            >
              <span className="nav-icon">🔧</span>
              <span className="nav-text">工具管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'search' ? 'active' : ''}`}
              onClick={() => setActiveSection('search')}
            >
              <span className="nav-icon">🔍</span>
              <span className="nav-text">搜索管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'system' ? 'active' : ''}`}
              onClick={() => setActiveSection('system')}
            >
              <span className="nav-icon">⚙️</span>
              <span className="nav-text">系统功能管理</span>
            </button>
            
            <button 
              className={`nav-item ${activeSection === 'globalMemory' ? 'active' : ''}`}
              onClick={() => setActiveSection('globalMemory')}
            >
              <span className="nav-icon">💾</span>
              <span className="nav-text">全局记忆</span>
            </button>
              

        </nav>
      </div>
        
        {/* 悬浮按钮 */}
        <button 
          className="sidebar-toggle-btn"
          onClick={toggleSidebar}
          title={sidebarExpanded ? "收缩导航栏" : "展开导航栏"}
        >
          {sidebarExpanded ? "◀" : "▶"}
        </button>
        
        {/* 右侧内容区域 */}
        <div className={`settings-main ${sidebarExpanded ? '' : 'expanded'}`}>
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default Settings;