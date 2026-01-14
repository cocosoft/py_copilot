import React, { useState } from 'react';
import { useRateTranslation, useSubmitTranslationFeedback } from '../hooks/useTranslation';
import { showSuccess, showError } from './UI';

const TranslationQualityFeedback = ({ 
  translationId, 
  sourceText, 
  translatedText, 
  sourceLanguage, 
  targetLanguage,
  onClose 
}) => {
  const [activeTab, setActiveTab] = useState('rating');
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackType, setFeedbackType] = useState('quality');
  const [suggestedTranslation, setSuggestedTranslation] = useState('');
  
  const rateMutation = useRateTranslation();
  const feedbackMutation = useSubmitTranslationFeedback();

  const handleRatingSubmit = async () => {
    if (!rating) {
      showError('请选择评分');
      return;
    }

    try {
      await rateMutation.mutateAsync({
        translation_id: translationId,
        rating: rating,
        feedback: feedbackText,
      });
      
      setRating(0);
      setFeedbackText('');
      showSuccess('评分已提交');
    } catch (error) {
      console.error('评分提交失败:', error);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackText.trim()) {
      showError('请输入反馈内容');
      return;
    }

    try {
      await feedbackMutation.mutateAsync({
        translation_id: translationId,
        feedback_type: feedbackType,
        feedback_text: feedbackText.trim(),
        suggested_translation: suggestedTranslation.trim() || undefined,
      });
      
      setFeedbackText('');
      setFeedbackType('quality');
      setSuggestedTranslation('');
      showSuccess('反馈已提交');
    } catch (error) {
      console.error('反馈提交失败:', error);
    }
  };

  const feedbackTypes = [
    { value: 'quality', label: '翻译质量' },
    { value: 'accuracy', label: '准确性' },
    { value: 'fluency', label: '流畅度' },
    { value: 'other', label: '其他问题' },
  ];

  return (
    <div className="quality-feedback-modal">
      <div className="modal-header">
        <h3>翻译质量反馈</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      
      <div className="modal-tabs">
        <button 
          className={`tab-btn ${activeTab === 'rating' ? 'active' : ''}`}
          onClick={() => setActiveTab('rating')}
        >
          评分
        </button>
        <button 
          className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`}
          onClick={() => setActiveTab('feedback')}
        >
          详细反馈
        </button>
      </div>

      <div className="modal-content">
        {activeTab === 'rating' && (
          <div className="rating-tab">
            <div className="translation-preview">
              <div className="preview-item">
                <label>原文:</label>
                <p>{sourceText}</p>
              </div>
              <div className="preview-item">
                <label>译文:</label>
                <p>{translatedText}</p>
              </div>
            </div>
            
            <div className="rating-section">
              <label>请为本次翻译评分 (1-5分):</label>
              <div className="star-rating">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    className={`star ${rating >= star ? 'filled' : ''}`}
                    onClick={() => setRating(star)}
                    type="button"
                  >
                    ★
                  </button>
                ))}
              </div>
              <div className="rating-labels">
                <span>1分 - 很差</span>
                <span>3分 - 一般</span>
                <span>5分 - 优秀</span>
              </div>
            </div>
            
            <div className="feedback-section">
              <label>附加意见 (可选):</label>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="请告诉我们您的具体意见..."
                rows={3}
              />
            </div>
            
            <button 
              className="submit-btn"
              onClick={handleRatingSubmit}
              disabled={rateMutation.isLoading || !rating}
            >
              {rateMutation.isLoading ? '提交中...' : '提交评分'}
            </button>
          </div>
        )}

        {activeTab === 'feedback' && (
          <div className="feedback-tab">
            <div className="feedback-form">
              <div className="form-group">
                <label>反馈类型:</label>
                <select 
                  value={feedbackType} 
                  onChange={(e) => setFeedbackType(e.target.value)}
                >
                  {feedbackTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>反馈内容:</label>
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="请详细描述您遇到的问题或建议..."
                  rows={4}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>建议的翻译 (可选):</label>
                <textarea
                  value={suggestedTranslation}
                  onChange={(e) => setSuggestedTranslation(e.target.value)}
                  placeholder="如果您有更好的翻译建议，请在此处填写..."
                  rows={3}
                />
              </div>
              
              <button 
                className="submit-btn"
                onClick={handleFeedbackSubmit}
                disabled={feedbackMutation.isLoading || !feedbackText.trim()}
              >
                {feedbackMutation.isLoading ? '提交中...' : '提交反馈'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TranslationQualityFeedback;