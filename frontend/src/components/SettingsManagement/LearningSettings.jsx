import React, { useState } from 'react';

const LearningSettings = ({ settings, saveSettings, isLoading }) => {
  const [localSettings, setLocalSettings] = useState(settings);

  const handleToggle = (setting) => {
    setLocalSettings(prev => ({
      ...prev,
      [setting]: !prev[setting]
    }));
  };

  const handleSave = async () => {
    const success = await saveSettings(localSettings);
    if (success) {
      alert('学习设置保存成功！');
    } else {
      alert('保存失败，请重试。');
    }
  };

  return (
    <div className="learning-settings">
      <h3>学习</h3>
      
      <div className="setting-group">
        <label className="setting-label">自适应学习</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.adaptiveLearning}
              onChange={() => handleToggle('adaptiveLearning')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手从您的交互中学习</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">模式识别</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.patternRecognition}
              onChange={() => handleToggle('patternRecognition')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手识别您的行为模式</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">预测建议</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.predictiveSuggestions}
              onChange={() => handleToggle('predictiveSuggestions')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手主动提供预测性建议</span>
        </div>
      </div>

      <div className="setting-actions">
        <button 
          className="save-button"
          onClick={handleSave}
          disabled={isLoading}
        >
          保存设置
        </button>
      </div>
    </div>
  );
};

export default LearningSettings;