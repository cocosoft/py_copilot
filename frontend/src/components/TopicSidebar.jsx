import React, { useState, useEffect } from 'react';
import conversationApi from '../utils/api/conversationApi';
import TopicItem from './TopicItem';
import './TopicSidebar.css';

const TopicSidebar = ({ 
  conversationId, 
  activeTopic, 
  setActiveTopic, 
  refreshFlag, 
  setRefreshFlag,
  collapsed, 
  setCollapsed 
}) => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
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
    try {
    // 调用API创建话题，不传递topic_name，由后端自动生成
    const response = await conversationApi.createTopic(conversationId, '');
    
    if (response) {
      setTopics([response, ...topics]);
      
      // 移除对未定义参数的引用
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
      
      // 移除对未定义参数的引用
    } catch (error) {
      console.error('删除话题失败:', error);
      alert('删除话题失败，请重试');
    }
  };

  const handleTopicClick = (topic) => {
    if (setActiveTopic) {
      setActiveTopic(topic);
    }
  };

  return (
    <div className={`topic-sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="topic-sidebar-header">
        {!collapsed && <h3>话题列表</h3>}
        <div className="topic-sidebar-actions">
          {!collapsed && (
            <button 
              className="create-topic-button"
              onClick={handleCreateTopic}
              title="新建话题"
            >
              + 新建话题
            </button>
          )}
          <button 
            className="collapse-button"
            onClick={() => setCollapsed && setCollapsed(!collapsed)}
            title={collapsed ? '展开' : '收缩'}
          >
            {collapsed ? '▶' : '◀'}
          </button>
        </div>
      </div>

      {!collapsed && (
        <>
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
        </>
      )}
    </div>
  );
};

export default TopicSidebar;
