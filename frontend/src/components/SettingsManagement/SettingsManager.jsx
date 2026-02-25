import React, { useState, useEffect } from 'react';
import PersonalizationSettings from './PersonalizationSettings';
import EmotionSettings from './EmotionSettings';
import LearningSettings from './LearningSettings';
import RelationshipSettings from './RelationshipSettings';
import GeneralSettings from './GeneralSettings';
import { useI18n } from '../../hooks/useI18n';
import { request } from '../../utils/api';
import './settings.css';

const SettingsManager = () => {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState('general');
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState({
    general: {
      assistantName: 'Py Copilot',
      language: 'zh-CN',
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
      // 使用本地默认设置，避免API调用
      console.log('使用本地默认设置');
      // 模拟加载延迟
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('加载设置失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async (settingType, settingData) => {
    setIsLoading(true);
    try {
      // 只更新本地设置，避免API调用
      console.log('保存设置到本地:', settingType, settingData);
      // 模拟保存延迟
      await new Promise(resolve => setTimeout(resolve, 300));
      // 更新本地设置
      setSettings(prev => ({
        ...prev,
        [settingType]: settingData
      }));
      return true;
    } catch (error) {
      console.error('保存设置失败:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // 导出设置为MD文件
  const exportSettings = () => {
    // 构建MD内容
    let mdContent = `# 智能个人助手设置

## 导出时间
${new Date().toLocaleString()}

`;

    // 通用设置
    mdContent += `## 通用设置

`;
    mdContent += `- 助手名称: ${settings.general.assistantName}
`;
    mdContent += `- 语言: ${settings.general.language === 'zh-CN' ? '简体中文' : 'English'}
`;
    mdContent += `- 主题: ${settings.general.theme === 'light' ? '浅色' : '深色'}

`;

    // 个性化设置
    mdContent += `## 个性化设置

`;
    mdContent += `### 个性特质
`;
    mdContent += `- 友好度: ${(settings.personalization.personalityTraits.friendly * 100).toFixed(0)}%
`;
    mdContent += `- 专业度: ${(settings.personalization.personalityTraits.professional * 100).toFixed(0)}%
`;
    mdContent += `- 幽默感: ${(settings.personalization.personalityTraits.humorous * 100).toFixed(0)}%
`;
    mdContent += `- 同理心: ${(settings.personalization.personalityTraits.empathetic * 100).toFixed(0)}%
`;
    mdContent += `- 创造力: ${(settings.personalization.personalityTraits.creative * 100).toFixed(0)}%

`;
    mdContent += `- 沟通风格: ${settings.personalization.communicationStyle === 'balanced' ? '平衡' : settings.personalization.communicationStyle === 'formal' ? '正式' : '非正式'}
`;
    mdContent += `- 响应速度: ${settings.personalization.responseSpeed === 'fast' ? '快速' : settings.personalization.responseSpeed === 'medium' ? '中等' : '慢速'}

`;

    // 情感设置
    mdContent += `## 情感设置

`;
    mdContent += `- 情感识别: ${settings.emotion.emotionRecognition ? '启用' : '禁用'}
`;
    mdContent += `- 情感回应: ${settings.emotion.emotionResponse ? '启用' : '禁用'}
`;
    mdContent += `- 情感记忆: ${settings.emotion.emotionMemory ? '启用' : '禁用'}

`;

    // 学习设置
    mdContent += `## 学习设置

`;
    mdContent += `- 自适应学习: ${settings.learning.adaptiveLearning ? '启用' : '禁用'}
`;
    mdContent += `- 模式识别: ${settings.learning.patternRecognition ? '启用' : '禁用'}
`;
    mdContent += `- 预测建议: ${settings.learning.predictiveSuggestions ? '启用' : '禁用'}

`;

    // 关系设置
    mdContent += `## 关系设置

`;
    mdContent += `- 关系记忆: ${settings.relationship.relationshipMemory ? '启用' : '禁用'}
`;
    mdContent += `- 里程碑提醒: ${settings.relationship.milestoneReminders ? '启用' : '禁用'}
`;
    mdContent += `- 关系洞察: ${settings.relationship.relationshipInsights ? '启用' : '禁用'}

`;

    // 添加JSON格式的设置数据（用于导入）
    mdContent += `## 设置数据（JSON格式，用于导入）

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
          alert('设置导入成功！');
        } else {
          alert('无法从文件中提取设置数据，请确保文件格式正确。');
        }
      } catch (error) {
        console.error('导入设置失败:', error);
        alert('导入设置失败，请检查文件格式是否正确。');
      }
    };
    reader.onerror = () => {
      alert('读取文件失败，请重试。');
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
      alert('导出配置失败，请重试。');
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
        alert('导入配置失败，请检查文件格式是否正确。');
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
      </div>
      
      <div className="settings-content">
        {isLoading && <div className="settings-loading">加载中...</div>}
        {!isLoading && renderSettingsTab()}
      </div>
    </div>
  );
};

export default SettingsManager;