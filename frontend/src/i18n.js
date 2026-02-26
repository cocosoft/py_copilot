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


const resources = {
  'zh-CN': {
    translation: translation_zhCN
  },
  'en-US': {
    translation: translation_enUS
  }
};

// 从 localStorage 读取保存的语言设置
const savedLanguage = localStorage.getItem('app-language') || 'zh-CN';

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: savedLanguage,
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

    }
  });

export default i18n;
