import React, { useState } from 'react';
import './agent.css';

const Agent = () => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    avatar: '🤖',
    prompt: '',
    knowledgeBase: ''
  });

  const handleCreateAgent = () => {
    setShowCreateDialog(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // 这里可以添加创建智能体的API调用逻辑
    console.log('创建新智能体:', newAgent);
    // 模拟API调用后的重置和关闭对话框
    setNewAgent({ name: '', description: '', avatar: '🤖', prompt: '', knowledgeBase: '' });
    setShowCreateDialog(false);
    // 实际项目中，这里应该调用后端API创建智能体
    alert('智能体创建成功！');
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
              <li className="active">所有智能体</li>
              <li>我的创建</li>
              <li>推荐智能体</li>
              <li>已收藏</li>
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
          
          <div className="agent-grid">
            {/* 智能体卡片示例 */}
            <div className="agent-card">
              <div className="agent-avatar">🤖</div>
              <h3>助手智能体</h3>
              <p>通用人工智能助手，回答各类问题</p>
              <div className="agent-actions">
                <button className="chat-btn">开始聊天</button>
                <button className="more-btn">...</button>
              </div>
            </div>
            
            <div className="agent-card">
              <div className="agent-avatar">👨‍💻</div>
              <h3>编程助手</h3>
              <p>帮助编写、调试和优化代码</p>
              <div className="agent-actions">
                <button className="chat-btn">开始聊天</button>
                <button className="more-btn">...</button>
              </div>
            </div>
            
            <div className="agent-card">
              <div className="agent-avatar">📝</div>
              <h3>写作助手</h3>
              <p>辅助创作文章、报告和各类文档</p>
              <div className="agent-actions">
                <button className="chat-btn">开始聊天</button>
                <button className="more-btn">...</button>
              </div>
            </div>
            
            <div className="agent-card">
              <div className="agent-avatar">📊</div>
              <h3>数据分析</h3>
              <p>帮助分析数据和生成可视化报告</p>
              <div className="agent-actions">
                <button className="chat-btn">开始聊天</button>
                <button className="more-btn">...</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 创建智能体对话框 */}
      {showCreateDialog && (
        <div className="dialog-overlay">
          <div className="create-agent-dialog">
            <div className="dialog-header">
              <h3>创建新智能体</h3>
              <button 
                className="close-btn" 
                onClick={() => setShowCreateDialog(false)}
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
                  name="knowledgeBase"
                  value={newAgent.knowledgeBase}
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

              <div className="dialog-actions">
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={() => setShowCreateDialog(false)}
                >
                  取消
                </button>
                <button type="submit" className="confirm-btn">
                  创建
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