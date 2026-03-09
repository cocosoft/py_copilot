/**
 * Webhook管理组件
 * 提供Webhook配置和管理功能
 */

import React, { useState } from 'react';
import { useWebhooks, useCreateWebhook, useUpdateWebhook, useDeleteWebhook, useTestWebhook } from '../../hooks/useModelManagement';
import { useI18n } from '../../hooks/useI18n';
import './webhook.css';

const WebhookManagement = () => {
  const { t } = useI18n('model');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEventTypes, setSelectedEventTypes] = useState([]);

  const { data: webhooksData, isLoading, error, refetch } = useWebhooks({
    search: searchTerm,
    event_types: selectedEventTypes,
  });

  const createMutation = useCreateWebhook();
  const updateMutation = useUpdateWebhook();
  const deleteMutation = useDeleteWebhook();
  const testMutation = useTestWebhook();

  const webhooks = webhooksData?.data?.items || [];

  const handleCreate = () => {
    setEditingWebhook(null);
    setIsModalOpen(true);
  };

  const handleEdit = (webhook) => {
    setEditingWebhook(webhook);
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm(t('webhook.confirmDelete'))) {
      try {
        await deleteMutation.mutateAsync(id);
        refetch();
      } catch (error) {
        console.error('删除Webhook失败:', error);
      }
    }
  };

  const handleTest = async (id) => {
    try {
      await testMutation.mutateAsync(id);
      alert(t('webhook.testSuccess'));
    } catch (error) {
      console.error('测试Webhook失败:', error);
      alert(t('webhook.testFailed'));
    }
  };

  const handleSubmit = async (data) => {
    try {
      if (editingWebhook) {
        await updateMutation.mutateAsync({ id: editingWebhook.id, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      setIsModalOpen(false);
      refetch();
    } catch (error) {
      console.error('保存Webhook失败:', error);
    }
  };

  const getEventTypeLabel = (eventType) => {
    const labels = {
      'model.created': t('webhook.eventTypeOptions.modelCreated'),
      'model.updated': t('webhook.eventTypeOptions.modelUpdated'),
      'model.deleted': t('webhook.eventTypeOptions.modelDeleted'),
      'config.changed': t('webhook.eventTypeOptions.configChanged'),
      'lifecycle.transition': t('webhook.eventTypeOptions.lifecycleTransition'),
    };
    return labels[eventType] || eventType;
  };

  const getStatusBadge = (isActive) => {
    return (
      <span className={`status-badge ${isActive ? 'active' : 'inactive'}`}>
        {isActive ? t('webhook.status.active') : t('webhook.status.inactive')}
      </span>
    );
  };

  if (isLoading) {
    return <div className="loading">{t('common.loading')}</div>;
  }

  if (error) {
    return <div className="error">{t('webhook.loadError')}: {error.message}</div>;
  }

  return (
    <div className="webhook-management">
      <div className="webhook-header">
        <h2>{t('webhook.title')}</h2>
        <button className="btn btn-primary" onClick={handleCreate}>
          {t('webhook.create')}
        </button>
      </div>

      <div className="webhook-filters">
        <input
          type="text"
          className="search-input"
          placeholder={t('webhook.searchPlaceholder')}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          className="event-type-filter"
          value={selectedEventTypes[0] || ''}
          onChange={(e) => setSelectedEventTypes(e.target.value ? [e.target.value] : [])}
        >
          <option value="">{t('webhook.allEventTypes')}</option>
          <option value="model.created">{t('webhook.eventTypeOptions.modelCreated')}</option>
          <option value="model.updated">{t('webhook.eventTypeOptions.modelUpdated')}</option>
          <option value="model.deleted">{t('webhook.eventTypeOptions.modelDeleted')}</option>
          <option value="config.changed">{t('webhook.eventTypeOptions.configChanged')}</option>
          <option value="lifecycle.transition">{t('webhook.eventTypeOptions.lifecycleTransition')}</option>
        </select>
      </div>

      <div className="webhook-list">
        {webhooks.length === 0 ? (
          <div className="empty-state">
            <p>{t('webhook.noWebhooks')}</p>
          </div>
        ) : (
          webhooks.map((webhook) => (
            <div key={webhook.id} className="webhook-item">
              <div className="webhook-info">
                <h3>{webhook.name}</h3>
                <p className="webhook-url">{webhook.url}</p>
                <div className="webhook-details">
                  <span className="event-types">
                    {webhook.event_types.map((type) => getEventTypeLabel(type)).join(', ')}
                  </span>
                  {getStatusBadge(webhook.is_active)}
                </div>
              </div>
              <div className="webhook-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleTest(webhook.id)}
                  disabled={testMutation.isLoading}
                >
                  {t('webhook.test')}
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleEdit(webhook)}
                >
                  {t('common.edit')}
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(webhook.id)}
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
        <WebhookModal
          webhook={editingWebhook}
          onSubmit={handleSubmit}
          onCancel={() => setIsModalOpen(false)}
        />
      )}
    </div>
  );
};

const WebhookModal = ({ webhook, onSubmit, onCancel }) => {
  const { t } = useI18n(['model', 'common']);
  const [formData, setFormData] = useState({
    name: webhook?.name || '',
    url: webhook?.url || '',
    event_types: webhook?.event_types || [],
    secret: webhook?.secret || '',
    is_active: webhook?.is_active ?? true,
  });

  const availableEventTypes = [
    'model.created',
    'model.updated',
    'model.deleted',
    'config.changed',
    'lifecycle.transition',
  ];

  const getEventTypeLabel = (eventType) => {
    const labels = {
      'model.created': t('webhook.eventTypeOptions.modelCreated'),
      'model.updated': t('webhook.eventTypeOptions.modelUpdated'),
      'model.deleted': t('webhook.eventTypeOptions.modelDeleted'),
      'config.changed': t('webhook.eventTypeOptions.configChanged'),
      'lifecycle.transition': t('webhook.eventTypeOptions.lifecycleTransition'),
    };
    return labels[eventType] || eventType;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleEventTypeToggle = (eventType) => {
    setFormData((prev) => ({
      ...prev,
      event_types: prev.event_types.includes(eventType)
        ? prev.event_types.filter((t) => t !== eventType)
        : [...prev.event_types, eventType],
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const generateSecret = () => {
    const secret = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    setFormData((prev) => ({ ...prev, secret }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal webhook-modal">
        <div className="modal-header">
          <h3>{webhook ? t('webhook.edit') : t('webhook.create')}</h3>
          <button className="modal-close" onClick={onCancel}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label>{t('webhook.name')}</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>{t('webhook.url')}</label>
            <input
              type="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>{t('webhook.eventTypes')}</label>
            <div className="event-type-checkboxes">
              {availableEventTypes.map((eventType) => (
                <label key={eventType} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.event_types.includes(eventType)}
                    onChange={() => handleEventTypeToggle(eventType)}
                  />
                  {getEventTypeLabel(eventType)}
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>{t('webhook.secret')}</label>
            <div className="secret-input-group">
              <input
                type="text"
                name="secret"
                value={formData.secret}
                onChange={handleChange}
                required
              />
              <button type="button" className="btn btn-secondary" onClick={generateSecret}>
                {t('webhook.generateSecret')}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
              />
              {t('webhook.isActive')}
            </label>
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

export default WebhookManagement;
