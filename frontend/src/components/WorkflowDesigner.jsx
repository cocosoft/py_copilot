import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  Handle,
  Position,
  useReactFlow
} from 'reactflow';
import 'reactflow/dist/style.css';
import './WorkflowDesigner.css';
import { nodeParamsConfig, getAllInputSources } from '../configs/nodeParams';


// 自定义节点组件
const KnowledgeSearchNode = ({ data }) => (
  <div className="knowledge-search-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">🔍</span>
      <span className="node-title">知识搜索</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>搜索查询:</label>
        <span>{data.query || '未设置'}</span>
      </div>
      <div className="node-property">
        <label>知识库:</label>
        <span>{data.knowledgeBase || '默认'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const EntityExtractionNode = ({ data }) => (
  <div className="entity-extraction-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">🏷️</span>
      <span className="node-title">实体抽取</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>输入文本:</label>
        <span>{data.textInput ? `${data.textInput.substring(0, 20)}...` : '未设置'}</span>
      </div>
      <div className="node-property">
        <label>实体类型:</label>
        <span>{data.entityTypes?.join(', ') || '全部'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const RelationshipAnalysisNode = ({ data }) => (
  <div className="relationship-analysis-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">🔗</span>
      <span className="node-title">关系分析</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>分析深度:</label>
        <span>{data.maxDepth || 2}</span>
      </div>
      <div className="node-property">
        <label>关系类型:</label>
        <span>{data.relationshipTypes?.join(', ') || '全部'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const VisualizationNode = ({ data }) => (
  <div className="visualization-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">📊</span>
      <span className="node-title">知识图谱可视化</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>可视化类型:</label>
        <span>{data.visualizationType || '图谱'}</span>
      </div>
      <div className="node-property">
        <label>实体数量:</label>
        <span>{data.entityCount || '自动'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

// 基础节点组件
const StartNode = ({ data }) => (
  <div className="start-node">
    <div className="node-header">
      <span className="node-icon">▶️</span>
      <span className="node-title">开始</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>工作流入口</label>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const EndNode = ({ data }) => (
  <div className="end-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">⏹️</span>
      <span className="node-title">结束</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>工作流出口</label>
      </div>
    </div>
  </div>
);

const BranchNode = ({ data }) => (
  <div className="branch-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">🔀</span>
      <span className="node-title">分支</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>分支数量:</label>
        <span>{data.branchCount || 2}</span>
      </div>
      <div className="node-property">
        <label>分支类型:</label>
        <span>{data.branchType || '条件分支'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} id="source1" style={{ left: '30%' }} />
    <Handle type="source" position={Position.Bottom} id="source2" style={{ right: '30%' }} />
  </div>
);

const ConditionNode = ({ data }) => (
  <div className="condition-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">❓</span>
      <span className="node-title">条件判断</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>条件:</label>
        <span>{data.conditionField || '未设置'}</span>
      </div>
      <div className="node-property">
        <label>操作符:</label>
        <span>{data.operator || '==='}</span>
      </div>
      <div className="node-property">
        <label>值:</label>
        <span>{data.value || '未设置'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} id="source1" style={{ left: '30%' }} />
    <Handle type="source" position={Position.Bottom} id="source2" style={{ right: '30%' }} />
  </div>
);

const InputNode = ({ data }) => (
  <div className="input-node">
    <div className="node-header">
      <span className="node-icon">📥</span>
      <span className="node-title">输入</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>输入字段:</label>
        <span>{data.inputField || '未设置'}</span>
      </div>
      <div className="node-property">
        <label>默认值:</label>
        <span>{data.defaultValue || '无'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const OutputNode = ({ data }) => (
  <div className="output-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">📤</span>
      <span className="node-title">输出</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>输出格式:</label>
        <span>{data.format || 'json'}</span>
      </div>
      <div className="node-property">
        <label>字段数:</label>
        <span>{data.fields ? data.fields.length : '全部'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const ProcessNode = ({ data }) => (
  <div className="process-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">⚙️</span>
      <span className="node-title">处理</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>处理类型:</label>
        <span>{data.processType || 'string'}</span>
      </div>
      <div className="node-property">
        <label>输入字段:</label>
        <span>{data.inputField || '未设置'}</span>
      </div>
      <div className="node-property">
        <label>输出字段:</label>
        <span>{data.outputField || 'processed_data'}</span>
      </div>
      <div className="node-property">
        <label>操作:</label>
        <span>{data.processParams?.operation || '未设置'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

// MCP 节点组件
const MCPNode = ({ data }) => (
  <div className="mcp-node">
    <Handle type="target" position={Position.Top} />
    <div className="node-header">
      <span className="node-icon">🔗</span>
      <span className="node-title">MCP 工具</span>
    </div>
    <div className="node-content">
      <div className="node-property">
        <label>工具名称:</label>
        <span>{data.tool_name || '未设置'}</span>
      </div>
      <div className="node-property">
        <label>超时时间:</label>
        <span>{data.timeout || 30}s</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const nodeTypes = {
  knowledgeSearch: KnowledgeSearchNode,
  entityExtraction: EntityExtractionNode,
  relationshipAnalysis: RelationshipAnalysisNode,
  visualization: VisualizationNode,
  // 基础节点
  start: StartNode,
  end: EndNode,
  branch: BranchNode,
  condition: ConditionNode,
  input: InputNode,
  output: OutputNode,
  process: ProcessNode,
  // MCP 节点
  mcp: MCPNode,
};

// 节点面板组件
const NodePanel = ({ onNodeAdd }) => {
  // 节点类型分类
  const nodeCategories = [
    {
      name: '基础节点',
      nodes: [
        {
          type: 'start',
          name: '开始',
          icon: '▶️',
          description: '工作流入口节点'
        },
        {
          type: 'end',
          name: '结束',
          icon: '⏹️',
          description: '工作流出口节点'
        },
        {
          type: 'branch',
          name: '分支',
          icon: '🔀',
          description: '条件分支节点'
        },
        {
          type: 'condition',
          name: '条件判断',
          icon: '❓',
          description: '条件判断节点'
        },
        {
          type: 'input',
          name: '输入',
          icon: '📥',
          description: '处理用户输入数据节点'
        },
        {
          type: 'process',
          name: '处理',
          icon: '⚙️',
          description: '数据处理节点'
        },
        {
          type: 'output',
          name: '输出',
          icon: '📤',
          description: '格式化输出结果节点'
        }
      ]
    },
    {
      name: '知识图谱节点',
      nodes: [
        {
          type: 'knowledgeSearch',
          name: '知识搜索',
          icon: '🔍',
          description: '在知识图谱中搜索实体和关系'
        },
        {
          type: 'entityExtraction',
          name: '实体抽取',
          icon: '🏷️',
          description: '从文本中抽取命名实体'
        },
        {
          type: 'relationshipAnalysis',
          name: '关系分析',
          icon: '🔗',
          description: '分析实体之间的关系网络'
        },
        {
          type: 'visualization',
          name: '可视化',
          icon: '📊',
          description: '生成知识图谱可视化'
        }
      ]
    },
    {
      name: 'MCP 节点',
      nodes: [
        {
          type: 'mcp',
          name: 'MCP 工具',
          icon: '🔗',
          description: '调用外部 MCP 服务提供的工具'
        }
      ]
    }
  ];

  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState({});

  // 切换分类展开状态
  const toggleCategory = (categoryName) => {
    setExpandedCategories(prev => ({
      ...prev,
      [categoryName]: !prev[categoryName]
    }));
  };

  // 实时过滤节点
  const filteredCategories = nodeCategories.map(category => {
    const filteredNodes = category.nodes.filter(node => 
      node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
    return {
      ...category,
      nodes: filteredNodes
    };
  }).filter(category => category.nodes.length > 0);

  const handleDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
    // 添加拖拽开始的视觉反馈
    event.currentTarget.style.opacity = '0.5';
    event.currentTarget.style.transform = 'scale(0.95)';
  };

  const handleDragEnd = (event) => {
    // 移除拖拽开始的视觉反馈
    event.currentTarget.style.opacity = '1';
    event.currentTarget.style.transform = 'scale(1)';
  };

  return (
    <div className="node-panel">
      {/* 搜索框 */}
      <div className="node-panel-header">
        <input
          type="text"
          className="node-search-input"
          placeholder="搜索节点..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* 分类节点列表 */}
      {filteredCategories.map((category, index) => (
        <div key={index} className="node-category">
          <div 
            className="node-category-header"
            onClick={() => toggleCategory(category.name)}
          >
            <h3>{category.name}</h3>
            <span className={`category-toggle ${expandedCategories[category.name] ? 'expanded' : ''}`}>
              {expandedCategories[category.name] ? '▼' : '▶'}
            </span>
          </div>
          
          {/* 折叠面板内容 */}
          {expandedCategories[category.name] && (
            <div className="node-list">
              {category.nodes.map((node) => (
                <div
                  key={node.type}
                  className="node-item"
                  draggable
                  onDragStart={(e) => handleDragStart(e, node.type)}
                  onDragEnd={handleDragEnd}
                  onClick={() => onNodeAdd(node.type)}
                >
                  <span className="node-icon">{node.icon}</span>
                  <div className="node-info">
                    <div className="node-name">{node.name}</div>
                    <div className="node-description">{node.description}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// 节点配置面板
const NodeConfigPanel = ({ selectedNode, onConfigUpdate, onDelete, nodes, edges }) => {
  const [config, setConfig] = useState(selectedNode?.data || {});
  const [dataMapping, setDataMapping] = useState(selectedNode?.data?.dataMapping || {});

  const handleConfigChange = (key, value) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    onConfigUpdate(selectedNode.id, newConfig);
  };

  const handleDataMappingChange = (inputField, sourceField) => {
    const newDataMapping = { ...dataMapping, [inputField]: sourceField };
    setDataMapping(newDataMapping);
    handleConfigChange('dataMapping', newDataMapping);
  };

  // 获取所有可用的输入源
  const getAvailableInputSources = () => {
    // 获取所有指向当前节点的边
    const incomingEdges = edges.filter(edge => edge.target === selectedNode.id);
    const inputSources = [];
    
    incomingEdges.forEach(edge => {
      const sourceNode = nodes.find(node => node.id === edge.source);
      if (sourceNode) {
        const nodeParams = nodeParamsConfig[sourceNode.type];
        if (nodeParams && nodeParams.outputs) {
          nodeParams.outputs.forEach(output => {
            inputSources.push({
              nodeId: sourceNode.id,
              nodeType: sourceNode.type,
              fieldName: output.name,
              fieldType: output.type,
              fieldDescription: output.description,
              displayName: `${sourceNode.type}节点.${output.name}`
            });
          });
        }
      }
    });
    
    return inputSources;
  };

  // 渲染数据映射配置部分
  const renderDataMappingSection = () => {
    const nodeParams = nodeParamsConfig[selectedNode.type];
    if (!nodeParams || nodeParams.inputs.length === 0) {
      return null;
    }

    const inputSources = getAvailableInputSources();

    return (
      <div className="data-mapping-section">
        <h4>数据映射配置</h4>
        {nodeParams.inputs.map((input, index) => (
          <div key={index} className="form-group">
            <label>{input.name} ({input.type})</label>
            <select
              value={dataMapping[input.name] || ''}
              onChange={(e) => handleDataMappingChange(input.name, e.target.value)}
            >
              <option value="">直接输入值</option>
              {inputSources.map((source, idx) => (
                <option key={idx} value={source.displayName}>
                  {source.displayName} ({source.fieldType})
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    );
  };

  if (!selectedNode) {
    return (
      <div className="config-panel">
        <h3>节点配置</h3>
        <p>请选择一个节点进行配置</p>
      </div>
    );
  }

  const renderConfigForm = () => {
    switch (selectedNode.type) {
      case 'knowledgeSearch':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>搜索查询</label>
              <input
                type="text"
                value={config.query || ''}
                onChange={(e) => handleConfigChange('query', e.target.value)}
                placeholder="输入搜索关键词"
              />
            </div>
            <div className="form-group">
              <label>知识库</label>
              <select
                value={config.knowledgeBase || ''}
                onChange={(e) => handleConfigChange('knowledgeBase', e.target.value)}
              >
                <option value="">默认知识库</option>
                <option value="tech">技术知识库</option>
                <option value="business">商业知识库</option>
              </select>
            </div>
            <div className="form-group">
              <label>最大结果数</label>
              <input
                type="number"
                value={config.maxResults || 10}
                onChange={(e) => handleConfigChange('maxResults', parseInt(e.target.value))}
                min="1"
                max="100"
              />
            </div>
          </div>
        );

      case 'entityExtraction':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>输入文本</label>
              <textarea
                value={config.textInput || ''}
                onChange={(e) => handleConfigChange('textInput', e.target.value)}
                placeholder="输入要抽取实体的文本"
                rows="4"
              />
            </div>
            <div className="form-group">
              <label>实体类型</label>
              <div className="checkbox-group">
                {['人物', '组织', '地点', '产品', '事件'].map((type) => (
                  <label key={type} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={config.entityTypes?.includes(type) || false}
                      onChange={(e) => {
                        const newTypes = e.target.checked
                          ? [...(config.entityTypes || []), type]
                          : (config.entityTypes || []).filter(t => t !== type);
                        handleConfigChange('entityTypes', newTypes);
                      }}
                    />
                    {type}
                  </label>
                ))}
              </div>
            </div>
          </div>
        );

      case 'relationshipAnalysis':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>分析深度</label>
              <input
                type="number"
                value={config.maxDepth || 2}
                onChange={(e) => handleConfigChange('maxDepth', parseInt(e.target.value))}
                min="1"
                max="5"
              />
            </div>
            <div className="form-group">
              <label>关系类型</label>
              <div className="checkbox-group">
                {['包含', '属于', '合作', '竞争', '投资'].map((type) => (
                  <label key={type} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={config.relationshipTypes?.includes(type) || false}
                      onChange={(e) => {
                        const newTypes = e.target.checked
                          ? [...(config.relationshipTypes || []), type]
                          : (config.relationshipTypes || []).filter(t => t !== type);
                        handleConfigChange('relationshipTypes', newTypes);
                      }}
                    />
                    {type}
                  </label>
                ))}
              </div>
            </div>
          </div>
        );

      case 'visualization':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>可视化类型</label>
              <select
                value={config.visualizationType || 'graph'}
                onChange={(e) => handleConfigChange('visualizationType', e.target.value)}
              >
                <option value="graph">力导向图</option>
                <option value="network">网络图</option>
                <option value="tree">树状图</option>
              </select>
            </div>
            <div className="form-group">
              <label>最大实体数</label>
              <input
                type="number"
                value={config.maxEntities || 50}
                onChange={(e) => handleConfigChange('maxEntities', parseInt(e.target.value))}
                min="10"
                max="500"
              />
            </div>
          </div>
        );

      case 'start':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>工作流名称</label>
              <input
                type="text"
                value={config.workflowName || ''}
                onChange={(e) => handleConfigChange('workflowName', e.target.value)}
                placeholder="输入工作流名称"
              />
            </div>
            <div className="form-group">
              <label>描述</label>
              <textarea
                value={config.description || ''}
                onChange={(e) => handleConfigChange('description', e.target.value)}
                placeholder="输入工作流描述"
                rows="3"
              />
            </div>
          </div>
        );

      case 'end':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>完成消息</label>
              <input
                type="text"
                value={config.completionMessage || '工作流已完成'}
                onChange={(e) => handleConfigChange('completionMessage', e.target.value)}
                placeholder="输入完成消息"
              />
            </div>
          </div>
        );

      case 'branch':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>分支数量</label>
              <input
                type="number"
                value={config.branchCount || 2}
                onChange={(e) => handleConfigChange('branchCount', parseInt(e.target.value))}
                min="2"
                max="5"
              />
            </div>
            <div className="form-group">
              <label>分支类型</label>
              <select
                value={config.branchType || '条件分支'}
                onChange={(e) => handleConfigChange('branchType', e.target.value)}
              >
                <option value="条件分支">条件分支</option>
                <option value="并行分支">并行分支</option>
                <option value="循环分支">循环分支</option>
              </select>
            </div>
          </div>
        );

      case 'condition':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>条件字段</label>
              <input
                type="text"
                value={config.conditionField || ''}
                onChange={(e) => handleConfigChange('conditionField', e.target.value)}
                placeholder="输入条件字段"
              />
            </div>
            <div className="form-group">
              <label>操作符</label>
              <select
                value={config.operator || '==='}
                onChange={(e) => handleConfigChange('operator', e.target.value)}
              >
                <option value="===">等于</option>
                <option value="!==">不等于</option>
                <option value=">">&gt;</option>
                <option value="<">&lt;</option>
                <option value=">=">&gt;=</option>
                <option value="<=">&lt;=</option>
                <option value="contains">包含</option>
              </select>
            </div>
            <div className="form-group">
              <label>条件值</label>
              <input
                type="text"
                value={config.value || ''}
                onChange={(e) => handleConfigChange('value', e.target.value)}
                placeholder="输入条件值"
              />
            </div>
          </div>
        );

      case 'input':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>输入字段</label>
              <input
                type="text"
                value={config.inputField || ''}
                onChange={(e) => handleConfigChange('inputField', e.target.value)}
                placeholder="输入字段名"
              />
            </div>
            <div className="form-group">
              <label>默认值</label>
              <input
                type="text"
                value={config.defaultValue || ''}
                onChange={(e) => handleConfigChange('defaultValue', e.target.value)}
                placeholder="输入默认值"
              />
            </div>
          </div>
        );

      case 'output':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>输出格式</label>
              <select
                value={config.format || 'json'}
                onChange={(e) => handleConfigChange('format', e.target.value)}
              >
                <option value="json">JSON</option>
                <option value="xml">XML</option>
                <option value="csv">CSV</option>
                <option value="text">文本</option>
              </select>
            </div>
            <div className="form-group">
              <label>输出字段</label>
              <textarea
                value={config.fields ? config.fields.join('\n') : ''}
                onChange={(e) => handleConfigChange('fields', e.target.value.split('\n').filter(f => f.trim() !== ''))}
                placeholder="每行一个字段名"
                rows="4"
              />
            </div>
          </div>
        );

      case 'process':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>处理类型</label>
              <select
                value={config.processType || 'string'}
                onChange={(e) => handleConfigChange('processType', e.target.value)}
              >
                <option value="string">字符串处理</option>
                <option value="number">数值处理</option>
                <option value="json">JSON处理</option>
                <option value="array">数组处理</option>
              </select>
            </div>
            <div className="form-group">
              <label>输入字段</label>
              <input
                type="text"
                value={config.inputField || ''}
                onChange={(e) => handleConfigChange('inputField', e.target.value)}
                placeholder="输入要处理的字段名"
              />
            </div>
            <div className="form-group">
              <label>输出字段</label>
              <input
                type="text"
                value={config.outputField || 'processed_data'}
                onChange={(e) => handleConfigChange('outputField', e.target.value)}
                placeholder="输入处理后的数据字段名"
              />
            </div>
            
            {/* 字符串处理参数 */}
            {config.processType === 'string' && (
              <div className="form-group">
                <label>字符串操作</label>
                <select
                  value={config.processParams?.operation || 'uppercase'}
                  onChange={(e) => handleConfigChange('processParams', { ...config.processParams, operation: e.target.value })}
                >
                  <option value="uppercase">转为大写</option>
                  <option value="lowercase">转为小写</option>
                  <option value="trim">去除首尾空格</option>
                  <option value="substring">截取子串</option>
                  <option value="replace">替换文本</option>
                </select>
                
                {/* 子串截取参数 */}
                {config.processParams?.operation === 'substring' && (
                  <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                    <input
                      type="number"
                      placeholder="开始位置"
                      value={config.processParams?.start || 0}
                      onChange={(e) => handleConfigChange('processParams', { ...config.processParams, start: parseInt(e.target.value) })}
                    />
                    <input
                      type="number"
                      placeholder="结束位置"
                      value={config.processParams?.end || ''}
                      onChange={(e) => handleConfigChange('processParams', { ...config.processParams, end: e.target.value ? parseInt(e.target.value) : undefined })}
                    />
                  </div>
                )}
                
                {/* 文本替换参数 */}
                {config.processParams?.operation === 'replace' && (
                  <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                    <input
                      type="text"
                      placeholder="要替换的文本"
                      value={config.processParams?.old || ''}
                      onChange={(e) => handleConfigChange('processParams', { ...config.processParams, old: e.target.value })}
                    />
                    <input
                      type="text"
                      placeholder="替换为"
                      value={config.processParams?.new || ''}
                      onChange={(e) => handleConfigChange('processParams', { ...config.processParams, new: e.target.value })}
                    />
                  </div>
                )}
              </div>
            )}
            
            {/* 数值处理参数 */}
            {config.processType === 'number' && (
              <div className="form-group">
                <label>数值操作</label>
                <select
                  value={config.processParams?.operation || 'add'}
                  onChange={(e) => handleConfigChange('processParams', { ...config.processParams, operation: e.target.value })}
                >
                  <option value="add">加法</option>
                  <option value="subtract">减法</option>
                  <option value="multiply">乘法</option>
                  <option value="divide">除法</option>
                  <option value="round">四舍五入</option>
                </select>
                
                {/* 四则运算参数 */}
                {['add', 'subtract', 'multiply', 'divide'].includes(config.processParams?.operation) && (
                  <input
                    type="number"
                    placeholder="操作数"
                    value={config.processParams?.number || 0}
                    onChange={(e) => handleConfigChange('processParams', { ...config.processParams, number: parseFloat(e.target.value) })}
                    style={{ marginTop: '8px' }}
                  />
                )}
                
                {/* 四舍五入参数 */}
                {config.processParams?.operation === 'round' && (
                  <input
                    type="number"
                    placeholder="保留小数位数"
                    value={config.processParams?.decimals || 0}
                    onChange={(e) => handleConfigChange('processParams', { ...config.processParams, decimals: parseInt(e.target.value) })}
                    min="0"
                    style={{ marginTop: '8px' }}
                  />
                )}
              </div>
            )}
            
            {/* JSON处理参数 */}
            {config.processType === 'json' && (
              <div className="form-group">
                <label>JSON操作</label>
                <select
                  value={config.processParams?.operation || 'parse'}
                  onChange={(e) => handleConfigChange('processParams', { ...config.processParams, operation: e.target.value })}
                >
                  <option value="parse">解析JSON字符串</option>
                  <option value="stringify">转换为JSON字符串</option>
                </select>
              </div>
            )}
            
            {/* 数组处理参数 */}
            {config.processType === 'array' && (
              <div className="form-group">
                <label>数组操作</label>
                <select
                  value={config.processParams?.operation || 'join'}
                  onChange={(e) => handleConfigChange('processParams', { ...config.processParams, operation: e.target.value })}
                >
                  <option value="join">合并为字符串</option>
                  <option value="length">获取数组长度</option>
                  <option value="sort">排序</option>
                </select>
                
                {/* 合并参数 */}
                {config.processParams?.operation === 'join' && (
                  <input
                    type="text"
                    placeholder="分隔符"
                    value={config.processParams?.separator || ','}
                    onChange={(e) => handleConfigChange('processParams', { ...config.processParams, separator: e.target.value })}
                    style={{ marginTop: '8px' }}
                  />
                )}
              </div>
            )}
          </div>
        );

      case 'mcp':
        return (
          <div className="config-form">
            <div className="form-group">
              <label>MCP 工具名称</label>
              <input
                type="text"
                value={config.tool_name || ''}
                onChange={(e) => handleConfigChange('tool_name', e.target.value)}
                placeholder="输入 MCP 工具名称，如: mcp_github_search_code"
              />
            </div>
            <div className="form-group">
              <label>工具参数 (JSON 格式)</label>
              <textarea
                value={config.arguments ? JSON.stringify(config.arguments, null, 2) : '{}'}
                onChange={(e) => {
                  try {
                    const args = JSON.parse(e.target.value);
                    handleConfigChange('arguments', args);
                  } catch (err) {
                    // 允许无效的 JSON 在输入过程中
                  }
                }}
                placeholder='{"query": "搜索关键词", "language": "python"}'
                rows="6"
              />
              <small style={{ color: '#6c757d', marginTop: '4px', display: 'block' }}>
                使用 $变量名 引用上下文变量
              </small>
            </div>
            <div className="form-group">
              <label>超时时间 (秒)</label>
              <input
                type="number"
                value={config.timeout || 30}
                onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value))}
                min="1"
                max="300"
              />
            </div>
          </div>
        );

      default:
        return <p>该节点类型暂无配置选项</p>;
    }
  };

  return (
    <div className="config-panel">
      <h3>节点配置 - {selectedNode.type}</h3>
      <button 
        className="delete-node-button" 
        onClick={() => {
          if (window.confirm('确定要删除此节点吗？删除后无法恢复。')) {
            onDelete(selectedNode.id);
          }
        }}
      >
        删除节点
      </button>
      {renderConfigForm()}
      {renderDataMappingSection()}
    </div>
  );
};

// 主工作流设计器组件
const WorkflowDesigner = ({ workflow, onSave, onExecute }) => {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState(workflow?.name || '新工作流');
  const [workflowVariables, setWorkflowVariables] = useState(workflow?.variables || []);
  const [showVariableManager, setShowVariableManager] = useState(false);
  const [reactFlowInstance, setReactFlowInstance] = useState(null); // 使用状态存储reactFlowInstance
  
  // 当workflow变化时，加载已保存的节点和边
  useEffect(() => {
    if (workflow?.definition) {
      // 加载节点数据
      if (workflow.definition.nodes && Array.isArray(workflow.definition.nodes)) {
        setNodes(workflow.definition.nodes);
      }
      
      // 加载边数据
      if (workflow.definition.edges && Array.isArray(workflow.definition.edges)) {
        setEdges(workflow.definition.edges);
      }
      
      // 更新工作流名称
      if (workflow.name) {
        setWorkflowName(workflow.name);
      }
    }
  }, [workflow, setNodes, setEdges]);

  // 删除节点功能
  const handleDeleteNode = useCallback((nodeId) => {
    // 删除节点
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    // 删除与该节点相关的所有边
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    // 取消选中节点
    setSelectedNode(null);
  }, [setNodes, setEdges, setSelectedNode]);

  const onConnect = useCallback(
    (params) => {
      // 优化节点连接逻辑，确保符合工作流规则
      const { source, target } = params;
      
      // 获取源节点和目标节点
      const sourceNode = nodes.find(node => node.id === source);
      const targetNode = nodes.find(node => node.id === target);
      
      if (!sourceNode || !targetNode) return;
      
      // 检查连接规则
      const isValidConnection = () => {
        // 开始节点不能作为目标节点
        if (sourceNode.type === 'start' && targetNode.type === 'start') return false;
        
        // 结束节点不能作为源节点
        if (sourceNode.type === 'end') return false;
        
        // 开始节点只能连接到其他节点，不能作为目标节点
        if (targetNode.type === 'start') return false;
        
        // 结束节点只能接收连接，不能作为源节点
        if (targetNode.type === 'end' && sourceNode.type === 'end') return false;
        
        // 其他节点可以正常连接
        return true;
      };
      
      if (isValidConnection()) {
        setEdges((eds) => addEdge(params, eds));
      }
    },
    [nodes, setEdges]
  );

  // 计算拖拽放置位置，考虑ReactFlow的视图变换
  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      if (!reactFlowWrapper.current || !reactFlowInstance) return;

      // 获取鼠标在ReactFlow画布中的位置
      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top
      });

      // 网格对齐（可选，根据需要调整网格大小）
      const gridSize = 20;
      const alignedPosition = {
        x: Math.round(position.x / gridSize) * gridSize,
        y: Math.round(position.y / gridSize) * gridSize
      };

      const newNode = {
        id: `${type}-${Date.now()}`,
        type,
        position: alignedPosition,
        data: {}, // 空数据对象，节点组件会根据类型显示默认内容
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes, reactFlowInstance]
  );

  // 优化拖拽过程中的视觉反馈
  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    // 添加拖拽过程中的视觉反馈（可以通过CSS实现）
    event.currentTarget.classList.add('drag-over');
  }, []);

  // 移除拖拽结束的视觉反馈
  const onDragLeave = useCallback((event) => {
    event.currentTarget.classList.remove('drag-over');
  }, []);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleConfigUpdate = (nodeId, config) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...config } } : node
      )
    );
  };

  // 工作流变量管理函数
  const addWorkflowVariable = () => {
    const newVariable = {
      id: `var_${Date.now()}`,
      name: '',
      type: 'string',
      defaultValue: '',
      description: ''
    };
    setWorkflowVariables([...workflowVariables, newVariable]);
  };

  const updateWorkflowVariable = (variableId, field, value) => {
    const updatedVariables = workflowVariables.map(variable => {
      if (variable.id === variableId) {
        return { ...variable, [field]: value };
      }
      return variable;
    });
    setWorkflowVariables(updatedVariables);
  };

  const deleteWorkflowVariable = (variableId) => {
    const updatedVariables = workflowVariables.filter(variable => variable.id !== variableId);
    setWorkflowVariables(updatedVariables);
  };

  const handleSave = () => {
    const workflowData = {
      id: workflow?.id,
      name: workflowName,
      description: workflow?.description || '基于知识图谱的工作流',
      status: workflow?.status || 'draft',
      variables: workflowVariables,
      definition: {
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.type,
          position: node.position,
          data: node.data
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle
        }))
      }
    };
    onSave(workflowData);
  };

  // 渲染工作流变量管理弹窗
  const renderVariableManager = () => {
    if (!showVariableManager) return null;

    return (
      <div className="variable-manager-modal">
        <div className="variable-manager-content">
          <div className="modal-header">
            <h3>工作流变量管理</h3>
            <button className="close-button" onClick={() => setShowVariableManager(false)}>×</button>
          </div>
          <div className="modal-body">
            <table className="variables-table">
              <thead>
                <tr>
                  <th>变量名</th>
                  <th>类型</th>
                  <th>默认值</th>
                  <th>描述</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {workflowVariables.map(variable => (
                  <tr key={variable.id}>
                    <td>
                      <input
                        type="text"
                        value={variable.name}
                        onChange={(e) => updateWorkflowVariable(variable.id, 'name', e.target.value)}
                        placeholder="变量名"
                      />
                    </td>
                    <td>
                      <select
                        value={variable.type}
                        onChange={(e) => updateWorkflowVariable(variable.id, 'type', e.target.value)}
                      >
                        <option value="string">字符串</option>
                        <option value="number">数字</option>
                        <option value="boolean">布尔值</option>
                        <option value="object">对象</option>
                        <option value="array">数组</option>
                      </select>
                    </td>
                    <td>
                      <input
                        type={variable.type === 'boolean' ? 'checkbox' : 'text'}
                        checked={variable.type === 'boolean' ? variable.defaultValue === true : false}
                        value={variable.type === 'boolean' ? '' : variable.defaultValue}
                        onChange={(e) => {
                          const value = variable.type === 'boolean' ? e.target.checked : e.target.value;
                          updateWorkflowVariable(variable.id, 'defaultValue', value);
                        }}
                        placeholder="默认值"
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={variable.description}
                        onChange={(e) => updateWorkflowVariable(variable.id, 'description', e.target.value)}
                        placeholder="描述"
                      />
                    </td>
                    <td>
                      <button className="delete-button" onClick={() => deleteWorkflowVariable(variable.id)}>删除</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button className="add-variable-button" onClick={addWorkflowVariable}>添加变量</button>
          </div>
        </div>
      </div>
    );
  };

  const handleExecute = () => {
    const executionData = {
      workflowId: workflow?.id,
      inputData: {
        workflowDefinition: {
          nodes: nodes,
          edges: edges
        }
      }
    };
    onExecute(executionData);
  };

  return (
    <div className="workflow-designer">
      <div className="designer-header">
        <input
          type="text"
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          className="workflow-name-input"
          placeholder="输入工作流名称"
        />
        <div className="header-actions">
          <button className="variable-button" onClick={() => setShowVariableManager(true)}>变量管理</button>
          <button className="save-button" onClick={handleSave}>保存</button>
          <button className="execute-button" onClick={handleExecute}>执行</button>
        </div>
      </div>
      {renderVariableManager()}
      
      <div className="designer-content">
        <NodePanel onNodeAdd={(type) => {
          const newNode = {
            id: `${type}-${Date.now()}`,
            type,
            position: { x: 100, y: 100 },
            data: {}, // 空数据对象，节点组件会根据类型显示默认内容
          };
          setNodes((nds) => nds.concat(newNode));
        }} />
        
        <div className="flow-container">
          <ReactFlowProvider>
            <div
              className="reactflow-wrapper"
              ref={reactFlowWrapper}
              style={{ width: '100%', height: '600px' }}
            >
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onInit={setReactFlowInstance}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                nodeTypes={nodeTypes}
                fitView
              >
                <Controls />
                <MiniMap />
                <Background variant="dots" gap={12} size={1} />
              </ReactFlow>
            </div>
          </ReactFlowProvider>
        </div>
        
        <NodeConfigPanel 
          selectedNode={selectedNode} 
          onConfigUpdate={handleConfigUpdate} 
          onDelete={handleDeleteNode}
          nodes={nodes}
          edges={edges}
        />
      </div>
    </div>
  );
};

export default WorkflowDesigner;