import React, { useState } from 'react';
import { useI18n } from '../../hooks/useI18n';

const EmotionSettings = ({ settings, saveSettings, isLoading }) => {
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
    <div className="emotion-settings">
      <h3>{t('settings.emotion.title')}</h3>

      <div className="setting-group">
        <label className="setting-label">{t('settings.emotion.emotionRecognition')}</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.emotionRecognition}
              onChange={() => handleToggle('emotionRecognition')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">{t('settings.emotion.emotionRecognitionDesc')}</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">{t('settings.emotion.emotionResponse')}</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.emotionResponse}
              onChange={() => handleToggle('emotionResponse')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">{t('settings.emotion.emotionResponseDesc')}</span>
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">{t('settings.emotion.emotionMemory')}</label>
        <div className="toggle-option">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={localSettings.emotionMemory}
              onChange={() => handleToggle('emotionMemory')}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className="toggle-label">{t('settings.emotion.emotionMemoryDesc')}</span>
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

export default EmotionSettings;