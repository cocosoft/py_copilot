import React from 'react';
import './knowledge.css';

const Knowledge = () => {
  return (
    <div className="knowledge-container">
      <div className="content-header">
        <h2>知识库管理</h2>
        <p>管理和查询您的知识库文档</p>
      </div>
      
      <div className="knowledge-content">
        {/* 工具栏区域 */}
        <div className="knowledge-toolbar">
          <div className="search-container">
            <input
              type="text"
              placeholder="搜索知识库..."
              className="knowledge-search"
            />
            <button className="search-btn">
              🔍
            </button>
          </div>
          
          <div className="toolbar-actions">
            <button className="import-btn">
              导入文档
            </button>
            <button className="create-btn">
              + 新建知识库
            </button>
          </div>
        </div>
        
        {/* 视图切换和筛选 */}
        <div className="view-controls">
          <div className="view-buttons">
            <button className="view-btn active" title="网格视图">
              📋
            </button>
            <button className="view-btn" title="列表视图">
              📝
            </button>
          </div>
          
          <div className="filter-controls">
            <select className="sort-select">
              <option value="newest">最新创建</option>
              <option value="oldest">最早创建</option>
              <option value="name-asc">名称 A-Z</option>
              <option value="name-desc">名称 Z-A</option>
            </select>
            
            <select className="category-select">
              <option value="all">所有分类</option>
              <option value="personal">个人</option>
              <option value="team">团队</option>
              <option value="project">项目</option>
            </select>
          </div>
        </div>
        
        {/* 知识库列表/网格 */}
        <div className="knowledge-grid">
          {/* 示例知识库项 1 */}
          <div className="knowledge-item">
            <div className="knowledge-icon">
              📚
            </div>
            <div className="knowledge-info">
              <h3 className="knowledge-title">产品文档库</h3>
              <p className="knowledge-description">包含公司所有产品的使用说明和技术文档</p>
              <div className="knowledge-meta">
                <span className="document-count">24 个文档</span>
                <span className="last-updated">2 天前更新</span>
              </div>
            </div>
            <div className="knowledge-actions">
              <button className="action-btn" title="编辑">✏️</button>
              <button className="action-btn" title="分享">🔗</button>
              <button className="action-btn" title="删除">🗑️</button>
            </div>
          </div>
          
          {/* 示例知识库项 2 */}
          <div className="knowledge-item">
            <div className="knowledge-icon">
              📝
            </div>
            <div className="knowledge-info">
              <h3 className="knowledge-title">研究笔记</h3>
              <p className="knowledge-description">AI 技术研究资料和学习笔记</p>
              <div className="knowledge-meta">
                <span className="document-count">18 个文档</span>
                <span className="last-updated">5 天前更新</span>
              </div>
            </div>
            <div className="knowledge-actions">
              <button className="action-btn" title="编辑">✏️</button>
              <button className="action-btn" title="分享">🔗</button>
              <button className="action-btn" title="删除">🗑️</button>
            </div>
          </div>
          
          {/* 示例知识库项 3 */}
          <div className="knowledge-item">
            <div className="knowledge-icon">
              💼
            </div>
            <div className="knowledge-info">
              <h3 className="knowledge-title">项目计划</h3>
              <p className="knowledge-description">各项目的规划文档、进度报告和相关资料</p>
              <div className="knowledge-meta">
                <span className="document-count">32 个文档</span>
                <span className="last-updated">1 周前更新</span>
              </div>
            </div>
            <div className="knowledge-actions">
              <button className="action-btn" title="编辑">✏️</button>
              <button className="action-btn" title="分享">🔗</button>
              <button className="action-btn" title="删除">🗑️</button>
            </div>
          </div>
          
          {/* 示例知识库项 4 */}
          <div className="knowledge-item">
            <div className="knowledge-icon">
              📊
            </div>
            <div className="knowledge-info">
              <h3 className="knowledge-title">市场分析报告</h3>
              <p className="knowledge-description">行业趋势、竞品分析和市场调研报告</p>
              <div className="knowledge-meta">
                <span className="document-count">12 个文档</span>
                <span className="last-updated">3 周前更新</span>
              </div>
            </div>
            <div className="knowledge-actions">
              <button className="action-btn" title="编辑">✏️</button>
              <button className="action-btn" title="分享">🔗</button>
              <button className="action-btn" title="删除">🗑️</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Knowledge;