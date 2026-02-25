import React, { useState } from 'react';
import { useI18n } from '../../hooks/useI18n';

const GeneralSettings = ({ settings, saveSettings, isLoading }) => {
  const { t, i18n, changeLanguage } = useI18n();
  const [localSettings, setLocalSettings] = useState(settings);

  const handleAssistantNameChange = (e) => {
    setLocalSettings(prev => ({
      ...prev,
      assistantName: e.target.value
    }));
  };

  const handleLanguageChange = (e) => {
    const newLang = e.target.value;
    setLocalSettings(prev => ({
      ...prev,
      language: newLang
    }));
    changeLanguage(newLang);
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
      alert(t('common.success'));
    } else {
      alert(t('common.error'));
    }
  };

  return (
    <div className="general-settings">
      <h3>{t('settings.general.title')}</h3>

      <div className="setting-group">
        <label className="setting-label">{t('settings.general.assistantName')}</label>
        <input
          type="text"
          className="setting-input"
          value={localSettings.assistantName || 'Py Copilot'}
          onChange={handleAssistantNameChange}
          placeholder={t('settings.general.assistantName')}
        />
      </div>

      <div className="setting-group">
        <label className="setting-label">{t('settings.general.language')}</label>
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
        <label className="setting-label">{t('settings.general.theme')}</label>
        <div className="theme-options">
          {
            [
              { value: 'light', label: t('settings.general.themeLight') },
              { value: 'dark', label: t('settings.general.themeDark') },
              { value: 'system', label: t('settings.general.themeSystem') }
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
          {t('common.save')}
        </button>
      </div>
    </div>
  );
};

export default GeneralSettings;