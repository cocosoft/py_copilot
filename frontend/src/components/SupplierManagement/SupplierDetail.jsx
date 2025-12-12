import React, { useState, useEffect } from 'react';
import { getImageUrl, DEFAULT_IMAGES } from '../../config/imageConfig';
import { supplierApi } from '../../utils/api/supplierApi';
import { API_BASE_URL } from '../../utils/apiUtils';
import SupplierModal from './SupplierModal';
import './SupplierDetail.css';

const SupplierDetail = ({ selectedSupplier, onSupplierSelect, onSupplierUpdate }) => {
  const [currentSupplier, setCurrentSupplier] = useState(null);
  const [isSupplierModalOpen, setIsSupplierModalOpen] = useState(false);
  const [supplierModalMode, setSupplierModalMode] = useState('edit');
  const [saving, setSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [localApiConfig, setLocalApiConfig] = useState({
    apiUrl: '',
    apiKey: ''
  });
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  // 添加收缩/展开状态 - 默认设置为收缩状态
  const [isExpanded, setIsExpanded] = useState(false);

  // 当选中的供应商变化时，更新本地API配置
  useEffect(() => {
    if (selectedSupplier) {
      setLocalApiConfig({
        apiUrl: selectedSupplier.apiUrl || selectedSupplier.api_endpoint || '',
        apiKey: selectedSupplier.api_key || ''
      });
      // 重置状态
      setTestResult(null);
      setSaveStatus(null);
      // 当选择新供应商时保持收缩状态
      setIsExpanded(false);
    }
  }, [selectedSupplier]);

  // 切换收缩/展开状态
  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const handleToggleSupplierStatus = async (supplier) => {
    try {
      const newStatus = !supplier.is_active;
      const confirmMessage = newStatus
        ? `确定要启用供应商 "${supplier.name}" 吗？`
        : `确定要停用供应商 "${supplier.name}" 吗？`;

      if (!window.confirm(confirmMessage)) {
        return;
      }

      const apiUrl = `${API_BASE_URL}/model-management/suppliers/${supplier.id}`;

      await supplierApi.updateSupplierStatus(supplier.id, newStatus);

      if (onSupplierUpdate) {
        setTimeout(() => onSupplierUpdate(), 0);
      }

    } catch (err) {
      console.error('Failed to toggle supplier status:', err);
    }
  };

  const handleEditSupplier = (supplier) => {
    setCurrentSupplier({ ...supplier });
    setSupplierModalMode('edit');
    setIsSupplierModalOpen(true);
  };

  const handleCloseSupplierModal = () => {
    setIsSupplierModalOpen(false);
    setCurrentSupplier(null);
  };

  const handleSaveSupplier = async (apiData, frontendData) => {
    try {
      setSaving(true);

      const isFormData = apiData instanceof FormData;
      // 创建新的数据副本，避免直接修改传入的数据
      let dataToSend;
      if (isFormData) {
        // 对于FormData，创建新的FormData并复制所有键值对
        dataToSend = new FormData();
        // 复制原始FormData中的所有键值对
        if (apiData instanceof FormData) {
          for (const [key, value] of apiData.entries()) {
            dataToSend.append(key, value);
          }
        }
        // 如果有isDomestic信息，添加到FormData中
        if (frontendData && frontendData.isDomestic !== undefined) {
          dataToSend.append('is_domestic', frontendData.isDomestic ? 'true' : 'false');
        }
        // 添加API地址和API密钥（映射前端字段到后端期望的字段名）
        if (frontendData) {
          if (frontendData.apiUrl !== undefined) {
            dataToSend.append('api_endpoint', frontendData.apiUrl);
          }
          if (frontendData.apiKey !== undefined) {
            dataToSend.append('api_key', frontendData.apiKey);
          }
        }

        // 添加api_key_env_name
        const supplierKey = currentSupplier ?
          (currentSupplier.key || currentSupplier.name).toUpperCase() :
          (dataToSend.get('name') || '').toUpperCase();
        dataToSend.append('api_key_env_name', `API_KEY_${supplierKey}`);
      } else {
        // 对于普通对象，创建新对象
        dataToSend = {
          ...apiData,
          // 映射前端字段到后端期望的字段名
          api_endpoint: frontendData?.apiUrl ?? apiData.api_endpoint ?? apiData.apiUrl,
          api_key: frontendData?.apiKey ?? apiData.api_key ?? apiData.apiKey,
          // 设置默认值
          is_active: apiData.is_active !== undefined ? apiData.is_active : true,
          is_domestic: frontendData?.isDomestic ?? apiData.is_domestic ?? false
        };

        // 使用currentSupplier的key或name作为环境变量名的一部分
        const supplierKey = currentSupplier ?
          (currentSupplier.key || currentSupplier.name).toUpperCase() :
          (dataToSend.name || '').toUpperCase();

        dataToSend.api_key_env_name = `API_KEY_${supplierKey}`;
      }


      let updatedSupplierData;

      if (supplierModalMode === 'edit' && currentSupplier) {
        const supplierId = Number(currentSupplier.id);

        // 使用supplierApi.update方法
        updatedSupplierData = await supplierApi.update(supplierId, dataToSend);

      } else {
        // 添加模式下，调用create方法
        updatedSupplierData = await supplierApi.create(dataToSend);
      }

      // 映射API返回的数据到前端格式
      const frontendFormat = {
        id: updatedSupplierData.id,
        key: String(updatedSupplierData.id),
        name: updatedSupplierData.name,
        description: updatedSupplierData.description,
        isDomestic: frontendData && frontendData.isDomestic !== undefined ? frontendData.isDomestic : updatedSupplierData.is_domestic || false
      };

      // 立即更新本地currentSupplier状态
      setCurrentSupplier(frontendFormat);

      // 如果更新的是当前选中的供应商，同步更新选中状态
      if (selectedSupplier?.id === updatedSupplierData.id) {
        if (onSupplierSelect) {
          onSupplierSelect(frontendFormat);
        }
      }

      // 刷新供应商列表
      if (onSupplierUpdate) {
        // 使用setTimeout确保UI更新后再刷新
        setTimeout(() => onSupplierUpdate(), 0);
      }

      // 关闭模态窗口
      handleCloseSupplierModal();

    } catch (error) {
      console.error('保存供应商失败:', error);
      const errorMessage = `${supplierModalMode === 'add' ? '添加' : '更新'}供应商失败`;
      throw new Error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const getSupplierLogo = (supplier) => {
    if (!supplier) return '';

    try {
      // 如果有logo
      if (supplier.logo) {
        // 检测是否为外部URL
        if (supplier.logo.startsWith('http')) {
          // 使用后端代理端点处理外部URL，避免ORB安全限制
          const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(supplier.logo)}`;
          return proxyUrl;
        } else {
          // 使用配置的图片路径生成函数
          return getImageUrl('providers', supplier.logo);
        }
      }
      // 没有logo时的默认路径
      return DEFAULT_IMAGES.provider;
    } catch (error) {
      console.error('获取供应商logo失败:', error);
      return DEFAULT_IMAGES.provider;
    }
  };

  const handleDeleteSupplier = async (supplier) => {
    
    // 防止多次点击
    if (isDeleting) {
      return;
    }
    
    setIsDeleting(true);
    
    if (!window.confirm(`确定要删除供应商 "${supplier.name}" 吗？删除后将无法恢复。`)) {
      setIsDeleting(false);
      return;
    }

    try {
      // 使用api.supplierApi.delete方法删除供应商，确保使用正确的API端口
      await supplierApi.delete(supplier.id);

      // 显示成功消息
      alert('供应商删除成功');

      // 延迟刷新和取消选中，确保请求完成
      setTimeout(() => {
        // 刷新供应商列表
        if (onSupplierUpdate) {
          onSupplierUpdate();
        }

        // 取消选中当前供应商
        if (onSupplierSelect) {
          onSupplierSelect(null);
        }
      }, 100);

    } catch (err) {
      console.error('❌ Failed to delete supplier:', err);
      console.error('❌ 错误详情:', JSON.stringify(err, null, 2));
      alert('删除供应商失败，请稍后重试');
    } finally {
      setIsDeleting(false);
    }
  };

  // 保存API配置
  const handleSaveApiConfig = async () => {
    try {
      setSaving(true);
      setSaveStatus(null);

      // 准备更新数据
      const updateData = {
        api_endpoint: localApiConfig.apiUrl,
        api_key: localApiConfig.apiKey
      };

      console.log('保存API配置：', updateData);
      
      // 更新供应商信息
      const response = await supplierApi.update(selectedSupplier.id, updateData);
      console.log('保存API配置响应：', response);

      // 显示保存成功
      setSaveStatus({
        type: 'success',
        message: 'API配置保存成功'
      });

      // 刷新供应商列表
      if (onSupplierUpdate) {
        setTimeout(() => onSupplierUpdate(), 0);
      }
    } catch (error) {
      console.error('保存API配置失败:', error);
      setSaveStatus({
        type: 'error',
        message: '保存失败，请稍后重试'
      });
    } finally {
      setSaving(false);
    }
  };

  // 测试API配置
  const handleTestApiConfig = async () => {
    try {
      setTesting(true);
      setTestResult(null);

      // 前端验证API配置
      if (!localApiConfig.apiUrl) {
        setTestResult({
          type: 'error',
          message: 'API测试失败',
          details: 'API端点不能为空'
        });
        return;
      }

      // 验证API端点格式是否正确（必须包含http://或https://）
      if (!(/^https?:\/\/.+/.test(localApiConfig.apiUrl))) {
        setTestResult({
          type: 'error',
          message: 'API测试失败',
          details: 'API端点格式不正确，必须包含http://或https://'
        });
        return;
      }

      if (!localApiConfig.apiKey) {
        setTestResult({
          type: 'error',
          message: 'API测试失败',
          details: 'API密钥不能为空'
        });
        return;
      }

      // 测试API配置
      console.log('即将调用testApiConfig，传递的参数:', {
        id: selectedSupplier.id,
        apiConfig: {
          apiUrl: localApiConfig.apiUrl,
          apiKey: localApiConfig.apiKey
        }
      });
      const result = await supplierApi.testApiConfig(selectedSupplier.id, {
        apiUrl: localApiConfig.apiUrl,
        apiKey: localApiConfig.apiKey
      });

      // 根据后端返回的状态设置测试结果
      if (result.status === 'success') {
        setTestResult({
          type: 'success',
          message: 'API测试成功！',
          details: result.message || 'API连接正常'
        });
      } else {
        setTestResult({
          type: 'error',
          message: 'API测试失败',
          details: result.message || '无法连接到API'
        });
      }
    } catch (error) {
        console.error('测试API失败:', error);
        console.error('错误消息:', error.message);
        console.error('错误对象:', error);
        
        // 解析错误信息，优先使用error.message（apiUtils.js已处理）
        let errorDetails = '无法连接到API';
        
        // 首先使用apiUtils.js处理过的错误消息
        if (error.message) {
          errorDetails = error.message;
        } else if (error.response && error.response.data) {
          // 如果没有处理过的消息，尝试从response.data中提取
          const responseData = error.response.data;
          errorDetails = responseData.message || 
                        responseData.detail || 
                        responseData.response_text || 
                        JSON.stringify(responseData);
        }
        
        setTestResult({
          type: 'error',
          message: 'API测试失败',
          details: errorDetails
        });
    } finally {
      setTesting(false);
    }
  };

  // 格式化API密钥显示
  const formatApiKey = (apiKey) => {
    if (!apiKey || typeof apiKey !== 'string') return '';
    if (apiKey.length <= 8) return '••••••••';
    return `${apiKey.slice(0, 4)}••••${apiKey.slice(-4)}`;
  };

  if (!selectedSupplier) {
    return (
      <div className="no-supplier-selected">
        <p>请从左侧选择一个供应商</p>
      </div>
    );
  }

  return (
    <div className="supplier-detail">
      <div className="supplier-header">
        <div className="supplier-title">
          <img
            className="supplier-logo"
            src={getSupplierLogo(selectedSupplier)}
            alt={`${selectedSupplier.name} Logo`}
            onError={(e) => {
              // 图片加载失败时显示默认占位
              e.target.src = DEFAULT_IMAGES.provider;
            }}
          />
          <h2>{selectedSupplier.name}</h2>
          {selectedSupplier.website && (
            <a
              href={selectedSupplier.website}
              target="_blank"
              rel="noopener noreferrer"
              className="supplier-website"
            >
              官网
            </a>
          )}
        </div>
        <div className="action-buttons">
          {/* 收缩/展开按钮 */}
          <button
            className="btn-expand"
            onClick={toggleExpand}
            title={isExpanded ? '收缩详情' : '展开详情'}
          >
            {isExpanded ? '▲' : '▼'}
          </button>
          <button
            className="btn-edit"
            onClick={() => handleEditSupplier(selectedSupplier)}
            title="编辑供应商信息"
          >
            ✏️
          </button>
          <button
            className="btn-delete"
            onClick={() => handleDeleteSupplier(selectedSupplier)}
            title="删除供应商"
          >
            🗑️
          </button>
        </div>
        <div className="supplier-actions">
          <label className="toggle-switch" title={selectedSupplier.is_active ? '当前已启用，点击停用' : '当前已停用，点击启用'}>
            <input
              type="checkbox"
              checked={selectedSupplier.is_active}
              onChange={(e) => {
                const newStatus = !selectedSupplier.is_active;
                const confirmMessage = newStatus
                  ? `确定要启用供应商 "${selectedSupplier.name}" 吗？`
                  : `确定要停用供应商 "${selectedSupplier.name}" 吗？`;

                if (window.confirm(confirmMessage)) {
                  supplierApi.updateSupplierStatus(selectedSupplier.id, newStatus)
                    .then(() => {
                      if (onSupplierUpdate) {
                        setTimeout(() => onSupplierUpdate(), 0);
                      }
                    })
                    .catch(err => {
                      console.error('Failed to toggle supplier status:', err);
                    });
                }
              }}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>
      </div>
      
      {/* 内容区域，根据展开状态控制显示 */}
      <div className={`supplier-content ${isExpanded ? 'expanded' : 'collapsed'}`}>
        <div className="supplier-description">
          {selectedSupplier.description || '未提供描述'}
        </div>
        
        <div className="supplier-info-panel">
          <div className="supplier-info-grid">
            <div className="info-row">
              <span className="info-label">API地址:</span>
              <input
                type="url"
                className="info-value"
                value={localApiConfig.apiUrl}
                onChange={(e) => setLocalApiConfig({ ...localApiConfig, apiUrl: e.target.value })}
                placeholder="请输入API地址"
              />
            </div>

            <div className="api-key-row">
              <span className="info-label">API密钥:</span>
              <div className="api-key-input-group">
                {isEditMode ? (
                  <input
                    type="text"
                    className="info-value"
                    value={localApiConfig.apiKey}
                    onChange={(e) => setLocalApiConfig({ ...localApiConfig, apiKey: e.target.value })}
                    placeholder="请输入API密钥"
                    autoFocus
                    onBlur={() => setIsEditMode(false)}
                  />
                ) : (
                  <div 
                    className="info-value api-key-display"
                    onClick={() => setIsEditMode(true)}
                  >
                    {localApiConfig.apiKey ? formatApiKey(localApiConfig.apiKey) : '点击输入API密钥'}
                  </div>
                )}
                <button
                  className="btn-copy"
                  onClick={() => navigator.clipboard.writeText(localApiConfig.apiKey)}
                  title="复制API密钥"
                  disabled={!localApiConfig.apiKey}
                >
                  复制
                </button>
              </div>
            </div>

            {/* API配置操作按钮 */}
            <div className="api-config-actions">
              <button
                className="btn-save"
                onClick={handleSaveApiConfig}
                disabled={saving}
              >
                {saving ? '保存中...' : '保存配置'}
              </button>
              <button
                className="btn-test"
                onClick={handleTestApiConfig}
                disabled={testing || !localApiConfig.apiUrl || !localApiConfig.apiKey}
              >
                {testing ? '测试中...' : '测试API'}
              </button>
            </div>

            {/* 保存状态提示 */}
            {saveStatus && (
              <div className="status-message">
                <div
                  className={`status-message ${saveStatus.type}`}
                >
                  {saveStatus.message}
                </div>
              </div>
            )}

            {/* 测试结果提示 */}
            {testResult && (
              <div className="status-message">
                <div
                  className={`status-message ${testResult.type}`}
                >
                  <strong>{testResult.message}</strong>
                  {testResult.details && <p>{testResult.details}</p>}
                </div>
              </div>
            )}

            {selectedSupplier.api_docs && (
              <div className="api-docs-link">
                <span className="info-label">查看 {selectedSupplier.name} 的</span>
                <a
                  href={selectedSupplier.api_docs}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  API文档
                </a>，以获得更多信息
              </div>
            )}
          </div>
        </div>
      </div>

      <SupplierModal
        isOpen={isSupplierModalOpen}
        onClose={handleCloseSupplierModal}
        onSave={handleSaveSupplier}
        supplier={currentSupplier}
        mode={supplierModalMode}
      />
    </div>
  );
};

export default SupplierDetail;