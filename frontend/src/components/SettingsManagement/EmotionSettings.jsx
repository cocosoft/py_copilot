import React, { useState } from 'react';

const EmotionSettings = ({ settings, saveSettings, isLoading }) => {
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
      alert('情感设置保存成功！');
    } else {
      alert('保存失败，请重试。');
    }
  };

  return (
    <div className="emotion-settings">
      <h3>情感</h3>
      
      <div className="setting-group">
        <label className="setting-label">情感识别</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.emotionRecognition}
              onChange={() => handleToggle('emotionRecognition')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手识别您的情绪状态</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">情感回应</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.emotionResponse}
              onChange={() => handleToggle('emotionResponse')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手根据您的情绪调整回应方式</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">情感记忆</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.emotionMemory}
              onChange={() => handleToggle('emotionMemory')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手记住您的情绪模式</span>
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

export default EmotionSettings;