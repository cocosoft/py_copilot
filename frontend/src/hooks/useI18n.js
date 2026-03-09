import { useTranslation } from 'react-i18next';

/**
 * 国际化 Hook
 * @param {string|string[]} ns - 命名空间，默认为 ['common', 'model', 'settings', 'nav', 'agent', 'chat', 'knowledge', 'workflow', 'skill', 'errors']
 * @returns {Object} 包含 t 函数、i18n 实例、语言切换函数和当前语言的对象
 */
export const useI18n = (ns = ['common', 'model', 'settings', 'nav', 'agent', 'chat', 'knowledge', 'workflow', 'skill', 'errors']) => {
  const { t, i18n } = useTranslation(ns, { useSuspense: false });

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    // 保存语言设置到 localStorage
    localStorage.setItem('app-language', lng);
  };

  return {
    t,
    i18n,
    changeLanguage,
    currentLanguage: i18n.language
  };
};

export default useI18n;
