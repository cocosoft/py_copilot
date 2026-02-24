import React, { useState } from 'react';

const RelationshipSettings = ({ settings, saveSettings, isLoading }) => {
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
      alert('关系设置保存成功！');
    } else {
      alert('保存失败，请重试。');
    }
  };

  return (
    <div className="relationship-settings">
      <h3>关系</h3>
      
      <div className="setting-group">
        <label className="setting-label">关系记忆</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.relationshipMemory}
              onChange={() => handleToggle('relationshipMemory')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手记住重要的人际关系</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">里程碑提醒</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.milestoneReminders}
              onChange={() => handleToggle('milestoneReminders')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手提醒重要的关系里程碑</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">关系洞察</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.relationshipInsights}
              onChange={() => handleToggle('relationshipInsights')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">允许助手提供关系管理的洞察</span>
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

export default RelationshipSettings;