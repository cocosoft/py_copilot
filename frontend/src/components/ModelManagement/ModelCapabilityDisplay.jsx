import React, { useState, useEffect } from 'react';
import './ModelCapabilityDisplay.css';

const ModelCapabilityDisplay = ({ 
  model = null,
  selectedCapabilities = []
}) => {
  const [capabilityScores, setCapabilityScores] = useState({});
  const [overallScore, setOverallScore] = useState(0);
  const [adaptationSuggestions, setAdaptationSuggestions] = useState([]);

  // 计算模型能力评分
  useEffect(() => {
    if (!model || !model.capabilities) {
      setCapabilityScores({});
      setOverallScore(0);
      setAdaptationSuggestions([]);
      return;
    }

    const scores = {};
    let totalScore = 0;
    let capabilityCount = 0;

    // 计算每个能力的评分
    model.capabilities.forEach(capability => {
      const strength = capability.strength || 0;
      scores[capability.id] = {
        strength: strength,
        normalizedScore: Math.round((strength / 5) * 100),
        isSelected: selectedCapabilities.some(cap => cap.id === capability.id)
      };
      totalScore += strength;
      capabilityCount++;
    });

    // 计算总体评分
    const avgScore = capabilityCount > 0 ? Math.round((totalScore / capabilityCount / 5) * 100) : 0;
    
    setCapabilityScores(scores);
    setOverallScore(avgScore);

    // 生成适配建议
    generateAdaptationSuggestions(model, scores, selectedCapabilities);
  }, [model, selectedCapabilities]);

  // 生成适配建议
  const generateAdaptationSuggestions = (model, scores, selectedCapabilities) => {
    const suggestions = [];

    // 检查是否有选中的能力但模型评分较低
    selectedCapabilities.forEach(capability => {
      const score = scores[capability.id];
      if (score && score.strength < 3) {
        suggestions.push({
          type: 'warning',
          message: `该模型在"${capability.display_name}"能力上表现较弱（评分：${score.strength}/5），建议选择其他模型`,
          capability: capability
        });
      }
    });

    // 检查模型的优势能力
    const strongCapabilities = Object.entries(scores)
      .filter(([_, score]) => score.strength >= 4)
      .map(([id, score]) => {
        const capability = model.capabilities.find(cap => cap.id === id);
        return { capability, score };
      });

    if (strongCapabilities.length > 0) {
      suggestions.push({
        type: 'info',
        message: `该模型在以下能力上表现优秀：${strongCapabilities.map(item => item.capability.display_name).join('、')}`,
        capabilities: strongCapabilities.map(item => item.capability)
      });
    }

    // 根据总体评分给出建议
    if (overallScore >= 80) {
      suggestions.push({
        type: 'success',
        message: '该模型整体能力优秀，适合多种翻译场景',
        priority: 'high'
      });
    } else if (overallScore >= 60) {
      suggestions.push({
        type: 'info',
        message: '该模型能力良好，适合一般翻译任务',
        priority: 'medium'
      });
    } else {
      suggestions.push({
        type: 'warning',
        message: '该模型能力有限，建议选择更合适的模型',
        priority: 'high'
      });
    }

    setAdaptationSuggestions(suggestions);
  };

  // 获取评分颜色
  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  // 获取建议图标
  const getSuggestionIcon = (type) => {
    switch (type) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return 'ℹ️';
    }
  };

  if (!model) {
    return (
      <div className="model-capability-display empty">
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <p>请选择一个模型查看能力详情</p>
        </div>
      </div>
    );
  }

  return (
    <div className="model-capability-display">
      {/* 模型信息头部 */}
      <div className="model-header">
        <h3 className="model-name">{model.name || model.id}</h3>
        <div className="overall-score">
          <span className="score-label">总体评分：</span>
          <div 
            className="score-circle" 
            style={{ 
              background: `conic-gradient(${getScoreColor(overallScore)} ${overallScore * 3.6}deg, #e5e7eb 0deg)` 
            }}
          >
            <span className="score-value">{overallScore}</span>
          </div>
        </div>
      </div>

      {/* 能力详情 */}
      <div className="capability-details">
        <h4>能力详情</h4>
        <div className="capability-list">
          {model.capabilities && model.capabilities.map(capability => {
            const score = capabilityScores[capability.id];
            if (!score) return null;

            return (
              <div key={capability.id} className="capability-item">
                <div className="capability-info">
                  <span className="capability-name">{capability.display_name || capability.name}</span>
                  {score.isSelected && <span className="selected-badge">已选择</span>}
                </div>
                <div className="capability-score">
                  <div className="strength-bar">
                    <div 
                      className="strength-fill"
                      style={{ width: `${score.normalizedScore}%` }}
                    ></div>
                  </div>
                  <span className="strength-value">{score.strength}/5</span>
                </div>
                {capability.description && (
                  <div className="capability-description">{capability.description}</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 适配建议 */}
      {adaptationSuggestions.length > 0 && (
        <div className="adaptation-suggestions">
          <h4>适配建议</h4>
          <div className="suggestion-list">
            {adaptationSuggestions.map((suggestion, index) => (
              <div key={index} className={`suggestion-item ${suggestion.type}`}>
                <span className="suggestion-icon">{getSuggestionIcon(suggestion.type)}</span>
                <span className="suggestion-text">{suggestion.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelCapabilityDisplay;