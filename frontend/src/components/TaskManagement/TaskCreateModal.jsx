import React, { useState } from 'react';
import { motion } from 'framer-motion';

function TaskCreateModal({ onClose, onCreate }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    working_directory: '',
    execute_command: false,
    command: ''
  });

  const [errors, setErrors] = useState({});
  const [showDirectoryPicker, setShowDirectoryPicker] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
    
    // 清除对应字段的错误
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: ''
      });
    }
  };

  const handleSelectDirectory = async () => {
    try {
      // 尝试使用 Electron 的 dialog API
      if (window.electron && window.electron.dialog) {
        const result = await window.electron.dialog.showOpenDialog({
          properties: ['openDirectory']
        });
        
        if (!result.canceled && result.filePaths && result.filePaths.length > 0) {
          setFormData({
            ...formData,
            working_directory: result.filePaths[0]
          });
        }
      } else {
        // 如果不是 Electron 环境，使用 Web API
        const dirHandle = await window.showDirectoryPicker();
        setFormData({
          ...formData,
          working_directory: dirHandle.name
        });
      }
    } catch (error) {
      console.error('选择目录失败:', error);
      // 如果浏览器不支持，回退到手动输入
      setShowDirectoryPicker(true);
    }
  };

  const handleQuickDirectory = (path) => {
    setFormData({
      ...formData,
      working_directory: path
    });
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.title.trim()) {
      newErrors.title = '任务标题不能为空';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      onCreate(formData);
    }
  };

  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="modal-content"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>创建任务</h2>
          <button
            className="modal-close"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label htmlFor="task-title">
              任务标题 <span className="required">*</span>
            </label>
            <input
              id="task-title"
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="请输入任务标题"
              className={`form-input ${errors.title ? 'error' : ''}`}
            />
            {errors.title && (
              <span className="error-message">{errors.title}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="task-description">
              任务描述
            </label>
            <textarea
              id="task-description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="请详细描述您的任务需求..."
              rows="6"
              className="form-input"
            />
            <div className="form-hint">
              描述越详细，系统分析越准确
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="task-priority">
              优先级
            </label>
            <select
              id="task-priority"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
              className="form-select"
            >
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="working-directory">
              工作目录
            </label>
            <div className="directory-input-group">
              <input
                id="working-directory"
                type="text"
                name="working_directory"
                value={formData.working_directory}
                onChange={handleChange}
                placeholder="请选择或输入工作目录路径（可选）"
                className="form-input directory-input"
                readOnly={!showDirectoryPicker}
              />
              <button
                type="button"
                className="btn btn-secondary directory-select-btn"
                onClick={handleSelectDirectory}
                title="选择文件夹"
              >
                📁
              </button>
            </div>
            <div className="form-hint">
              任务将在该目录下执行，留空则使用默认目录
            </div>
            
            {/* 常用目录快捷按钮 */}
            <div className="quick-directories">
              <span className="quick-directories-label">常用目录：</span>
              <button
                type="button"
                className="quick-dir-btn"
                onClick={() => handleQuickDirectory('e:\\PY\\CODES\\py copilot IV')}
              >
                项目目录
              </button>
              <button
                type="button"
                className="quick-dir-btn"
                onClick={() => handleQuickDirectory('e:\\PY\\CODES\\py copilot IV\\backend')}
              >
                后端目录
              </button>
              <button
                type="button"
                className="quick-dir-btn"
                onClick={() => handleQuickDirectory('e:\\PY\\CODES\\py copilot IV\\frontend')}
              >
                前端目录
              </button>
              <button
                type="button"
                className="quick-dir-btn"
                onClick={() => handleQuickDirectory('e:\\')}
              >
                E盘
              </button>
              <button
                type="button"
                className="quick-dir-btn"
                onClick={() => handleQuickDirectory('C:\\Users')}
              >
                用户目录
              </button>
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="execute_command"
                checked={formData.execute_command}
                onChange={handleChange}
                className="form-checkbox"
              />
              <span>执行系统命令</span>
            </label>
          </div>

          {formData.execute_command && (
            <div className="form-group">
              <label htmlFor="command">
                系统命令
              </label>
              <textarea
                id="command"
                name="command"
                value={formData.command}
                onChange={handleChange}
                placeholder="请输入要执行的命令..."
                rows="4"
                className="form-input"
              />
              <div className="form-hint">
                支持Windows命令，如：dir, cd, python等
              </div>
            </div>
          )}

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
            >
              取消
            </button>
            <button
              type="submit"
              className="btn btn-primary"
            >
              创建
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}

export default TaskCreateModal;
