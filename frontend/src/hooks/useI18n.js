import { useTranslation } from 'react-i18next';

export const useI18n = () => {
  const { t, i18n } = useTranslation(['translation'], { useSuspense: false });

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
