import React, { useState, useEffect } from 'react';
import { skillApi } from '../../services/skillApi';

function SkillDependencyManagement({ skillId, skillName }) {
  const [dependencies, setDependencies] = useState([]);
  const [availableSkills, setAvailableSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newDependency, setNewDependency] = useState({
    dependency_skill_id: '',
    version_requirement: ''
  });

  useEffect(() => {
    loadDependencies();
    loadAvailableSkills();
  }, [skillId]);

  const loadDependencies = async () => {
    try {
      setLoading(true);
      const data = await skillApi.getDependencies(skillId);
      setDependencies(data);
    } catch (err) {
      setError('加载依赖失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableSkills = async () => {
    try {
      const data = await skillApi.list();
      // 过滤掉当前技能本身
      const filteredSkills = data.filter(skill => skill.id !== parseInt(skillId));
      setAvailableSkills(filteredSkills);
    } catch (err) {
      console.error('加载可用技能失败:', err);
    }
  };

  const handleAddDependency = async () => {
    if (!newDependency.dependency_skill_id || !newDependency.version_requirement) {
      setError('请填写完整的依赖信息');
      return;
    }

    try {
      await skillApi.addDependency(skillId, newDependency);
      setShowAddForm(false);
      setNewDependency({ dependency_skill_id: '', version_requirement: '' });
      await loadDependencies();
      setError('');
    } catch (err) {
      setError('添加依赖失败: ' + err.message);
    }
  };

  const handleRemoveDependency = async (dependencyId) => {
    if (!confirm('确定要删除这个依赖吗？')) return;

    try {
      await skillApi.removeDependency(skillId, dependencyId);
      await loadDependencies();
    } catch (err) {
      setError('删除依赖失败: ' + err.message);
    }
  };

  const handleCheckCompatibility = async () => {
    try {
      const result = await skillApi.checkDependencyCompatibility(skillId);
      if (result.compatible) {
        alert('所有依赖都兼容！');
      } else {
        alert(`发现不兼容的依赖:\n${result.incompatible_dependencies.map(d => d.name).join(', ')}`);
      }
    } catch (err) {
      setError('检查兼容性失败: ' + err.message);
    }
  };

  const handleResolveDependencies = async () => {
    try {
      const result = await skillApi.resolveDependencies(skillId);
      alert(`依赖解析完成:\n${result.resolved_dependencies.map(d => d.name + ' ' + d.version).join('\n')}`);
    } catch (err) {
      setError('解析依赖失败: ' + err.message);
    }
  };

  if (loading) {
    return <div className="dependency-management"><div className="loading-spinner"></div> 加载中...</div>;
  }

  return (
    <div className="dependency-management">
      <div className="dependency-header">
        <h3>技能依赖管理 - {skillName}</h3>
        <div className="dependency-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            + 添加依赖
          </button>
          <button 
            className="btn btn-secondary"
            onClick={handleCheckCompatibility}
          >
            检查兼容性
          </button>
          <button 
            className="btn btn-secondary"
            onClick={handleResolveDependencies}
          >
            解析依赖
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {showAddForm && (
        <div className="dependency-form">
          <h4>添加新依赖</h4>
          <div className="form-row">
            <div className="form-field">
              <label>依赖技能:</label>
              <select 
                value={newDependency.dependency_skill_id}
                onChange={e => setNewDependency({...newDependency, dependency_skill_id: e.target.value})}
              >
                <option value="">选择技能</option>
                {availableSkills.map(skill => (
                  <option key={skill.id} value={skill.id}>
                    {skill.name} (v{skill.version})
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>版本要求:</label>
              <input 
                type="text" 
                placeholder="例如: >=1.0.0, ^2.1.0, ~1.2.3"
                value={newDependency.version_requirement}
                onChange={e => setNewDependency({...newDependency, version_requirement: e.target.value})}
              />
              <div style={{fontSize: '12px', color: '#6b7280', marginTop: '4px'}}>
                支持的版本约束: &gt;=, &lt;=, &gt;, &lt;, ==, ^, ~
              </div>
            </div>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={handleAddDependency}>
              添加
            </button>
            <button className="btn btn-outline" onClick={() => setShowAddForm(false)}>
              取消
            </button>
          </div>
        </div>
      )}

      <div className="dependency-list">
        <h4>当前依赖 ({dependencies.length})</h4>
        {dependencies.length === 0 ? (
          <div className="empty-state">暂无依赖</div>
        ) : (
          <div>
            {dependencies.map(dep => (
              <div key={dep.id} className="dependency-item">
                <div className="dependency-info">
                  <div className="dependency-name">{dep.dependency_skill_name}</div>
                  <div className="dependency-version">
                    <span>v{dep.dependency_skill_version}</span>
                    <span style={{marginLeft: '8px', color: '#6b7280'}}>要求: {dep.version_requirement}</span>
                  </div>
                  <div style={{marginTop: '4px'}}>
                    <span className={`btn btn-xs ${dep.compatible ? 'btn-success' : 'btn-danger'}`}>
                      {dep.compatible ? '兼容' : '不兼容'}
                    </span>
                  </div>
                </div>
                <div className="dependency-actions">
                  <button 
                    className="btn btn-danger btn-sm"
                    onClick={() => handleRemoveDependency(dep.id)}
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default SkillDependencyManagement;