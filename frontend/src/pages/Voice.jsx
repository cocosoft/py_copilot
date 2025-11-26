import React from 'react';
import './voice.css';

const Voice = () => {
  return (
    <div className="voice-container">
      <div className="voice-header">
        <h1>语音生成与管理</h1>
        <p>文本转语音和语音文件管理</p>
      </div>
      
      <div className="voice-content">
        <div className="voice-toolbar">
          <div className="text-to-speech">
            <label htmlFor="voice-text">输入文本</label>
            <textarea
              id="voice-text"
              placeholder="输入你想要转换为语音的文本..."
              className="text-input"
              rows="4"
            />
            
            <div className="voice-options">
              <div className="option-group">
                <label>语音类型</label>
                <select className="voice-select">
                  <option value="male">男声</option>
                  <option value="female">女声</option>
                  <option value="child">童声</option>
                  <option value="neutral">中性</option>
                </select>
              </div>
              
              <div className="option-group">
                <label>语速</label>
                <input 
                  type="range" 
                  min="0.5" 
                  max="2" 
                  step="0.1" 
                  defaultValue="1" 
                  className="speed-slider"
                />
                <span className="speed-value">1.0x</span>
              </div>
              
              <div className="option-group">
                <label>语调</label>
                <input 
                  type="range" 
                  min="0.5" 
                  max="2" 
                  step="0.1" 
                  defaultValue="1" 
                  className="pitch-slider"
                />
                <span className="pitch-value">1.0x</span>
              </div>
            </div>
            
            <div className="voice-actions">
              <button className="generate-btn">
                生成语音
              </button>
              <button className="preview-btn">
                预览
              </button>
            </div>
          </div>
        </div>
        
        <div className="voice-results">
          <div className="results-header">
            <h3>语音文件</h3>
            <div className="search-bar">
              <input 
                type="text" 
                placeholder="搜索语音文件..." 
                className="search-input"
              />
              <button className="search-btn">🔍</button>
            </div>
          </div>
          
          <div className="voice-list">
            {/* 示例语音文件 */}
            <div className="voice-item">
              <div className="voice-icon">🎵</div>
              <div className="voice-info">
                <h4>示例语音 1</h4>
                <p>这是一段示例语音内容的描述文本...</p>
                <span className="voice-duration">00:15</span>
              </div>
              <div className="voice-controls">
                <button className="play-btn">▶️</button>
                <button className="download-btn">💾</button>
                <button className="delete-btn">🗑️</button>
              </div>
            </div>
            
            <div className="voice-item">
              <div className="voice-icon">🎤</div>
              <div className="voice-info">
                <h4>示例语音 2</h4>
                <p>这是另一段示例语音内容的描述文本...</p>
                <span className="voice-duration">00:22</span>
              </div>
              <div className="voice-controls">
                <button className="play-btn">▶️</button>
                <button className="download-btn">💾</button>
                <button className="delete-btn">🗑️</button>
              </div>
            </div>
            
            <div className="voice-item">
              <div className="voice-icon">🎧</div>
              <div className="voice-info">
                <h4>示例语音 3</h4>
                <p>这是第三段示例语音内容的描述文本...</p>
                <span className="voice-duration">00:18</span>
              </div>
              <div className="voice-controls">
                <button className="play-btn">▶️</button>
                <button className="download-btn">💾</button>
                <button className="delete-btn">🗑️</button>
              </div>
            </div>
            
            <div className="voice-item">
              <div className="voice-icon">🔊</div>
              <div className="voice-info">
                <h4>示例语音 4</h4>
                <p>这是第四段示例语音内容的描述文本...</p>
                <span className="voice-duration">00:30</span>
              </div>
              <div className="voice-controls">
                <button className="play-btn">▶️</button>
                <button className="download-btn">💾</button>
                <button className="delete-btn">🗑️</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Voice;