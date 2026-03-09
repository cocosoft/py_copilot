/**
 * 配置管理组件
 * 提供配置中心化管理功能
 */

import React, { useState } from 'react';
import { useConfigs, useCreateConfig, useUpdateConfig, useDeleteConfig, useConfigHistory, useRollbackConfig } from '../../hooks/useModelManagement';
import { useI18n } from '../../hooks/useI18n';
import './config.css';

const ConfigManagement = () => {
  const { t } = useI18n('model');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [selectedConfigKey, setSelectedConfigKey] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEnvironment, setSelectedEnvironment] = useState('production');

  const { data: configsData, isLoading, error, refetch } = useConfigs({
    search: searchTerm,
    environment: selectedEnvironment,
  });

  const createMutation = useCreateConfig();
  const updateMutation = useUpdateConfig();
  const deleteMutation = useDeleteConfig();

  const configs = configsData?.data?.items || [];

  const handleCreate = () => {
    setEditingConfig(null);
    setIsModalOpen(true);
  };

  const handleEdit = (config) => {
    setEditingConfig(config);
    setIsModalOpen(true);
  };

  const handleDelete = async (key) => {
    if (window.confirm(t('config.confirmDelete'))) {
      try {
        await deleteMutation.mutateAsync(key);
        refetch();
      } catch (error) {
        console.error('删除配置失败:', error);
      }
    }
  };

  const handleViewHistory = (key) => {
    setSelectedConfigKey(key);
    setIsHistoryModalOpen(true);
  };

  const handleSubmit = async (data) => {
    try {
      if (editingConfig) {
        await updateMutation.mutateAsync({ key: editingConfig.key, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      setIsModalOpen(false);
      refetch();
    } catch (error) {
      console.error('保存配置失败:', error);
    }
  };

  const getEnvironmentBadge = (environment) => {
    const badges = {
      development: { color: '#ffc107', label: t('config.environments.development') },
      staging: { color: '#17a2b8', label: t('config.environments.staging') },
      production: { color: '#28a745', label: t('config.environments.production') },
    };
    const badge = badges[environment] || badges.development;
    return (
      <span className="environment-badge" style={{ backgroundColor: badge.color }}>
        {badge.label}
      </span>
    );
  };

  const formatValue = (value) => {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  };

  if (isLoading) {
    return <div className="loading">{t('common.loading')}</div>;
  }

  if (error) {
    return <div className="error">{t('config.loadError')}: {error.message}</div>;
  }

  return (
    <div className="config-management">
      <div className="config-header">
        <h2>{t('config.title')}</h2>
        <button className="btn btn-primary" onClick={handleCreate}>
          {t('config.create')}
        </button>
      </div>

      <div className="config-filters">
        <input
          type="text"
          className="search-input"
          placeholder={t('config.searchPlaceholder')}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          className="environment-filter"
          value={selectedEnvironment}
          onChange={(e) => setSelectedEnvironment(e.target.value)}
        >
          <option value="development">{t('config.environments.development')}</option>
          <option value="staging">{t('config.environments.staging')}</option>
          <option value="production">{t('config.environments.production')}</option>
        </select>
      </div>

      <div className="config-list">
        {configs.length === 0 ? (
          <div className="empty-state">
            <p>{t('config.noConfigs')}</p>
          </div>
        ) : (
          configs.map((config) => (
            <div key={config.key} className="config-item">
              <div className="config-info">
                <div className="config-header-row">
                  <h3>{config.key}</h3>
                  {getEnvironmentBadge(config.environment)}
                </div>
                <p className="config-description">{config.description || '-'}</p>
                <div className="config-details">
                  <span className="config-type">{config.type}</span>
                  <span className="config-version">v{config.version}</span>
                  <span className="config-updated">
                    {new Date(config.updated_at).toLocaleString()}
                  </span>
                </div>
              </div>
              <div className="config-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleViewHistory(config.key)}
                >
                  {t('config.history')}
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleEdit(config)}
                >
                  {t('common.edit')}
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(config.key)}
                  disabled={deleteMutation.isLoading}
                >
                  {t('common.delete')}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {isModalOpen && (
        <ConfigModal
          config={editingConfig}
          onSubmit={handleSubmit}
          onCancel={() => setIsModalOpen(false)}
        />
      )}

      {isHistoryModalOpen && (
        <ConfigHistoryModal
          configKey={selectedConfigKey}
          onClose={() => setIsHistoryModalOpen(false)}
        />
      )}
    </div>
  );
};

const ConfigModal = ({ config, onSubmit, onCancel }) => {
  const { t } = useI18n(['model', 'common']);
  const [formData, setFormData] = useState({
    key: config?.key || '',
    value: config?.value || '',
    type: config?.type || 'string',
    description: config?.description || '',
    environment: config?.environment || 'production',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal config-modal">
        <div className="modal-header">
          <h3>{config ? t('config.edit') : t('config.create')}</h3>
          <button className="modal-close" onClick={onCancel}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label>{t('config.key')}</label>
            <input
              type="text"
              name="key"
              value={formData.key}
              onChange={handleChange}
              required
              disabled={!!config}
            />
          </div>

          <div className="form-group">
            <label>{t('config.value')}</label>
            <textarea
              name="value"
              value={formData.value}
              onChange={handleChange}
              required
              rows={10}
            />
          </div>

          <div className="form-group">
            <label>{t('config.valueType')}</label>
            <select
              name="type"
              value={formData.type}
              onChange={handleChange}
            >
              <option value="string">{t('config.valueTypes.string')}</option>
              <option value="number">{t('config.valueTypes.number')}</option>
              <option value="boolean">{t('config.valueTypes.boolean')}</option>
              <option value="json">{t('config.valueTypes.json')}</option>
            </select>
          </div>

          <div className="form-group">
            <label>{t('config.environment')}</label>
            <select
              name="environment"
              value={formData.environment}
              onChange={handleChange}
            >
              <option value="development">{t('config.environments.development')}</option>
              <option value="staging">{t('config.environments.staging')}</option>
              <option value="production">{t('config.environments.production')}</option>
            </select>
          </div>

          <div className="form-group">
            <label>{t('config.description')}</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
            />
          </div>
        </form>
        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            {t('common.cancel')}
          </button>
          <button type="submit" className="btn btn-primary" onClick={handleSubmit}>
            {t('common.save')}
          </button>
        </div>
      </div>
    </div>
  );
};

const ConfigHistoryModal = ({ configKey, onClose }) => {
  const { t } = useI18n(['model', 'common']);
  const { data: historyData, isLoading } = useConfigHistory(configKey);
  const rollbackMutation = useRollbackConfig();

  const history = historyData?.data?.items || [];

  const handleRollback = async (versionId) => {
    if (window.confirm(t('config.confirmRollback'))) {
      try {
        await rollbackMutation.mutateAsync({ key: configKey, data: { version_id: versionId } });
        onClose();
      } catch (error) {
        console.error('回滚配置失败:', error);
      }
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal config-history-modal">
        <div className="modal-header">
          <h3>{t('config.historyTitle', { key: configKey })}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">
          {isLoading ? (
            <div className="loading">{t('common.loading')}</div>
          ) : history.length === 0 ? (
            <div className="empty-state">
              <p>{t('config.noHistory')}</p>
            </div>
          ) : (
            <div className="config-history-list">
              {history.map((item) => (
                <div key={item.id} className="config-history-item">
                  <div className="history-info">
                    <div className="history-header">
                      <span className="version-badge">v{item.version}</span>
                      <span className="history-date">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="history-changed-by">
                      {t('config.changedBy')}: {item.changed_by}
                    </p>
                    <p className="history-change-reason">
                      {t('config.changeReason')}: {item.change_reason || '-'}
                    </p>
                  </div>
                  <div className="history-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleRollback(item.id)}
                      disabled={rollbackMutation.isLoading}
                    >
                      {t('config.rollback')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfigManagement;
