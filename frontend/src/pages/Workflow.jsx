import React, { useState, useEffect } from 'react';
import WorkflowDesigner from '../components/WorkflowDesigner';
import workflowService from '../services/workflowService';
import './workflow.css';

const Workflow = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAutoComposeModal, setShowAutoComposeModal] = useState(false);
  const [showDesigner, setShowDesigner] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [workflows, setWorkflows] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoComposeLoading, setAutoComposeLoading] = useState(false);
  const [taskDescription, setTaskDescription] = useState('');
  const [optimizeWorkflow, setOptimizeWorkflow] = useState(false);

  useEffect(() => {
    loadWorkflows();
    loadExecutions();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const data = await workflowService.getWorkflows();
      
      // 计算每个工作流的步骤数量
      const workflowsWithSteps = data.map(workflow => {
        // 计算definition.nodes数组的长度作为步骤数量
        const stepCount = workflow.definition?.nodes?.length || 0;
        return {
          ...workflow,
          steps: stepCount
        };
      });
      
      setWorkflows(workflowsWithSteps);
    } catch (err) {
      setError('加载工作流失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadExecutions = async () => {
    try {
      const data = await workflowService.getWorkflowExecutions();
      setExecutions(data);
    } catch (err) {
      // 不设置全局错误，因为这不是关键功能
    }
  };

  const handleCreateWorkflow = () => {
    setShowCreateModal(true);
  };

  const handleWorkflowSelect = (workflow) => {
    setSelectedWorkflow(workflow);
  };

  const handleEditWorkflow = (workflow) => {
    setEditingWorkflow(workflow);
    setShowDesigner(true);
  };

  const handleCreateNewWorkflow = (template) => {
    const newWorkflow = {
      id: Date.now(),
      name: `新工作流-${Date.now()}`,
      description: '基于模板创建的新工作流',
      steps: 0,
      status: 'draft',
      createdAt: new Date().toISOString().split('T')[0],
      lastRun: null,
      icon: '📝',
      type: template
    };
    setEditingWorkflow(newWorkflow);
    setShowDesigner(true);
    setShowCreateModal(false);
  };

  const handleSaveWorkflow = async (workflowData) => {
    try {
      
      if (workflowData.id) {
        // 更新现有工作流
        await workflowService.updateWorkflow(workflowData.id, workflowData);
        alert('工作流更新成功！');
      } else {
        // 创建新工作流
        await workflowService.createWorkflow(workflowData);
        alert('工作流创建成功！');
      }
      
      // 重新加载工作流列表
      await loadWorkflows();
    } catch (error) {
      alert('保存工作流失败: ' + error.message);
    }
  };

  const handleExecuteWorkflow = async (executionData) => {
    try {
      const result = await workflowService.executeWorkflow(
        executionData.workflowId, 
        executionData.inputData
      );
      
      alert(`工作流执行已启动！执行ID: ${result.execution_id}`);
    } catch (error) {
      alert('执行工作流失败: ' + error.message);
    }
  };

  const handleCloseDesigner = () => {
    setShowDesigner(false);
    setEditingWorkflow(null);
  };

  const handleDeleteWorkflow = async (workflowId) => {
    try {
      if (window.confirm('确定要删除这个工作流吗？此操作不可撤销。')) {
        await workflowService.deleteWorkflow(workflowId);
        alert('工作流删除成功！');
        
        // 重新加载工作流列表
        await loadWorkflows();
        
        // 如果删除的是当前选中的工作流，关闭详情视图
        if (selectedWorkflow && selectedWorkflow.id === workflowId) {
          setSelectedWorkflow(null);
        }
      }
    } catch (error) {
      alert('删除工作流失败: ' + error.message);
    }
  };

  const handleAutoComposeWorkflow = async () => {
    try {
      if (!taskDescription.trim()) {
        alert('请输入任务描述');
        return;
      }
      
      setAutoComposeLoading(true);
      
      // 调用自动生成工作流API
      const result = await workflowService.autoComposeWorkflow(taskDescription, optimizeWorkflow);
      
      // 重新加载工作流列表
      await loadWorkflows();
      
      // 自动跳转到编辑界面
      setEditingWorkflow(result.workflow);
      setShowDesigner(true);
      
      // 关闭自动生成模态框
      setShowAutoComposeModal(false);
      
      alert('工作流自动生成成功！');
      
    } catch (error) {
      alert('工作流生成失败: ' + error.message);
    } finally {
      setAutoComposeLoading(false);
    }
  };

  // 辅助函数
  const getWorkflowIcon = (type) => {
    const iconMap = {
      'document': '📄',
      'image': '🖼️',
      'data': '🧹',
      'translation': '🌐',
      'knowledge_graph': '🧠',
      'analysis': '📊',
      'default': '📝'
    };
    return iconMap[type] || iconMap.default;
  };

  const getStatusText = (status) => {
    const statusMap = {
      'active': '活跃',
      'inactive': '停用',
      'draft': '草稿',
      'archived': '已归档',
      'running': '运行中',
      'completed': '已完成',
      'failed': '失败',
      'canceled': '已取消',
      'paused': '已暂停',
      'default': '未知'
    };
    return statusMap[status] || statusMap.default;
  };

  const handleExecutionSelect = (execution) => {
    setSelectedExecution(execution);
  };

  const handleCloseExecutionDetail = () => {
    setSelectedExecution(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
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
          <button className="secondary-button" onClick={() => setShowAutoComposeModal(true)}>
            自动生成工作流
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

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>加载工作流中...</p>
        </div>
      )}
      
      {error && (
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={loadWorkflows} className="retry-button">重试</button>
        </div>
      )}
      
      {!loading && !error && (
        <div className={`workflow-container ${viewMode}`}>
          {workflows.length === 0 ? (
            <div className="empty-state">
              <p>暂无工作流，点击"创建新工作流"开始创建</p>
            </div>
          ) : (
            workflows.map((workflow) => (
              <div 
                key={workflow.id} 
                className={`workflow-item ${workflow.status}`}
                onClick={() => handleWorkflowSelect(workflow)}
              >
                <div className="workflow-icon">{getWorkflowIcon(workflow.type)}</div>
                <h3 className="workflow-name">{workflow.name}</h3>
                <p className="workflow-description">{workflow.description}</p>
                <div className="workflow-meta">
                  <span className="step-count">{workflow.steps || 0} 个步骤</span>
                  <span className={`status-badge ${workflow.status}`}>
                    {getStatusText(workflow.status)}
                  </span>
                </div>
                <div className="workflow-timestamps">
                  <span>创建于: {formatDate(workflow.created_at)}</span>
                  <span>最后运行: {workflow.last_run ? formatDate(workflow.last_run) : '从未运行'}</span>
                </div>
                <div className="workflow-actions">
                  <button 
                    className="action-button run"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleExecuteWorkflow({ workflowId: workflow.id, inputData: {} });
                    }}
                  >
                    运行
                  </button>
                  <button 
                    className="action-button edit"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditWorkflow(workflow);
                    }}
                  >
                    编辑
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

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

              <div className="workflow-executions">
                <h3>执行历史</h3>
                <div className="executions-list">
                  {executions
                    .filter(exec => exec.workflow_id === selectedWorkflow.id)
                    .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
                    .map((execution) => (
                    <div
                      key={execution.id}
                      className={`execution-item ${execution.status}`}
                      onClick={() => handleExecutionSelect(execution)}
                    >
                      <div className="execution-info">
                        <div className="execution-id">执行 ID: {execution.id}</div>
                        <div className="execution-time">
                          {formatDate(execution.started_at)}
                        </div>
                      </div>
                      <div className="execution-status">
                        <span className={`status-badge ${execution.status}`}>
                          {getStatusText(execution.status)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="detail-actions">
                <button 
                  className="primary-button"
                  onClick={() => handleExecuteWorkflow({ workflowId: selectedWorkflow.id, inputData: {} })}
                >
                  运行工作流
                </button>
                <button 
                  className="secondary-button"
                  onClick={() => handleEditWorkflow(selectedWorkflow)}
                >
                  编辑工作流
                </button>
                <button 
                  className="danger-button"
                  onClick={() => handleDeleteWorkflow(selectedWorkflow.id)}
                >
                  删除工作流
                </button>
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

      {showAutoComposeModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>自动生成工作流</h2>
              <button 
                className="close-button"
                onClick={() => setShowAutoComposeModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>任务描述</label>
                <textarea 
                  placeholder="输入您想要完成的任务描述，例如：'搜索关于公司A的基本信息，提取关键实体和属性，分析公司A与其他实体的关系'" 
                  rows="5"
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>
                  <input 
                    type="checkbox" 
                    checked={optimizeWorkflow}
                    onChange={(e) => setOptimizeWorkflow(e.target.checked)}
                  />
                  优化工作流
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="secondary-button"
                onClick={() => setShowAutoComposeModal(false)}
              >
                取消
              </button>
              <button 
                className="primary-button"
                onClick={handleAutoComposeWorkflow}
                disabled={autoComposeLoading}
              >
                {autoComposeLoading ? '生成中...' : '生成工作流'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showDesigner && (
        <div className="workflow-designer-overlay">
          <div className="workflow-designer-container">
            <WorkflowDesigner
              workflow={editingWorkflow}
              onSave={handleSaveWorkflow}
              onExecute={handleExecuteWorkflow}
            />
            <button 
              className="close-designer-button"
              onClick={handleCloseDesigner}
            >
              ✕ 关闭设计器
            </button>
          </div>
        </div>
      )}

      {selectedExecution && (
        <div className="execution-detail-overlay">
          <div className="execution-detail">
            <div className="detail-header">
              <h2>执行详情 - ID: {selectedExecution.id}</h2>
              <button 
                className="close-button"
                onClick={handleCloseExecutionDetail}
              >
                ✕
              </button>
            </div>
            <div className="detail-content">
              <div className="execution-meta">
                <div className="meta-item">
                  <label>工作流:</label>
                  <span>{workflows.find(wf => wf.id === selectedExecution.workflow_id)?.name || '未知'}</span>
                </div>
                <div className="meta-item">
                  <label>状态:</label>
                  <span className={`status-badge ${selectedExecution.status}`}>
                    {getStatusText(selectedExecution.status)}
                  </span>
                </div>
                <div className="meta-item">
                  <label>开始时间:</label>
                  <span>{formatDate(selectedExecution.started_at)}</span>
                </div>
                {selectedExecution.completed_at && (
                  <div className="meta-item">
                    <label>结束时间:</label>
                    <span>{formatDate(selectedExecution.completed_at)}</span>
                  </div>
                )}
              </div>

              <div className="execution-data">
                <h3>输入数据</h3>
                <pre>{JSON.stringify(selectedExecution.input_data, null, 2)}</pre>
              </div>

              {selectedExecution.output_data && (
                <div className="execution-data">
                  <h3>输出数据</h3>
                  <pre>{JSON.stringify(selectedExecution.output_data, null, 2)}</pre>
                </div>
              )}

              {selectedExecution.error && (
                <div className="execution-error">
                  <h3>错误信息</h3>
                  <pre>{selectedExecution.error}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Workflow;