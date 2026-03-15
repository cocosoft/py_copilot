/**
 * 提取进度组件
 *
 * 显示实体提取进度信息
 */

import React from 'react';

/**
 * 提取进度组件
 */
const ExtractionProgress = ({
  extracting,
  extractProgress,
  extractStage,
  processedDocs,
  selectedDocuments,
}) => {
  if (!extracting) return null;

  return (
    <div className="extraction-progress">
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${extractProgress}%` }}
        />
      </div>
      <div className="progress-info">
        <span className="progress-stage">{extractStage}</span>
        <span className="progress-percent">{extractProgress}%</span>
      </div>
      {processedDocs > 0 && selectedDocuments.length > 1 && (
        <div className="progress-details">
          <span>已处理文档: {processedDocs} / {selectedDocuments.length}</span>
        </div>
      )}
    </div>
  );
};

export default ExtractionProgress;
