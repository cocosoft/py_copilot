import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';
import Button from './Button';
import Badge from './Badge';

const Table = ({
  columns = [],
  data = [],
  loading = false,
  pagination = false,
  pageSize = 10,
  onPageChange,
  selection = false,
  selectedRows = [],
  onSelectionChange,
  sortBy,
  sortOrder,
  onSort,
  rowKey = 'id',
  className,
  striped = false,
  hoverable = true,
  compact = false,
  emptyText = '暂无数据',
  ...props
}) => {
  const [currentPage, setCurrentPage] = useState(1);

  const sortedData = useMemo(() => {
    if (!sortBy) return data;
    
    return [...data].sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      
      if (aVal === bVal) return 0;
      
      let result = 0;
      if (aVal > bVal) result = 1;
      if (aVal < bVal) result = -1;
      
      return sortOrder === 'desc' ? -result : result;
    });
  }, [data, sortBy, sortOrder]);

  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;
    
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return sortedData.slice(start, end);
  }, [sortedData, currentPage, pageSize, pagination]);

  const totalPages = Math.ceil(data.length / pageSize);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    onPageChange?.(page);
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      const allRowKeys = paginatedData.map(row => row[rowKey]);
      onSelectionChange?.(allRowKeys);
    } else {
      onSelectionChange?.([]);
    }
  };

  const handleSelectRow = (rowKeyValue) => {
    const isSelected = selectedRows.includes(rowKeyValue);
    const newSelection = isSelected
      ? selectedRows.filter(key => key !== rowKeyValue)
      : [...selectedRows, rowKeyValue];
    onSelectionChange?.(newSelection);
  };

  const handleSort = (columnKey) => {
    const newSortOrder = 
      sortBy === columnKey && sortOrder === 'asc' ? 'desc' : 'asc';
    onSort?.(columnKey, newSortOrder);
  };

  const paddingClasses = compact ? 'py-2' : 'py-3';
  const fontSizeClasses = compact ? 'text-sm' : 'text-sm';
  const checkboxSize = compact ? 'w-3 h-3' : 'w-4 h-4';

  const renderSortIcon = (columnKey) => {
    if (sortBy !== columnKey) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }
    
    const iconClass = "w-4 h-4 text-blue-600";
    return sortOrder === 'asc' ? (
      <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  const renderCell = (value, column, row) => {
    if (column.render) {
      return column.render(value, row);
    }
    return value;
  };

  const isAllSelected = paginatedData.length > 0 && 
    paginatedData.every(row => selectedRows.includes(row[rowKey]));

  const isIndeterminate = selectedRows.length > 0 && 
    !isAllSelected && 
    paginatedData.some(row => selectedRows.includes(row[rowKey]));

  return (
    <div className={classNames('bg-white rounded-lg shadow-sm border border-gray-200', className)}>
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {selection && (
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    ref={(input) => {
                      if (input) input.indeterminate = isIndeterminate;
                    }}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className={classNames(
                      'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
                      checkboxSize
                    )}
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={classNames(
                    'px-4 text-left font-medium text-gray-900',
                    column.sortable ? 'cursor-pointer hover:bg-gray-100' : '',
                    fontSizeClasses
                  )}
                  onClick={() => column.sortable && handleSort(column.key)}
                >
                  <div className="flex items-center gap-2">
                    {column.title}
                    {column.sortable && renderSortIcon(column.key)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length + (selection ? 1 : 0)} className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <svg className="animate-spin w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span className="text-gray-500">加载中...</span>
                  </div>
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (selection ? 1 : 0)} className="text-center py-8 text-gray-500">
                  {emptyText}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, index) => (
                <motion.tr
                  key={row[rowKey]}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className={classNames(
                    'border-b border-gray-100',
                    striped && index % 2 === 0 ? 'bg-gray-50' : 'bg-white',
                    hoverable && 'hover:bg-gray-50'
                  )}
                >
                  {selection && (
                    <td className="px-4">
                      <input
                        type="checkbox"
                        checked={selectedRows.includes(row[rowKey])}
                        onChange={() => handleSelectRow(row[rowKey])}
                        className={classNames(
                          'rounded border-gray-300 text-blue-600 focus:ring-blue-500',
                          checkboxSize
                        )}
                      />
                    </td>
                  )}
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={classNames(
                        'px-4 text-gray-900',
                        paddingClasses,
                        fontSizeClasses
                      )}
                    >
                      {renderCell(row[column.key], column, row)}
                    </td>
                  ))}
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
          <div className="text-sm text-gray-700">
            显示 {(currentPage - 1) * pageSize + 1} 到{' '}
            {Math.min(currentPage * pageSize, data.length)} 项，共 {data.length} 项
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="small"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              上一页
            </Button>
            
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={classNames(
                      'px-3 py-1 text-sm rounded',
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <Button
              variant="ghost"
              size="small"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

Table.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    render: PropTypes.func,
    sortable: PropTypes.bool,
    width: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  })),
  data: PropTypes.array.isRequired,
  loading: PropTypes.bool,
  pagination: PropTypes.bool,
  pageSize: PropTypes.number,
  onPageChange: PropTypes.func,
  selection: PropTypes.bool,
  selectedRows: PropTypes.array,
  onSelectionChange: PropTypes.func,
  sortBy: PropTypes.string,
  sortOrder: PropTypes.oneOf(['asc', 'desc']),
  onSort: PropTypes.func,
  rowKey: PropTypes.string,
  className: PropTypes.string,
  striped: PropTypes.bool,
  hoverable: PropTypes.bool,
  compact: PropTypes.bool,
  emptyText: PropTypes.string,
};

export default Table;