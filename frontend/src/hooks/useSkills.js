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
      await fetchSkills();
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, [fetchSkills]);

  const disableSkill = useCallback(async (skillId) => {
    try {
      await skillApi.disable(skillId);
      await fetchSkills();
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }, [fetchSkills]);

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
  };
}

export function useSkillExecution() {
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const executeSkill = useCallback(async (skillId, task) => {
    setExecuting(true);
    setError(null);
    setResult(null);
    try {
      const executionResult = await skillApi.execute(skillId, task);
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
