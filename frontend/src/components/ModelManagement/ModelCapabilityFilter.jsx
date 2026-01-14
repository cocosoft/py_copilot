import React, { useState, useEffect } from 'react';
import './ModelCapabilityFilter.css';

const ModelCapabilityFilter = ({ 
  models = [], 
  onFilteredModelsChange,
  initialSelectedCapabilities = []
}) => {
  // 状态管理
  const [selectedCapabilities, setSelectedCapabilities] = useState(initialSelectedCapabilities);
  const [minStrength, setMinStrength] = useState(3);
  const [maxStrength, setMaxStrength] = useState(5);
  const [capabilityFilterEnabled, setCapabilityFilterEnabled] = useState(false);
  const [availableCapabilities, setAvailableCapabilities] = useState([]);
  const [modelMatchScores, setModelMatchScores] = useState({});

  // 从模型中提取所有可用的能力
  useEffect(() => {
    const allCapabilities = new Set();
    
    models.forEach(model => {
      if (model.capabilities && Array.isArray(model.capabilities)) {
        model.capabilities.forEach(capability => {
          allCapabilities.add(JSON.stringify({
            id: capability.id,
            name: capability.name,
            display_name: capability.display_name,
            description: capability.description
          }));
        });
      }
    });
    
    const uniqueCapabilities = Array.from(allCapabilities).map(str => JSON.parse(str));
    setAvailableCapabilities(uniqueCapabilities);
  }, [models]);

  // 根据选定的能力筛选模型
  useEffect(() => {
    if (!capabilityFilterEnabled || selectedCapabilities.length === 0) {
      // 如果筛选未启用或没有选择能力，返回所有模型
      onFilteredModelsChange(models);
      setModelMatchScores({});
      return;
    }

    const filteredModels = models.filter(model => {
      if (!model.capabilities || !Array.isArray(model.capabilities)) {
        return false;
      }

      // 检查模型是否具有所有选定的能力
      const modelCapabilityNames = model.capabilities.map(cap => cap.name);
      const hasAllCapabilities = selectedCapabilities.every(cap => 
        modelCapabilityNames.includes(cap.name)
      );

      if (!hasAllCapabilities) {
        return false;
      }

      // 检查能力强度是否符合要求
      return selectedCapabilities.every(selectedCap => {
        const modelCapability = model.capabilities.find(cap => cap.name === selectedCap.name);
        return modelCapability && 
               modelCapability.actual_strength >= minStrength &&
               modelCapability.actual_strength <= maxStrength;
      });
    });

    // 计算匹配分数
    const scores = {};
    models.forEach(model => {
      if (model.capabilities && Array.isArray(model.capabilities)) {
        const matchingCapabilities = model.capabilities.filter(cap => 
          selectedCapabilities.some(selectedCap => selectedCap.name === cap.name)
        );
        
        if (matchingCapabilities.length > 0) {
          const avgStrength = matchingCapabilities.reduce((sum, cap) => sum + cap.actual_strength, 0) / matchingCapabilities.length;
          const avgConfidence = matchingCapabilities.reduce((sum, cap) => sum + cap.confidence_score, 0) / matchingCapabilities.length;
          scores[model.model_name] = {
            matchScore: (avgStrength / 5) * (avgConfidence / 100),
            matchPercentage: Math.round((avgStrength / 5) * (avgConfidence / 100) * 100),
            matchingCapabilities: matchingCapabilities.length
          };
        } else {
          scores[model.model_name] = {
            matchScore: 0,
            matchPercentage: 0,
            matchingCapabilities: 0
          };
        }
      }
    });

    setModelMatchScores(scores);
    onFilteredModelsChange(filteredModels);
  }, [models, selectedCapabilities, minStrength, maxStrength, capabilityFilterEnabled, onFilteredModelsChange]);

  // 处理能力选择
  const handleCapabilitySelect = (capability) => {
    setSelectedCapabilities(prev => {
      const isSelected = prev.some(cap => cap.id === capability.id);
      if (isSelected) {
        return prev.filter(cap => cap.id !== capability.id);
      } else {
        return [...prev, capability];
      }
    });
  };

  // 清空所有选定的能力
  const clearSelectedCapabilities = () => {
    setSelectedCapabilities([]);
  };

  // 按匹配度排序模型
  const getSortedModels = (modelsList) => {
    return modelsList.sort((a, b) => {
      const scoreA = modelMatchScores[a.model_name]?.matchScore || 0;
      const scoreB = modelMatchScores[b.model_name]?.matchScore || 0;
      return scoreB - scoreA;
    });
  };

  return (
    <div className="model-capability-filter">
      <h4>模型能力筛选</h4>
      
      <div className="toggle-item">
        <label>
          <input 
            type="checkbox" 
            checked={capabilityFilterEnabled} 
            onChange={(e) => setCapabilityFilterEnabled(e.target.checked)}
          />
          启用能力筛选
        </label>
      </div>
      
      {capabilityFilterEnabled && (
        <>
          <div className="filter-controls">
            <div className="sort-options">
              <label>能力强度排序：</label>
              <select 
                value={`${minStrength}-${maxStrength}`} 
                onChange={(e) => {
                  const [min, max] = e.target.value.split('-').map(Number);
                  setMinStrength(min);
                  setMaxStrength(max);
                }}
              >
                <option value="1-5">所有强度 (1-5)</option>
                <option value="3-5">中等及以上 (3-5)</option>
                <option value="4-5">较强 (4-5)</option>
                <option value="5-5">最强 (5)</option>
              </select>
            </div>
            
            <div className="strength-slider">
              <label>强度范围：{minStrength} - {maxStrength}</label>
              <div className="slider-container">
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={minStrength}
                  onChange={(e) => setMinStrength(Number(e.target.value))}
                  className="min-slider"
                />
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={maxStrength}
                  onChange={(e) => setMaxStrength(Number(e.target.value))}
                  className="max-slider"
                />
              </div>
            </div>
          </div>

          <div className="capability-selection">
            <div className="section-header">
              <h5>选择所需能力 ({selectedCapabilities.length} 已选)</h5>
              {selectedCapabilities.length > 0 && (
                <button 
                  className="clear-btn"
                  onClick={clearSelectedCapabilities}
                >
                  清空
                </button>
              )}
            </div>
            
            <div className="capability-grid">
              {availableCapabilities.map(capability => (
                <div
                  key={capability.id}
                  className={`capability-card ${
                    selectedCapabilities.some(cap => cap.id === capability.id) ? 'selected' : ''
                  }`}
                  onClick={() => handleCapabilitySelect(capability)}
                >
                  <div className="capability-info">
                    <h6>{capability.display_name || capability.name}</h6>
                    {capability.description && (
                      <p className="capability-description">{capability.description}</p>
                    )}
                  </div>
                  <div className="selection-indicator">
                    {selectedCapabilities.some(cap => cap.id === capability.id) ? '✓' : '+'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="filter-results">
            <h5>筛选结果</h5>
            <div className="results-summary">
              <span>找到 {getSortedModels(models).length} 个模型</span>
              <span>符合条件：{selectedCapabilities.length} 个能力，强度 {minStrength}-{maxStrength}</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelCapabilityFilter;