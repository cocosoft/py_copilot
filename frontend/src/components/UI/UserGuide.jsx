/**
 * 用户引导组件
 *
 * 为用户提供操作指导，帮助用户快速了解知识图谱管理界面的功能
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import './UserGuide.css';

/**
 * 用户引导组件
 *
 * @param {Object} props - 组件属性
 * @param {boolean} props.show - 是否显示引导
 * @param {Function} props.onClose - 关闭引导的回调函数
 * @param {string} props.page - 当前页面名称
 * @returns {JSX.Element} 用户引导界面
 */
const UserGuide = ({ show, onClose, page = 'knowledge-graph' }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState(null);
  const guideRef = useRef(null);

  // 引导步骤配置
  const guideSteps = {
    'knowledge-graph': [
      {
        title: '欢迎使用知识图谱管理',
        content: '知识图谱是一种强大的数据可视化工具，帮助您发现实体之间的关系。',
        position: 'center',
        highlight: null
      },
      {
        title: '标签页导航',
        content: '通过这些标签页可以切换不同的管理功能，包括图谱查看、实体管理、关系管理等。',
        position: 'bottom',
        highlight: '.manager-tabs'
      },
      {
        title: '图谱可视化',
        content: '在图谱视图中，您可以查看实体之间的关系，调整布局，使用分析工具。',
        position: 'left',
        highlight: '.graph-display'
      },
      {
        title: '实体管理',
        content: '管理知识图谱中的实体，包括添加、编辑、删除和合并实体。',
        position: 'right',
        highlight: '.entities-list'
      },
      {
        title: '关系管理',
        content: '管理实体之间的关系，包括添加、编辑、删除关系和设置关系类型。',
        position: 'right',
        highlight: '.relations-list'
      },
      {
        title: '分析工具',
        content: '使用社区发现、中心性分析和路径发现等工具深入分析图谱数据。',
        position: 'bottom',
        highlight: '.analysis-tools'
      }
    ],
    'entity-management': [
      {
        title: '实体管理',
        content: '在这里您可以管理知识图谱中的所有实体。',
        position: 'center',
        highlight: null
      },
      {
        title: '搜索和筛选',
        content: '使用搜索框和筛选器快速找到特定实体。',
        position: 'bottom',
        highlight: '.entity-filters'
      },
      {
        title: '批量操作',
        content: '选择多个实体进行批量激活、停用或删除操作。',
        position: 'bottom',
        highlight: '.batch-actions-bar'
      },
      {
        title: '实体详情',
        content: '点击实体查看详细信息，包括属性和关联关系。',
        position: 'right',
        highlight: '.entity-item'
      }
    ],
    'relation-management': [
      {
        title: '关系管理',
        content: '在这里您可以管理实体之间的关系。',
        position: 'center',
        highlight: null
      },
      {
        title: '添加关系',
        content: '点击添加按钮创建新的实体关系。',
        position: 'bottom',
        highlight: '.relation-actions'
      },
      {
        title: '编辑关系',
        content: '点击编辑按钮修改现有关系的属性。',
        position: 'right',
        highlight: '.action-btn.edit'
      },
      {
        title: '关系状态',
        content: '激活或停用关系，控制其在图谱中的显示。',
        position: 'right',
        highlight: '.status-badge'
      }
    ]
  };

  const steps = guideSteps[page] || guideSteps['knowledge-graph'];

  // 获取目标元素的位置信息
  const updateTargetRect = useCallback(() => {
    const currentGuide = steps[currentStep];
    if (currentGuide.highlight) {
      const target = document.querySelector(currentGuide.highlight);
      if (target) {
        const rect = target.getBoundingClientRect();
        setTargetRect(rect);
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [currentStep, steps]);

  useEffect(() => {
    if (show) {
      setCurrentStep(0);
    }
  }, [show, page]);

  // 当步骤变化时更新目标位置
  useEffect(() => {
    if (show) {
      // 延迟一点执行，确保DOM已经更新
      const timer = setTimeout(() => {
        updateTargetRect();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [currentStep, show, updateTargetRect]);

  // 监听窗口大小变化
  useEffect(() => {
    if (show) {
      const handleResize = () => {
        updateTargetRect();
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, [show, updateTargetRect]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onClose();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    onClose();
  };

  // 计算引导卡片的位置样式
  const getGuideCardStyle = () => {
    const currentGuide = steps[currentStep];

    if (currentGuide.position === 'center' || !targetRect) {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)'
      };
    }

    const cardWidth = 400;
    const cardHeight = 200;
    const offset = 16;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let style = {
      position: 'fixed'
    };

    // 计算各个方向的位置
    let top, left, transform;

    switch (currentGuide.position) {
      case 'top':
        left = targetRect.left + targetRect.width / 2;
        top = targetRect.top - offset;
        transform = 'translate(-50%, -100%)';
        // 如果上方空间不足，改为显示在下方
        if (top < cardHeight) {
          top = targetRect.bottom + offset;
          transform = 'translate(-50%, 0)';
        }
        break;
      case 'bottom':
        left = targetRect.left + targetRect.width / 2;
        top = targetRect.bottom + offset;
        transform = 'translate(-50%, 0)';
        // 如果下方空间不足，改为显示在上方
        if (top + cardHeight > viewportHeight) {
          top = targetRect.top - offset;
          transform = 'translate(-50%, -100%)';
        }
        break;
      case 'left':
        left = targetRect.left - offset;
        top = targetRect.top + targetRect.height / 2;
        transform = 'translate(-100%, -50%)';
        // 如果左侧空间不足，改为显示在右侧
        if (left < cardWidth) {
          left = targetRect.right + offset;
          transform = 'translate(0, -50%)';
        }
        break;
      case 'right':
        left = targetRect.right + offset;
        top = targetRect.top + targetRect.height / 2;
        transform = 'translate(0, -50%)';
        // 如果右侧空间不足，改为显示在左侧
        if (left + cardWidth > viewportWidth) {
          left = targetRect.left - offset;
          transform = 'translate(-100%, -50%)';
        }
        break;
      default:
        left = viewportWidth / 2;
        top = viewportHeight / 2;
        transform = 'translate(-50%, -50%)';
    }

    // 确保不超出视口边界
    if (left < cardWidth / 2) {
      left = cardWidth / 2 + 10;
    } else if (left + cardWidth / 2 > viewportWidth) {
      left = viewportWidth - cardWidth / 2 - 10;
    }

    if (top < cardHeight) {
      top = cardHeight + 10;
    } else if (top > viewportHeight - 100) {
      top = viewportHeight - cardHeight - 10;
    }

    style.left = left;
    style.top = top;
    style.transform = transform;

    return style;
  };

  // 计算高亮框的样式
  const getHighlightStyle = () => {
    if (!targetRect) return { display: 'none' };

    return {
      position: 'fixed',
      left: targetRect.left - 4,
      top: targetRect.top - 4,
      width: targetRect.width + 8,
      height: targetRect.height + 8,
      borderRadius: '4px'
    };
  };

  if (!show) return null;

  const currentGuide = steps[currentStep];
  const guideCardStyle = getGuideCardStyle();
  const highlightStyle = getHighlightStyle();

  // 处理遮罩层点击
  const handleBackdropClick = () => {
    onClose();
  };

  return (
    <div className="user-guide-overlay" ref={guideRef}>
      {/* 遮罩层 */}
      <div className="guide-backdrop" onClick={handleBackdropClick}></div>

      {/* 高亮元素 */}
      {currentGuide.highlight && targetRect && (
        <div className="guide-highlight" style={highlightStyle}></div>
      )}

      {/* 引导卡片 */}
      <div
        className={`guide-card guide-${currentGuide.position}`}
        style={guideCardStyle}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="guide-header">
          <h3>{currentGuide.title}</h3>
          <button className="guide-close" onClick={handleSkip}>
            ×
          </button>
        </div>
        <div className="guide-content">
          <p>{currentGuide.content}</p>
        </div>
        <div className="guide-footer">
          <div className="guide-progress">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`progress-dot ${index === currentStep ? 'active' : ''}`}
              ></div>
            ))}
          </div>
          <div className="guide-buttons">
            <button
              className="guide-btn guide-btn-secondary"
              onClick={handleSkip}
            >
              跳过
            </button>
            <button
              className="guide-btn guide-btn-secondary"
              onClick={handlePrevious}
              disabled={currentStep === 0}
            >
              上一步
            </button>
            <button className="guide-btn guide-btn-primary" onClick={handleNext}>
              {currentStep === steps.length - 1 ? '完成' : '下一步'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserGuide;
