import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import common_zhCN from './locales/zh-CN/common.json';
import nav_zhCN from './locales/zh-CN/nav.json';
import settings_zhCN from './locales/zh-CN/settings.json';
import agent_zhCN from './locales/zh-CN/agent.json';
import chat_zhCN from './locales/zh-CN/chat.json';
import model_zhCN from './locales/zh-CN/model.json';
import knowledge_zhCN from './locales/zh-CN/knowledge.json';
import workflow_zhCN from './locales/zh-CN/workflow.json';
import skill_zhCN from './locales/zh-CN/skill.json';
import errors_zhCN from './locales/zh-CN/errors.json';

import common_enUS from './locales/en-US/common.json';
import nav_enUS from './locales/en-US/nav.json';
import settings_enUS from './locales/en-US/settings.json';
import agent_enUS from './locales/en-US/agent.json';
import chat_enUS from './locales/en-US/chat.json';
import model_enUS from './locales/en-US/model.json';
import knowledge_enUS from './locales/en-US/knowledge.json';
import workflow_enUS from './locales/en-US/workflow.json';
import skill_enUS from './locales/en-US/skill.json';
import errors_enUS from './locales/en-US/errors.json';

// 调试：检查导入的翻译文件
console.log('Debug: common_zhCN:', common_zhCN);
console.log('Debug: settings_zhCN:', settings_zhCN);
console.log('Debug: settings_zhCN.title:', settings_zhCN.title);
console.log('Debug: settings_zhCN.general.title:', settings_zhCN.general?.title);

// 合并所有翻译到一个命名空间，使用嵌套对象的结构
const translation_zhCN = {
  common: common_zhCN,
  settings: settings_zhCN,
  nav: nav_zhCN,
  agent: agent_zhCN,
  chat: chat_zhCN,
  model: model_zhCN,
  knowledge: knowledge_zhCN,
  workflow: workflow_zhCN,
  skill: skill_zhCN,
  errors: errors_zhCN
};

const translation_enUS = {
  common: common_enUS,
  settings: settings_enUS,
  nav: nav_enUS,
  agent: agent_enUS,
  chat: chat_enUS,
  model: model_enUS,
  knowledge: knowledge_enUS,
  workflow: workflow_enUS,
  skill: skill_enUS,
  errors: errors_enUS
};

// 调试：检查合并后的翻译文件
console.log('Debug: translation_zhCN:', translation_zhCN);
console.log('Debug: translation_zhCN.common:', translation_zhCN.common);
console.log('Debug: translation_zhCN.settings:', translation_zhCN.settings);
console.log('Debug: translation_zhCN.settings.title:', translation_zhCN.settings?.title);
console.log('Debug: translation_zhCN.settings.general.title:', translation_zhCN.settings?.general?.title);
console.log('Debug: translation_zhCN.common.export:', translation_zhCN.common?.export);

const resources = {
  'zh-CN': {
    translation: translation_zhCN
  },
  'en-US': {
    translation: translation_enUS
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'zh-CN',
    fallbackLng: 'zh-CN',
    defaultNS: 'translation',
    ns: ['translation'],
    interpolation: {
      escapeValue: false
    },
    debug: true
  }, (err) => {
    if (err) {
      console.error('i18n initialization error:', err);
    } else {
      console.log('i18n initialized successfully');
      console.log('i18n resources:', i18n.options.resources);
      console.log('i18n language:', i18n.language);
      console.log('Test translation:', i18n.t('settings.title'));
      console.log('Test common translation:', i18n.t('common.export'));
    }
  });

export default i18n;
