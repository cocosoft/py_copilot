/**
 * 配额管理组件
 * 提供用户配额管理功能
 */

import React, { useState } from 'react';
import { useAllQuotas, useSetQuota, useUpdateQuota, useQuotaHistory } from '../../hooks/useModelManagement';
import { useI18n } from '../../hooks/useI18n';
import './quota.css';

const QuotaManagement = () => {
  const { t } = useI18n('model');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [editingQuota, setEditingQuota] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: quotasData, isLoading, error, refetch } = useAllQuotas({
    search: searchTerm,
  });

  const setQuotaMutation = useSetQuota();
  const updateQuotaMutation = useUpdateQuota();

  const quotas = quotasData?.data?.items || [];

  const handleCreate = () => {
    setEditingQuota(null);
    setIsModalOpen(true);
  };

  const handleEdit = (quota) => {
    setEditingQuota(quota);
    setIsModalOpen(true);
  };

  const handleDelete = async (userId) => {
    if (window.confirm(t('quota.confirmDelete'))) {
      try {
        await updateQuotaMutation.mutateAsync({ userId, data: { limit: 0 } });
        refetch();
      } catch (error) {
        console.error('删除配额失败:', error);
      }
    }
  };

  const handleViewHistory = (userId) => {
    setSelectedUserId(userId);
    setIsHistoryModalOpen(true);
  };

  const handleSubmit = async (data) => {
    try {
      if (editingQuota) {
        await updateQuotaMutation.mutateAsync({ userId: editingQuota.user_id, data });
      } else {
        await setQuotaMutation.mutateAsync(data);
      }
      setIsModalOpen(false);
      refetch();
    } catch (error) {
      console.error('保存配额失败:', error);
    }
  };

  const getUsagePercentage = (used, limit) => {
    if (limit === 0) return 0;
    return Math.round((used / limit) * 100);
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return '#dc3545';
    if (percentage >= 70) return '#ffc107';
    return '#28a745';
  };

  if (isLoading) {
    return <div className="loading">{t('common.loading')}</div>;
  }

  if (error) {
    return <div className="error">{t('quota.loadError')}: {error.message}</div>;
  }

  return (
    <div className="quota-management">
      <div className="quota-header">
        <h2>{t('quota.title')}</h2>
        <button className="btn btn-primary" onClick={handleCreate}>
          {t('quota.create')}
        </button>
      </div>

      <div className="quota-filters">
        <input
          type="text"
          className="search-input"
          placeholder={t('quota.searchPlaceholder')}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="quota-list">
        {quotas.length === 0 ? (
          <div className="empty-state">
            <p>{t('quota.noQuotas')}</p>
          </div>
        ) : (
          quotas.map((quota) => {
            const percentage = getUsagePercentage(quota.used, quota.limit);
            const color = getUsageColor(percentage);

            return (
              <div key={quota.user_id} className="quota-item">
                <div className="quota-info">
                  <h3>{quota.username || quota.user_id}</h3>
                  <p className="quota-user-id">{t('quota.userId')}: {quota.user_id}</p>
                  <div className="quota-details">
                    <div className="quota-usage-bar">
                      <div
                        className="quota-usage-fill"
                        style={{ width: `${percentage}%`, backgroundColor: color }}
                      />
                    </div>
                    <div className="quota-usage-text">
                      <span className="quota-used">{quota.used.toLocaleString()}</span>
                      <span className="quota-separator">/</span>
                      <span className="quota-limit">{quota.limit.toLocaleString()}</span>
                      <span className="quota-percentage">({percentage}%)</span>
                    </div>
                  </div>
                  <div className="quota-meta">
                    <span className="quota-period">{t('quota.period')}: {quota.period}</span>
                    <span className="quota-updated">
                      {t('quota.updatedAt')}: {new Date(quota.updated_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="quota-actions">
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleViewHistory(quota.user_id)}
                  >
                    {t('quota.history')}
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleEdit(quota)}
                  >
                    {t('common.edit')}
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(quota.user_id)}
                    disabled={updateQuotaMutation.isLoading}
                  >
                    {t('common.delete')}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {isModalOpen && (
        <QuotaModal
          quota={editingQuota}
          onSubmit={handleSubmit}
          onCancel={() => setIsModalOpen(false)}
        />
      )}

      {isHistoryModalOpen && (
        <QuotaHistoryModal
          userId={selectedUserId}
          onClose={() => setIsHistoryModalOpen(false)}
        />
      )}
    </div>
  );
};

const QuotaModal = ({ quota, onSubmit, onCancel }) => {
  const { t } = useI18n(['model', 'common']);
  const [formData, setFormData] = useState({
    user_id: quota?.user_id || '',
    limit: quota?.limit || 1000,
    period: quota?.period || 'monthly',
    alert_threshold: quota?.alert_threshold || 80,
  });

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value, 10) : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal quota-modal">
        <div className="modal-header">
          <h3>{quota ? t('quota.edit') : t('quota.create')}</h3>
          <button className="modal-close" onClick={onCancel}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label>{t('quota.userId')}</label>
            <input
              type="text"
              name="user_id"
              value={formData.user_id}
              onChange={handleChange}
              required
              disabled={!!quota}
            />
          </div>

          <div className="form-group">
            <label>{t('quota.limit')}</label>
            <input
              type="number"
              name="limit"
              value={formData.limit}
              onChange={handleChange}
              required
              min="0"
            />
          </div>

          <div className="form-group">
            <label>{t('quota.period')}</label>
            <select
              name="period"
              value={formData.period}
              onChange={handleChange}
            >
              <option value="daily">{t('quota.periods.daily')}</option>
              <option value="weekly">{t('quota.periods.weekly')}</option>
              <option value="monthly">{t('quota.periods.monthly')}</option>
              <option value="yearly">{t('quota.periods.yearly')}</option>
            </select>
          </div>

          <div className="form-group">
            <label>{t('quota.alertThreshold')}</label>
            <input
              type="number"
              name="alert_threshold"
              value={formData.alert_threshold}
              onChange={handleChange}
              required
              min="0"
              max="100"
            />
            <small>{t('quota.alertThresholdHint')}</small>
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

const QuotaHistoryModal = ({ userId, onClose }) => {
  const { t } = useI18n(['model', 'common']);
  const { data: historyData, isLoading } = useQuotaHistory(userId);

  const history = historyData?.data?.items || [];

  return (
    <div className="modal-overlay">
      <div className="modal quota-history-modal">
        <div className="modal-header">
          <h3>{t('quota.historyTitle', { userId })}</h3>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">
          {isLoading ? (
            <div className="loading">{t('common.loading')}</div>
          ) : history.length === 0 ? (
            <div className="empty-state">
              <p>{t('quota.noHistory')}</p>
            </div>
          ) : (
            <div className="quota-history-list">
              {history.map((item) => (
                <div key={item.id} className="quota-history-item">
                  <div className="history-info">
                    <div className="history-header">
                      <span className="history-amount">{item.amount.toLocaleString()}</span>
                      <span className="history-type">
                        {t(`quota.historyTypes.${item.type}`)}
                      </span>
                    </div>
                    <p className="history-date">
                      {new Date(item.created_at).toLocaleString()}
                    </p>
                    <p className="history-description">
                      {item.description || '-'}
                    </p>
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

export default QuotaManagement;
