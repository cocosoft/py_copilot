import React, { useState, useEffect } from 'react';
import PersonalizationSettings from './PersonalizationSettings';
import EmotionSettings from './EmotionSettings';
import LearningSettings from './LearningSettings';
import RelationshipSettings from './RelationshipSettings';
import GeneralSettings from './GeneralSettings';
import MCPSettings from '../MCPSettings';
import { useI18n } from '../../hooks/useI18n';
import { request } from '../../utils/api';
import './settings.css';

const SettingsManager = () => {
  const { t, changeLanguage } = useI18n();
  const [activeTab, setActiveTab] = useState('general');
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState({
    general: {
      assistantName: 'Py Copilot',
      language: localStorage.getItem('app-language') || 'zh-CN',
      theme: 'light'
    },
    personalization: {
      personalityTraits: {
        friendly: 0.8,
        professional: 0.7,
        humorous: 0.5,
        empathetic: 0.7,
        creative: 0.6
      },
      communicationStyle: 'balanced',
      responseSpeed: 'medium',
      customPrompt: ''
    },
    emotion: {
      emotionRecognition: true,
      emotionResponse: true,
      emotionMemory: true
    },
    learning: {
      adaptiveLearning: true,
      patternRecognition: true,
      predictiveSuggestions: true
    },
    relationship: {
      relationshipMemory: true,
      milestoneReminders: true,
      relationshipInsights: true
    }
  });

  useEffect(() => {
    // 加载设置
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      // 从后端 API 加载设置
      const result = await request('/v1/settings', {
        method: 'GET'
      });

      if (result.success && result.data) {
        setSettings(prev => ({
          ...prev,
          ...result.data
        }));

        // 同步语言设置到 i18n
        if (result.data.general?.language) {
          changeLanguage(result.data.general.language);
        }
      }
    } catch (error) {
      console.error('加载设置失败:', error);
      // 如果 API 调用失败，使用 localStorage 作为备选
      const savedLanguage = localStorage.getItem('app-language');
      if (savedLanguage) {
        setSettings(prev => ({
          ...prev,
          general: {
            ...prev.general,
            language: savedLanguage
          }
        }));
        changeLanguage(savedLanguage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async (settingType, settingData) => {
    setIsLoading(true);
    try {
      // 调用后端 API 保存设置
      const result = await request('/v1/settings', {
        method: 'POST',
        data: {
          type: settingType,
          data: settingData
        }
      });

      if (result.success) {
        // 更新本地设置
        setSettings(prev => ({
          ...prev,
          [settingType]: settingData
        }));

        // 如果是通用设置且语言发生变化，同步更新 i18n 语言和 localStorage
        if (settingType === 'general' && settingData.language) {
          changeLanguage(settingData.language);
          localStorage.setItem('app-language', settingData.language);
        }

        return true;
      } else {
        console.error('保存设置失败:', result.message);
        return false;
      }
    } catch (error) {
      console.error('保存设置失败:', error);
      // API 调用失败时，仍然更新本地状态和 localStorage
      setSettings(prev => ({
        ...prev,
        [settingType]: settingData
      }));

      if (settingType === 'general' && settingData.language) {
        changeLanguage(settingData.language);
        localStorage.setItem('app-language', settingData.language);
      }

      return true; // 本地保存成功
    } finally {
      setIsLoading(false);
    }
  };

  // 导出设置为MD文件
  const exportSettings = () => {
    // 构建MD内容
    let mdContent = `# ${t('settings.settingsManager.export.title')}

## ${t('settings.settingsManager.export.exportTime')}
${new Date().toLocaleString()}

`;

    // 通用设置
    mdContent += `## ${t('settings.settingsManager.export.general')}

`;
    mdContent += `- ${t('settings.settingsManager.export.assistantName')}: ${settings.general.assistantName}
`;
    mdContent += `- ${t('settings.settingsManager.export.language')}: ${settings.general.language === 'zh-CN' ? t('settings.settingsManager.export.zhCN') : t('settings.settingsManager.export.enUS')}
`;
    mdContent += `- ${t('settings.settingsManager.export.theme')}: ${settings.general.theme === 'light' ? t('settings.settingsManager.export.light') : t('settings.settingsManager.export.dark')}

`;

    // 个性化设置
    mdContent += `## ${t('settings.settingsManager.export.personalization')}

`;
    mdContent += `### ${t('settings.settingsManager.export.personalityTraits')}
`;
    mdContent += `- ${t('settings.settingsManager.export.friendly')}: ${(settings.personalization.personalityTraits.friendly * 100).toFixed(0)}%
`;
    mdContent += `- ${t('settings.settingsManager.export.professional')}: ${(settings.personalization.personalityTraits.professional * 100).toFixed(0)}%
`;
    mdContent += `- ${t('settings.settingsManager.export.humorous')}: ${(settings.personalization.personalityTraits.humorous * 100).toFixed(0)}%
`;
    mdContent += `- ${t('settings.settingsManager.export.empathetic')}: ${(settings.personalization.personalityTraits.empathetic * 100).toFixed(0)}%
`;
    mdContent += `- ${t('settings.settingsManager.export.creative')}: ${(settings.personalization.personalityTraits.creative * 100).toFixed(0)}%

`;
    const communicationStyle = settings.personalization.communicationStyle;
    let styleText = t('settings.settingsManager.export.balanced');
    if (communicationStyle === 'formal') styleText = t('settings.settingsManager.export.formal');
    else if (communicationStyle === 'informal') styleText = t('settings.settingsManager.export.informal');
    mdContent += `- ${t('settings.settingsManager.export.communicationStyle')}: ${styleText}
`;
    const responseSpeed = settings.personalization.responseSpeed;
    let speedText = t('settings.settingsManager.export.medium');
    if (responseSpeed === 'fast') speedText = t('settings.settingsManager.export.fast');
    else if (responseSpeed === 'slow') speedText = t('settings.settingsManager.export.slow');
    mdContent += `- ${t('settings.settingsManager.export.responseSpeed')}: ${speedText}

`;

    // 情感设置
    mdContent += `## ${t('settings.settingsManager.export.emotion')}

`;
    mdContent += `- ${t('settings.settingsManager.export.emotionRecognition')}: ${settings.emotion.emotionRecognition ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}
`;
    mdContent += `- ${t('settings.settingsManager.export.emotionResponse')}: ${settings.emotion.emotionResponse ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}
`;
    mdContent += `- ${t('settings.settingsManager.export.emotionMemory')}: ${settings.emotion.emotionMemory ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}

`;

    // 学习设置
    mdContent += `## ${t('settings.settingsManager.export.learning')}

`;
    mdContent += `- ${t('settings.settingsManager.export.adaptiveLearning')}: ${settings.learning.adaptiveLearning ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}
`;
    mdContent += `- ${t('settings.settingsManager.export.patternRecognition')}: ${settings.learning.patternRecognition ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}
`;
    mdContent += `- ${t('settings.settingsManager.export.predictiveSuggestions')}: ${settings.learning.predictiveSuggestions ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}

`;

    // 关系设置
    mdContent += `## ${t('settings.settingsManager.export.relationship')}

`;
    mdContent += `- ${t('settings.settingsManager.export.relationshipMemory')}: ${settings.relationship.relationshipMemory ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}
`;
    mdContent += `- ${t('settings.settingsManager.export.milestoneReminders')}: ${settings.relationship.milestoneReminders ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}
`;
    mdContent += `- ${t('settings.settingsManager.export.relationshipInsights')}: ${settings.relationship.relationshipInsights ? t('settings.settingsManager.export.enabled') : t('settings.settingsManager.export.disabled')}

`;

    // 添加JSON格式的设置数据（用于导入）
    mdContent += `## ${t('settings.settingsManager.export.jsonData')}

json
${JSON.stringify(settings, null, 2)}

`;

    // 创建Blob对象并下载
    const blob = new Blob([mdContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `assistant-settings-${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 导入设置从MD文件
  const importSettings = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        // 提取JSON格式的设置数据
        const jsonMatch = content.match(/```json[\s\S]*?```/);
        if (jsonMatch) {
          const jsonContent = jsonMatch[0].replace(/```json|```/g, '').trim();
          const importedSettings = JSON.parse(jsonContent);
          // 更新本地设置
          setSettings(importedSettings);
          // 保存到后端
          Object.keys(importedSettings).forEach(type => {
            saveSettings(type, importedSettings[type]);
          });
          alert(t('settings.settingsManager.messages.importSuccess'));
        } else {
          alert(t('settings.settingsManager.messages.importError'));
        }
      } catch (error) {
        console.error('导入设置失败:', error);
        alert(t('settings.settingsManager.messages.importFailed'));
      }
    };
    reader.onerror = () => {
      alert(t('settings.settingsManager.messages.readFileFailed'));
    };
    reader.readAsText(file);
  };

  const renderSettingsTab = () => {
    switch (activeTab) {
      case 'general':
        return <GeneralSettings 
          settings={settings.general} 
          saveSettings={(data) => saveSettings('general', data)} 
          isLoading={isLoading} 
        />;
      case 'personalization':
        return <PersonalizationSettings 
          settings={settings.personalization} 
          saveSettings={(data) => saveSettings('personalization', data)} 
          isLoading={isLoading} 
        />;
      case 'emotion':
        return <EmotionSettings 
          settings={settings.emotion} 
          saveSettings={(data) => saveSettings('emotion', data)} 
          isLoading={isLoading} 
        />;
      case 'learning':
        return <LearningSettings 
          settings={settings.learning} 
          saveSettings={(data) => saveSettings('learning', data)} 
          isLoading={isLoading} 
        />;
      case 'relationship':
        return <RelationshipSettings 
          settings={settings.relationship} 
          saveSettings={(data) => saveSettings('relationship', data)} 
          isLoading={isLoading} 
        />;
      case 'mcp':
        return <MCPSettings />;
      default:
        return <GeneralSettings 
          settings={settings.general} 
          saveSettings={(data) => saveSettings('general', data)} 
          isLoading={isLoading} 
        />;
    }
  };

  // 导出配置到JSON文件
  const exportConfigToFile = async () => {
    try {
      const result = await request('/v1/config/export', {
        method: 'GET'
      });

      if (result.success) {
        alert(`配置导出成功！\n文件路径: ${result.file_path}\n导出类型: ${result.exported_types.join(', ')}`);
      } else {
        alert(`配置导出失败: ${result.message}`);
      }
    } catch (error) {
      console.error('导出配置失败:', error);
      alert(t('settings.settingsManager.messages.exportFailed'));
    }
  };

  // 从JSON文件导入配置
  const importConfigFromFile = async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        const text = await file.text();
        const configData = JSON.parse(text);

        const result = await request('/v1/config/import', {
          method: 'POST',
          data: {
            config_data: configData,
            mode: 'merge'
          }
        });

        if (result.success) {
          alert(`配置导入成功！\n导入类型: ${result.imported_types.join(', ')}`);
          loadSettings();
        } else {
          alert(`配置导入失败: ${result.message}`);
        }
      } catch (error) {
        console.error('导入配置失败:', error);
        alert(t('settings.settingsManager.messages.configImportFailed'));
      }
    };
    input.click();
  };

  // 获取配置状态
  const [configStatus, setConfigStatus] = useState(null);

  const loadConfigStatus = async () => {
    try {
      const result = await request('/v1/config/status', {
        method: 'GET'
      });
      setConfigStatus(result);
    } catch (error) {
      console.error('获取配置状态失败:', error);
    }
  };

  useEffect(() => {
    loadConfigStatus();
  }, []);

  return (
    <div className="settings-manager">
      <div className="settings-header">
        <h2>{t('settings.title')}</h2>
        <div className="settings-actions">
          <button
            className="settings-action-btn"
            onClick={exportConfigToFile}
            title="导出配置到JSON文件"
          >
            {t('common.export')}JSON
          </button>
          <button
            className="settings-action-btn"
            onClick={importConfigFromFile}
            title="从JSON文件导入配置"
          >
            {t('common.import')}JSON
          </button>
          <button
            className="settings-action-btn export-btn"
            onClick={exportSettings}
            title="导出设置为MD文件"
          >
            {t('common.export')}MD
          </button>
          <label
            className="settings-action-btn import-btn"
            title="从MD文件导入设置"
          >
            {t('common.import')}MD
            <input
              type="file"
              accept=".md,.markdown"
              onChange={importSettings}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>
      
      <div className="settings-nav">
        <button
          className={`settings-nav-item ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          {t('settings.general.title')}
        </button>
        <button
          className={`settings-nav-item ${activeTab === 'personalization' ? 'active' : ''}`}
          onClick={() => setActiveTab('personalization')}
        >
          {t('settings.personalization.title')}
        </button>
        <button
          className={`settings-nav-item ${activeTab === 'emotion' ? 'active' : ''}`}
          onClick={() => setActiveTab('emotion')}
        >
          {t('settings.emotion.title')}
        </button>
        <button
          className={`settings-nav-item ${activeTab === 'learning' ? 'active' : ''}`}
          onClick={() => setActiveTab('learning')}
        >
          {t('settings.learning.title')}
        </button>
        <button
          className={`settings-nav-item ${activeTab === 'relationship' ? 'active' : ''}`}
          onClick={() => setActiveTab('relationship')}
        >
          {t('settings.relationship.title')}
        </button>
        <button
          className={`settings-nav-item ${activeTab === 'mcp' ? 'active' : ''}`}
          onClick={() => setActiveTab('mcp')}
        >
          MCP 服务
        </button>
      </div>
      
      <div className="settings-content">
        {isLoading && <div className="settings-loading">加载中...</div>}
        {!isLoading && renderSettingsTab()}
      </div>
    </div>
  );
};

export default SettingsManager;