import React from 'react';
import './translate.css';

const Translate = () => {
  return (
    <div className="translate-container">
      <div className="translate-header">
        <h1>多语言翻译</h1>
        <p>支持多种语言之间的文本翻译</p>
      </div>
      
      <div className="translate-content">
        <div className="translate-main">
          <div className="translate-panel">
            {/* 源语言输入区域 */}
            <div className="language-panel source-panel">
              <div className="panel-header">
                <select className="language-select">
                  <option value="auto">自动检测</option>
                  <option value="zh-CN">中文</option>
                  <option value="en-US">英语</option>
                  <option value="ja-JP">日语</option>
                  <option value="ko-KR">韩语</option>
                  <option value="fr-FR">法语</option>
                  <option value="de-DE">德语</option>
                  <option value="es-ES">西班牙语</option>
                  <option value="ru-RU">俄语</option>
                </select>
                <div className="panel-actions">
                  <button className="action-btn" title="清空">🗑️</button>
                  <button className="action-btn" title="粘贴">📋</button>
                  <button className="action-btn" title="语音输入">🎤</button>
                </div>
              </div>
              <textarea
                className="translate-textarea source-textarea"
                placeholder="请输入要翻译的文本..."
                rows={8}
              />
            </div>
            
            {/* 交换语言按钮 */}
            <button className="swap-btn" title="交换语言">
              ⇅
            </button>
            
            {/* 目标语言输出区域 */}
            <div className="language-panel target-panel">
              <div className="panel-header">
                <select className="language-select">
                  <option value="zh-CN">中文</option>
                  <option value="en-US">英语</option>
                  <option value="ja-JP">日语</option>
                  <option value="ko-KR">韩语</option>
                  <option value="fr-FR">法语</option>
                  <option value="de-DE">德语</option>
                  <option value="es-ES">西班牙语</option>
                  <option value="ru-RU">俄语</option>
                </select>
                <div className="panel-actions">
                  <button className="action-btn" title="复制">📋</button>
                  <button className="action-btn" title="语音朗读">🔊</button>
                </div>
              </div>
              <div className="translate-result">
                <p className="result-text">翻译结果将显示在这里...</p>
              </div>
            </div>
          </div>
          
          {/* 翻译按钮 */}
          <button className="translate-btn">
            立即翻译
          </button>
        </div>
        
        <div className="translate-sidebar">
          <div className="history-header">
            <h3>翻译历史</h3>
            <button className="clear-history-btn" title="清空历史">
              🗑️
            </button>
          </div>
          
          <div className="history-list">
            {/* 示例翻译历史 */}
            <div className="history-item">
              <div className="history-source">你好，世界！</div>
              <div className="history-target">Hello, world!</div>
              <div className="history-language">中文 → 英语</div>
            </div>
            
            <div className="history-item">
              <div className="history-source">こんにちは</div>
              <div className="history-target">你好</div>
              <div className="history-language">日语 → 中文</div>
            </div>
            
            <div className="history-item">
              <div className="history-source">How are you?</div>
              <div className="history-target">你好吗？</div>
              <div className="history-language">英语 → 中文</div>
            </div>
            
            <div className="history-item">
              <div className="history-source">Bonjour</div>
              <div className="history-target">Hello</div>
              <div className="history-language">法语 → 英语</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Translate;