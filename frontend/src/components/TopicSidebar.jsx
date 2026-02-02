import React, { useState, useEffect } from 'react';
import conversationApi from '../utils/api/conversationApi';
import TopicItem from './TopicItem';
import './TopicSidebar.css';

const TopicSidebar = ({ conversationId, activeTopic, onTopicSelect, onTopicCreate, onTopicDelete, refreshFlag }) => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTopicName, setNewTopicName] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [topicToDelete, setTopicToDelete] = useState(null);

  useEffect(() => {
    loadTopics();
  }, [conversationId, refreshFlag]);

  const loadTopics = async () => {
    if (!conversationId) return;

    try {
      setLoading(true);
      const response = await conversationApi.getTopics(conversationId);
      
      if (response && response.topics) {
        setTopics(response.topics);
      }
    } catch (error) {
      console.error('加载话题列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (keyword) => {
    setSearchKeyword(keyword);

    if (!keyword.trim()) {
      loadTopics();
      return;
    }

    try {
      setLoading(true);
      const response = await conversationApi.searchTopics(conversationId, keyword);
      
      if (response && response.topics) {
        setTopics(response.topics);
      }
    } catch (error) {
      console.error('搜索话题失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTopic = async () => {
    if (!newTopicName.trim()) {
      alert('请输入话题名称');
      return;
    }

    try {
      const response = await conversationApi.createTopic(conversationId, newTopicName);
      
      if (response) {
        setTopics([response, ...topics]);
        setNewTopicName('');
        setShowCreateModal(false);
        
        if (onTopicCreate) {
          onTopicCreate(response);
        }
      }
    } catch (error) {
      console.error('创建话题失败:', error);
      alert('创建话题失败，请重试');
    }
  };

  const handleDeleteTopic = async (topicId) => {
    const topic = topics.find(t => t.id === topicId);
    
    if (!topic) return;

    const message = topic.message_count > 0
      ? `确定要删除话题"${topic.topic_name}"吗？\n该话题包含 ${topic.message_count} 条消息，删除后将无法恢复。`
      : `确定要删除话题"${topic.topic_name}"吗？`;

    if (!confirm(message)) {
      return;
    }

    try {
      await conversationApi.deleteTopic(conversationId, topicId, true);
      
      setTopics(topics.filter(t => t.id !== topicId));
      
      if (onTopicDelete) {
        onTopicDelete(topicId);
      }
    } catch (error) {
      console.error('删除话题失败:', error);
      alert('删除话题失败，请重试');
    }
  };

  const handleTopicClick = (topic) => {
    if (onTopicSelect) {
      onTopicSelect(topic);
    }
  };

  return (
    <div className="topic-sidebar">
      <div className="topic-sidebar-header">
        <h3>话题列表</h3>
        <button 
          className="create-topic-button"
          onClick={() => setShowCreateModal(true)}
        >
          + 新建话题
        </button>
      </div>

      <div className="topic-search">
        <input
          type="text"
          placeholder="搜索话题..."
          value={searchKeyword}
          onChange={(e) => handleSearch(e.target.value)}
          className="topic-search-input"
        />
      </div>

      <div className="topic-list">
        {loading ? (
          <div className="topic-loading">加载中...</div>
        ) : topics.length === 0 ? (
          <div className="topic-empty">暂无话题</div>
        ) : (
          topics.map(topic => (
            <TopicItem
              key={topic.id}
              topic={topic}
              isActive={activeTopic && activeTopic.id === topic.id}
              onClick={() => handleTopicClick(topic)}
              onDelete={() => handleDeleteTopic(topic.id)}
            />
          ))
        )}
      </div>

      {showCreateModal && (
        <div className="topic-modal-overlay">
          <div className="topic-modal">
            <h3>创建新话题</h3>
            <input
              type="text"
              placeholder="请输入话题名称（最多20字）"
              value={newTopicName}
              onChange={(e) => setNewTopicName(e.target.value.slice(0, 20))}
              maxLength={20}
              className="topic-modal-input"
            />
            <div className="topic-modal-actions">
              <button 
                className="topic-modal-button topic-modal-cancel"
                onClick={() => {
                  setShowCreateModal(false);
                  setNewTopicName('');
                }}
              >
                取消
              </button>
              <button 
                className="topic-modal-button topic-modal-confirm"
                onClick={handleCreateTopic}
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopicSidebar;
