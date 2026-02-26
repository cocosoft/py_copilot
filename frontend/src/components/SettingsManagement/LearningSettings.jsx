import React, { useState } from 'react';
import { useI18n } from '../../hooks/useI18n';

const LearningSettings = ({ settings, saveSettings, isLoading }) => {
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
    <div className="learning-settings">
      <h3>{t('settings.learning.title')}</h3>

      <div className="setting-group">
        <label className="setting-label">{t('settings.learning.adaptiveLearning')}</label>
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={localSettings.adaptiveLearning}
            onChange={() => handleToggle('adaptiveLearning')}
          />
          <span className="toggle-slider"></span>
        </label>
        <span className="toggle-label">{t('settings.learning.adaptiveLearningDesc')}</span>
      </div>

      <div className="setting-group">
        <label className="setting-label">{t('settings.learning.patternRecognition')}</label>
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={localSettings.patternRecognition}
            onChange={() => handleToggle('patternRecognition')}
          />
          <span className="toggle-slider"></span>
        </label>
        <span className="toggle-label">{t('settings.learning.patternRecognitionDesc')}</span>
      </div>

      <div className="setting-group">
        <label className="setting-label">{t('settings.learning.predictiveSuggestions')}</label>
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={localSettings.predictiveSuggestions}
            onChange={() => handleToggle('predictiveSuggestions')}
          />
          <span className="toggle-slider"></span>
        </label>
        <span className="toggle-label">{t('settings.learning.predictiveSuggestionsDesc')}</span>
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

export default LearningSettings;