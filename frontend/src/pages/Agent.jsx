import React, { useState, useEffect } from 'react';
import './agent.css';
import { createAgent, getAgents, deleteAgent, getPublicAgents, getRecommendedAgents, updateAgent, searchAgents, testAgent, copyAgent, restoreAgent, getDeletedAgents, exportAgent, importAgent } from '../services/agentService';
import { createAgentCategory, getAgentCategories, updateAgentCategory, deleteAgentCategory, getAgentCategoryTree } from '../services/agentCategoryService';
import { getKnowledgeBases } from '../utils/api/knowledgeApi';
import defaultModelApi from '../utils/api/defaultModelApi';
import modelApi from '../utils/api/modelApi';
import skillApi from '../services/skillApi';
import AgentParameterManagement from '../components/ModelManagement/AgentParameterManagement';
import ModelSelectDropdown from '../components/ModelManagement/ModelSelectDropdown';
import ModelDataManager from '../services/modelDataManager';

const Agent = () => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    avatar: '🤖',
    prompt: '',
    knowledge_base: '',
    category_id: null,
    default_model: null,
    skills: [],
    is_public: false,
    is_recommended: false
  });
  const [agents, setAgents] = useState([]);
  const [currentCategory, setCurrentCategory] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [totalAgents, setTotalAgents] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  // 参数管理视图状态
  const [showParameterManagement, setShowParameterManagement] = useState(false);
  const [selectedAgentForParams, setSelectedAgentForParams] = useState(null);
  
  // 头像预览状态
  const [avatarPreview, setAvatarPreview] = useState('🤖');

  // 分类相关状态
  const [agentCategories, setAgentCategories] = useState([]);
  const [categoryTree, setCategoryTree] = useState([]);
  const [showCategoryDialog, setShowCategoryDialog] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [newCategory, setNewCategory] = useState({
    name: '',
    logo: '📁',
    is_system: false
  });

  // 知识库相关状态
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [loadingKnowledgeBases, setLoadingKnowledgeBases] = useState(false);

  // 默认模型相关状态
  const [defaultModels, setDefaultModels] = useState([]);
  const [loadingDefaultModels, setLoadingDefaultModels] = useState(false);

  // 技能相关状态
  const [skills, setSkills] = useState([]);
  const [loadingSkills, setLoadingSkills] = useState(false);

  // 搜索相关状态
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // 软删除相关状态
  const [showDeletedAgents, setShowDeletedAgents] = useState(false);
  const [deletedAgents, setDeletedAgents] = useState([]);
  const [totalDeletedAgents, setTotalDeletedAgents] = useState(0);

  const handleCreateAgent = () => {
    setShowCreateDialog(true);
  };

  // 获取智能体列表
  const fetchAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      let result;
      if (currentCategory === 'public') {
        result = await getPublicAgents(currentPage, pageSize);
      } else if (currentCategory === 'recommended') {
        result = await getRecommendedAgents(currentPage, pageSize);
      } else if (typeof currentCategory === 'number') {
        // 如果是数字ID，按分类ID获取智能体
        result = await getAgents(currentPage, pageSize, currentCategory);
      } else {
        result = await getAgents(currentPage, pageSize);
      }
      setAgents(result.agents);
      setTotalAgents(result.total);
    } catch (err) {
      setError('获取智能体列表失败，请重试');
      console.error('Error fetching agents:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 搜索智能体
  const handleSearchAgents = async () => {
    if (!searchKeyword.trim()) {
      setIsSearching(false);
      fetchAgents();
      return;
    }
    
    setIsSearching(true);
    setLoading(true);
    setError(null);
    try {
      const categoryId = typeof currentCategory === 'number' ? currentCategory : null;
      const result = await searchAgents(searchKeyword, currentPage, pageSize, categoryId);
      setAgents(result.agents);
      setTotalAgents(result.total);
    } catch (err) {
      setError('搜索智能体失败，请重试');
      console.error('Error searching agents:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 处理搜索输入变化
  const handleSearchInputChange = (e) => {
    setSearchKeyword(e.target.value);
  };

  // 处理搜索按钮点击
  const handleSearchButtonClick = () => {
    setCurrentPage(1);
    handleSearchAgents();
  };

  // 处理搜索输入回车
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearchButtonClick();
    }
  };

  // 创建或更新智能体
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (editingAgent) {
        // 更新智能体
        await updateAgent(editingAgent.id, newAgent);
        alert('智能体更新成功！');
      } else {
        // 创建智能体
        await createAgent(newAgent);
        alert('智能体创建成功！');
      }

      // 重置表单并关闭对话框
      setNewAgent({
        name: '',
        description: '',
        avatar: '🤖',
        prompt: '',
        knowledge_base: '',
        category_id: null,
        default_model: null,
        skills: [],
        is_public: false,
        is_recommended: false
      });
      setEditingAgent(null);
      setShowCreateDialog(false);
      // 重新获取智能体列表
      fetchAgents();
    } catch (err) {
      setError(editingAgent ? '更新智能体失败，请重试' : '创建智能体失败，请重试');
      console.error('Error creating/updating agent:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewAgent(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAvatarChange = (avatar) => {
    setNewAgent(prev => ({
      ...prev,
      avatar
    }));
  };

  // 处理技能选择
  const handleSkillToggle = (skillId) => {
    setNewAgent(prev => {
      const isSelected = prev.skills.includes(skillId);
      if (isSelected) {
        return {
          ...prev,
          skills: prev.skills.filter(id => id !== skillId)
        };
      } else {
        return {
          ...prev,
          skills: [...prev.skills, skillId]
        };
      }
    });
  };

  // 处理默认模型选择
  const handleDefaultModelSelect = (model) => {
    setNewAgent(prev => ({
      ...prev,
      default_model: model ? model.id : null
    }));
  };

  // 获取当前选中的模型对象
  const getSelectedDefaultModel = () => {
    if (!newAgent.default_model || !defaultModels.length) return null;
    return defaultModels.find(model => model.id === newAgent.default_model) || null;
  };

  // 编辑智能体
  const handleEditAgent = (agent) => {
    setEditingAgent(agent);
    setNewAgent({
      name: agent.name,
      description: agent.description,
      avatar: agent.avatar || '🤖',
      prompt: agent.prompt,
      knowledge_base: agent.knowledge_base || '',
      category_id: agent.category_id || null,
      default_model: agent.default_model || null,
      skills: agent.skills || [],
      is_public: agent.is_public || false,
      is_recommended: agent.is_recommended || false
    });
    setShowCreateDialog(true);
  };
  
  // 头像预览逻辑
  useEffect(() => {
    if (newAgent.avatar) {
      if (newAgent.avatar.startsWith(('http://', 'https://'))) {
        setAvatarPreview(newAgent.avatar);
      } else {
        setAvatarPreview(newAgent.avatar);
      }
    } else {
      setAvatarPreview('🤖');
    }
  }, [newAgent.avatar]);

  // 删除智能体
  const handleDeleteAgent = async (agentId) => {
    if (window.confirm('确定要删除这个智能体吗？')) {
      setLoading(true);
      setError(null);
      try {
        await deleteAgent(agentId);
        fetchAgents();
        alert('智能体删除成功！');
      } catch (err) {
        setError('删除智能体失败，请重试');
        console.error('Error deleting agent:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  // 获取已删除智能体列表
  const fetchDeletedAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDeletedAgents(currentPage, pageSize);
      setDeletedAgents(result.agents);
      setTotalDeletedAgents(result.total);
    } catch (err) {
      setError('获取已删除智能体列表失败，请重试');
      console.error('Error fetching deleted agents:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 恢复智能体
  const handleRestoreAgent = async (agentId) => {
    if (window.confirm('确定要恢复这个智能体吗？')) {
      setLoading(true);
      setError(null);
      try {
        await restoreAgent(agentId);
        fetchDeletedAgents();
        alert('智能体恢复成功！');
      } catch (err) {
        setError('恢复智能体失败，请重试');
        console.error('Error restoring agent:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  // 切换显示已删除智能体
  const handleToggleDeletedAgents = () => {
    setShowDeletedAgents(!showDeletedAgents);
    if (!showDeletedAgents) {
      fetchDeletedAgents();
    }
  };

  // 导出智能体
  const handleExportAgent = async (agent) => {
    try {
      setLoading(true);
      const exportData = await exportAgent(agent.id);
      
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${agent.name}_config.json`;
      link.click();
      URL.revokeObjectURL(url);
      
      alert('智能体导出成功！');
    } catch (err) {
      alert(`导出失败：${err.message || '未知错误'}`);
      console.error('Error exporting agent:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 导入智能体
  const handleImportAgent = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      try {
        setLoading(true);
        const fileContent = await file.text();
        const importData = JSON.parse(fileContent);
        
        const result = await importAgent(importData);
        
        alert(`智能体导入成功！新智能体名称：${result.agent.name}`);
        
        fetchAgents();
      } catch (err) {
        alert(`导入失败：${err.message || '未知错误'}`);
        console.error('Error importing agent:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      } finally {
        setLoading(false);
      }
    };
    input.click();
  };

  // 复制智能体
  const handleCopyAgent = async (agent) => {
    const newName = prompt(`复制智能体 "${agent.name}"，请输入新名称：`, `${agent.name} (副本)`);
    if (newName === null) {
      return;
    }
    
    const name = newName.trim() || `${agent.name} (副本)`;
    
    try {
      setLoading(true);
      const result = await copyAgent(agent.id, name);
      
      alert(`智能体复制成功！新智能体名称：${result.agent.name}`);
      
      fetchAgents();
    } catch (err) {
      alert(`复制失败：${err.message || '未知错误'}`);
      console.error('Error copying agent:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 测试智能体
  const handleTestAgent = async (agent) => {
    const testMessage = prompt('请输入测试消息：', '你好，请介绍一下你自己');
    if (testMessage === null) {
      return;
    }
    
    const message = testMessage.trim() || '你好，请介绍一下你自己';
    
    try {
      setLoading(true);
      const result = await testAgent(agent.id, message);
      
      if (result.success) {
        alert(`测试成功！\n\n回复：${result.response}\n\n使用模型：${result.model_used}\n消耗Token：${result.tokens_used}`);
      } else {
        alert(`测试失败：${result.error || '未知错误'}`);
      }
    } catch (err) {
      alert(`测试失败：${err.message || '未知错误'}`);
      console.error('Error testing agent:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 打开参数管理
  const handleManageParameters = (agent) => {
    setSelectedAgentForParams(agent);
    setShowParameterManagement(true);
  };

  // 返回智能体列表
  const handleBackToAgentList = () => {
    setShowParameterManagement(false);
    setSelectedAgentForParams(null);
  };

  // 刷新智能体数据
  const handleRefreshAgent = () => {
    fetchAgents();
  };

  // 处理分类切换
  const handleCategoryChange = (category) => {
    setCurrentCategory(category);
  };

  // 获取分类列表
  const fetchCategories = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getAgentCategories();
      setAgentCategories(response.categories);
    } catch (err) {
      setError('获取分类列表失败，请重试');
      console.error('Error fetching categories:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 创建或更新分类
  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (editingCategory) {
        // 更新分类
        await updateAgentCategory(editingCategory.id, newCategory);
        alert('分类更新成功！');
      } else {
        // 创建分类
        await createAgentCategory(newCategory);
        alert('分类创建成功！');
      }

      // 重置表单并关闭对话框
      setNewCategory({
        name: '',
        logo: '📁',
        is_system: false
      });
      setEditingCategory(null);
      setShowCategoryDialog(false);
      // 重新获取分类列表
      fetchCategories();
    } catch (err) {
      setError(editingCategory ? '更新分类失败，请重试' : '创建分类失败，请重试');
      console.error('Error creating/updating category:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 编辑分类
  const handleEditCategory = (category) => {
    setEditingCategory(category);
    setNewCategory({
      name: category.name,
      logo: category.logo || '📁',
      is_system: category.is_system || false
    });
    setShowCategoryDialog(true);
  };

  // 删除分类
  const handleDeleteCategory = async (categoryId, is_system) => {
    if (is_system) {
      alert('系统分类不可删除！');
      return;
    }
    if (window.confirm('确定要删除这个分类吗？')) {
      setLoading(true);
      setError(null);
      try {
        await deleteAgentCategory(categoryId);
        // 重新获取分类列表
        fetchCategories();
        alert('分类删除成功！');
      } catch (err) {
        setError('删除分类失败，请重试');
        console.error('Error deleting category:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
      } finally {
        setLoading(false);
      }
    }
  };

  // 切换分类时重置到第一页
  useEffect(() => {
    setCurrentPage(1);
  }, [currentCategory]);

  // 加载智能体列表
  useEffect(() => {
    if (isSearching) {
      handleSearchAgents();
    } else {
      fetchAgents();
    }
  }, [currentCategory, currentPage, pageSize]);

  // 搜索关键词变化时触发搜索
  useEffect(() => {
    if (searchKeyword.trim()) {
      setIsSearching(true);
    } else {
      setIsSearching(false);
    }
  }, [searchKeyword]);

  // 递归渲染分类树组件
  const CategoryTreeItem = ({ category, level = 0 }) => {
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = category.isExpanded !== false; // 默认展开

    return (
      <div className="category-tree-item">
        <div
          className={`category-info ${currentCategory === category.id ? 'active' : ''}`}
          onClick={() => handleCategoryChange(category.id)}
          style={{ paddingLeft: `${level * 8 + 8}px` }}
        >
          {hasChildren && (
            <span
              className="expand-icon"
              onClick={(e) => {
                e.stopPropagation();
                // 切换展开状态
                const updatedTree = toggleCategoryExpansion(categoryTree, category.id);
                setCategoryTree(updatedTree);
              }}
            >
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          {!hasChildren && <span className="expand-placeholder"></span>}
          <span className="category-logo">{category.logo || '📁'}</span>
          <span className="category-name">{category.name}</span>
        </div>
        <div className="category-actions">
          <button
            className="category-action-btn edit-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleEditCategory(category);
            }}
            title="编辑分类"
          >
            ✏️
          </button>
          <button
            className="category-action-btn delete-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteCategory(category.id, category.is_system);
            }}
            disabled={category.is_system}
            title={category.is_system ? '系统分类不可删除' : '删除分类'}
          >
            🗑️
          </button>
        </div>
        {hasChildren && isExpanded && (
          <div className="category-children">
            {category.children.map(child => (
              <CategoryTreeItem
                key={child.id}
                category={child}
                level={level + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  // 切换分类展开状态的辅助函数
  const toggleCategoryExpansion = (tree, categoryId) => {
    return tree.map(category => {
      if (category.id === categoryId) {
        return { ...category, isExpanded: !category.isExpanded };
      }
      if (category.children) {
        return {
          ...category,
          children: toggleCategoryExpansion(category.children, categoryId)
        };
      }
      return category;
    });
  };

  // 获取分类树结构
  const fetchCategoryTree = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getAgentCategoryTree();
      // 为每个节点添加展开状态
      const treeWithExpansion = addExpansionState(response.categories);
      setCategoryTree(treeWithExpansion);
    } catch (err) {
      setError('获取分类树失败，请重试');
      console.error('Error fetching category tree:', JSON.stringify({ message: err.message, stack: err.stack }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  // 获取知识库列表
  const fetchKnowledgeBases = async () => {
    setLoadingKnowledgeBases(true);
    try {
      const response = await getKnowledgeBases(0, 50); // 获取最多50个知识库（后端限制）
      setKnowledgeBases(response || []);
    } catch (err) {
      console.error('获取知识库列表失败:', err);
      setKnowledgeBases([]);
    } finally {
      setLoadingKnowledgeBases(false);
    }
  };

  // 获取默认模型列表
  const fetchDefaultModels = async () => {
    setLoadingDefaultModels(true);
    try {
      // 使用ModelDataManager加载模型数据，确保数据格式一致
      const models = await ModelDataManager.loadModels('agent');
      setDefaultModels(models || []);
    } catch (err) {
      console.error('获取模型列表失败:', err);
      setDefaultModels([]);
    } finally {
      setLoadingDefaultModels(false);
    }
  };

  // 获取技能列表
  const fetchSkills = async () => {
    setLoadingSkills(true);
    try {
      const response = await skillApi.list({ status: 'active', limit: 100 });
      setSkills(response.skills || []);
    } catch (err) {
      console.error('获取技能列表失败:', err);
      setSkills([]);
    } finally {
      setLoadingSkills(false);
    }
  };

  // 为树节点添加展开状态的辅助函数
  const addExpansionState = (tree) => {
    return tree.map(category => ({
      ...category,
      isExpanded: true, // 默认展开
      children: category.children ? addExpansionState(category.children) : []
    }));
  };

  // 页面加载时获取分类树、分类列表、知识库列表、默认模型列表和技能列表
  useEffect(() => {
    fetchCategoryTree();
    fetchCategories();
    fetchKnowledgeBases();
    fetchDefaultModels();
    fetchSkills();
  }, []);

  return (
    <div className="agent-container">
      <div className="content-header">
        <h2>智能体管理</h2>
        <p>创建和管理您的智能助手</p>
      </div>

      <div className="agent-content">
        <div className="agent-sidebar">
          <button className="create-agent-btn" onClick={handleCreateAgent}>
            <span className="plus-icon">+</span>
            创建新智能体
          </button>
          <button className="import-agent-btn" onClick={handleImportAgent}>
            <span className="import-icon">📥</span>
            导入智能体
          </button>
          <button className="create-category-btn" onClick={() => {
            setEditingCategory(null);
            setNewCategory({
              name: '',
              logo: '📁',
              is_system: false
            });
            setShowCategoryDialog(true);
          }}>
            <span className="plus-icon">+</span>
            创建分类
          </button>

          <div className="agent-categories">
            <h3>智能体分类</h3>
            <div className="category-group">
              <div className="category-tree">
                {categoryTree.length > 0 ? (
                  categoryTree.map(category => (
                    <CategoryTreeItem key={category.id} category={category} />
                  ))
                ) : (
                  <div className="no-categories">
                    <span>暂无自定义分类</span>
                    <button
                      className="create-category-quick-btn"
                      onClick={() => {
                        setEditingCategory(null);
                        setNewCategory({
                          name: '',
                          logo: '📁',
                          is_system: false
                        });
                        setShowCategoryDialog(true);
                      }}
                    >
                      创建第一个分类
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="agent-main">
          <div className="agent-filters">
            <div className="search-bar">
              <input
                type="text"
                placeholder="搜索智能体..."
                className="search-input"
                value={searchKeyword}
                onChange={handleSearchInputChange}
                onKeyPress={handleSearchKeyPress}
              />
              <button className="search-btn" onClick={handleSearchButtonClick}>🔍</button>
            </div>

            <div className="filter-options">
              <button 
                className="filter-btn"
                onClick={handleToggleDeletedAgents}
              >
                {showDeletedAgents ? '返回列表' : '查看已删除'}
                <span className="dropdown-icon">{showDeletedAgents ? '◀' : '🗑️'}</span>
              </button>

              <button className="filter-btn">
                筛选
                <span className="dropdown-icon">▼</span>
              </button>

              <button className="sort-btn">
                排序
                <span className="dropdown-icon">▼</span>
              </button>
            </div>
          </div>

          {loading && <div className="loading">加载中...</div>}
          {error && <div className="error">{error}</div>}

          <div className="agent-grid">
            {showDeletedAgents ? (
              <>
                {deletedAgents.length === 0 && !loading ? (
                  <div className="empty-state">
                    <h3>暂无已删除的智能体</h3>
                    <p>点击"返回列表"查看正常智能体</p>
                  </div>
                ) : (
                  deletedAgents.map(agent => (
                    <div key={agent.id} className="agent-card deleted-card">
                      <div className="agent-avatar">
                        {agent.avatar_url && agent.avatar_url.startsWith(('http://', 'https://')) ? (
                          <img 
                            src={agent.avatar_url} 
                            alt={agent.name} 
                            className="agent-avatar-image"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'inline';
                            }}
                          />
                        ) : null}
                        <span className="agent-avatar-fallback">{agent.avatar || '🤖'}</span>
                      </div>
                      <h3>{agent.name}</h3>
                      <p>{agent.description}</p>
                      {agent.category && (
                        <div className="agent-category-tag">
                          <span className="category-logo">{agent.category.logo || '📁'}</span>
                          <span className="category-name">{agent.category.name}</span>
                        </div>
                      )}
                      <div className="agent-actions">
                        <button 
                          className="restore-btn"
                          onClick={() => handleRestoreAgent(agent.id)}
                        >
                          恢复
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </>
            ) : (
              <>
                {agents.length === 0 && !loading ? (
                  <div className="empty-state">
                    <h3>暂无智能体</h3>
                    <p>点击"创建新智能体"按钮开始创建您的第一个智能助手</p>
                  </div>
                ) : (
                  agents.map(agent => (
                    <div key={agent.id} className="agent-card">
                      <div className="agent-avatar">
                        {agent.avatar_url && agent.avatar_url.startsWith(('http://', 'https://')) ? (
                          <img 
                            src={agent.avatar_url} 
                            alt={agent.name} 
                            className="agent-avatar-image"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'inline';
                            }}
                          />
                        ) : null}
                        <span className="agent-avatar-fallback">{agent.avatar || '🤖'}</span>
                      </div>
                      <h3>{agent.name}</h3>
                      <p>{agent.description}</p>
                      {agent.category && (
                        <div className="agent-category-tag">
                          <span className="category-logo">{agent.category.logo || '📁'}</span>
                          <span className="category-name">{agent.category.name}</span>
                        </div>
                      )}
                      <div className="agent-actions">
                        <button className="chat-btn" onClick={() => handleTestAgent(agent)}>测试</button>
                        <button
                          className="edit-btn"
                          onClick={() => handleEditAgent(agent)}
                        >
                          编辑
                        </button>
                        <button
                          className="param-btn"
                          onClick={() => handleManageParameters(agent)}
                        >
                          参数
                        </button>
                        <button
                          className="copy-btn"
                          onClick={() => handleCopyAgent(agent)}
                        >
                          复制
                        </button>
                        <button
                          className="export-btn"
                          onClick={() => handleExportAgent(agent)}
                        >
                          导出
                        </button>
                        <button
                          className="del-btn"
                          onClick={() => handleDeleteAgent(agent.id)}
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </>
            )}
          </div>

          {/* 分页控件 */}
          {totalAgents > 0 && (
            <div className="pagination">
              <button
                className="page-btn"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(prev => prev - 1)}
              >
                上一页
              </button>

              <div className="page-info">
                第 {currentPage} 页 / 共 {Math.ceil(totalAgents / pageSize)} 页
              </div>

              <div className="page-size-selector">
                <label htmlFor="pageSize">每页显示：</label>
                <select
                  id="pageSize"
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>

              <button
                className="page-btn"
                disabled={currentPage === Math.ceil(totalAgents / pageSize)}
                onClick={() => setCurrentPage(prev => prev + 1)}
              >
                下一页
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 创建智能体对话框 */}
      {showCreateDialog && (
        <div className="dialog-overlay">
          <div className="create-agent-dialog">
            <div className="dialog-header">
              <h3>{editingAgent ? '编辑智能体' : '创建新智能体'}</h3>
              <button
                className="close-btn"
                onClick={() => {
                  setShowCreateDialog(false);
                  setEditingAgent(null);
                  setNewAgent({
                    name: '',
                    description: '',
                    avatar: '🤖',
                    prompt: '',
                    knowledge_base: '',
                    category_id: null,
                    is_public: false,
                    is_recommended: false
                  });
                }}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="create-agent-form">
              <div className="form-group">
                <label htmlFor="agentName">智能体名称</label>
                <input
                  type="text"
                  id="agentName"
                  name="name"
                  value={newAgent.name}
                  onChange={handleInputChange}
                  placeholder="请输入智能体名称"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="agentDescription">智能体描述</label>
                <textarea
                  id="agentDescription"
                  name="description"
                  value={newAgent.description}
                  onChange={handleInputChange}
                  placeholder="请描述智能体的功能和用途"
                  rows="4"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="agentPrompt">提示词</label>
                <textarea
                  id="agentPrompt"
                  name="prompt"
                  value={newAgent.prompt}
                  onChange={handleInputChange}
                  placeholder="输入提示词以指导智能体的行为和响应方式"
                  rows="6"
                  required
                />
              </div>

              <div className="form-group">
                <label>选择头像</label>
                
                {/* 头像预览区域 */}
                <div className="avatar-preview">
                  <div className="avatar-preview-label">头像预览：</div>
                  <div className="preview-container">
                    {avatarPreview && avatarPreview.startsWith(('http://', 'https://')) ? (
                      <>
                        <img 
                          src={avatarPreview} 
                          alt="Avatar Preview" 
                          className="preview-image"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'block';
                          }}
                        />
                        <div className="preview-fallback" style={{ display: 'none' }}>{newAgent.avatar || '🤖'}</div>
                      </>
                    ) : (
                      <div className="preview-emoji">{newAgent.avatar || '🤖'}</div>
                    )}
                  </div>
                </div>
                
                {/* 头像选项 */}
                <div className="avatar-options">
                  {['🤖', '👨‍💻', '📝', '📊', '🎨', '🧠', '🔍', '💡'].map(avatar => (
                    <button
                      key={avatar}
                      type="button"
                      className={`avatar-option ${newAgent.avatar === avatar ? 'selected' : ''}`}
                      onClick={() => handleAvatarChange(avatar)}
                    >
                      {avatar}
                    </button>
                  ))}
                </div>
                
                {/* 自定义头像输入 */}
                <div className="custom-avatar-input">
                  <input
                    type="text"
                    placeholder="输入自定义头像（表情符号或图片URL）"
                    value={newAgent.avatar}
                    onChange={(e) => setNewAgent(prev => ({ ...prev, avatar: e.target.value }))}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="agentKnowledgeBase">知识库</label>
                <select
                  id="agentKnowledgeBase"
                  name="knowledge_base"
                  value={newAgent.knowledge_base}
                  onChange={handleInputChange}
                  className="knowledge-base-select"
                  disabled={loadingKnowledgeBases}
                >
                  <option value="">无（不绑定知识库）</option>
                  {loadingKnowledgeBases ? (
                    <option value="">加载中...</option>
                  ) : (
                    knowledgeBases.map(kb => (
                      <option key={kb.id} value={kb.id}>
                        {kb.name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="agentCategory">智能体分类</label>
                <select
                  id="agentCategory"
                  name="category_id"
                  value={newAgent.category_id || ''}
                  onChange={(e) => setNewAgent(prev => ({
                    ...prev,
                    category_id: e.target.value ? parseInt(e.target.value) : null
                  }))}
                  className="category-select"
                >
                  <option value="">无（不分类）</option>
                  {agentCategories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="agentDefaultModel">默认模型</label>
                {loadingDefaultModels ? (
                  <div className="loading-models">加载中...</div>
                ) : (
                  <ModelSelectDropdown
                    models={defaultModels}
                    selectedModel={getSelectedDefaultModel()}
                    onModelSelect={handleDefaultModelSelect}
                    placeholder="无（使用系统默认）"
                    disabled={loadingDefaultModels}
                    scene="agent"
                  />
                )}
              </div>

              <div className="form-group">
                <label>技能</label>
                <div className="skills-selection">
                  {loadingSkills ? (
                    <div>加载中...</div>
                  ) : skills.length === 0 ? (
                    <div>暂无可用技能</div>
                  ) : (
                    skills.map(skill => (
                      <label key={skill.id} className="skill-checkbox">
                        <input
                          type="checkbox"
                          checked={newAgent.skills.includes(skill.id)}
                          onChange={() => handleSkillToggle(skill.id)}
                        />
                        <span>{skill.name}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    name="is_public"
                    checked={newAgent.is_public}
                    onChange={(e) => setNewAgent(prev => ({
                      ...prev,
                      is_public: e.target.checked
                    }))}
                  />
                  公开智能体（其他用户可见）
                </label>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    name="is_recommended"
                    checked={newAgent.is_recommended}
                    onChange={(e) => setNewAgent(prev => ({
                      ...prev,
                      is_recommended: e.target.checked
                    }))}
                  />
                  推荐智能体（显示在推荐列表）
                </label>
              </div>

              <div className="dialog-actions">
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={() => setShowCreateDialog(false)}
                >
                  取消
                </button>
                <button type="submit" className="confirm-btn">
                  {editingAgent ? '更新' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 创建/编辑分类对话框 */}
      {showCategoryDialog && (
        <div className="dialog-overlay">
          <div className="create-agent-dialog">
            <div className="dialog-header">
              <h3>{editingCategory ? '编辑分类' : '创建新分类'}</h3>
              <button
                className="close-btn"
                onClick={() => {
                  setShowCategoryDialog(false);
                  setEditingCategory(null);
                  setNewCategory({
                    name: '',
                    logo: '📁',
                    is_system: false
                  });
                }}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCategorySubmit} className="create-agent-form">
              <div className="form-group">
                <label htmlFor="categoryName">分类名称</label>
                <input
                  type="text"
                  id="categoryName"
                  name="name"
                  value={newCategory.name}
                  onChange={(e) => setNewCategory(prev => ({
                    ...prev,
                    name: e.target.value
                  }))}
                  placeholder="请输入分类名称"
                  required
                />
              </div>

              <div className="form-group">
                <label>选择分类图标</label>
                <div className="avatar-options">
                  {['📁', '🤖', '👨‍💻', '📝', '📊', '🎨', '🧠', '🔍', '💡', '📚'].map(logo => (
                    <button
                      key={logo}
                      type="button"
                      className={`avatar-option ${newCategory.logo === logo ? 'selected' : ''}`}
                      onClick={() => setNewCategory(prev => ({
                        ...prev,
                        logo
                      }))}
                    >
                      {logo}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    name="is_system"
                    checked={newCategory.is_system}
                    onChange={(e) => setNewCategory(prev => ({
                      ...prev,
                      is_system: e.target.checked
                    }))}
                  />
                  系统分类（不可删除）
                </label>
              </div>

              <div className="dialog-actions">
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={() => setShowCategoryDialog(false)}
                >
                  取消
                </button>
                <button type="submit" className="confirm-btn">
                  {editingCategory ? '更新' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 参数管理视图 */}
      {showParameterManagement && selectedAgentForParams && (
        <AgentParameterManagement
          agent={selectedAgentForParams}
          onBack={handleBackToAgentList}
          onRefreshAgent={handleRefreshAgent}
        />
      )}
    </div>
  );
};

export default Agent;