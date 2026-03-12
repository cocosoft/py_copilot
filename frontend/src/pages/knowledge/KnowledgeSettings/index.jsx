/**
 * 知识库设置页面
 * 
 * 管理知识库的配置和参数
 */

import React, { useState, useCallback } from 'react';
import { FiSave, FiTrash2, FiAlertTriangle } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { message } from '../../../components/UI/Message/Message';
import './styles.css';

/**
 * 知识库设置页面
 */
const KnowledgeSettings = () => {
  const { currentKnowledgeBase } = useKnowledgeStore();

  // 本地状态
  const [settings, setSettings] = useState({
    name: currentKnowledgeBase?.name || '',
    description: currentKnowledgeBase?.description || '',
    isPublic: false,
    autoVectorize: true,
    chunkSize: 1000,
    overlap: 200,
    embeddingModel: 'text-embedding-3-small',
    maxFileSize: 100,
    allowedFileTypes: ['.pdf', '.doc', '.docx', '.txt', '.md'],
  });

  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  /**
   * 保存设置
   */
  const handleSave = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setIsSaving(true);
    try {
      // TODO: 替换为实际 API 调用
      // await knowledgeApi.updateKnowledgeBase(currentKnowledgeBase.id, settings);
      
      message.success({ content: '设置已保存' });
    } catch (error) {
      message.error({ content: '保存失败：' + error.message });
    } finally {
      setIsSaving(false);
    }
  }, [currentKnowledgeBase, settings]);

  /**
   * 删除知识库
   */
  const handleDelete = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      // TODO: 替换为实际 API 调用
      // await knowledgeApi.deleteKnowledgeBase(currentKnowledgeBase.id);
      
      message.success({ content: '知识库已删除' });
      // TODO: 跳转到知识库列表
    } catch (error) {
      message.error({ content: '删除失败：' + error.message });
    }
  }, [currentKnowledgeBase]);

  /**
   * 更新设置字段
   */
  const updateSetting = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  if (!currentKnowledgeBase) {
    return (
      <div className="knowledge-settings-empty">
        <div className="empty-icon">⚙️</div>
        <h3>请选择一个知识库</h3>
        <p>从左侧边栏选择一个知识库进行设置</p>
      </div>
    );
  }

  return (
    <div className="knowledge-settings">
      <div className="settings-header">
        <h2>知识库设置</h2>
        <Button
          variant="primary"
          icon={<FiSave />}
          onClick={handleSave}
          loading={isSaving}
        >
          保存设置
        </Button>
      </div>

      <div className="settings-content">
        {/* 基本信息 */}
        <section className="settings-section">
          <h3>基本信息</h3>
          
          <div className="form-group">
            <label>知识库名称</label>
            <input
              type="text"
              value={settings.name}
              onChange={(e) => updateSetting('name', e.target.value)}
              placeholder="输入知识库名称"
            />
          </div>

          <div className="form-group">
            <label>描述</label>
            <textarea
              value={settings.description}
              onChange={(e) => updateSetting('description', e.target.value)}
              placeholder="输入知识库描述"
              rows={4}
            />
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={settings.isPublic}
                onChange={(e) => updateSetting('isPublic', e.target.checked)}
              />
              公开知识库
            </label>
            <p className="help-text">允许其他用户访问此知识库</p>
          </div>
        </section>

        {/* 向量化设置 */}
        <section className="settings-section">
          <h3>向量化设置</h3>
          
          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={settings.autoVectorize}
                onChange={(e) => updateSetting('autoVectorize', e.target.checked)}
              />
              自动向量化
            </label>
            <p className="help-text">上传文档后自动进行向量化处理</p>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>分块大小</label>
              <input
                type="number"
                value={settings.chunkSize}
                onChange={(e) => updateSetting('chunkSize', parseInt(e.target.value))}
                min={100}
                max={10000}
              />
              <p className="help-text">字符数</p>
            </div>

            <div className="form-group">
              <label>重叠大小</label>
              <input
                type="number"
                value={settings.overlap}
                onChange={(e) => updateSetting('overlap', parseInt(e.target.value))}
                min={0}
                max={1000}
              />
              <p className="help-text">字符数</p>
            </div>
          </div>

          <div className="form-group">
            <label>嵌入模型</label>
            <select
              value={settings.embeddingModel}
              onChange={(e) => updateSetting('embeddingModel', e.target.value)}
            >
              <option value="text-embedding-3-small">text-embedding-3-small</option>
              <option value="text-embedding-3-large">text-embedding-3-large</option>
              <option value="text-embedding-ada-002">text-embedding-ada-002</option>
            </select>
          </div>
        </section>

        {/* 文件上传设置 */}
        <section className="settings-section">
          <h3>文件上传设置</h3>
          
          <div className="form-group">
            <label>最大文件大小 (MB)</label>
            <input
              type="number"
              value={settings.maxFileSize}
              onChange={(e) => updateSetting('maxFileSize', parseInt(e.target.value))}
              min={1}
              max={500}
            />
          </div>

          <div className="form-group">
            <label>允许的文件类型</label>
            <div className="file-types">
              {['.pdf', '.doc', '.docx', '.txt', '.md', '.html', '.json'].map(type => (
                <label key={type} className="file-type-checkbox">
                  <input
                    type="checkbox"
                    checked={settings.allowedFileTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        updateSetting('allowedFileTypes', [...settings.allowedFileTypes, type]);
                      } else {
                        updateSetting('allowedFileTypes', settings.allowedFileTypes.filter(t => t !== type));
                      }
                    }}
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>
        </section>

        {/* 危险操作 */}
        <section className="settings-section danger">
          <h3>危险操作</h3>
          
          <div className="danger-zone">
            <div className="danger-info">
              <FiAlertTriangle size={24} color="#ff4d4f" />
              <div>
                <h4>删除知识库</h4>
                <p>此操作不可撤销，将永久删除该知识库及其所有文档</p>
              </div>
            </div>
            <Button
              variant="danger"
              icon={<FiTrash2 />}
              onClick={() => setShowDeleteConfirm(true)}
            >
              删除知识库
            </Button>
          </div>
        </section>
      </div>

      {/* 删除确认弹窗 */}
      {showDeleteConfirm && (
        <div className="delete-confirm-modal">
          <div className="modal-overlay" onClick={() => setShowDeleteConfirm(false)} />
          <div className="modal-content">
            <h3>确认删除</h3>
            <p>您确定要删除知识库 "{currentKnowledgeBase.name}" 吗？</p>
            <p className="warning-text">此操作不可撤销，所有文档和数据将被永久删除。</p>
            <div className="modal-actions">
              <Button variant="secondary" onClick={() => setShowDeleteConfirm(false)}>
                取消
              </Button>
              <Button variant="danger" onClick={handleDelete}>
                确认删除
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeSettings;
