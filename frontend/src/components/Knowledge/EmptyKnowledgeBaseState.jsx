/**
 * 知识库为空状态组件
 *
 * 当没有可用的知识库时显示引导界面
 *
 * @module EmptyKnowledgeBaseState
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './EmptyKnowledgeBaseState.css';

/**
 * 知识库为空状态组件
 *
 * @param {Object} props - 组件属性
 * @param {string} props.title - 标题
 * @param {string} props.description - 描述
 * @param {string} props.buttonText - 按钮文本
 * @param {Function} props.onButtonClick - 按钮点击回调
 * @returns {JSX.Element} 组件元素
 */
export const EmptyKnowledgeBaseState = ({
  title = '暂无知识库',
  description = '您还没有创建任何知识库，请先创建知识库',
  buttonText = '创建知识库',
  onButtonClick,
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onButtonClick) {
      onButtonClick();
    } else {
      navigate('/knowledge/settings');
    }
  };

  return (
    <div className="empty-knowledge-base-state">
      <div className="empty-state-content">
        <div className="empty-icon">📚</div>
        <h3>{title}</h3>
        <p>{description}</p>
        <button className="create-knowledge-base-btn" onClick={handleClick}>
          {buttonText}
        </button>
      </div>
    </div>
  );
};

export default EmptyKnowledgeBaseState;
