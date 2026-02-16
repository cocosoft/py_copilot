import React from 'react';

function TaskFilter({ filter, onFilterChange }) {
  const handleStatusChange = (e) => {
    onFilterChange({
      ...filter,
      status: e.target.value
    });
  };

  const handleKeywordChange = (e) => {
    onFilterChange({
      ...filter,
      keyword: e.target.value
    });
  };

  const handleReset = () => {
    onFilterChange({
      status: '',
      keyword: ''
    });
  };

  return (
    <div className="task-filter">
      <div className="filter-item">
        <label htmlFor="status-filter">状态:</label>
        <select
          id="status-filter"
          value={filter.status}
          onChange={handleStatusChange}
          className="form-select"
        >
          <option value="">全部</option>
          <option value="pending">待处理</option>
          <option value="analyzing">分析中</option>
          <option value="running">执行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>

      <div className="filter-item">
        <label htmlFor="keyword-filter">关键词:</label>
        <input
          id="keyword-filter"
          type="text"
          value={filter.keyword}
          onChange={handleKeywordChange}
          placeholder="搜索任务..."
          className="form-input"
        />
      </div>

      <button
        className="btn btn-secondary"
        onClick={handleReset}
      >
        重置
      </button>
    </div>
  );
}

export default TaskFilter;
