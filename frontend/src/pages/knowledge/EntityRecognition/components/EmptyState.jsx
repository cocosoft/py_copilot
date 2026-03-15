/**
 * 空状态组件
 *
 * 当没有选择知识库时显示
 */

import React from 'react';
import { FiFolder } from 'react-icons/fi';
import { Button } from '../../../components/UI';

/**
 * 空状态组件
 */
const EmptyState = ({ navigate }) => {
  return (
    <div className="entity-recognition-empty">
      <div className="empty-icon">🔍</div>
      <h3>请选择一个知识库</h3>
      <p>从左侧边栏选择一个知识库开始实体识别</p>
      
      <div className="empty-actions">
        <Button
          variant="primary"
          onClick={() => navigate('/knowledge/documents')}
          icon={<FiFolder />}
        >
          前往知识库管理
        </Button>
      </div>
      
      <div className="empty-guide">
        <h4>使用步骤</h4>
        <ol>
          <li>选择或创建一个知识库</li>
          <li>上传文档到知识库</li>
          <li>选择文档进行实体提取</li>
          <li>确认或编辑提取的实体</li>
        </ol>
      </div>
    </div>
  );
};

export default EmptyState;
