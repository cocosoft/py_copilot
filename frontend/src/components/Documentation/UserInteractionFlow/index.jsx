/**
 * 用户交互流程图组件
 *
 * 展示用户交互流程
 *
 * 任务编号: Phase2-Week5
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState } from 'react';
import { Card, Button, Badge } from '../../UnifiedComponentLibrary';

/**
 * 流程步骤组件
 * @param {Object} props - 组件属性
 * @param {Object} props.step - 步骤数据
 * @param {number} props.index - 步骤索引
 * @param {boolean} props.isActive - 是否激活
 * @param {Function} props.onClick - 点击回调
 */
const FlowStep = ({ step, index, isActive, onClick }) => {
  const stepIcons = {
    start: '🚀',
    input: '⌨️',
    process: '⚙️',
    decision: '❓',
    output: '📤',
    end: '✅',
    error: '❌',
    loop: '🔄',
  };

  return (
    <div
      className={`flow-step ${step.type} ${isActive ? 'active' : ''}`}
      onClick={() => onClick?.(step, index)}
    >
      <div className="step-icon">{stepIcons[step.type] || '📍'}</div>
      <div className="step-content">
        <div className="step-title">{step.title}</div>
        <div className="step-description">{step.description}</div>
        {step.details && (
          <div className="step-details">
            {step.details.map((detail, i) => (
              <span key={i} className="detail-item">
                {detail}
              </span>
            ))}
          </div>
        )}
      </div>
      {step.duration && (
        <div className="step-duration">
          <Badge variant="info" size="sm">{step.duration}</Badge>
        </div>
      )}
    </div>
  );
};

/**
 * 流程连接线组件
 * @param {Object} props - 组件属性
 * @param {string} props.type - 连接类型
 * @param {string} props.label - 标签
 */
const FlowConnector = ({ type = 'default', label }) => {
  const connectorStyles = {
    default: '→',
    success: '✓',
    error: '✗',
    loop: '↻',
    decision: {
      yes: '是 →',
      no: '否 →',
    },
  };

  return (
    <div className={`flow-connector ${type}`}>
      <div className="connector-line"></div>
      {label && <div className="connector-label">{label}</div>}
      <div className="connector-arrow">
        {typeof connectorStyles[type] === 'string'
          ? connectorStyles[type]
          : connectorStyles.default}
      </div>
    </div>
  );
};

/**
 * 用户交互流程图组件
 * @param {Object} props - 组件属性
 * @param {string} props.flowType - 流程类型
 */
const UserInteractionFlow = ({ flowType = 'document-upload' }) => {
  const [activeStep, setActiveStep] = useState(null);

  // 流程定义
  const flows = {
    'document-upload': {
      title: '文档上传流程',
      description: '用户上传文档到知识库的完整流程',
      steps: [
        {
          type: 'start',
          title: '开始',
          description: '用户进入文档上传页面',
          details: ['访问权限检查', '页面初始化'],
        },
        {
          type: 'input',
          title: '选择文件',
          description: '用户选择要上传的文档',
          details: ['支持格式: PDF, DOC, TXT', '文件大小限制: 50MB'],
          duration: '< 1s',
        },
        {
          type: 'decision',
          title: '文件验证',
          description: '系统验证文件格式和大小',
          details: ['格式检查', '大小检查', '病毒扫描'],
          duration: '< 1s',
        },
        {
          type: 'process',
          title: '文档解析',
          description: '解析文档内容',
          details: ['文本提取', '格式转换', '编码检测'],
          duration: '1-5s',
        },
        {
          type: 'process',
          title: '内容处理',
          description: '处理文档内容',
          details: ['分词处理', '实体识别', '语义分析'],
          duration: '2-10s',
        },
        {
          type: 'process',
          title: '向量化',
          description: '生成文档向量',
          details: ['文本向量化', '特征提取', '索引构建'],
          duration: '3-15s',
        },
        {
          type: 'decision',
          title: '处理结果',
          description: '检查处理是否成功',
          details: ['结果验证', '错误处理'],
        },
        {
          type: 'output',
          title: '保存到知识库',
          description: '保存处理后的文档',
          details: ['数据存储', '索引更新', '关联建立'],
          duration: '< 2s',
        },
        {
          type: 'end',
          title: '完成',
          description: '文档上传成功',
          details: ['成功提示', '页面跳转'],
        },
      ],
    },
    'semantic-search': {
      title: '语义搜索流程',
      description: '用户执行语义搜索的完整流程',
      steps: [
        {
          type: 'start',
          title: '开始',
          description: '用户进入搜索页面',
        },
        {
          type: 'input',
          title: '输入查询',
          description: '用户输入搜索关键词',
          details: ['实时建议', '历史记录', '热门搜索'],
          duration: '< 1s',
        },
        {
          type: 'process',
          title: '查询分析',
          description: '分析用户查询意图',
          details: ['关键词提取', '意图识别', '查询扩展'],
          duration: '< 1s',
        },
        {
          type: 'process',
          title: '语义向量化',
          description: '将查询转换为向量',
          details: ['文本编码', '向量生成', '语义理解'],
          duration: '< 1s',
        },
        {
          type: 'process',
          title: '相似度计算',
          description: '计算与文档的相似度',
          details: ['向量比对', '相似度排序', '结果筛选'],
          duration: '1-3s',
        },
        {
          type: 'process',
          title: '结果重排序',
          description: '对搜索结果进行重排序',
          details: ['相关性评分', '个性化调整', '多样性优化'],
          duration: '< 1s',
        },
        {
          type: 'output',
          title: '展示结果',
          description: '显示搜索结果',
          details: ['结果列表', '高亮显示', '分页加载'],
          duration: '< 1s',
        },
        {
          type: 'decision',
          title: '用户反馈',
          description: '收集用户反馈',
          details: ['点击率', '满意度', '改进建议'],
        },
        {
          type: 'end',
          title: '完成',
          description: '搜索流程结束',
        },
      ],
    },
    'entity-recognition': {
      title: '实体识别流程',
      description: '实体识别功能的完整流程',
      steps: [
        {
          type: 'start',
          title: '开始',
          description: '用户进入实体识别页面',
        },
        {
          type: 'input',
          title: '配置参数',
          description: '用户配置识别参数',
          details: ['实体类型选择', '置信度设置', '处理选项'],
          duration: '< 1s',
        },
        {
          type: 'input',
          title: '输入文本',
          description: '用户输入待识别文本',
          details: ['文本输入', '文件上传', '实时预览'],
          duration: '< 1s',
        },
        {
          type: 'process',
          title: '预处理',
          description: '文本预处理',
          details: ['分词', '词性标注', '句法分析'],
          duration: '< 1s',
        },
        {
          type: 'process',
          title: '实体识别',
          description: '识别文本中的实体',
          details: ['模式匹配', '机器学习', '规则引擎'],
          duration: '1-3s',
        },
        {
          type: 'process',
          title: '实体链接',
          description: '将实体链接到知识库',
          details: ['实体消歧', '知识库查询', '关系建立'],
          duration: '1-2s',
        },
        {
          type: 'output',
          title: '展示结果',
          description: '显示识别结果',
          details: ['实体高亮', '类型标注', '置信度显示'],
          duration: '< 1s',
        },
        {
          type: 'decision',
          title: '用户确认',
          description: '用户确认或修正结果',
          details: ['结果编辑', '批量操作', '保存确认'],
        },
        {
          type: 'end',
          title: '完成',
          description: '实体识别完成',
        },
      ],
    },
    'knowledge-graph': {
      title: '知识图谱浏览流程',
      description: '用户浏览知识图谱的完整流程',
      steps: [
        {
          type: 'start',
          title: '开始',
          description: '用户进入知识图谱页面',
        },
        {
          type: 'process',
          title: '加载图谱',
          description: '加载知识图谱数据',
          details: ['数据获取', '图构建', '布局计算'],
          duration: '2-5s',
        },
        {
          type: 'output',
          title: '渲染图谱',
          description: '渲染可视化图谱',
          details: ['节点渲染', '边渲染', '交互绑定'],
          duration: '1-3s',
        },
        {
          type: 'input',
          title: '用户交互',
          description: '用户与图谱交互',
          details: ['缩放', '拖拽', '筛选', '搜索'],
          duration: '持续',
        },
        {
          type: 'decision',
          title: '选择节点',
          description: '用户选择节点查看详情',
          details: ['单击选择', '双击展开', '右键菜单'],
        },
        {
          type: 'process',
          title: '加载详情',
          description: '加载节点详细信息',
          details: ['属性查询', '关系查询', '关联数据'],
          duration: '< 1s',
        },
        {
          type: 'output',
          title: '展示详情',
          description: '显示节点详情面板',
          details: ['属性列表', '关系图', '相关文档'],
          duration: '< 1s',
        },
        {
          type: 'decision',
          title: '继续浏览',
          description: '用户决定是否继续浏览',
        },
        {
          type: 'end',
          title: '完成',
          description: '浏览结束',
        },
      ],
    },
  };

  const currentFlow = flows[flowType] || flows['document-upload'];

  return (
    <Card className="user-interaction-flow">
      <div className="flow-header">
        <h3>{currentFlow.title}</h3>
        <p className="flow-description">{currentFlow.description}</p>
      </div>

      <div className="flow-type-selector">
        {Object.keys(flows).map((key) => (
          <Button
            key={key}
            variant={flowType === key ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setActiveStep(null)}
          >
            {flows[key].title}
          </Button>
        ))}
      </div>

      <div className="flow-content">
        {currentFlow.steps.map((step, index) => (
          <React.Fragment key={index}>
            <FlowStep
              step={step}
              index={index}
              isActive={activeStep === index}
              onClick={(_, idx) => setActiveStep(idx)}
            />
            {index < currentFlow.steps.length - 1 && (
              <FlowConnector
                type={step.type === 'decision' ? 'decision' : 'default'}
                label={step.type === 'decision' ? '是' : undefined}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {activeStep !== null && (
        <div className="flow-detail-panel">
          <h4>步骤详情</h4>
          <div className="detail-content">
            <div className="detail-item">
              <span className="detail-label">步骤:</span>
              <span className="detail-value">{currentFlow.steps[activeStep].title}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">描述:</span>
              <span className="detail-value">
                {currentFlow.steps[activeStep].description}
              </span>
            </div>
            {currentFlow.steps[activeStep].duration && (
              <div className="detail-item">
                <span className="detail-label">预计耗时:</span>
                <span className="detail-value">
                  {currentFlow.steps[activeStep].duration}
                </span>
              </div>
            )}
            {currentFlow.steps[activeStep].details && (
              <div className="detail-item">
                <span className="detail-label">详细操作:</span>
                <ul className="detail-list">
                  {currentFlow.steps[activeStep].details.map((detail, i) => (
                    <li key={i}>{detail}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
};

export default UserInteractionFlow;
export { FlowStep, FlowConnector };
