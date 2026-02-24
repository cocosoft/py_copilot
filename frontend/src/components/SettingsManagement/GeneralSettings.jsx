import React, { useState } from 'react';

const GeneralSettings = ({ settings, saveSettings, isLoading }) => {
  const [localSettings, setLocalSettings] = useState(settings);

  const handleAssistantNameChange = (e) => {
    setLocalSettings(prev => ({
      ...prev,
      assistantName: e.target.value
    }));
  };

  const handleLanguageChange = (e) => {
    setLocalSettings(prev => ({
      ...prev,
      language: e.target.value
    }));
  };

  const handleThemeChange = (theme) => {
    setLocalSettings(prev => ({
      ...prev,
      theme: theme
    }));
  };

  const handleSave = async () => {
    const success = await saveSettings(localSettings);
    if (success) {
      alert('通用设置保存成功！');
    } else {
      alert('保存失败，请重试。');
    }
  };

  return (
    <div className="general-settings">
      <h3>常规</h3>
      
      <div className="setting-group">
        <label className="setting-label">助手名称</label>
        <input
          type="text"
          className="setting-input"
          value={localSettings.assistantName || 'Py Copilot'}
          onChange={handleAssistantNameChange}
          placeholder="输入助手名称"
        />
      </div>
      
      <div className="setting-group">
        <label className="setting-label">语言</label>
        <select
          className="setting-select"
          value={localSettings.language}
          onChange={handleLanguageChange}
        >
          <option value="zh-CN">简体中文</option>
          <option value="en-US">English</option>
          <option value="ja-JP">日本語</option>
          <option value="ko-KR">한국어</option>
        </select>
      </div>

      <div className="setting-group">
        <label className="setting-label">主题</label>
        <div className="theme-options">
          {
            [
              { value: 'light', label: '浅色' },
              { value: 'dark', label: '深色' },
              { value: 'system', label: '跟随系统' }
            ].map(theme => (
              <label key={theme.value} className="theme-option">
                <input
                  type="radio"
                  name="theme"
                  value={theme.value}
                  checked={localSettings.theme === theme.value}
                  onChange={() => handleThemeChange(theme.value)}
                />
                {theme.label}
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

export default GeneralSettings;