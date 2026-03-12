/**
 * 上传按钮组件
 * 
 * 提供文件上传功能，支持拖拽上传
 */

import React, { useRef, useState, useCallback } from 'react';
import { FiUpload, FiX, FiFile, FiCheckCircle } from 'react-icons/fi';
import { Button } from '../../UI';
import { message } from '../../UI/Message/Message';
import './styles.css';

/**
 * 上传按钮组件
 * 
 * @param {Object} props
 * @param {Function} props.onUpload - 上传回调 (files) => void
 * @param {string[]} props.accept - 接受的文件类型
 * @param {number} props.maxSize - 最大文件大小（字节）
 * @param {boolean} props.multiple - 是否支持多文件
 * @param {string} props.variant - 按钮样式变体
 */
const UploadButton = ({
  onUpload,
  accept = ['.pdf', '.doc', '.docx', '.txt', '.md'],
  maxSize = 100 * 1024 * 1024, // 100MB
  multiple = true,
  variant = 'primary',
}) => {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadQueue, setUploadQueue] = useState([]);

  /**
   * 验证文件
   */
  const validateFile = (file) => {
    // 检查文件类型
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!accept.includes(fileExtension)) {
      return {
        valid: false,
        error: `不支持的文件类型: ${fileExtension}`,
      };
    }

    // 检查文件大小
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `文件过大: ${(file.size / 1024 / 1024).toFixed(2)}MB (最大 ${(maxSize / 1024 / 1024).toFixed(0)}MB)`,
      };
    }

    return { valid: true };
  };

  /**
   * 处理文件选择
   */
  const handleFileSelect = useCallback((files) => {
    const validFiles = [];
    const errors = [];

    Array.from(files).forEach((file) => {
      const validation = validateFile(file);
      if (validation.valid) {
        validFiles.push({
          file,
          id: Date.now() + Math.random(),
          status: 'pending',
          progress: 0,
        });
      } else {
        errors.push(`${file.name}: ${validation.error}`);
      }
    });

    // 显示错误
    errors.forEach((error) => {
      message.error({ content: error });
    });

    if (validFiles.length > 0) {
      setUploadQueue((prev) => [...prev, ...validFiles]);
      onUpload?.(validFiles.map((f) => f.file));
    }
  }, [accept, maxSize, onUpload]);

  /**
   * 处理 input change
   */
  const handleInputChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files);
    }
    // 重置 input
    e.target.value = '';
  };

  /**
   * 处理点击上传
   */
  const handleClick = () => {
    inputRef.current?.click();
  };

  /**
   * 处理拖拽进入
   */
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  /**
   * 处理拖拽离开
   */
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  /**
   * 处理拖拽悬停
   */
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  /**
   * 处理放置
   */
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileSelect(files);
    }
  };

  /**
   * 移除上传队列中的文件
   */
  const handleRemoveFile = (fileId) => {
    setUploadQueue((prev) => prev.filter((f) => f.id !== fileId));
  };

  /**
   * 清空上传队列
   */
  const handleClearQueue = () => {
    setUploadQueue([]);
  };

  return (
    <div className="upload-button-wrapper">
      {/* 上传按钮 */}
      <div
        className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept.join(',')}
          multiple={multiple}
          onChange={handleInputChange}
          className="upload-input"
        />
        
        <Button
          variant={variant}
          icon={<FiUpload />}
          onClick={handleClick}
        >
          上传文档
        </Button>
        
        <span className="upload-hint">
          或将文件拖拽到此处
        </span>
      </div>

      {/* 上传队列 */}
      {uploadQueue.length > 0 && (
        <div className="upload-queue">
          <div className="upload-queue-header">
            <span>上传队列 ({uploadQueue.length})</span>
            <button className="upload-queue-clear" onClick={handleClearQueue}>
              <FiX size={14} />
              清空
            </button>
          </div>
          
          <div className="upload-queue-list">
            {uploadQueue.map((item) => (
              <div key={item.id} className={`upload-queue-item ${item.status}`}>
                <div className="upload-queue-item-icon">
                  <FiFile size={16} />
                </div>
                
                <div className="upload-queue-item-info">
                  <span className="upload-queue-item-name" title={item.file.name}>
                    {item.file.name}
                  </span>
                  <span className="upload-queue-item-size">
                    {(item.file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
                
                <div className="upload-queue-item-status">
                  {item.status === 'pending' && (
                    <span className="status-pending">等待中</span>
                  )}
                  {item.status === 'uploading' && (
                    <div className="upload-progress">
                      <div 
                        className="upload-progress-bar"
                        style={{ width: `${item.progress}%` }}
                      />
                      <span>{item.progress}%</span>
                    </div>
                  )}
                  {item.status === 'success' && (
                    <FiCheckCircle className="status-success" size={18} />
                  )}
                  {item.status === 'error' && (
                    <span className="status-error">失败</span>
                  )}
                </div>
                
                <button
                  className="upload-queue-item-remove"
                  onClick={() => handleRemoveFile(item.id)}
                >
                  <FiX size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadButton;
