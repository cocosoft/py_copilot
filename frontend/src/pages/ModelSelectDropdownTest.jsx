import React, { useState } from 'react';
import ModelSelectDropdown from '../components/ModelManagement/ModelSelectDropdown';

/**
 * ModelSelectDropdown 测试页面
 * 用于测试模型选择下拉列表组件的各种功能
 */
const ModelSelectDropdownTest = () => {
  // 测试用例1：基本用法
  const [selectedModel1, setSelectedModel1] = useState(null);
  
  // 测试用例2：自定义占位符
  const [selectedModel2, setSelectedModel2] = useState(null);
  
  // 测试用例3：禁用状态
  const [selectedModel3, setSelectedModel3] = useState(null);
  
  // 测试用例4：自定义徽章
  const [selectedModel4, setSelectedModel4] = useState(null);
  
  // 测试用例5：不同场景
  const [selectedModel5, setSelectedModel5] = useState(null);
  
  // 自定义徽章函数
  const customGetModelBadge = (model) => {
    return (
      <span className="model-badge" style={{ 
        background: '#4CAF50', 
        color: 'white', 
        padding: '2px 8px', 
        borderRadius: '10px', 
        fontSize: '12px',
        marginLeft: '8px'
      }}>
        {model.capabilities ? '多能力' : '基础'}
      </span>
    );
  };
  
  return (
    <div className="model-select-test-container" style={{
      maxWidth: '800px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ textAlign: 'center', marginBottom: '40px' }}>
        ModelSelectDropdown 组件测试
      </h1>
      
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '20px' }}>测试用例 1: 基本用法</h2>
        <p>默认场景下的模型选择器，自动从API加载模型数据</p>
        <div style={{ width: '400px' }}>
          <ModelSelectDropdown
            selectedModel={selectedModel1}
            onModelSelect={setSelectedModel1}
          />
        </div>
        {selectedModel1 && (
          <div style={{ marginTop: '10px', padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
            <strong>已选择模型:</strong> {selectedModel1.model_name} ({selectedModel1.model_id})
          </div>
        )}
      </div>
      
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '20px' }}>测试用例 2: 自定义占位符</h2>
        <p>使用自定义的占位文本</p>
        <div style={{ width: '400px' }}>
          <ModelSelectDropdown
            selectedModel={selectedModel2}
            onModelSelect={setSelectedModel2}
            placeholder="请选择一个AI模型..."
          />
        </div>
        {selectedModel2 && (
          <div style={{ marginTop: '10px', padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
            <strong>已选择模型:</strong> {selectedModel2.model_name} ({selectedModel2.model_id})
          </div>
        )}
      </div>
      
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '20px' }}>测试用例 3: 禁用状态</h2>
        <p>禁用状态下的模型选择器</p>
        <div style={{ width: '400px' }}>
          <ModelSelectDropdown
            selectedModel={selectedModel3}
            onModelSelect={setSelectedModel3}
            disabled={true}
          />
        </div>
      </div>
      
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '20px' }}>测试用例 4: 自定义徽章</h2>
        <p>带有自定义徽章的模型选择器</p>
        <div style={{ width: '400px' }}>
          <ModelSelectDropdown
            selectedModel={selectedModel4}
            onModelSelect={setSelectedModel4}
            getModelBadge={customGetModelBadge}
          />
        </div>
        {selectedModel4 && (
          <div style={{ marginTop: '10px', padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
            <strong>已选择模型:</strong> {selectedModel4.model_name} ({selectedModel4.model_id})
          </div>
        )}
      </div>
      
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '20px' }}>测试用例 5: 不同场景</h2>
        <p>在不同场景下使用模型选择器</p>
        <div style={{ width: '400px', marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>聊天场景:</label>
          <ModelSelectDropdown
            selectedModel={selectedModel5}
            onModelSelect={setSelectedModel5}
            scene="chat"
          />
        </div>
        {selectedModel5 && (
          <div style={{ marginTop: '10px', padding: '10px', background: '#f0f0f0', borderRadius: '4px' }}>
            <strong>已选择模型:</strong> {selectedModel5.model_name} ({selectedModel5.model_id})
          </div>
        )}
      </div>
      
      <div style={{ marginTop: '60px', padding: '20px', background: '#e3f2fd', borderRadius: '8px' }}>
        <h3>组件特性说明:</h3>
        <ul>
          <li>支持自动从API加载模型数据</li>
          <li>支持按供应商分组显示模型</li>
          <li>支持模型搜索功能</li>
          <li>支持自定义占位文本</li>
          <li>支持禁用状态</li>
          <li>支持自定义模型徽章</li>
          <li>支持不同使用场景</li>
          <li>响应式设计，适配不同屏幕尺寸</li>
        </ul>
      </div>
    </div>
  );
};

export default ModelSelectDropdownTest;