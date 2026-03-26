/**
 * 知识库验证 Hook
 *
 * 用于验证当前知识库是否存在，如果不存在则引导用户创建知识库
 *
 * @module useKnowledgeBaseValidation
 */

import { useEffect, useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useKnowledgeStore from '../stores/knowledgeStore';
import { getKnowledgeBase, getKnowledgeBases } from '../utils/api/knowledgeApi';

/**
 * 知识库验证 Hook
 *
 * @returns {Object} 验证结果和状态
 * @returns {boolean} returns.isValid - 知识库是否有效
 * @returns {boolean} returns.isChecking - 是否正在验证
 * @returns {Object} returns.currentKnowledgeBase - 当前知识库
 * @returns {Function} returns.validateKnowledgeBase - 手动验证函数
 */
export const useKnowledgeBaseValidation = () => {
  const navigate = useNavigate();
  const {
    currentKnowledgeBase,
    setCurrentKnowledgeBase,
  } = useKnowledgeStore();

  const [isValid, setIsValid] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  /**
   * 验证当前知识库是否存在
   */
  const validateKnowledgeBase = useCallback(async () => {
    if (!currentKnowledgeBase) {
      setIsValid(false);
      return false;
    }

    setIsChecking(true);
    try {
      await getKnowledgeBase(currentKnowledgeBase.id);
      setIsValid(true);
      return true;
    } catch (error) {
      if (error.status === 404) {
        console.warn(`[useKnowledgeBaseValidation] 知识库 ${currentKnowledgeBase.id} 不存在，清除当前知识库状态`);
        setIsValid(false);
        setCurrentKnowledgeBase(null);
        return false;
      }
      console.error('[useKnowledgeBaseValidation] 验证知识库存在性失败:', error);
      return true;
    } finally {
      setIsChecking(false);
    }
  }, [currentKnowledgeBase, setCurrentKnowledgeBase]);

  /**
   * 加载知识库列表
   * 如果没有当前知识库，自动选择第一个
   */
  const loadKnowledgeBases = useCallback(async () => {
    // 如果已经有当前知识库，先验证知识库是否存在
    if (currentKnowledgeBase) {
      const exists = await validateKnowledgeBase();
      if (exists) return true;
      // 如果知识库不存在，继续加载知识库列表
    }

    try {
      const response = await getKnowledgeBases(0, 10);
      const knowledgeBasesList = response.knowledge_bases || response;

      if (knowledgeBasesList.length > 0) {
        setCurrentKnowledgeBase(knowledgeBasesList[0]);
        setIsValid(true);
        return true;
      } else {
        console.warn('[useKnowledgeBaseValidation] 没有可用的知识库');
        setIsValid(false);
        return false;
      }
    } catch (error) {
      console.error('[useKnowledgeBaseValidation] 加载知识库列表失败:', error);
      setIsValid(false);
      return false;
    }
  }, [currentKnowledgeBase, setCurrentKnowledgeBase, validateKnowledgeBase]);

  /**
   * 跳转到知识库设置页面
   */
  const goToKnowledgeBaseSettings = useCallback(() => {
    navigate('/knowledge/settings');
  }, [navigate]);

  // 组件加载时自动验证
  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  return {
    isValid,
    isChecking,
    currentKnowledgeBase,
    validateKnowledgeBase,
    loadKnowledgeBases,
    goToKnowledgeBaseSettings,
  };
};

export default useKnowledgeBaseValidation;
