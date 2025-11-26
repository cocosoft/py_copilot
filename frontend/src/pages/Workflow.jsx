import React, { useState } from 'react';
import './workflow.css';

const Workflow = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'

  // 示例工作流数据
  const workflows = [
    {
      id: 1,
      name: '文档生成工作流',
      description: '自动从数据生成PDF和Word文档',
      steps: 4,
      status: 'active',
      createdAt: '2023-06-15',
      lastRun: '2023-06-20',
      icon: '📄'
    },
    {
      id: 2,
      name: '图像预处理工作流',
      description: '批量调整图像大小和格式转换',
      steps: 3,
      status: 'active',
      createdAt: '2023-06-10',
      lastRun: '2023-06-18',
      icon: '🖼️'
    },
    {
      id: 3,
      name: '数据清洗管道',
      description: '数据去重、格式化和验证',
      steps: 5,
      status: 'inactive',
      createdAt: '2023-05-25',
      lastRun: '2023-06-10',
      icon: '🧹'
    },
    {
      id: 4,
      name: '多语言翻译流程',
      description: '批量文档多语言翻译',
      steps: 4,
      status: 'active',
      createdAt: '2023-06-05',
      lastRun: '2023-06-15',
      icon: '🌐'
    }
  ];

  const handleCreateWorkflow = () => {
    setShowCreateModal(true);
  };

  const handleWorkflowSelect = (workflow) => {
    setSelectedWorkflow(workflow);
  };

  return (
    <div className="workflow-page">
      <div className="content-header">
        <h2>工作流管理</h2>
        <p>创建和管理您的工作流，定义和执行自动化任务。</p>
      </div>
        <div className="header-actions">
          <button className="primary-button" onClick={handleCreateWorkflow}>
            创建新工作流
          </button>
        </div>
      <div className="workflow-controls">
        <div className="search-filter">
          <input
            type="text"
            placeholder="搜索工作流..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="view-controls">
          <button 
            className={`view-button ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
          >
            🗂️ 网格视图
          </button>
          <button 
            className={`view-button ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            📋 列表视图
          </button>
        </div>
      </div>

      <div className={`workflow-container ${viewMode}`}>
        {workflows.map((workflow) => (
          <div 
            key={workflow.id} 
            className={`workflow-item ${workflow.status}`}
            onClick={() => handleWorkflowSelect(workflow)}
          >
            <div className="workflow-icon">{workflow.icon}</div>
            <h3 className="workflow-name">{workflow.name}</h3>
            <p className="workflow-description">{workflow.description}</p>
            <div className="workflow-meta">
              <span className="step-count">{workflow.steps} 个步骤</span>
              <span className={`status-badge ${workflow.status}`}>
                {workflow.status === 'active' ? '活跃' : '停用'}
              </span>
            </div>
            <div className="workflow-timestamps">
              <span>创建于: {workflow.createdAt}</span>
              <span>最后运行: {workflow.lastRun}</span>
            </div>
            <div className="workflow-actions">
              <button className="action-button run">运行</button>
              <button className="action-button edit">编辑</button>
            </div>
          </div>
        ))}
      </div>

      {selectedWorkflow && (
        <div className="workflow-detail-overlay">
          <div className="workflow-detail">
            <div className="detail-header">
              <h2>{selectedWorkflow.name}</h2>
              <button 
                className="close-button"
                onClick={() => setSelectedWorkflow(null)}
              >
                ✕
              </button>
            </div>
            <div className="detail-content">
              <p>{selectedWorkflow.description}</p>
              <div className="workflow-steps">
                <h3>工作流步骤</h3>
                <div className="steps-list">
                  {Array.from({ length: selectedWorkflow.steps }).map((_, index) => (
                    <div key={index} className="step-item">
                      <div className="step-number">{index + 1}</div>
                      <div className="step-content">
                        <p>步骤 {index + 1}: 处理任务 #{index + 1}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="detail-actions">
                <button className="primary-button">运行工作流</button>
                <button className="secondary-button">编辑工作流</button>
                <button className="danger-button">删除工作流</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>创建新工作流</h2>
              <button 
                className="close-button"
                onClick={() => setShowCreateModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>工作流名称</label>
                <input type="text" placeholder="输入工作流名称" />
              </div>
              <div className="form-group">
                <label>工作流描述</label>
                <textarea placeholder="输入工作流描述" rows="3" />
              </div>
              <div className="form-group">
                <label>选择工作流模板</label>
                <select>
                  <option value="">自定义工作流</option>
                  <option value="document">文档处理</option>
                  <option value="image">图像处理</option>
                  <option value="data">数据处理</option>
                  <option value="translation">翻译流程</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="secondary-button"
                onClick={() => setShowCreateModal(false)}
              >
                取消
              </button>
              <button className="primary-button">创建工作流</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workflow;