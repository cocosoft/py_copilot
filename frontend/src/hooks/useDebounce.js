/**
 * 防抖 Hook
 * 
 * 用于延迟执行函数，减少频繁调用
 * 
 * @param {any} value - 需要防抖的值
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {any} 防抖后的值
 * 
 * @example
 * const debouncedSearch = useDebounce(searchQuery, 300);
 */

import { useState, useEffect } from 'react';

const useDebounce = (value, delay = 300) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // 设置定时器
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // 清除定时器
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};

export default useDebounce;
