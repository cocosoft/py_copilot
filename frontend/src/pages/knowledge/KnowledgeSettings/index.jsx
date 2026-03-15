/**
 * 知识库设置页面
 *
 * 管理知识库的配置和参数，包括默认模型配置
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSave, FiTrash2, FiAlertTriangle, FiCpu } from 'react-icons/fi';
import useKnowledgeStore from '../../../stores/knowledgeStore';
import { Button } from '../../../components/UI';
import { message } from '../../../components/UI/Message/Message';
import { updateKnowledgeBase, deleteKnowledgeBase } from '../../../utils/api/knowledgeApi';
import defaultModelApi from '../../../utils/api/defaultModelApi';
import { supplierApi } from '../../../utils/api/supplierApi';
import ModelDataManager from '../../../services/modelDataManager';
import ModelSelectDropdown from '../../../components/ModelManagement/ModelSelectDropdown';
import './styles.css';

/**
 * 知识库设置页面
 */
const KnowledgeSettings = () => {
  const { currentKnowledgeBase, setCurrentKnowledgeBase } = useKnowledgeStore();
  const navigate = useNavigate();

  // 本地状态
  const [settings, setSettings] = useState({
    name: '',
    description: '',
    isPublic: false,
    autoVectorize: true,
    chunkSize: 1000,
    overlap: 200,
    embeddingModel: 'text-embedding-3-small',
    maxFileSize: 100,
    allowedFileTypes: ['.pdf', '.doc', '.docx', '.txt', '.md'],
  });

  // 默认模型配置状态
  const [defaultModelConfig, setDefaultModelConfig] = useState({
    knowledgeModel: null,
    extractionModel: null,
  });
  const [isSavingModelConfig, setIsSavingModelConfig] = useState(false);

  // 嵌入模型列表状态
  const [embeddingModels, setEmbeddingModels] = useState([]);
  const [isLoadingEmbeddingModels, setIsLoadingEmbeddingModels] = useState(false);

  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  /**
   * 加载嵌入模型列表
   * 使用与"设置-模型管理-默认模型"页面中"向量化场景"相同的API
   */
  const loadEmbeddingModels = useCallback(async () => {
    setIsLoadingEmbeddingModels(true);
    try {
      // 使用supplierApi.getModelsByScene获取嵌入模型列表
      // 这与SceneDefaultModels组件使用的API一致
      console.log('开始加载嵌入模型列表...');
      const response = await supplierApi.getModelsByScene('embedding');
      console.log('嵌入模型API返回:', response);
      let models = Array.isArray(response) ? response : (response?.models || response?.items || []);
      console.log('解析后的模型列表:', models);

      // 如果API返回的模型列表为空，尝试获取所有模型并进行筛选
      if (models.length === 0) {
        console.log('API返回空列表，尝试获取所有模型并进行筛选...');
        const allModelsResponse = await supplierApi.getModels();
        const allModels = Array.isArray(allModelsResponse) ? allModelsResponse : (allModelsResponse?.models || allModelsResponse?.items || []);
        
        // 使用与useModelManagement.jsx相同的回退逻辑
        models = allModels.filter(model => {
          const modelType = model.model_type_name || model.type || '';
          const modelName = (model.model_name || model.name || '').toLowerCase();
          const modelId = (model.model_id || '').toLowerCase();
          
          // 基本类型匹配
          if (modelType === 'embedding') {
            return true;
          }
          
          // 根据模型名称和ID进行匹配
          return modelName.includes('embedding') || 
                 modelName.includes('embed') || 
                 modelName.includes('bge') || 
                 modelName.includes('baai') ||
                 modelId.includes('embedding') ||
                 modelId.includes('embed');
        });
        console.log('筛选后的模型列表:', models);
      }

      setEmbeddingModels(models);
    } catch (error) {
      console.error('加载嵌入模型列表失败:', error);
      setEmbeddingModels([]);
    } finally {
      setIsLoadingEmbeddingModels(false);
    }
  }, []);

  /**
   * 加载默认模型配置
   * 按照优先级获取知识库专属的默认模型
   */
  const loadDefaultModelConfig = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      const kbId = currentKnowledgeBase.id;
      const scenes = [
        { key: 'knowledge', scene: `knowledge_kb_${kbId}` },
        { key: 'extraction', scene: `knowledge_kb_${kbId}_extraction` },
      ];

      const config = {
        knowledgeModel: null,
        extractionModel: null,
      };

      for (const { key, scene } of scenes) {
        try {
          const response = await defaultModelApi.getSceneDefaultModel(scene);
          if (response && response.model_id) {
            // 构造模型对象，用于ModelSelectDropdown
            const modelObj = {
              model_id: response.model_id,
              model_name: response.model_name || response.model_id,
              supplier_name: response.supplier_name || '未知供应商',
              supplier_logo: response.supplier_logo,
            };
            config[key === 'knowledge' ? 'knowledgeModel' : 'extractionModel'] = modelObj;
          }
        } catch (error) {
          // 该场景未配置模型，忽略错误
          console.log(`场景 ${scene} 未配置模型`);
        }
      }

      setDefaultModelConfig(config);
    } catch (error) {
      console.error('加载默认模型配置失败:', error);
    }
  }, [currentKnowledgeBase]);

  // 当当前知识库变化时更新设置
  useEffect(() => {
    if (currentKnowledgeBase) {
      setSettings(prev => ({
        ...prev,
        name: currentKnowledgeBase.name || '',
        description: currentKnowledgeBase.description || '',
      }));
      // 加载默认模型配置
      loadDefaultModelConfig();
      // 加载嵌入模型列表
      loadEmbeddingModels();
    }
  }, [currentKnowledgeBase, loadDefaultModelConfig, loadEmbeddingModels]);

  /**
   * 保存默认模型配置
   */
  const handleSaveModelConfig = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setIsSavingModelConfig(true);
    try {
      const kbId = currentKnowledgeBase.id;

      // 保存知识库级默认模型
      if (defaultModelConfig.knowledgeModel) {
        await defaultModelApi.setSceneDefaultModel({
          scene: `knowledge_kb_${kbId}`,
          model_id: parseInt(defaultModelConfig.knowledgeModel.model_id),
          priority: 100,
        });
      }

      // 保存知识库任务级默认模型（实体提取）
      if (defaultModelConfig.extractionModel) {
        await defaultModelApi.setSceneDefaultModel({
          scene: `knowledge_kb_${kbId}_extraction`,
          model_id: parseInt(defaultModelConfig.extractionModel.model_id),
          priority: 100,
        });
      }

      message.success({ content: '默认模型配置已保存' });
    } catch (error) {
      console.error('保存默认模型配置失败:', error);
      message.error({ content: '保存默认模型配置失败：' + error.message });
    } finally {
      setIsSavingModelConfig(false);
    }
  }, [currentKnowledgeBase, defaultModelConfig]);

  /**
   * 更新默认模型配置
   */
  const updateModelConfig = (field, model) => {
    setDefaultModelConfig(prev => ({ ...prev, [field]: model }));
  };

  /**
   * 保存设置
   */
  const handleSave = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    setIsSaving(true);
    try {
      // 调用真实 API 更新知识库
      const updatedKB = await updateKnowledgeBase(
        currentKnowledgeBase.id,
        settings.name,
        settings.description
      );

      // 更新 store 中的当前知识库
      if (updatedKB) {
        setCurrentKnowledgeBase({
          ...currentKnowledgeBase,
          name: settings.name,
          description: settings.description,
        });
      }

      message.success({ content: '设置已保存' });
    } catch (error) {
      message.error({ content: '保存失败：' + error.message });
    } finally {
      setIsSaving(false);
    }
  }, [currentKnowledgeBase, settings, setCurrentKnowledgeBase]);

  /**
   * 删除知识库
   */
  const handleDelete = useCallback(async () => {
    if (!currentKnowledgeBase) return;

    try {
      // 调用真实 API 删除知识库
      await deleteKnowledgeBase(currentKnowledgeBase.id);

      message.success({ content: '知识库已删除' });
      // 清空当前知识库并跳转到知识库列表
      setCurrentKnowledgeBase(null);
      navigate('/knowledge');
    } catch (error) {
      message.error({ content: '删除失败：' + error.message });
    }
  }, [currentKnowledgeBase, setCurrentKnowledgeBase, navigate]);

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

        {/* 默认模型配置 */}
        <section className="settings-section">
          <div className="section-header">
            <h3>
              <FiCpu style={{ marginRight: '8px' }} />
              默认模型配置
            </h3>
            <Button
              variant="primary"
              size="small"
              onClick={handleSaveModelConfig}
              loading={isSavingModelConfig}
            >
              保存模型配置
            </Button>
          </div>

          <div className="model-config-info">
            <p className="help-text">
              为当前知识库配置专属的默认模型。配置后，该知识库的所有操作（包括实体提取）将优先使用这些模型。
            </p>
          </div>

          <div className="form-group">
            <label>知识库默认模型</label>
            <div className="model-select-wrapper">
              <ModelSelectDropdown
                selectedModel={defaultModelConfig.knowledgeModel}
                onModelSelect={(model) => updateModelConfig('knowledgeModel', model)}
                placeholder="-- 选择模型 --"
                scene="knowledge"
                singleLine={false}
              />
            </div>
            <p className="help-text">
              用于知识库的一般操作，如文档处理、问答等
              {defaultModelConfig.knowledgeModel && (
                <span className="scene-tag">场景: knowledge_kb_{currentKnowledgeBase.id}</span>
              )}
            </p>
          </div>

          <div className="form-group">
            <label>实体提取专用模型</label>
            <div className="model-select-wrapper">
              <ModelSelectDropdown
                selectedModel={defaultModelConfig.extractionModel}
                onModelSelect={(model) => updateModelConfig('extractionModel', model)}
                placeholder="-- 选择模型（可选）--"
                scene="knowledge"
                singleLine={false}
              />
            </div>
            <p className="help-text">
              专门用于实体提取任务，如果不设置则使用知识库默认模型
              {defaultModelConfig.extractionModel && (
                <span className="scene-tag">场景: knowledge_kb_{currentKnowledgeBase.id}_extraction</span>
              )}
            </p>
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
            <div className="model-select-wrapper">
              <ModelSelectDropdown
                models={embeddingModels}
                selectedModel={embeddingModels.find(model =>
                  String(model.id || model.model_id) === String(settings.embeddingModel)
                ) || null}
                onModelSelect={(model) => updateSetting('embeddingModel', model ? (model.id || model.model_id) : 'text-embedding-3-small')}
                placeholder="-- 选择嵌入模型 --"
                disabled={isLoadingEmbeddingModels}
                singleLine={false}
              />
            </div>
            <p className="help-text">用于将文档转换为向量表示</p>
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
