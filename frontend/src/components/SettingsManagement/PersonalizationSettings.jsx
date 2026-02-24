import React, { useState } from 'react';

const PersonalizationSettings = ({ settings, saveSettings, isLoading }) => {
  const [localSettings, setLocalSettings] = useState(settings);

  const handleTraitChange = (trait, value) => {
    setLocalSettings(prev => ({
      ...prev,
      personalityTraits: {
        ...prev.personalityTraits,
        [trait]: value
      }
    }));
  };

  const handleStyleChange = (style) => {
    setLocalSettings(prev => ({
      ...prev,
      communicationStyle: style
    }));
  };

  const handleSpeedChange = (speed) => {
    setLocalSettings(prev => ({
      ...prev,
      responseSpeed: speed
    }));
  };

  const handleSave = async () => {
    const success = await saveSettings(localSettings);
    if (success) {
      alert('个性化设置保存成功！');
    } else {
      alert('保存失败，请重试。');
    }
  };

  return (
    <div className="personalization-settings">
      <h3>个性化</h3>
      
      <div className="setting-group">
        <label className="setting-label">个性特质</label>
        <div className="traits-container">
          {Object.entries(localSettings.personalityTraits).map(([trait, value]) => (
            <div key={trait} className="trait-item">
              <span className="trait-name">
                {trait.charAt(0).toUpperCase() + trait.slice(1)}
              </span>
              <input
                type="range"
                className="trait-slider"
                min="0"
                max="1"
                step="0.1"
                value={value}
                onChange={(e) => handleTraitChange(trait, parseFloat(e.target.value))}
              />
              <span className="trait-value">{value.toFixed(1)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">沟通风格</label>
        <div className="style-options">
          {
            [
              { value: 'formal', label: '正式' },
              { value: 'balanced', label: '平衡' },
              { value: 'casual', label: '随意' },
              { value: 'friendly', label: '友好' }
            ].map(style => (
              <label key={style.value} className="style-option">
                <input
                  type="radio"
                  name="communicationStyle"
                  value={style.value}
                  checked={localSettings.communicationStyle === style.value}
                  onChange={() => handleStyleChange(style.value)}
                />
                {style.label}
              </label>
            ))
          }
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">响应速度</label>
        <div className="speed-options">
          {
            [
              { value: 'fast', label: '快速' },
              { value: 'medium', label: '中等' },
              { value: 'slow', label: '缓慢' }
            ].map(speed => (
              <label key={speed.value} className="speed-option">
                <input
                  type="radio"
                  name="responseSpeed"
                  value={speed.value}
                  checked={localSettings.responseSpeed === speed.value}
                  onChange={() => handleSpeedChange(speed.value)}
                />
                {speed.label}
              </label>
            ))
          }
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

export default PersonalizationSettings;