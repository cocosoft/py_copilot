/**
 * 重新切片对话框组件
 *
 * 用于重新切分文档，优化实体提取性能
 */

import React, { useState, useEffect } from 'react';
import { FiScissors, FiAlertTriangle, FiInfo, FiCheck } from 'react-icons/fi';
import { Modal, Button } from '../../UI';
import { message } from '../../UI/Message/Message';
import { getDocumentChunkStats, rechunkDocument } from '../../../utils/api/knowledgeApi';
import './styles.css';

/**
 * 重新切片对话框
 */
const RechunkDialog = ({ documentId, documentTitle, visible, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [config, setConfig] = useState({
    maxChunkSize: 1500,
    minChunkSize: 300,
    overlap: 100
  });

  // 加载切片统计
  useEffect(() => {
    if (visible && documentId) {
      loadStats();
    }
  }, [visible, documentId]);

  const loadStats = async () => {
    try {
      const data = await getDocumentChunkStats(documentId);
      setStats(data);
    } catch (error) {
      console.error('加载切片统计失败:', error);
      message.error('加载切片统计失败');
    }
  };

  const handleRechunk = async () => {
    try {
      setLoading(true);
      const result = await rechunkDocument(documentId, config);
      message.success(`重新切片成功！生成 ${result.new_chunks} 个新切片`);
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('重新切片失败:', error);
      message.error('重新切片失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num === undefined || num === null) return '-';
    return num.toLocaleString();
  };

  return (
    <Modal
      isOpen={visible}
      onClose={onClose}
      title="重新切片文档"
      size="large"
      footer={
        <div className="rechunk-dialog-footer">
          <Button onClick={onClose} disabled={loading}>
            取消
          </Button>
          <Button
            type="primary"
            onClick={handleRechunk}
            loading={loading}
            icon={<FiScissors />}
          >
            开始重新切片
          </Button>
        </div>
      }
    >
      <div className="rechunk-dialog-content">
        {/* 文档信息 */}
        <div className="rechunk-section">
          <h4>文档信息</h4>
          <div className="rechunk-info-grid">
            <div className="rechunk-info-item">
              <span className="label">文档标题:</span>
              <span className="value" title={documentTitle}>
                {documentTitle || '-'}
              </span>
            </div>
            <div className="rechunk-info-item">
              <span className="label">文档ID:</span>
              <span className="value">{documentId}</span>
            </div>
          </div>
        </div>

        {/* 当前切片统计 */}
        {stats && (
          <div className="rechunk-section">
            <h4>当前切片统计</h4>
            <div className="rechunk-stats-grid">
              <div className="rechunk-stat-card">
                <span className="stat-value">{formatNumber(stats.chunk_count)}</span>
                <span className="stat-label">切片数量</span>
              </div>
              <div className="rechunk-stat-card">
                <span className="stat-value">{formatNumber(stats.avg_chunk_length)}</span>
                <span className="stat-label">平均大小(字符)</span>
              </div>
              <div className="rechunk-stat-card">
                <span className="stat-value">{formatNumber(stats.max_chunk_length)}</span>
                <span className="stat-label">最大切片(字符)</span>
              </div>
              <div className="rechunk-stat-card">
                <span className="stat-value">{formatNumber(stats.entity_count)}</span>
                <span className="stat-label">实体数量</span>
              </div>
            </div>

            {stats.needs_rechunking && (
              <div className="rechunk-warning">
                <FiAlertTriangle />
                <span>检测到切片过大（最大 {formatNumber(stats.max_chunk_length)} 字符），建议重新切片以优化实体提取性能</span>
              </div>
            )}

            {!stats.needs_rechunking && stats.chunk_count > 0 && (
              <div className="rechunk-info">
                <FiCheck />
                <span>切片大小正常，无需重新切片</span>
              </div>
            )}
          </div>
        )}

        {/* 切片配置 */}
        <div className="rechunk-section">
          <h4>切片配置</h4>
          <div className="rechunk-config-form">
            <div className="form-item">
              <label>最大切片大小 (字符)</label>
              <input
                type="number"
                value={config.maxChunkSize}
                onChange={(e) => setConfig({ ...config, maxChunkSize: parseInt(e.target.value) || 1500 })}
                min={500}
                max={5000}
                step={100}
              />
              <span className="form-hint">建议: 1000-2000</span>
            </div>

            <div className="form-item">
              <label>最小切片大小 (字符)</label>
              <input
                type="number"
                value={config.minChunkSize}
                onChange={(e) => setConfig({ ...config, minChunkSize: parseInt(e.target.value) || 300 })}
                min={100}
                max={1000}
                step={50}
              />
              <span className="form-hint">建议: 200-500</span>
            </div>

            <div className="form-item">
              <label>重叠大小 (字符)</label>
              <input
                type="number"
                value={config.overlap}
                onChange={(e) => setConfig({ ...config, overlap: parseInt(e.target.value) || 100 })}
                min={0}
                max={500}
                step={50}
              />
              <span className="form-hint">建议: 50-200，保持上下文连续性</span>
            </div>
          </div>
        </div>

        {/* 警告提示 */}
        <div className="rechunk-section">
          <div className="rechunk-notice">
            <FiInfo />
            <div className="notice-content">
              <p><strong>注意：</strong></p>
              <ul>
                <li>重新切片会删除所有旧切片和已提取的实体</li>
                <li>重新切片后需要重新执行实体提取</li>
                <li>此操作不可撤销</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default RechunkDialog;
