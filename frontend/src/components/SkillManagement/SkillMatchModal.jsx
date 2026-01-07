import React, { useState, useEffect } from 'react';
import { useSkillExecution } from '../../hooks/useSkills';
import SkillCard from './SkillCard';
import './SkillManagement.css';

function SkillMatchModal({ onClose }) {
  const { matchSkills } = useSkillExecution();
  const [taskDescription, setTaskDescription] = useState('');
  const [matchedSkills, setMatchedSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [showExecution, setShowExecution] = useState(false);

  useEffect(() => {
    if (selectedSkill && showExecution) {
      // 执行技能后重置状态
      setSelectedSkill(null);
      setShowExecution(false);
    }
  }, [selectedSkill, showExecution]);

  const handleMatch = async () => {
    if (!taskDescription.trim()) {
      setError('请输入任务描述');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const result = await matchSkills(taskDescription);
      setMatchedSkills(result.matched_skills || []);
    } catch (err) {
      setError(err.message || '匹配技能失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteSkill = (skill) => {
    setSelectedSkill(skill);
    setShowExecution(true);
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="skill-modal-backdrop" onClick={handleBackdropClick}>
      <div className="skill-modal skill-match-modal">
        <div className="skill-modal-header">
          <h2>技能匹配</h2>
          <button className="close-btn" onClick={onClose} disabled={loading}>
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        
        <div className="skill-modal-body">
          <div className="skill-match-section">
            <div className="skill-match-input">
              <h3>任务描述</h3>
              <textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="请描述您需要完成的任务..."
                rows={4}
                disabled={loading}
                className="match-input"
              />
              
              {error && (
                <div className="match-error">
                  <strong>错误:</strong> {error}
                </div>
              )}
              
              <button
                onClick={handleMatch}
                disabled={loading || !taskDescription.trim()}
                className="match-btn"
              >
                {loading ? (
                  <>
                    <span className="loading-spinner-small"></span>
                    匹配中...
                  </>
                ) : (
                  '查找匹配技能'
                )}
              </button>
            </div>
            
            {matchedSkills.length > 0 && (
              <div className="skill-match-results">
                <h3>匹配结果</h3>
                <p className="match-count">
                  找到 {matchedSkills.length} 个匹配的技能
                </p>
                <div className="matched-skills-list">
                  {matchedSkills.map((skill, index) => (
                    <div key={skill.id} className="matched-skill-item">
                      <div className="match-rank">{index + 1}</div>
                      <div className="match-skill-card">
                        <SkillCard skill={skill} showActions={true} onExecute={() => handleExecuteSkill(skill)} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {matchedSkills.length === 0 && loading === false && taskDescription.trim() && !error && (
              <div className="no-matches">
                <h3>未找到匹配技能</h3>
                <p>请尝试调整任务描述，或创建新的技能来完成此任务。</p>
              </div>
            )}
          </div>
        </div>
        
        <div className="skill-modal-footer">
          <button className="cancel-btn" onClick={onClose} disabled={loading}>
            关闭
          </button>
        </div>
      </div>
      
      {selectedSkill && showExecution && (
        <div className="skill-modal-backdrop">
          <div className="skill-modal skill-execution-modal">
            <div className="skill-modal-header">
              <h2>执行技能: {selectedSkill.name}</h2>
              <button className="close-btn" onClick={() => setShowExecution(false)}>
                <svg viewBox="0 0 24 24" width="24" height="24">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              </button>
            </div>
            <div className="skill-modal-body">
              <div className="skill-execution-info">
                <h3>技能信息</h3>
                <p><strong>名称:</strong> {selectedSkill.name}</p>
                <p><strong>版本:</strong> v{selectedSkill.version}</p>
                <p><strong>状态:</strong> {selectedSkill.status === 'enabled' ? '已启用' : '已禁用'}</p>
                {selectedSkill.tags && selectedSkill.tags.length > 0 && (
                  <p><strong>标签:</strong> {selectedSkill.tags.join(', ')}</p>
                )}
              </div>
              <div className="skill-execution-task">
                <h3>任务内容</h3>
                <textarea
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                  rows={6}
                  disabled={loading}
                  className="task-input"
                />
              </div>
              <div className="execution-actions">
                <button className="execute-btn">
                  执行技能
                </button>
                <button className="cancel-btn" onClick={() => setShowExecution(false)}>
                  返回
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SkillMatchModal;