import React from 'react';
import './tool.css';

const Tool = () => {
  return (
    <div className="tool-container">
      <div className="content-header">
        <h2>工具集</h2>
        <p>发现和使用各种实用工具</p>
      </div>
      
      <div className="tool-content">
        {/* 左侧分类导航 */}
        <div className="tool-sidebar">
          <div className="sidebar-header">
            <h3>工具分类</h3>
          </div>
          
          <div className="category-list">
            <button className="category-item active">
              📋 全部工具
            </button>
            <button className="category-item">
              🧮 数据处理
            </button>
            <button className="category-item">
              📊 图表生成
            </button>
            <button className="category-item">
              🔧 开发工具
            </button>
            <button className="category-item">
              📝 文本处理
            </button>
            <button className="category-item">
              🧠 AI 增强
            </button>
            <button className="category-item">
              ⚙️ 实用工具
            </button>
          </div>
          
          <div className="sidebar-footer">
            <button className="add-tool-btn">
              + 添加自定义工具
            </button>
          </div>
        </div>
        
        {/* 右侧工具列表 */}
        <div className="tool-main">
          {/* 搜索和筛选区域 */}
          <div className="tool-controls">
            <div className="search-bar">
              <input
                type="text"
                placeholder="搜索工具..."
                className="tool-search"
              />
              <button className="search-icon">🔍</button>
            </div>
            
            <div className="sort-options">
              <label>排序:</label>
              <select className="sort-select">
                <option value="popular">最受欢迎</option>
                <option value="recent">最近添加</option>
                <option value="name">名称排序</option>
                <option value="usage">使用频率</option>
              </select>
            </div>
          </div>
          
          {/* 工具卡片网格 */}
          <div className="tool-grid">
            {/* 示例工具卡片 1 */}
            <div className="tool-card">
              <div className="tool-card-header">
                <div className="tool-icon">
                  📊
                </div>
                <div className="tool-card-actions">
                  <button className="star-btn" title="收藏">⭐</button>
                  <button className="more-btn" title="更多">⋮</button>
                </div>
              </div>
              
              <div className="tool-card-content">
                <h3 className="tool-name">数据可视化</h3>
                <p className="tool-description">将数据转换为直观的图表和图形</p>
                <div className="tool-meta">
                  <span className="tool-category">图表生成</span>
                  <span className="tool-usage">使用次数: 128</span>
                </div>
              </div>
              
              <div className="tool-card-footer">
                <button className="use-tool-btn">使用工具</button>
              </div>
            </div>
            
            {/* 示例工具卡片 2 */}
            <div className="tool-card">
              <div className="tool-card-header">
                <div className="tool-icon">
                  📝
                </div>
                <div className="tool-card-actions">
                  <button className="star-btn active" title="已收藏">⭐</button>
                  <button className="more-btn" title="更多">⋮</button>
                </div>
              </div>
              
              <div className="tool-card-content">
                <h3 className="tool-name">文本摘要</h3>
                <p className="tool-description">自动提取长篇文本的关键信息</p>
                <div className="tool-meta">
                  <span className="tool-category">文本处理</span>
                  <span className="tool-usage">使用次数: 96</span>
                </div>
              </div>
              
              <div className="tool-card-footer">
                <button className="use-tool-btn">使用工具</button>
              </div>
            </div>
            
            {/* 示例工具卡片 3 */}
            <div className="tool-card">
              <div className="tool-card-header">
                <div className="tool-icon">
                  🔧
                </div>
                <div className="tool-card-actions">
                  <button className="star-btn" title="收藏">⭐</button>
                  <button className="more-btn" title="更多">⋮</button>
                </div>
              </div>
              
              <div className="tool-card-content">
                <h3 className="tool-name">代码格式化</h3>
                <p className="tool-description">自动格式化多种编程语言的代码</p>
                <div className="tool-meta">
                  <span className="tool-category">开发工具</span>
                  <span className="tool-usage">使用次数: 87</span>
                </div>
              </div>
              
              <div className="tool-card-footer">
                <button className="use-tool-btn">使用工具</button>
              </div>
            </div>
            
            {/* 示例工具卡片 4 */}
            <div className="tool-card">
              <div className="tool-card-header">
                <div className="tool-icon">
                  🧮
                </div>
                <div className="tool-card-actions">
                  <button className="star-btn" title="收藏">⭐</button>
                  <button className="more-btn" title="更多">⋮</button>
                </div>
              </div>
              
              <div className="tool-card-content">
                <h3 className="tool-name">数据分析</h3>
                <p className="tool-description">快速分析CSV和Excel数据，生成统计结果</p>
                <div className="tool-meta">
                  <span className="tool-category">数据处理</span>
                  <span className="tool-usage">使用次数: 73</span>
                </div>
              </div>
              
              <div className="tool-card-footer">
                <button className="use-tool-btn">使用工具</button>
              </div>
            </div>
            
            {/* 示例工具卡片 5 */}
            <div className="tool-card">
              <div className="tool-card-header">
                <div className="tool-icon">
                  🧠
                </div>
                <div className="tool-card-actions">
                  <button className="star-btn active" title="已收藏">⭐</button>
                  <button className="more-btn" title="更多">⋮</button>
                </div>
              </div>
              
              <div className="tool-card-content">
                <h3 className="tool-name">内容生成</h3>
                <p className="tool-description">根据关键词和指令生成各种类型的内容</p>
                <div className="tool-meta">
                  <span className="tool-category">AI 增强</span>
                  <span className="tool-usage">使用次数: 156</span>
                </div>
              </div>
              
              <div className="tool-card-footer">
                <button className="use-tool-btn">使用工具</button>
              </div>
            </div>
            
            {/* 示例工具卡片 6 */}
            <div className="tool-card">
              <div className="tool-card-header">
                <div className="tool-icon">
                  ⚙️
                </div>
                <div className="tool-card-actions">
                  <button className="star-btn" title="收藏">⭐</button>
                  <button className="more-btn" title="更多">⋮</button>
                </div>
              </div>
              
              <div className="tool-card-content">
                <h3 className="tool-name">JSON 解析器</h3>
                <p className="tool-description">验证和格式化JSON数据，支持语法高亮</p>
                <div className="tool-meta">
                  <span className="tool-category">实用工具</span>
                  <span className="tool-usage">使用次数: 65</span>
                </div>
              </div>
              
              <div className="tool-card-footer">
                <button className="use-tool-btn">使用工具</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Tool;