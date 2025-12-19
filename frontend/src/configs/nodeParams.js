// 节点参数定义配置文件
// 为每个节点类型定义输入输出参数结构

export const nodeParamsConfig = {
  // 基础节点
  start: {
    inputs: [], // 开始节点没有输入
    outputs: [
      { name: 'workflowData', type: 'object', description: '工作流初始数据' }
    ]
  },
  end: {
    inputs: [
      { name: 'finalData', type: 'object', description: '工作流最终数据' }
    ],
    outputs: [] // 结束节点没有输出
  },
  branch: {
    inputs: [
      { name: 'inputData', type: 'object', description: '分支前的数据' }
    ],
    outputs: [
      { name: 'branchData', type: 'array', description: '分支数据数组' },
      { name: 'branchCount', type: 'number', description: '分支数量' }
    ]
  },
  condition: {
    inputs: [
      { name: 'conditionField', type: 'any', description: '条件字段值' },
      { name: 'value', type: 'any', description: '比较值' }
    ],
    outputs: [
      { name: 'condition_result', type: 'boolean', description: '条件判断结果' },
      { name: 'next_branch', type: 'string', description: '下一个分支名称' }
    ]
  },
  input: {
    inputs: [], // 输入节点没有输入
    outputs: [
      { name: 'input_field', type: 'string', description: '输入字段名' },
      { name: 'input_value', type: 'any', description: '输入值' }
    ]
  },
  output: {
    inputs: [
      { name: 'output_data', type: 'object', description: '输出数据' }
    ],
    outputs: [
      { name: 'formatted_output', type: 'any', description: '格式化后的输出' },
      { name: 'field_count', type: 'number', description: '输出字段数量' }
    ]
  },
  process: {
    inputs: [
      { name: 'inputField', type: 'any', description: '输入字段值' }
    ],
    outputs: [
      { name: 'outputField', type: 'string', description: '输出字段名' },
      { name: 'processed_value', type: 'any', description: '处理后的值' }
    ]
  },
  
  // 知识图谱节点
  knowledgeSearch: {
    inputs: [
      { name: 'search_query', type: 'string', description: '搜索查询语句' },
      { name: 'knowledge_base_id', type: 'string', description: '知识库ID' },
      { name: 'entity_types', type: 'array', description: '实体类型列表' },
      { name: 'max_results', type: 'number', description: '最大结果数' }
    ],
    outputs: [
      { name: 'results', type: 'array', description: '搜索结果列表' },
      { name: 'total_count', type: 'number', description: '结果总数' },
      { name: 'search_params', type: 'object', description: '搜索参数' }
    ]
  },
  entityExtraction: {
    inputs: [
      { name: 'text_input', type: 'string', description: '用于实体抽取的文本' },
      { name: 'entity_types', type: 'array', description: '实体类型列表' },
      { name: 'confidence_threshold', type: 'number', description: '置信度阈值' }
    ],
    outputs: [
      { name: 'entities', type: 'array', description: '抽取的实体列表' },
      { name: 'total_count', type: 'number', description: '实体总数' },
      { name: 'extraction_params', type: 'object', description: '抽取参数' }
    ]
  },
  relationshipAnalysis: {
    inputs: [
      { name: 'entity_ids', type: 'array', description: '实体ID列表' },
      { name: 'relationship_types', type: 'array', description: '关系类型列表' },
      { name: 'max_depth', type: 'number', description: '分析深度' }
    ],
    outputs: [
      { name: 'relationships', type: 'array', description: '分析的关系列表' },
      { name: 'total_count', type: 'number', description: '关系总数' },
      { name: 'analysis_params', type: 'object', description: '分析参数' }
    ]
  },
  visualization: {
    inputs: [
      { name: 'entity_ids', type: 'array', description: '实体ID列表' },
      { name: 'visualization_type', type: 'string', description: '可视化类型' }
    ],
    outputs: [
      { name: 'data', type: 'object', description: '可视化数据' },
      { name: 'entity_count', type: 'number', description: '实体数量' },
      { name: 'relationship_count', type: 'number', description: '关系数量' }
    ]
  }
};

// 获取节点类型的输入参数
export const getNodeInputs = (nodeType) => {
  return nodeParamsConfig[nodeType]?.inputs || [];
};

// 获取节点类型的输出参数
export const getNodeOutputs = (nodeType) => {
  return nodeParamsConfig[nodeType]?.outputs || [];
};

// 获取所有可能的输入源字段
export const getAllInputSources = (nodes, edges, targetNodeId) => {
  const inputSources = [];
  
  // 查找所有指向目标节点的边
  const incomingEdges = edges.filter(edge => edge.target === targetNodeId);
  
  // 遍历每条边，获取源节点的输出参数
  incomingEdges.forEach(edge => {
    const sourceNode = nodes.find(node => node.id === edge.source);
    if (sourceNode) {
      const outputs = getNodeOutputs(sourceNode.type);
      outputs.forEach(output => {
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
  });
  
  return inputSources;
};