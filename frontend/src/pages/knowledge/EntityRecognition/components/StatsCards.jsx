/**
 * 统计卡片组件
 *
 * 显示实体统计数据
 */

import React from 'react';

/**
 * 统计卡片组件
 */
const StatsCards = ({ stats }) => {
  return (
    <div className="stats-cards">
      <div className="stat-card">
        <span className="stat-value">{stats.total}</span>
        <span className="stat-label">总实体</span>
      </div>
      <div className="stat-card pending">
        <span className="stat-value">{stats.pending}</span>
        <span className="stat-label">待确认</span>
      </div>
      <div className="stat-card confirmed">
        <span className="stat-value">{stats.confirmed}</span>
        <span className="stat-label">已确认</span>
      </div>
      <div className="stat-card rejected">
        <span className="stat-value">{stats.rejected}</span>
        <span className="stat-label">已拒绝</span>
      </div>
      <div className="stat-card modified">
        <span className="stat-value">{stats.modified}</span>
        <span className="stat-label">已修改</span>
      </div>
    </div>
  );
};

export default StatsCards;
