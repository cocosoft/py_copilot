import React, { useState } from 'react';
import { useI18n } from '../../hooks/useI18n';

const RelationshipSettings = ({ settings, saveSettings, isLoading }) => {
  const { t } = useI18n();
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
      alert(t('common.success'));
    } else {
      alert(t('common.error'));
    }
  };

  return (
    <div className="relationship-settings">
      <h3>{t('settings.relationship.title')}</h3>

      <div className="setting-group">
        <label className="setting-label">{t('settings.relationship.relationshipMemory')}</label>
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

      <div className="setting-group">
        <label className="setting-label">{t('settings.relationship.milestoneReminders')}</label>
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

      <div className="setting-group">
        <label className="setting-label">{t('settings.relationship.relationshipInsights')}</label>
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

export default RelationshipSettings;