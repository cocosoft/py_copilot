import React, { useState } from 'react';
import { useI18n } from '../../hooks/useI18n';

const PersonalizationSettings = ({ settings, saveSettings, isLoading }) => {
  const { t } = useI18n();
  const [localSettings, setLocalSettings] = useState({
    personalityTraits: {
      friendly: 0.8,
      professional: 0.7,
      humorous: 0.5,
      empathetic: 0.7,
      creative: 0.6
    },
    communicationStyle: 'balanced',
    responseSpeed: 'medium',
    customPrompt: '',
    ...settings
  });

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

  const handleCustomPromptChange = (e) => {
    setLocalSettings(prev => ({
      ...prev,
      customPrompt: e.target.value
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
    <div className="personalization-settings">
      <h3>{t('settings.personalization.title')}</h3>
      
      <div className="setting-group">
        <label className="setting-label">{t('settings.personalization.personalityTraits')}</label>
        <div className="traits-container">
          {Object.entries(localSettings.personalityTraits).map(([trait, value]) => (
            <div key={trait} className="trait-item">
              <span className="trait-name">
                {t(`settings.personalization.traits.${trait}`)}
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
        <label className="setting-label">{t('settings.personalization.communicationStyle')}</label>
        <div className="style-options">
          {
            [
              { value: 'formal', label: t('settings.personalization.styles.formal') },
              { value: 'balanced', label: t('settings.personalization.styles.balanced') },
              { value: 'casual', label: t('settings.personalization.styles.casual') },
              { value: 'friendly', label: t('settings.personalization.styles.friendly') }
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
        <label className="setting-label">{t('settings.personalization.responseSpeed')}</label>
        <div className="speed-options">
          {
            [
              { value: 'fast', label: t('settings.personalization.speeds.fast') },
              { value: 'medium', label: t('settings.personalization.speeds.medium') },
              { value: 'slow', label: t('settings.personalization.speeds.slow') }
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

      <div className="setting-group">
        <label className="setting-label">{t('settings.personalization.customPrompt')}</label>
        <p className="setting-description">
          {t('settings.personalization.customPromptDescription')}
        </p>
        <textarea
          className="custom-prompt-textarea"
          value={localSettings.customPrompt || ''}
          onChange={handleCustomPromptChange}
          placeholder={t('settings.personalization.customPromptPlaceholder')}
          rows={6}
        />
        <p className="setting-hint">
          {t('settings.personalization.customPromptHint')}
        </p>
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

export default PersonalizationSettings;