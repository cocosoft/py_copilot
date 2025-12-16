import React, { useState, useEffect } from 'react';
import './knowledge.css';
import { uploadDocument, searchDocuments, listDocuments, deleteDocument, getKnowledgeStats } from '../utils/api/knowledgeApi';

const Knowledge = () => {
  const [uploading, setUploading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({});
  
  useEffect(() => {
    loadDocuments();
    loadStats();
  }, []);

  const loadDocuments = async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (error) {
      setError('加载文档列表失败');
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await getKnowledgeStats();
      setStats(statsData);
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // 检查文件格式
    const supportedFormats = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExt = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    if (!supportedFormats.includes(fileExt)) {
      setError(`不支持的文件格式: ${fileExt}，请上传PDF、Word或TXT文件`);
      return;
    }
    
    // 检查文件大小（10MB限制）
    if (file.size > 10 * 1024 * 1024) {
      setError('文件大小超过10MB限制，请上传较小的文件');
      return;
    }
    
    setUploading(true);
    setError('');
    setSuccess('');
    
    try {
      const result = await uploadDocument(file);
      setSuccess(`文档上传成功！文档ID: ${result.document_id}`);
      event.target.value = ''; // 清空文件选择
      loadDocuments(); // 重新加载文档列表
      loadStats(); // 重新加载统计信息
    } catch (error) {
      setError(`上传失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      const results = await searchDocuments(query);
      setSearchResults(results);
      if (results.length === 0) {
        setError('未找到相关文档，请尝试其他关键词');
      } else {
        setError('');
      }
    } catch (error) {
      setError('搜索失败，请检查网络连接或稍后重试');
      setSearchResults([]);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (window.confirm('确定要删除这个文档吗？')) {
      try {
        await deleteDocument(documentId);
        setSuccess('文档删除成功');
        loadDocuments();
        loadStats();
      } catch (error) {
        setError('删除失败，请稍后重试');
      }
    }
  };

  const displayResults = searchQuery ? searchResults : documents;

  return (
    <div className="knowledge-container">
      <div className="content-header">
        <h2>知识库管理</h2>
        <p>管理和查询您的知识库文档</p>
        {stats.total_documents !== undefined && (
          <div className="stats-info">
            文档总数: {stats.total_documents} | 向量文档: {stats.vector_documents}
          </div>
        )}
      </div>
      
      <div className="knowledge-content">
        {/* 错误和成功提示 */}
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        {/* 工具栏区域 */}
        <div className="knowledge-toolbar">
          <div className="search-container">
            <input
              type="text"
              placeholder="搜索知识库..."
              className="knowledge-search"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                handleSearch(e.target.value);
              }}
            />
            <button className="search-btn">
              🔍
            </button>
          </div>
          
          <div className="toolbar-actions">
            <input 
              type="file" 
              id="file-upload"
              onChange={handleFileUpload} 
              disabled={uploading}
              accept=".pdf,.docx,.doc,.txt"
              style={{ display: 'none' }}
            />
            <label htmlFor="file-upload" className="import-btn">
              {uploading ? '上传中...' : '导入文档'}
            </label>
          </div>
        </div>
        
        {/* 搜索结果展示 */}
        {searchQuery && (
          <div className="search-results">
            {searchResults.length > 0 && (
              <p className="results-count">找到 {searchResults.length} 个相关文档</p>
            )}
            {searchResults.map(result => (
              <div key={result.id} className="search-result">
                <h5>{result.title}</h5>
                <p className="result-content">{result.content.substring(0, 200)}...</p>
                <span className="similarity-score">相似度: {result.score.toFixed(2)}</span>
              </div>
            ))}
            {searchResults.length === 0 && (
              <div className="empty-state">
                <p>未找到相关文档，请尝试其他关键词</p>
              </div>
            )}
          </div>
        )}
        
        {/* 文档列表 */}
        {!searchQuery && (
          <div className="knowledge-grid">
            {documents.map(document => (
              <div key={document.id} className="knowledge-item">
                <div className="knowledge-icon">
                  {document.file_type === '.pdf' ? '📄' : 
                   document.file_type === '.docx' || document.file_type === '.doc' ? '📝' : '📄'}
                </div>
                <div className="knowledge-info">
                  <h3 className="knowledge-title">{document.title}</h3>
                  <p className="knowledge-description">
                    {document.content ? document.content.substring(0, 100) + '...' : '无内容预览'}
                  </p>
                  <div className="knowledge-meta">
                    <span className="document-type">{document.file_type.toUpperCase()}</span>
                    <span className="last-updated">
                      {new Date(document.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="knowledge-actions">
                  <button 
                    className="action-btn" 
                    title="删除"
                    onClick={() => handleDeleteDocument(document.id)}
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
            
            {documents.length === 0 && (
              <div className="empty-state">
                <p>暂无文档，请点击"导入文档"开始使用知识库</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Knowledge;