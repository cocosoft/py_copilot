/**
 * 开发中心页面
 *
 * 提供创建Skill、创建Tool、配置MCP的统一入口
 * 是能力中心的子功能模块
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import SkillFormModal from '../components/SkillManagement/SkillFormModal';
import './dev-center.css';

/**
 * 开发中心主组件
 */
function DevCenter() {
  const { t } = useTranslation();
  const [activeModal, setActiveModal] = useState(null);

  /**
   * 开发选项配置
   */
  const devOptions = [
    {
      id: 'skill',
      title: t('devCenter.createSkill'),
      description: t('devCenter.createSkillDesc'),
      icon: '🎯',
      color: '#52c41a',
      action: () => setActiveModal('skill')
    },
    {
      id: 'tool',
      title: t('devCenter.createTool'),
      description: t('devCenter.createToolDesc'),
      icon: '🔧',
      color: '#1890ff',
      action: () => setActiveModal('tool')
    },
    {
      id: 'mcp',
      title: t('devCenter.configMCP'),
      description: t('devCenter.configMCPDesc'),
      icon: '🔗',
      color: '#fa8c16',
      action: () => setActiveModal('mcp')
    }
  ];

  /**
   * 处理创建技能
   */
  const handleCreateSkill = async (skillData) => {
    try {
      const response = await fetch('/api/v1/skills', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(skillData)
      });

      if (response.ok) {
        setActiveModal(null);
        // 可以添加成功提示
        alert(t('devCenter.createSkillSuccess'));
      } else {
        const error = await response.json();
        alert(error.message || t('devCenter.createSkillError'));
      }
    } catch (err) {
      console.error('Failed to create skill:', err);
      alert(t('devCenter.createSkillError'));
    }
  };

  /**
   * 处理创建工具
   */
  const handleCreateTool = async (toolData) => {
    try {
      const response = await fetch('/api/v1/tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(toolData)
      });

      if (response.ok) {
        setActiveModal(null);
        alert(t('devCenter.createToolSuccess'));
      } else {
        const error = await response.json();
        alert(error.message || t('devCenter.createToolError'));
      }
    } catch (err) {
      console.error('Failed to create tool:', err);
      alert(t('devCenter.createToolError'));
    }
  };

  /**
   * 处理配置MCP
   */
  const handleConfigMCP = async (mcpData) => {
    try {
      const response = await fetch('/api/v1/mcp/clients', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(mcpData)
      });

      if (response.ok) {
        setActiveModal(null);
        alert(t('devCenter.configMCPSuccess'));
      } else {
        const error = await response.json();
        alert(error.message || t('devCenter.configMCPError'));
      }
    } catch (err) {
      console.error('Failed to config MCP:', err);
      alert(t('devCenter.configMCPError'));
    }
  };

  /**
   * 渲染工具创建表单
   */
  const renderToolForm = () => (
    <div className="modal-overlay" onClick={() => setActiveModal(null)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('devCenter.createTool')}</h2>
          <button className="close-button" onClick={() => setActiveModal(null)}>×</button>
        </div>
        <div className="modal-body">
          <ToolForm onSubmit={handleCreateTool} onCancel={() => setActiveModal(null)} />
        </div>
      </div>
    </div>
  );

  /**
   * 渲染MCP配置表单
   */
  const renderMCPForm = () => (
    <div className="modal-overlay" onClick={() => setActiveModal(null)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('devCenter.configMCP')}</h2>
          <button className="close-button" onClick={() => setActiveModal(null)}>×</button>
        </div>
        <div className="modal-body">
          <MCPForm onSubmit={handleConfigMCP} onCancel={() => setActiveModal(null)} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="dev-center-container">
      <div className="dev-center-header">
        <h1 className="page-title">{t('devCenter.title')}</h1>
        <p className="page-description">{t('devCenter.description')}</p>
      </div>

      <div className="dev-options-grid">
        {devOptions.map((option) => (
          <div
            key={option.id}
            className="dev-option-card"
            onClick={option.action}
            style={{ '--card-color': option.color }}
          >
            <div className="option-icon" style={{ backgroundColor: `${option.color}15` }}>
              <span style={{ color: option.color }}>{option.icon}</span>
            </div>
            <div className="option-content">
              <h3 className="option-title">{option.title}</h3>
              <p className="option-description">{option.description}</p>
            </div>
            <div className="option-arrow">→</div>
          </div>
        ))}
      </div>

      {/* 模态框 */}
      {activeModal === 'skill' && (
        <SkillFormModal
          onClose={() => setActiveModal(null)}
          onSubmit={handleCreateSkill}
        />
      )}
      {activeModal === 'tool' && renderToolForm()}
      {activeModal === 'mcp' && renderMCPForm()}
    </div>
  );
}

/**
 * 工具创建表单组件
 */
function ToolForm({ onSubmit, onCancel }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category: 'general',
    tool_type: 'local',
    parameters_schema: {},
    config: {},
    icon: '🔧',
    version: '1.0.0'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="dev-form">
      <div className="form-group">
        <label>{t('devCenter.toolName')}</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder={t('devCenter.toolNamePlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.displayName')}</label>
        <input
          type="text"
          value={formData.display_name}
          onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
          placeholder={t('devCenter.displayNamePlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.description')}</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder={t('devCenter.descriptionPlaceholder')}
          rows={3}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.category')}</label>
        <select
          value={formData.category}
          onChange={(e) => setFormData({ ...formData, category: e.target.value })}
        >
          <option value="general">{t('devCenter.categories.general')}</option>
          <option value="search">{t('devCenter.categories.search')}</option>
          <option value="file">{t('devCenter.categories.file')}</option>
          <option value="data">{t('devCenter.categories.data')}</option>
          <option value="api">{t('devCenter.categories.api')}</option>
        </select>
      </div>

      <div className="form-group">
        <label>{t('devCenter.toolType')}</label>
        <select
          value={formData.tool_type}
          onChange={(e) => setFormData({ ...formData, tool_type: e.target.value })}
        >
          <option value="local">{t('devCenter.toolTypes.local')}</option>
          <option value="api">{t('devCenter.toolTypes.api')}</option>
          <option value="script">{t('devCenter.toolTypes.script')}</option>
        </select>
      </div>

      <div className="form-group">
        <label>{t('devCenter.icon')}</label>
        <input
          type="text"
          value={formData.icon}
          onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
          placeholder="🔧"
        />
      </div>

      <div className="form-actions">
        <button type="button" className="btn-cancel" onClick={onCancel}>
          {t('cancel')}
        </button>
        <button type="submit" className="btn-submit">
          {t('create')}
        </button>
      </div>
    </form>
  );
}

export default DevCenter;

/**
 * MCP配置表单组件
 */
function MCPForm({ onSubmit, onCancel }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    server_url: '',
    api_key: '',
    timeout: 30,
    enabled: true
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="dev-form">
      <div className="form-group">
        <label>{t('devCenter.mcpName')}</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder={t('devCenter.mcpNamePlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpDescription')}</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder={t('devCenter.mcpDescriptionPlaceholder')}
          rows={2}
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpServerUrl')}</label>
        <input
          type="url"
          value={formData.server_url}
          onChange={(e) => setFormData({ ...formData, server_url: e.target.value })}
          placeholder={t('devCenter.mcpServerUrlPlaceholder')}
          required
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpApiKey')}</label>
        <input
          type="password"
          value={formData.api_key}
          onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
          placeholder={t('devCenter.mcpApiKeyPlaceholder')}
        />
      </div>

      <div className="form-group">
        <label>{t('devCenter.mcpTimeout')}</label>
        <input
          type="number"
          value={formData.timeout}
          onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
          min={5}
          max={300}
        />
      </div>

      <div className="form-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={formData.enabled}
            onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
          />
          {t('devCenter.mcpEnabled')}
        </label>
      </div>

      <div className="form-actions">
        <button type="button" className="btn-cancel" onClick={onCancel}>
          {t('cancel')}
        </button>
        <button type="submit" className="btn-submit">
          {t('save')}
        </button>
      </div>
    </form>
  );
}
