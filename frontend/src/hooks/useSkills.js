import { useState, useEffect, useCallback } from 'react';
import { skillApi } from '../services/skillApi';

export function useSkills() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    status: null,
    tags: [],
    search: '',
  });

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await skillApi.list(filters);
      setSkills(response.skills || []);
    } catch (err) {
      setError(err.message);
      setSkills([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const enableSkill = useCallback(async (skillId) => {
    try {
      await skillApi.enable(skillId);
      // 直接在前端更新技能状态，避免重新请求整个列表
      setSkills(prev => prev.map(skill => 
        skill.id === skillId ? { ...skill, status: 'enabled' } : skill
      ));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, []);

  const disableSkill = useCallback(async (skillId) => {
    try {
      await skillApi.disable(skillId);
      // 直接在前端更新技能状态，避免重新请求整个列表
      setSkills(prev => prev.map(skill => 
        skill.id === skillId ? { ...skill, status: 'disabled' } : skill
      ));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, []);

  const deleteSkill = useCallback(async (skillId) => {
    try {
      await skillApi.delete(skillId);
      setSkills(prev => prev.filter(s => s.id !== skillId));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, []);

  const getSkill = useCallback(async (skillId) => {
    try {
      return await skillApi.get(skillId);
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, []);

  // 版本管理相关方法
  const getVersions = useCallback(async (skillId) => {
    try {
      return await skillApi.getVersions(skillId);
    } catch (err) {
      setError(err.message);
      return [];
    }
  }, []);

  const getVersion = useCallback(async (versionId) => {
    try {
      return await skillApi.getVersion(versionId);
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, []);

  const createVersion = useCallback(async (skillId, versionData) => {
    try {
      await skillApi.createVersion(skillId, versionData);
      // 更新技能列表，确保显示最新版本
      await fetchSkills();
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, [fetchSkills]);

  const rollbackVersion = useCallback(async (skillId, versionId) => {
    try {
      const updatedSkill = await skillApi.rollbackVersion(skillId, versionId);
      // 更新技能列表中的技能版本
      setSkills(prev => prev.map(skill => 
        skill.id === skillId ? updatedSkill : skill
      ));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, []);

  const compareVersions = useCallback(async (versionId1, versionId2) => {
    try {
      return await skillApi.compareVersions(versionId1, versionId2);
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, []);

  return {
    skills,
    loading,
    error,
    filters,
    setFilters,
    refetch: fetchSkills,
    enableSkill,
    disableSkill,
    deleteSkill,
    getSkill,
    // 版本管理相关方法
    getVersions,
    getVersion,
    createVersion,
    rollbackVersion,
    compareVersions,
  };
}

export function useSkillExecution() {
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const executeSkill = useCallback(async (skillId, task, params) => {
    setExecuting(true);
    setError(null);
    setResult(null);
    try {
      const executionResult = await skillApi.execute(skillId, task, params);
      setResult(executionResult);
      return executionResult;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setExecuting(false);
    }
  }, []);

  const matchSkills = useCallback(async (taskDescription) => {
    try {
      return await skillApi.match(taskDescription);
    } catch (err) {
      setError(err.message);
      return [];
    }
  }, []);

  return {
    executing,
    result,
    error,
    executeSkill,
    matchSkills,
  };
}
