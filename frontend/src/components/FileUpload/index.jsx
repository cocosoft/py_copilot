/**
 * 统一文件上传组件
 * 
 * 提供文件选择、上传、进度显示、预览等功能
 */

import React, { useState, useCallback, useRef } from 'react';
import { fileApi, FileCategory, formatFileSize, getFileIcon, isImageFile } from '../../utils/api/fileApi';
import { useI18n } from '../../hooks/useI18n';
import './FileUpload.css';

/**
 * 文件上传组件
 * 
 * @param {Object} props
 * @param {string} props.category - 文件分类（必需）
 * @param {number} props.conversationId - 关联对话ID
 * @param {number} props.knowledgeBaseId - 关联知识库ID
 * @param {number} props.relatedId - 通用关联ID
 * @param {string} props.accept - 接受的文件类型
 * @param {boolean} props.multiple - 是否允许多选
 * @param {Function} props.onUploadSuccess - 上传成功回调
 * @param {Function} props.onUploadError - 上传失败回调
 * @param {Function} props.onFileSelect - 文件选择回调
 * @param {boolean} props.showPreview - 是否显示预览
 * @param {string} props.buttonText - 按钮文字
 * @param {string} props.className - 自定义类名
 */
export const FileUpload = ({
  category,
  conversationId,
  knowledgeBaseId,
  relatedId,
  accept,
  multiple = false,
  onUploadSuccess,
  onUploadError,
  onFileSelect,
  showPreview = true,
  buttonText,
  className = ''
}) => {
  const { t } = useI18n();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = useRef(null);

  // 处理文件选择
  const handleFileSelect = useCallback((event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    const filesWithPreview = files.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      sizeFormatted: formatFileSize(file.size),
      icon: getFileIcon(file.name),
      isImage: isImageFile(file.name),
      preview: isImageFile(file.name) ? URL.createObjectURL(file) : null,
      status: 'pending'
    }));

    setSelectedFiles(filesWithPreview);
    onFileSelect?.(files);
  }, [onFileSelect]);

  // 上传单个文件
  const uploadSingleFile = async (fileInfo) => {
    try {
      setSelectedFiles(prev => prev.map(f => 
        f.id === fileInfo.id ? { ...f, status: 'uploading' } : f
      ));

      const result = await fileApi.upload(
        fileInfo.file,
        category,
        {
          conversationId,
          knowledgeBaseId,
          relatedId,
          onProgress: (p) => setProgress(p)
        }
      );

      setSelectedFiles(prev => prev.map(f => 
        f.id === fileInfo.id ? { ...f, status: 'success', result } : f
      ));

      onUploadSuccess?.(result);
      return result;
    } catch (error) {
      setSelectedFiles(prev => prev.map(f => 
        f.id === fileInfo.id ? { ...f, status: 'error', error: error.message } : f
      ));

      onUploadError?.(error);
      throw error;
    }
  };

  // 上传所有文件
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setProgress(0);

    try {
      for (const fileInfo of selectedFiles) {
        if (fileInfo.status === 'pending') {
          await uploadSingleFile(fileInfo);
        }
      }
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  // 移除文件
  const removeFile = (fileId) => {
    setSelectedFiles(prev => {
      const file = prev.find(f => f.id === fileId);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter(f => f.id !== fileId);
    });
  };

  // 清空所有文件
  const clearFiles = () => {
    selectedFiles.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });
    setSelectedFiles([]);
    setProgress(0);
  };

  // 触发文件选择
  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={`file-upload-container ${className}`}>
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      {/* 上传按钮 */}
      <div className="file-upload-actions">
        <button
          className="file-upload-button"
          onClick={triggerFileSelect}
          disabled={uploading}
        >
          {buttonText || t('settings.fileUpload.buttonText')}
        </button>
        
        {selectedFiles.length > 0 && (
          <>
            <button
              className="file-upload-submit"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? t('settings.fileUpload.uploading') : t('settings.fileUpload.uploadCount', { count: selectedFiles.length })}
            </button>
            <button
              className="file-upload-clear"
              onClick={clearFiles}
              disabled={uploading}
            >
              {t('settings.fileUpload.clear')}
            </button>
          </>
        )}
      </div>

      {/* 进度条 */}
      {uploading && progress > 0 && (
        <div className="file-upload-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="progress-text">{progress}%</span>
        </div>
      )}

      {/* 文件列表 */}
      {showPreview && selectedFiles.length > 0 && (
        <div className="file-upload-list">
          {selectedFiles.map(file => (
            <div 
              key={file.id}
              className={`file-item file-status-${file.status}`}
            >
              {/* 文件图标或预览 */}
              <div className="file-preview">
                {file.isImage && file.preview ? (
                  <img src={file.preview} alt={file.name} />
                ) : (
                  <span className="file-icon">{file.icon}</span>
                )}
              </div>

              {/* 文件信息 */}
              <div className="file-info">
                <div className="file-name" title={file.name}>
                  {file.name}
                </div>
                <div className="file-size">{file.sizeFormatted}</div>
              </div>

              {/* 状态指示 */}
              <div className="file-status">
                {file.status === 'uploading' && <span className="status-uploading">⏳</span>}
                {file.status === 'success' && <span className="status-success">✓</span>}
                {file.status === 'error' && <span className="status-error">✗</span>}
              </div>

              {/* 删除按钮 */}
              {!uploading && (
                <button
                  className="file-remove"
                  onClick={() => removeFile(file.id)}
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * 文件列表组件
 * 
 * @param {Object} props
 * @param {string} props.category - 文件分类筛选
 * @param {number} props.conversationId - 对话ID筛选
 * @param {Function} props.onFileClick - 文件点击回调
 * @param {Function} props.onFileDelete - 文件删除回调
 */
export const FileList = ({
  category,
  conversationId,
  onFileClick,
  onFileDelete
}) => {
  const { t } = useI18n();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 加载文件列表
  const loadFiles = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await fileApi.getList({
        category,
        conversationId
      });
      setFiles(result.files || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 删除文件
  const handleDelete = async (fileId) => {
    if (!window.confirm(t('settings.fileUpload.confirmDelete') || '确定要删除这个文件吗？')) return;

    try {
      await fileApi.delete(fileId);
      setFiles(prev => prev.filter(f => f.id !== fileId));
      onFileDelete?.(fileId);
    } catch (err) {
      alert(t('settings.fileUpload.deleteFailed') + ': ' + err.message);
    }
  };

  // 下载文件
  const handleDownload = async (file) => {
    try {
      const blob = await fileApi.download(file.id, true);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.original_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert(t('settings.fileUpload.downloadFailed') + ': ' + err.message);
    }
  };

  React.useEffect(() => {
    loadFiles();
  }, [category, conversationId]);

  if (loading) return <div className="file-list-loading">加载中...</div>;
  if (error) return <div className="file-list-error">错误: {error}</div>;
  if (files.length === 0) return <div className="file-list-empty">暂无文件</div>;

  return (
    <div className="file-list">
      {files.map(file => (
        <div 
          key={file.id}
          className="file-list-item"
          onClick={() => onFileClick?.(file)}
        >
          <span className="file-icon">{getFileIcon(file.original_name)}</span>
          <span className="file-name" title={file.original_name}>
            {file.original_name}
          </span>
          <span className="file-size">{file.file_size_human}</span>
          <span className="file-date">
            {new Date(file.created_at).toLocaleDateString()}
          </span>
          <div className="file-actions">
            <button 
              className="action-download"
              onClick={(e) => { e.stopPropagation(); handleDownload(file); }}
            >
              下载
            </button>
            <button 
              className="action-delete"
              onClick={(e) => { e.stopPropagation(); handleDelete(file.id); }}
            >
              删除
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * 存储使用情况组件
 */
export const StorageUsage = () => {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadUsage = async () => {
    setLoading(true);
    try {
      const result = await fileApi.getStorageUsage();
      setUsage(result);
    } catch (err) {
      console.error('获取存储使用情况失败:', err);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadUsage();
  }, []);

  if (loading) return <div className="storage-usage-loading">加载中...</div>;
  if (!usage) return <div className="storage-usage-error">无法获取存储信息</div>;

  return (
    <div className="storage-usage">
      <h3>存储使用情况</h3>
      <div className="storage-total">
        <div className="storage-total-size">{usage.total_size_human}</div>
        <div className="storage-total-files">{usage.total_files} 个文件</div>
      </div>
      
      {usage.breakdown && Object.entries(usage.breakdown).length > 0 && (
        <div className="storage-breakdown">
          <h4>分类详情</h4>
          {Object.entries(usage.breakdown).map(([key, value]) => (
            <div key={key} className="storage-category">
              <span className="category-name">{key}</span>
              <span className="category-size">{value.size_human}</span>
              <span className="category-files">({value.files} 个文件)</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
