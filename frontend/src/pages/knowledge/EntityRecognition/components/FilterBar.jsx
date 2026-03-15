/**
 * 筛选栏组件
 *
 * 提供实体搜索和筛选功能
 */

import React from 'react';
import { FiSearch } from 'react-icons/fi';

/**
 * 实体类型配置
 */
const ENTITY_TYPES = [
  { value: 'person', label: '人物', color: '#1890ff' },
  { value: 'organization', label: '组织', color: '#52c41a' },
  { value: 'location', label: '地点', color: '#faad14' },
  { value: 'time', label: '时间', color: '#722ed1' },
  { value: 'event', label: '事件', color: '#eb2f96' },
  { value: 'concept', label: '概念', color: '#13c2c2' },
  { value: 'product', label: '产品', color: '#f5222d' },
  { value: 'technology', label: '技术', color: '#2f54eb' },
];

/**
 * 筛选栏组件
 */
const FilterBar = ({
  searchQuery,
  setSearchQuery,
  filterType,
  setFilterType,
  filterStatus,
  setFilterStatus,
}) => {
  return (
    <div className="filter-bar">
      <div className="search-box">
        <FiSearch size={16} />
        <input
          type="text"
          placeholder="搜索实体..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      <div className="filter-group">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="all">全部类型</option>
          {ENTITY_TYPES.map(type => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">全部状态</option>
          <option value="pending">待确认</option>
          <option value="confirmed">已确认</option>
          <option value="rejected">已拒绝</option>
          <option value="modified">已修改</option>
        </select>
      </div>
    </div>
  );
};

export default FilterBar;
