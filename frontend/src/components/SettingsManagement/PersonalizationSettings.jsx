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
        <label className="setting-label">{t('settings.personalization.communicationStyle')}</label>
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
        <label className="setting-label">{t('settings.personalization.responseSpeed')}</label>
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

      <div className="setting-group">
        <label className="setting-label">{t('settings.personalization.customPrompt')}</label>
        <p className="setting-description">
          为您的智能助手编写个性化的提示词，用于定义助手的行为方式、回答风格，专业领域等
        </p>
        <textarea
          className="custom-prompt-textarea"
          value={localSettings.customPrompt || ''}
          onChange={handleCustomPromptChange}
          placeholder="例如：你是一位专业的技术顾问，擅长用通俗易懂的语言解释复杂的技术概念..."
          rows={6}
        />
        <p className="setting-hint">
          提示：这里的内容将作为系统提示词的一部分，影响助手的回答方式
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