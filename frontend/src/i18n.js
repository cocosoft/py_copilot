// 屏蔽 i18next 的 Locize 赞助信息
const originalConsoleLog = console.log;

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


// 定义资源，每个命名空间单独加载
const resources = {
  'zh-CN': {
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
  },
  'en-US': {
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
    defaultNS: 'common',
    ns: ['common', 'settings', 'nav', 'agent', 'chat', 'model', 'knowledge', 'workflow', 'skill', 'errors'],
    interpolation: {
      escapeValue: false
    },
    debug: false,
    // 支持嵌套键名，如 settings.general.title
    parseMissingKeyHandler: (key) => {
      // 如果键包含命名空间前缀（如 settings.xxx），尝试从对应命名空间查找
      const nsSeparator = key.indexOf('.');
      if (nsSeparator > 0) {
        const ns = key.substring(0, nsSeparator);
        const actualKey = key.substring(nsSeparator + 1);
        if (i18n.hasResourceBundle(i18n.language, ns)) {
          const translation = i18n.getResource(i18n.language, ns, actualKey);
          if (translation) return translation;
        }
      }
      return key;
    }
  }, (err) => {
    if (err) {
      console.error('i18n initialization error:', err);
    } else {
    }
  });

export default i18n;
