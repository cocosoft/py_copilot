/**
 * 智能体管理页面
 *
 * 按类型分类管理智能体：
 * - 单一功能智能体（Single-Purpose Agent）
 * - 复合智能体（Composite Agent）
 *
 * 提供创建向导、模板市场等功能
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import './agent-management.css';

/**
 * 智能体管理主组件
 */
function AgentManagement() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // 当前选中的标签页
  const [activeTab, setActiveTab] = useState('my-agents');

  // 智能体类型筛选
  const [agentTypeFilter, setAgentTypeFilter] = useState('all');

  // 智能体列表
  const [agents, setAgents] = useState([]);
  const [totalAgents, setTotalAgents] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 创建向导状态
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [wizardType, setWizardType] = useState(null); // 'single' | 'composite'

  // 加载智能体列表
  const loadAgents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (agentTypeFilter !== 'all') {
        params.append('agent_type', agentTypeFilter);
      }

      const queryString = params.toString();
      const url = queryString ? `/api/v1/agents/?${queryString}` : '/api/v1/agents/';

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
        setTotalAgents(data.total || 0);
      } else {
        setError(t('agentManagement.loadError'));
      }
    } catch (err) {
      console.error('Failed to load agents:', err);
      setError(t('agentManagement.loadError'));
    } finally {
      setLoading(false);
    }
  }, [agentTypeFilter, t]);

  useEffect(() => {
    if (activeTab === 'my-agents') {
      loadAgents();
    }
  }, [activeTab, agentTypeFilter, loadAgents]);

  // 标签页配置
  const tabs = [
    { id: 'my-agents', label: t('agentManagement.tabs.myAgents'), icon: '🤖' },
    { id: 'marketplace', label: t('agentManagement.tabs.marketplace'), icon: '🏪' }
  ];

  // 智能体类型筛选选项
  const typeFilters = [
    { id: 'all', label: t('agentManagement.filters.all'), icon: '🔍' },
    { id: 'single', label: t('agentManagement.filters.single'), icon: '🎯' },
    { id: 'composite', label: t('agentManagement.filters.composite'), icon: '🔧' }
  ];

  // 打开创建向导
  const openCreateWizard = (type) => {
    setWizardType(type);
    setShowCreateWizard(true);
  };

  return (
    <div className="agent-management-container">
      {/* 页面头部 */}
      <div className="agent-management-header">
        <div className="header-content">
          <div>
            <h1 className="page-title">{t('agentManagement.title')}</h1>
            <p className="page-description">{t('agentManagement.description')}</p>
          </div>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="agent-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`agent-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* 我的智能体标签页 */}
      {activeTab === 'my-agents' && (
        <div className="my-agents-section">
          {/* 创建按钮区域 */}
          <div className="create-section">
            <h3 className="section-title">{t('agentManagement.createTitle')}</h3>
            <div className="create-options">
              <div
                className="create-card single"
                onClick={() => openCreateWizard('single')}
              >
                <div className="create-icon">🎯</div>
                <div className="create-content">
                  <h4>{t('agentManagement.createSingle')}</h4>
                  <p>{t('agentManagement.createSingleDesc')}</p>
                </div>
                <div className="create-arrow">→</div>
              </div>

              <div
                className="create-card composite"
                onClick={() => openCreateWizard('composite')}
              >
                <div className="create-icon">🔧</div>
                <div className="create-content">
                  <h4>{t('agentManagement.createComposite')}</h4>
                  <p>{t('agentManagement.createCompositeDesc')}</p>
                </div>
                <div className="create-arrow">→</div>
              </div>
            </div>
          </div>

          {/* 筛选栏 */}
          <div className="filter-section">
            <h3 className="section-title">{t('agentManagement.myAgentsTitle')}</h3>
            <div className="type-filters">
              {typeFilters.map((filter) => (
                <button
                  key={filter.id}
                  className={`type-filter ${agentTypeFilter === filter.id ? 'active' : ''}`}
                  onClick={() => setAgentTypeFilter(filter.id)}
                >
                  <span className="filter-icon">{filter.icon}</span>
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* 智能体列表 */}
          <div className="agents-list">
            {loading ? (
              <div className="loading-state">{t('loading')}</div>
            ) : error ? (
              <div className="error-state">{error}</div>
            ) : agents.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🤖</div>
                <p>{t('agentManagement.noAgents')}</p>
                <p className="empty-hint">{t('agentManagement.createHint')}</p>
              </div>
            ) : (
              <div className="agents-grid">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onClick={() => navigate(`/agents/${agent.id}`)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 市场标签页 */}
      {activeTab === 'marketplace' && (
        <AgentMarketplace />
      )}

      {/* 创建向导模态框 */}
      {showCreateWizard && (
        <CreateAgentWizard
          type={wizardType}
          onClose={() => setShowCreateWizard(false)}
          onSuccess={() => {
            setShowCreateWizard(false);
            loadAgents();
          }}
        />
      )}
    </div>
  );
}

/**
 * 智能体卡片组件
 */
function AgentCard({ agent, onClick }) {
  const { t } = useTranslation();

  const getTypeIcon = () => {
    return agent.agent_type === 'single' ? '🎯' : '🔧';
  };

  const getTypeLabel = () => {
    return agent.agent_type === 'single'
      ? t('agentManagement.types.single')
      : t('agentManagement.types.composite');
  };

  const getTypeClass = () => {
    return agent.agent_type === 'single' ? 'type-single' : 'type-composite';
  };

  return (
    <div className="agent-card" onClick={onClick}>
      <div className="agent-card-header">
        <div className="agent-avatar">{agent.avatar || '🤖'}</div>
        <div className={`agent-type-badge ${getTypeClass()}`}>
          <span className="type-icon">{getTypeIcon()}</span>
          {getTypeLabel()}
        </div>
      </div>

      <div className="agent-card-body">
        <h4 className="agent-name">{agent.name}</h4>
        <p className="agent-description">{agent.description || t('agentManagement.noDescription')}</p>
      </div>

      <div className="agent-card-footer">
        {agent.is_official && (
          <span className="official-badge">🏛️ {t('agentManagement.official')}</span>
        )}
        {agent.is_template && (
          <span className="template-badge">📋 {t('agentManagement.template')}</span>
        )}
      </div>
    </div>
  );
}

/**
 * 智能体市场组件
 */
function AgentMarketplace() {
  const { t } = useTranslation();
  const [activeCategory, setActiveCategory] = useState('all');

  const categories = [
    { id: 'all', label: t('agentManagement.marketplace.all'), icon: '🔍' },
    { id: 'official', label: t('agentManagement.marketplace.official'), icon: '🏛️' },
    { id: 'single', label: t('agentManagement.marketplace.singleTemplates'), icon: '🎯' },
    { id: 'composite', label: t('agentManagement.marketplace.compositeTemplates'), icon: '🔧' }
  ];

  return (
    <div className="marketplace-section">
      {/* 分类筛选 */}
      <div className="marketplace-categories">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`category-btn ${activeCategory === cat.id ? 'active' : ''}`}
            onClick={() => setActiveCategory(cat.id)}
          >
            <span className="category-icon">{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </div>

      {/* 模板列表 */}
      <div className="templates-grid">
        <div className="coming-soon">
          <div className="coming-soon-icon">🏪</div>
          <h3>{t('agentManagement.marketplace.comingSoon')}</h3>
          <p>{t('agentManagement.marketplace.comingSoonDesc')}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 创建智能体向导组件
 */
function CreateAgentWizard({ type, onClose, onSuccess }) {
  const { t } = useTranslation();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    avatar: '🤖',
    agent_type: type,
    primary_capability_id: null,
    primary_capability_type: null,
    capabilities: [],
    orchestration_config: {},
    prompt: '',
    default_model: null
  });

  const totalSteps = type === 'single' ? 3 : 5;

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch('/api/v1/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        onSuccess();
      } else {
        const error = await response.json();
        alert(error.message || t('agentManagement.createError'));
      }
    } catch (err) {
      console.error('Failed to create agent:', err);
      alert(t('agentManagement.createError'));
    }
  };

  const renderStep = () => {
    if (type === 'single') {
      return renderSingleAgentStep();
    } else {
      return renderCompositeAgentStep();
    }
  };

  const renderSingleAgentStep = () => {
    switch (step) {
      case 1:
        return (
          <StepSelectPrimaryCapability
            formData={formData}
            setFormData={setFormData}
            t={t}
          />
        );
      case 2:
        return (
          <StepConfigureParameters
            formData={formData}
            setFormData={setFormData}
            t={t}
          />
        );
      case 3:
        return (
          <StepReviewAndCreate
            formData={formData}
            t={t}
          />
        );
      default:
        return null;
    }
  };

  const renderCompositeAgentStep = () => {
    switch (step) {
      case 1:
        return (
          <StepSelectCapabilities
            formData={formData}
            setFormData={setFormData}
            t={t}
          />
        );
      case 2:
        return (
          <StepConfigureOrchestration
            formData={formData}
            setFormData={setFormData}
            t={t}
          />
        );
      case 3:
        return (
          <StepSetTriggerConditions
            formData={formData}
            setFormData={setFormData}
            t={t}
          />
        );
      case 4:
        return (
          <StepTestAndVerify
            formData={formData}
            setFormData={setFormData}
            t={t}
          />
        );
      case 5:
        return (
          <StepReviewAndCreate
            formData={formData}
            t={t}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="wizard-overlay" onClick={onClose}>
      <div className="wizard-modal" onClick={(e) => e.stopPropagation()}>
        <div className="wizard-header">
          <h2>
            {type === 'single'
              ? t('agentManagement.wizard.singleTitle')
              : t('agentManagement.wizard.compositeTitle')
            }
          </h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="wizard-progress">
          {Array.from({ length: totalSteps }, (_, i) => (
            <div
              key={i}
              className={`progress-step ${i + 1 === step ? 'active' : ''} ${i + 1 < step ? 'completed' : ''}`}
            >
              <div className="step-number">{i + 1}</div>
              <div className="step-line" />
            </div>
          ))}
        </div>

        <div className="wizard-body">
          {renderStep()}
        </div>

        <div className="wizard-footer">
          <button
            className="btn-back"
            onClick={handleBack}
            disabled={step === 1}
          >
            {t('previous')}
          </button>
          <button
            className="btn-next"
            onClick={handleNext}
          >
            {step === totalSteps ? t('create') : t('next')}
          </button>
        </div>
      </div>
    </div>
  );
}

// 向导步骤组件（简化版）
function StepSelectPrimaryCapability({ formData, setFormData, t }) {
  const [capabilities, setCapabilities] = useState([]);

  useEffect(() => {
    // 加载能力列表
    fetch('/api/v1/capability-center/capabilities', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setCapabilities(data.data?.items || []);
        }
      });
  }, []);

  return (
    <div className="wizard-step">
      <h3>{t('agentManagement.wizard.step1Title')}</h3>
      <p className="step-description">{t('agentManagement.wizard.step1Desc')}</p>

      <div className="capability-grid">
        {capabilities.map((cap) => (
          <div
            key={cap.id}
            className={`capability-option ${formData.primary_capability_id === cap.id ? 'selected' : ''}`}
            onClick={() => setFormData({
              ...formData,
              primary_capability_id: cap.id,
              primary_capability_type: cap.type
            })}
          >
            <span className="cap-icon">{cap.icon}</span>
            <span className="cap-name">{cap.display_name}</span>
            <span className={`cap-type ${cap.type}`}>{cap.type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StepConfigureParameters({ formData, setFormData, t }) {
  return (
    <div className="wizard-step">
      <h3>{t('agentManagement.wizard.step2Title')}</h3>
      <p className="step-description">{t('agentManagement.wizard.step2Desc')}</p>

      <div className="form-group">
        <label>{t('agentManagement.wizard.agentName')}</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder={t('agentManagement.wizard.agentNamePlaceholder')}
        />
      </div>

      <div className="form-group">
        <label>{t('agentManagement.wizard.agentDescription')}</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder={t('agentManagement.wizard.agentDescriptionPlaceholder')}
          rows={3}
        />
      </div>

      <div className="form-group">
        <label>{t('agentManagement.wizard.agentAvatar')}</label>
        <div className="avatar-selector">
          {['🤖', '👨‍💻', '👩‍💻', '🎨', '🔍', '📝', '🌐', '💬'].map((emoji) => (
            <button
              key={emoji}
              className={`avatar-option ${formData.avatar === emoji ? 'selected' : ''}`}
              onClick={() => setFormData({ ...formData, avatar: emoji })}
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AgentManagement;

function StepSelectCapabilities({ formData, setFormData, t }) {
  return (
    <div className="wizard-step">
      <h3>{t('agentManagement.wizard.step1CompositeTitle')}</h3>
      <p className="step-description">{t('agentManagement.wizard.step1CompositeDesc')}</p>
      <p className="coming-soon-notice">{t('agentManagement.wizard.comingSoon')}</p>
    </div>
  );
}

function StepConfigureOrchestration({ formData, setFormData, t }) {
  return (
    <div className="wizard-step">
      <h3>{t('agentManagement.wizard.step2CompositeTitle')}</h3>
      <p className="step-description">{t('agentManagement.wizard.step2CompositeDesc')}</p>
      <p className="coming-soon-notice">{t('agentManagement.wizard.comingSoon')}</p>
    </div>
  );
}

function StepSetTriggerConditions({ formData, setFormData, t }) {
  return (
    <div className="wizard-step">
      <h3>{t('agentManagement.wizard.step3CompositeTitle')}</h3>
      <p className="step-description">{t('agentManagement.wizard.step3CompositeDesc')}</p>
      <p className="coming-soon-notice">{t('agentManagement.wizard.comingSoon')}</p>
    </div>
  );
}

function StepTestAndVerify({ formData, setFormData, t }) {
  return (
    <div className="wizard-step">
      <h3>{t('agentManagement.wizard.step4CompositeTitle')}</h3>
      <p className="step-description">{t('agentManagement.wizard.step4CompositeDesc')}</p>
      <p className="coming-soon-notice">{t('agentManagement.wizard.comingSoon')}</p>
    </div>
  );
}

function StepReviewAndCreate({ formData, t }) {
  return (
    <div className="wizard-step">
      <h3>{t('agentManagement.wizard.finalStepTitle')}</h3>
      <p className="step-description">{t('agentManagement.wizard.finalStepDesc')}</p>

      <div className="review-summary">
        <div className="review-item">
          <span className="review-label">{t('agentManagement.wizard.reviewName')}</span>
          <span className="review-value">{formData.name || '-'}</span>
        </div>
        <div className="review-item">
          <span className="review-label">{t('agentManagement.wizard.reviewType')}</span>
          <span className="review-value">
            {formData.agent_type === 'single'
              ? t('agentManagement.types.single')
              : t('agentManagement.types.composite')
            }
          </span>
        </div>
        <div className="review-item">
          <span className="review-label">{t('agentManagement.wizard.reviewAvatar')}</span>
          <span className="review-value">{formData.avatar}</span>
        </div>
      </div>
    </div>
  );
}
