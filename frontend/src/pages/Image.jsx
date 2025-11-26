import React from 'react';
import './image.css';

const Image = () => {
  return (
    <div className="image-container">
      <div className="image-header">
        <h1>图像生成与管理</h1>
        <p>创建和管理AI生成的图像</p>
      </div>
      
      <div className="image-content">
        <div className="image-toolbar">
          <div className="prompt-section">
            <label htmlFor="image-prompt">图像描述</label>
            <textarea
              id="image-prompt"
              placeholder="输入你想要生成的图像描述..."
              className="prompt-input"
              rows="3"
            />
            
            <div className="generation-options">
              <div className="option-group">
                <label>风格选择</label>
                <select className="style-select">
                  <option value="realistic">写实风格</option>
                  <option value="cartoon">卡通风格</option>
                  <option value="anime">动漫风格</option>
                  <option value="abstract">抽象风格</option>
                  <option value="sketch">素描风格</option>
                </select>
              </div>
              
              <div className="option-group">
                <label>图像尺寸</label>
                <select className="size-select">
                  <option value="1:1">1:1 (方形)</option>
                  <option value="16:9">16:9 (宽屏)</option>
                  <option value="9:16">9:16 (竖屏)</option>
                  <option value="4:3">4:3 (标准)</option>
                </select>
              </div>
            </div>
            
            <button className="generate-btn">
              生成图像
            </button>
          </div>
        </div>
        
        <div className="image-results">
          <div className="results-header">
            <h3>生成历史</h3>
            <div className="view-options">
              <button className="view-btn active">网格视图</button>
              <button className="view-btn">列表视图</button>
            </div>
          </div>
          
          <div className="image-grid">
            {/* 示例图像 */}
            <div className="image-item">
              <div className="image-thumbnail">
                <div className="image-placeholder">🖼️</div>
              </div>
              <div className="image-info">
                <p className="image-description">美丽的山水画</p>
                <div className="image-actions">
                  <button className="action-icon">👁️</button>
                  <button className="action-icon">💾</button>
                  <button className="action-icon">🗑️</button>
                </div>
              </div>
            </div>
            
            <div className="image-item">
              <div className="image-thumbnail">
                <div className="image-placeholder">🏞️</div>
              </div>
              <div className="image-info">
                <p className="image-description">未来城市夜景</p>
                <div className="image-actions">
                  <button className="action-icon">👁️</button>
                  <button className="action-icon">💾</button>
                  <button className="action-icon">🗑️</button>
                </div>
              </div>
            </div>
            
            <div className="image-item">
              <div className="image-thumbnail">
                <div className="image-placeholder">🐱</div>
              </div>
              <div className="image-info">
                <p className="image-description">可爱的猫咪</p>
                <div className="image-actions">
                  <button className="action-icon">👁️</button>
                  <button className="action-icon">💾</button>
                  <button className="action-icon">🗑️</button>
                </div>
              </div>
            </div>
            
            <div className="image-item">
              <div className="image-thumbnail">
                <div className="image-placeholder">🚀</div>
              </div>
              <div className="image-info">
                <p className="image-description">太空火箭发射</p>
                <div className="image-actions">
                  <button className="action-icon">👁️</button>
                  <button className="action-icon">💾</button>
                  <button className="action-icon">🗑️</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Image;