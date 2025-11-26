import React from 'react';
import './video.css';

const Video = () => {
  return (
    <div className="video-container">
      <div className="video-header">
        <h1>视频生成与管理</h1>
        <p>创建和管理AI生成的视频</p>
      </div>
      
      <div className="video-content">
        <div className="video-toolbar">
          <div className="prompt-section">
            <label htmlFor="video-prompt">视频描述</label>
            <textarea
              id="video-prompt"
              placeholder="输入你想要生成的视频描述..."
              className="prompt-input"
              rows="3"
            />
            
            <div className="generation-options">
              <div className="option-group">
                <label>视频风格</label>
                <select className="style-select">
                  <option value="realistic">写实风格</option>
                  <option value="cartoon">卡通风格</option>
                  <option value="anime">动漫风格</option>
                  <option value="abstract">抽象风格</option>
                  <option value="cinematic">电影风格</option>
                </select>
              </div>
              
              <div className="option-group">
                <label>视频时长</label>
                <select className="duration-select">
                  <option value="5">5秒</option>
                  <option value="10">10秒</option>
                  <option value="15">15秒</option>
                  <option value="30">30秒</option>
                </select>
              </div>
              
              <div className="option-group">
                <label>分辨率</label>
                <select className="resolution-select">
                  <option value="720p">720p (高清)</option>
                  <option value="1080p">1080p (全高清)</option>
                  <option value="4k">4K (超清)</option>
                </select>
              </div>
            </div>
            
            <button className="generate-btn">
              生成视频
            </button>
          </div>
        </div>
        
        <div className="video-results">
          <div className="results-header">
            <h3>生成历史</h3>
            <div className="view-options">
              <button className="view-btn active">网格视图</button>
              <button className="view-btn">列表视图</button>
            </div>
          </div>
          
          <div className="video-grid">
            {/* 示例视频 */}
            <div className="video-item">
              <div className="video-thumbnail">
                <div className="video-placeholder">🎬</div>
                <div className="video-duration">00:15</div>
              </div>
              <div className="video-info">
                <p className="video-description">山水风景视频</p>
                <div className="video-actions">
                  <button className="action-icon">▶️</button>
                  <button className="action-icon">💾</button>
                  <button className="action-icon">🗑️</button>
                </div>
              </div>
            </div>
            
            <div className="video-item">
              <div className="video-thumbnail">
                <div className="video-placeholder">🚗</div>
                <div className="video-duration">00:10</div>
              </div>
              <div className="video-info">
                <p className="video-description">赛车场景</p>
                <div className="video-actions">
                  <button className="action-icon">▶️</button>
                  <button className="action-icon">💾</button>
                  <button className="action-icon">🗑️</button>
                </div>
              </div>
            </div>
            
            <div className="video-item">
              <div className="video-thumbnail">
                <div className="video-placeholder">🏙️</div>
                <div className="video-duration">00:20</div>
              </div>
              <div className="video-info">
                <p className="video-description">城市延时摄影</p>
                <div className="video-actions">
                  <button className="action-icon">▶️</button>
                  <button className="action-icon">💾</button>
                  <button className="action-icon">🗑️</button>
                </div>
              </div>
            </div>
            
            <div className="video-item">
              <div className="video-thumbnail">
                <div className="video-placeholder">🐬</div>
                <div className="video-duration">00:08</div>
              </div>
              <div className="video-info">
                <p className="video-description">海底世界</p>
                <div className="video-actions">
                  <button className="action-icon">▶️</button>
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

export default Video;