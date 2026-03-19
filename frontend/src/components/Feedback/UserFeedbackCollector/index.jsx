/**
 * 用户反馈收集组件
 *
 * 收集用户反馈，基于实际使用场景
 *
 * 任务编号: Phase2-Week5
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import React, { useState, useCallback } from 'react';
import { Card, Button, Input, Badge, Modal } from '../../UnifiedComponentLibrary';

/**
 * 星级评分组件
 * @param {Object} props - 组件属性
 * @param {number} props.rating - 当前评分
 * @param {Function} props.onChange - 评分变更回调
 * @param {number} props.maxRating - 最大评分
 * @param {boolean} props.readOnly - 是否只读
 */
const StarRating = ({ rating = 0, onChange, maxRating = 5, readOnly = false }) => {
  const [hoverRating, setHoverRating] = useState(0);

  return (
    <div className="star-rating">
      {[...Array(maxRating)].map((_, index) => {
        const starValue = index + 1;
        const isFilled = starValue <= (hoverRating || rating);

        return (
          <button
            key={index}
            type="button"
            className={`star ${isFilled ? 'filled' : ''} ${readOnly ? 'readonly' : ''}`}
            onClick={() => !readOnly && onChange?.(starValue)}
            onMouseEnter={() => !readOnly && setHoverRating(starValue)}
            onMouseLeave={() => !readOnly && setHoverRating(0)}
            disabled={readOnly}
          >
            ★
          </button>
        );
      })}
    </div>
  );
};

/**
 * 反馈类型选择组件
 * @param {Object} props - 组件属性
 * @param {string} props.selectedType - 选中的类型
 * @param {Function} props.onChange - 变更回调
 */
const FeedbackTypeSelector = ({ selectedType, onChange }) => {
  const feedbackTypes = [
    { key: 'bug', label: 'Bug报告', icon: '🐛', description: '功能异常或错误' },
    { key: 'feature', label: '功能建议', icon: '💡', description: '新功能或改进建议' },
    { key: 'ui', label: '界面问题', icon: '🎨', description: '界面显示或交互问题' },
    { key: 'performance', label: '性能问题', icon: '⚡', description: '响应慢或卡顿' },
    { key: 'usability', label: '易用性', icon: '🤔', description: '操作困难或不直观' },
    { key: 'other', label: '其他', icon: '📝', description: '其他反馈' },
  ];

  return (
    <div className="feedback-type-selector">
      <label>反馈类型</label>
      <div className="type-options">
        {feedbackTypes.map((type) => (
          <button
            key={type.key}
            type="button"
            className={`type-option ${selectedType === type.key ? 'selected' : ''}`}
            onClick={() => onChange?.(type.key)}
          >
            <span className="type-icon">{type.icon}</span>
            <span className="type-label">{type.label}</span>
            <span className="type-description">{type.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

/**
 * 快速反馈按钮组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onFeedback - 反馈回调
 */
const QuickFeedbackButtons = ({ onFeedback }) => {
  const quickOptions = [
    { emoji: '😍', label: '非常满意', value: 5 },
    { emoji: '🙂', label: '满意', value: 4 },
    { emoji: '😐', label: '一般', value: 3 },
    { emoji: '😕', label: '不满意', value: 2 },
    { emoji: '😤', label: '非常不满意', value: 1 },
  ];

  return (
    <div className="quick-feedback-buttons">
      <p className="quick-feedback-title">您对本功能的体验如何？</p>
      <div className="quick-options">
        {quickOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            className="quick-option"
            onClick={() => onFeedback?.(option.value, option.label)}
            title={option.label}
          >
            <span className="option-emoji">{option.emoji}</span>
            <span className="option-label">{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

/**
 * 用户反馈收集组件
 * @param {Object} props - 组件属性
 * @param {boolean} props.isOpen - 是否打开
 * @param {Function} props.onClose - 关闭回调
 * @param {Function} props.onSubmit - 提交回调
 * @param {string} props.context - 反馈上下文
 * @param {boolean} props.showQuickFeedback - 是否显示快速反馈
 */
const UserFeedbackCollector = ({
  isOpen = false,
  onClose,
  onSubmit,
  context = '',
  showQuickFeedback = true,
}) => {
  const [step, setStep] = useState('quick'); // 'quick', 'detailed', 'success'
  const [feedback, setFeedback] = useState({
    type: '',
    rating: 0,
    content: '',
    email: '',
    screenshot: null,
    context: context,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // 处理快速反馈
  const handleQuickFeedback = useCallback((rating, label) => {
    setFeedback((prev) => ({ ...prev, rating }));

    if (rating >= 4) {
      // 高评分直接提交
      handleSubmit({ ...feedback, rating });
    } else {
      // 低评分进入详细反馈
      setStep('detailed');
    }
  }, [feedback]);

  // 处理详细反馈提交
  const handleDetailedSubmit = useCallback(async () => {
    if (!feedback.type) {
      setError('请选择反馈类型');
      return;
    }

    if (!feedback.content.trim()) {
      setError('请输入反馈内容');
      return;
    }

    await handleSubmit(feedback);
  }, [feedback]);

  // 提交反馈
  const handleSubmit = useCallback(async (feedbackData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      // 添加时间戳
      const finalFeedback = {
        ...feedbackData,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };

      // 调用提交回调
      await onSubmit?.(finalFeedback);

      setStep('success');
    } catch (err) {
      setError(err.message || '提交失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  }, [onSubmit]);

  // 重置状态
  const handleReset = useCallback(() => {
    setStep('quick');
    setFeedback({
      type: '',
      rating: 0,
      content: '',
      email: '',
      screenshot: null,
      context: context,
    });
    setError(null);
  }, [context]);

  // 关闭并重置
  const handleClose = useCallback(() => {
    handleReset();
    onClose?.();
  }, [handleReset, onClose]);

  if (!isOpen) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="用户反馈"
      size="md"
    >
      <div className="user-feedback-collector">
        {step === 'quick' && showQuickFeedback && (
          <div className="feedback-step quick-feedback">
            <QuickFeedbackButtons onFeedback={handleQuickFeedback} />

            <div className="step-actions">
              <button
                type="button"
                className="skip-button"
                onClick={() => setStep('detailed')}
              >
                跳过，进入详细反馈
              </button>
            </div>
          </div>
        )}

        {step === 'detailed' && (
          <div className="feedback-step detailed-feedback">
            <div className="feedback-rating">
              <label>总体评分</label>
              <StarRating
                rating={feedback.rating}
                onChange={(rating) => setFeedback((prev) => ({ ...prev, rating }))}
              />
            </div>

            <FeedbackTypeSelector
              selectedType={feedback.type}
              onChange={(type) => setFeedback((prev) => ({ ...prev, type }))}
            />

            <div className="feedback-content">
              <label>详细描述</label>
              <textarea
                value={feedback.content}
                onChange={(e) =>
                  setFeedback((prev) => ({ ...prev, content: e.target.value }))
                }
                placeholder="请详细描述您的问题或建议..."
                rows={4}
              />
            </div>

            <div className="feedback-email">
              <label>联系邮箱（可选）</label>
              <Input
                type="email"
                value={feedback.email}
                onChange={(e) =>
                  setFeedback((prev) => ({ ...prev, email: e.target.value }))
                }
                placeholder="如需回复，请留下您的邮箱"
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="step-actions">
              <Button variant="secondary" onClick={handleClose}>
                取消
              </Button>
              <Button
                variant="primary"
                onClick={handleDetailedSubmit}
                loading={isSubmitting}
              >
                提交反馈
              </Button>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div className="feedback-step success-feedback">
            <div className="success-icon">✅</div>
            <h3>感谢您的反馈！</h3>
            <p>您的意见对我们非常重要，我们会认真考虑并持续改进。</p>

            <div className="step-actions">
              <Button variant="primary" onClick={handleClose}>
                关闭
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

/**
 * 反馈按钮组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onClick - 点击回调
 * @param {string} props.position - 位置
 */
const FeedbackButton = ({ onClick, position = 'bottom-right' }) => {
  const positionStyles = {
    'bottom-right': { bottom: '20px', right: '20px' },
    'bottom-left': { bottom: '20px', left: '20px' },
    'top-right': { top: '20px', right: '20px' },
    'top-left': { top: '20px', left: '20px' },
  };

  return (
    <button
      className="feedback-floating-button"
      style={positionStyles[position]}
      onClick={onClick}
      title="提供反馈"
    >
      <span className="feedback-icon">💬</span>
      <span className="feedback-text">反馈</span>
    </button>
  );
};

/**
 * 反馈历史组件
 * @param {Object} props - 组件属性
 * @param {Array} props.feedbackList - 反馈列表
 */
const FeedbackHistory = ({ feedbackList = [] }) => {
  if (feedbackList.length === 0) {
    return (
      <Card className="feedback-history empty">
        <p>暂无反馈记录</p>
      </Card>
    );
  }

  return (
    <Card className="feedback-history">
      <h3>反馈历史</h3>
      <div className="feedback-list">
        {feedbackList.map((feedback) => (
          <div key={feedback.id} className="feedback-item">
            <div className="feedback-header">
              <Badge variant={getStatusVariant(feedback.status)}>
                {getStatusLabel(feedback.status)}
              </Badge>
              <span className="feedback-date">
                {new Date(feedback.timestamp).toLocaleDateString()}
              </span>
            </div>
            <div className="feedback-type">{feedback.type}</div>
            <div className="feedback-content">{feedback.content}</div>
            {feedback.rating > 0 && (
              <div className="feedback-rating">
                <StarRating rating={feedback.rating} readOnly />
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

// 获取状态样式
function getStatusVariant(status) {
  const variants = {
    pending: 'warning',
    processing: 'info',
    resolved: 'success',
    rejected: 'danger',
  };
  return variants[status] || 'secondary';
}

// 获取状态标签
function getStatusLabel(status) {
  const labels = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决',
    rejected: '已拒绝',
  };
  return labels[status] || status;
}

export default UserFeedbackCollector;
export {
  StarRating,
  FeedbackTypeSelector,
  QuickFeedbackButtons,
  FeedbackButton,
  FeedbackHistory,
};
