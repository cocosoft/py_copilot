import React, { useState, useEffect } from 'react';
import './agent.css';
import { createAgent, getAgents, deleteAgent, getPublicAgents, getRecommendedAgents, updateAgent } from '../services/agentService';

const Agent = () => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    avatar: '🤖',
    prompt: '',
    knowledge_base: '',
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
      } else {
        result = await getAgents(currentPage, pageSize);
      }
      setAgents(result.agents);
      setTotalAgents(result.total);
    } catch (err) {
      setError('获取智能体列表失败，请重试');
      console.error('Error fetching agents:', err);
    } finally {
      setLoading(false);
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
        is_public: false,
        is_recommended: false
      });
      setEditingAgent(null);
      setShowCreateDialog(false);
      // 重新获取智能体列表
      fetchAgents();
    } catch (err) {
      setError(editingAgent ? '更新智能体失败，请重试' : '创建智能体失败，请重试');
      console.error('Error creating/updating agent:', err);
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

  // 编辑智能体
  const handleEditAgent = (agent) => {
    setEditingAgent(agent);
    setNewAgent({
      name: agent.name,
      description: agent.description,
      avatar: agent.avatar || '🤖',
      prompt: agent.prompt,
      knowledge_base: agent.knowledge_base || '',
      is_public: agent.is_public || false,
      is_recommended: agent.is_recommended || false
    });
    setShowCreateDialog(true);
  };

  // 删除智能体
  const handleDeleteAgent = async (agentId) => {
    if (window.confirm('确定要删除这个智能体吗？')) {
      setLoading(true);
      setError(null);
      try {
        await deleteAgent(agentId);
        // 重新获取智能体列表
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

  // 处理分类切换
  const handleCategoryChange = (category) => {
    setCurrentCategory(category);
  };

  // 页面加载时获取智能体列表
  useEffect(() => {
    // 切换分类时重置到第一页
    setCurrentPage(1);
  }, [currentCategory]);

  // 当前页或分类变化时获取智能体列表
  useEffect(() => {
    fetchAgents();
  }, [currentPage, pageSize, currentCategory]);

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

          <div className="agent-categories">
            <h3>智能体分类</h3>
            <ul>
              <li
                className={currentCategory === 'all' ? 'active' : ''}
                onClick={() => handleCategoryChange('all')}
              >
                所有智能体
              </li>
              <li
                className={currentCategory === 'public' ? 'active' : ''}
                onClick={() => handleCategoryChange('public')}
              >
                公开智能体
              </li>
              <li
                className={currentCategory === 'recommended' ? 'active' : ''}
                onClick={() => handleCategoryChange('recommended')}
              >
                推荐智能体
              </li>
            </ul>
          </div>
        </div>

        <div className="agent-main">
          <div className="agent-filters">
            <div className="search-bar">
              <input
                type="text"
                placeholder="搜索智能体..."
                className="search-input"
              />
              <button className="search-btn">🔍</button>
            </div>

            <div className="filter-options">
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
            {agents.length === 0 && !loading ? (
              <div className="empty-state">
                <h3>暂无智能体</h3>
                <p>点击"创建新智能体"按钮开始创建您的第一个智能助手</p>
              </div>
            ) : (
              agents.map(agent => (
                <div key={agent.id} className="agent-card">
                  <div className="agent-avatar">
                    {agent.avatar_url ? (
                      <img
                        src={agent.avatar_url}
                        alt={agent.name}
                        style={{ width: '100%', height: '100%', borderRadius: '50%' }}
                        onError={(e) => {
                          e.target.style.display = 'none';
                          const fallback = document.createElement('div');
                          fallback.textContent = '🤖';
                          fallback.style.fontSize = '48px';
                          e.target.parentNode.appendChild(fallback);
                        }}
                      />
                    ) : (
                      agent.avatar || '🤖'
                    )}
                  </div>
                  <h3>{agent.name}</h3>
                  <p>{agent.description}</p>
                  <div className="agent-actions">
                    <button className="chat-btn" onClick={() => handleTestAgent(agent)}>测试</button>
                    <button
                      className="edit-btn"
                      onClick={() => handleEditAgent(agent)}
                    >
                      编辑
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
              </div>

              <div className="form-group">
                <label htmlFor="agentKnowledgeBase">知识库</label>
                <select
                  id="agentKnowledgeBase"
                  name="knowledge_base"
                  value={newAgent.knowledge_base}
                  onChange={handleInputChange}
                  className="knowledge-base-select"
                >
                  <option value="">无（不绑定知识库）</option>
                  <option value="general_knowledge">通用知识库</option>
                  <option value="product_docs">产品文档</option>
                  <option value="technical_manuals">技术手册</option>
                  <option value="company_info">公司信息</option>
                  <option value="user_guides">用户指南</option>
                </select>
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
    </div>
  );
};

export default Agent;