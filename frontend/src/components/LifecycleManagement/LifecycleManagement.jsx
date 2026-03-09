/**
 * 生命周期管理组件
 * 提供模型生命周期管理功能
 */

import React, { useState } from 'react';
import { useLifecycle, useRequestTransition, useTransitionHistory, usePendingApprovals, useApproveTransition, useCreateDeprecation, useDeprecationNotices } from '../../hooks/useModelManagement';
import { useI18n } from '../../hooks/useI18n';
import './lifecycle.css';

const LifecycleManagement = ({ modelId }) => {
  const { t } = useI18n('model');
  const [activeTab, setActiveTab] = useState('overview');
  const [isTransitionModalOpen, setIsTransitionModalOpen] = useState(false);
  const [isDeprecationModalOpen, setIsDeprecationModalOpen] = useState(false);

  const { data: lifecycleData, isLoading, refetch } = useLifecycle(modelId);
  const { data: historyData } = useTransitionHistory(modelId);
  const { data: approvalsData } = usePendingApprovals();

  const requestTransitionMutation = useRequestTransition();
  const approveTransitionMutation = useApproveTransition();
  const createDeprecationMutation = useCreateDeprecation();

  const lifecycle = lifecycleData?.data;
  const history = historyData?.data?.items || [];
  const pendingApprovals = approvalsData?.data?.items || [];

  const handleRequestTransition = (data) => {
    requestTransitionMutation.mutate(
      { modelId, data },
      {
        onSuccess: () => {
          setIsTransitionModalOpen(false);
          refetch();
        },
      }
    );
  };

  const handleApproveTransition = (approvalId, data) => {
    approveTransitionMutation.mutate(
      { approvalId, data },
      {
        onSuccess: () => {
          refetch();
        },
      }
    );
  };

  const handleCreateDeprecation = (data) => {
    createDeprecationMutation.mutate(
      { modelId, data },
      {
        onSuccess: () => {
          setIsDeprecationModalOpen(false);
          refetch();
        },
      }
    );
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: '#6c757d',
      testing: '#ffc107',
      stable: '#28a745',
      deprecated: '#dc3545',
      archived: '#17a2b8',
    };
    return colors[status] || '#6c757d';
  };

  const getStatusLabel = (status) => {
    return t(`lifecycle.status.${status}`);
  };

  if (isLoading) {
    return <div className="loading">{t('common.loading')}</div>;
  }

  return (
    <div className="lifecycle-management">
      <div className="lifecycle-header">
        <h2>{t('lifecycle.title')}</h2>
        <div className="lifecycle-actions">
          <button
            className="btn btn-primary"
            onClick={() => setIsTransitionModalOpen(true)}
          >
            {t('lifecycle.requestTransition')}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setIsDeprecationModalOpen(true)}
          >
            {t('lifecycle.createDeprecation')}
          </button>
        </div>
      </div>

      <div className="lifecycle-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          {t('lifecycle.tabs.overview')}
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          {t('lifecycle.tabs.history')}
        </button>
        <button
          className={`tab ${activeTab === 'approvals' ? 'active' : ''}`}
          onClick={() => setActiveTab('approvals')}
        >
          {t('lifecycle.tabs.approvals')}
          {pendingApprovals.length > 0 && (
            <span className="badge">{pendingApprovals.length}</span>
          )}
        </button>
      </div>

      <div className="lifecycle-content">
        {activeTab === 'overview' && lifecycle && (
          <LifecycleOverview
            lifecycle={lifecycle}
            getStatusColor={getStatusColor}
            getStatusLabel={getStatusLabel}
          />
        )}

        {activeTab === 'history' && (
          <TransitionHistory history={history} />
        )}

        {activeTab === 'approvals' && (
          <PendingApprovals
            approvals={pendingApprovals}
            onApprove={handleApproveTransition}
          />
        )}
      </div>

      {isTransitionModalOpen && (
        <TransitionModal
          onSubmit={handleRequestTransition}
          onCancel={() => setIsTransitionModalOpen(false)}
        />
      )}

      {isDeprecationModalOpen && (
        <DeprecationModal
          onSubmit={handleCreateDeprecation}
          onCancel={() => setIsDeprecationModalOpen(false)}
        />
      )}
    </div>
  );
};

const LifecycleOverview = ({ lifecycle, getStatusColor, getStatusLabel }) => {
  const { t } = useI18n('model');

  return (
    <div className="lifecycle-overview">
      <div className="status-card">
        <h3>{t('lifecycle.currentStatus')}</h3>
        <div
          className="status-indicator"
          style={{ backgroundColor: getStatusColor(lifecycle.current_status) }}
        >
          {getStatusLabel(lifecycle.current_status)}
        </div>
      </div>

      <div className="status-flow">
        <h3>{t('lifecycle.statusFlow')}</h3>
        <div className="flow-diagram">
          {['draft', 'testing', 'stable', 'deprecated', 'archived'].map((status, index) => (
            <React.Fragment key={status}>
              <div
                className={`flow-node ${status === lifecycle.current_status ? 'active' : ''}`}
                style={{ borderColor: getStatusColor(status) }}
              >
                <div
                  className="node-dot"
                  style={{ backgroundColor: getStatusColor(status) }}
                />
                <span>{getStatusLabel(status)}</span>
              </div>
              {index < 4 && <div className="flow-arrow">→</div>}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="lifecycle-info">
        <div className="info-item">
          <label>{t('lifecycle.createdAt')}</label>
          <span>{new Date(lifecycle.created_at).toLocaleString()}</span>
        </div>
        <div className="info-item">
          <label>{t('lifecycle.updatedAt')}</label>
          <span>{new Date(lifecycle.updated_at).toLocaleString()}</span>
        </div>
        <div className="info-item">
          <label>{t('lifecycle.version')}</label>
          <span>v{lifecycle.version}</span>
        </div>
      </div>
    </div>
  );
};

const TransitionHistory = ({ history }) => {
  const { t } = useI18n('model');

  return (
    <div className="transition-history">
      {history.length === 0 ? (
        <div className="empty-state">
          <p>{t('lifecycle.noHistory')}</p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className="history-item">
              <div className="history-from">
                {t(`lifecycle.status.${item.from_status}`)}
              </div>
              <div className="history-arrow">→</div>
              <div className="history-to">
                {t(`lifecycle.status.${item.to_status}`)}
              </div>
              <div className="history-info">
                <span className="history-date">
                  {new Date(item.created_at).toLocaleString()}
                </span>
                <span className="history-user">
                  {t('lifecycle.by')}: {item.requested_by}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const PendingApprovals = ({ approvals, onApprove }) => {
  const { t } = useI18n('model');

  return (
    <div className="pending-approvals">
      {approvals.length === 0 ? (
        <div className="empty-state">
          <p>{t('lifecycle.noPendingApprovals')}</p>
        </div>
      ) : (
        <div className="approvals-list">
          {approvals.map((approval) => (
            <div key={approval.id} className="approval-item">
              <div className="approval-info">
                <h4>
                  {t('lifecycle.transition')}: {t(`lifecycle.status.${approval.from_status}`)} →{' '}
                  {t(`lifecycle.status.${approval.to_status}`)}
                </h4>
                <p className="approval-model">
                  {t('lifecycle.model')}: {approval.model_name}
                </p>
                <p className="approval-reason">
                  {t('lifecycle.reason')}: {approval.reason || '-'}
                </p>
                <p className="approval-date">
                  {t('lifecycle.requestedAt')}: {new Date(approval.created_at).toLocaleString()}
                </p>
              </div>
              <div className="approval-actions">
                <button
                  className="btn btn-success btn-sm"
                  onClick={() => onApprove(approval.id, { approved: true })}
                >
                  {t('common.approve')}
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => onApprove(approval.id, { approved: false })}
                >
                  {t('common.reject')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const TransitionModal = ({ onSubmit, onCancel }) => {
  const { t } = useI18n('model');
  const [formData, setFormData] = useState({
    to_status: '',
    reason: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal transition-modal">
        <div className="modal-header">
          <h3>{t('lifecycle.requestTransition')}</h3>
          <button className="modal-close" onClick={onCancel}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label>{t('lifecycle.toStatus')}</label>
            <select
              name="to_status"
              value={formData.to_status}
              onChange={(e) => setFormData({ ...formData, to_status: e.target.value })}
              required
            >
              <option value="">{t('lifecycle.selectStatus')}</option>
              <option value="testing">{t('lifecycle.status.testing')}</option>
              <option value="stable">{t('lifecycle.status.stable')}</option>
              <option value="deprecated">{t('lifecycle.status.deprecated')}</option>
              <option value="archived">{t('lifecycle.status.archived')}</option>
            </select>
          </div>

          <div className="form-group">
            <label>{t('lifecycle.reason')}</label>
            <textarea
              name="reason"
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              rows={4}
            />
          </div>
        </form>
        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            {t('common.cancel')}
          </button>
          <button type="submit" className="btn btn-primary" onClick={handleSubmit}>
            {t('common.submit')}
          </button>
        </div>
      </div>
    </div>
  );
};

const DeprecationModal = ({ onSubmit, onCancel }) => {
  const { t } = useI18n('model');
  const [formData, setFormData] = useState({
    deprecation_date: '',
    reason: '',
    migration_guide: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal deprecation-modal">
        <div className="modal-header">
          <h3>{t('lifecycle.createDeprecation')}</h3>
          <button className="modal-close" onClick={onCancel}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label>{t('lifecycle.deprecationDate')}</label>
            <input
              type="date"
              name="deprecation_date"
              value={formData.deprecation_date}
              onChange={(e) => setFormData({ ...formData, deprecation_date: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label>{t('lifecycle.reason')}</label>
            <textarea
              name="reason"
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              rows={4}
              required
            />
          </div>

          <div className="form-group">
            <label>{t('lifecycle.migrationGuide')}</label>
            <textarea
              name="migration_guide"
              value={formData.migration_guide}
              onChange={(e) => setFormData({ ...formData, migration_guide: e.target.value })}
              rows={6}
            />
          </div>
        </form>
        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            {t('common.cancel')}
          </button>
          <button type="submit" className="btn btn-primary" onClick={handleSubmit}>
            {t('common.submit')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LifecycleManagement;
