import React, { useState, useEffect } from 'react';
import './knowledge.css';
import {
  uploadDocument,
  searchDocuments,
  listDocuments,
  deleteDocument,
  getKnowledgeStats,
  createKnowledgeBase,
  getKnowledgeBases,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  getDocument
} from '../utils/api/knowledgeApi';

const Knowledge = () => {
  // 状态管理
  const [uploading, setUploading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({});
  
  // 知识库相关状态
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState(null);
  
  // 模态框状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showDocumentDetail, setShowDocumentDetail] = useState(false);
  
  // 表单状态
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [editingKnowledgeBase, setEditingKnowledgeBase] = useState(null);
  const [deletingKnowledgeBase, setDeletingKnowledgeBase] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  
  // 初始化加载
  useEffect(() => {
    loadKnowledgeBases();
    loadStats();
  }, []);
  
  // 当选择的知识库变化时，加载对应的文档
  useEffect(() => {
    if (selectedKnowledgeBase) {
      loadDocuments();
    } else {
      setDocuments([]);
    }
  }, [selectedKnowledgeBase]);
  
  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    try {
      const data = await getKnowledgeBases();
      setKnowledgeBases(data);
      if (data.length > 0 && !selectedKnowledgeBase) {
        setSelectedKnowledgeBase(data[0]);
      }
    } catch (error) {
      setError('加载知识库列表失败');
    }
  };

  // 加载文档列表
  const loadDocuments = async () => {
    try {
      const docs = await listDocuments(0, 10, selectedKnowledgeBase?.id || null);
      setDocuments(docs);
    } catch (error) {
      setError('加载文档列表失败');
    }
  };

  // 加载统计信息
  const loadStats = async () => {
    try {
      const statsData = await getKnowledgeStats();
      setStats(statsData);
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  };
  
  // 创建知识库
  const handleCreateKnowledgeBase = async () => {
    if (!formData.name.trim()) {
      setError('知识库名称不能为空');
      return;
    }
    
    try {
      const newKB = await createKnowledgeBase(formData.name, formData.description);
      setKnowledgeBases([...knowledgeBases, newKB]);
      setSelectedKnowledgeBase(newKB);
      setShowCreateModal(false);
      setFormData({ name: '', description: '' });
      setSuccess('知识库创建成功');
      loadStats();
    } catch (error) {
      setError(`创建知识库失败: ${error.response?.data?.detail || error.message}`);
    }
  };
  
  // 更新知识库
  const handleUpdateKnowledgeBase = async () => {
    if (!formData.name.trim()) {
      setError('知识库名称不能为空');
      return;
    }
    
    try {
      const updatedKB = await updateKnowledgeBase(editingKnowledgeBase.id, formData.name, formData.description);
      const updatedList = knowledgeBases.map(kb => 
        kb.id === editingKnowledgeBase.id ? updatedKB : kb
      );
      setKnowledgeBases(updatedList);
      if (selectedKnowledgeBase.id === editingKnowledgeBase.id) {
        setSelectedKnowledgeBase(updatedKB);
      }
      setShowEditModal(false);
      setEditingKnowledgeBase(null);
      setFormData({ name: '', description: '' });
      setSuccess('知识库更新成功');
    } catch (error) {
      setError(`更新知识库失败: ${error.response?.data?.detail || error.message}`);
    }
  };
  
  // 删除知识库
  const handleDeleteKnowledgeBase = async () => {
    try {
      await deleteKnowledgeBase(deletingKnowledgeBase.id);
      const updatedList = knowledgeBases.filter(kb => kb.id !== deletingKnowledgeBase.id);
      setKnowledgeBases(updatedList);
      if (selectedKnowledgeBase.id === deletingKnowledgeBase.id) {
        setSelectedKnowledgeBase(updatedList.length > 0 ? updatedList[0] : null);
      }
      setShowDeleteModal(false);
      setDeletingKnowledgeBase(null);
      setSuccess('知识库删除成功');
      loadStats();
    } catch (error) {
      setError(`删除知识库失败: ${error.response?.data?.detail || error.message}`);
    }
  };
  
  // 打开编辑模态框
  const openEditModal = (kb) => {
    setEditingKnowledgeBase(kb);
    setFormData({ name: kb.name, description: kb.description });
    setShowEditModal(true);
  };
  
  // 打开删除确认模态框
  const openDeleteModal = (kb) => {
    setDeletingKnowledgeBase(kb);
    setShowDeleteModal(true);
  };
  
  // 打开文档详情
  const openDocumentDetail = async (documentId) => {
    try {
      const doc = await getDocument(documentId);
      setSelectedDocument(doc);
      setShowDocumentDetail(true);
    } catch (error) {
      setError('加载文档详情失败');
    }
  };

  // 上传文档
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!selectedKnowledgeBase) {
      setError('请先选择或创建一个知识库');
      return;
    }
    
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
      const result = await uploadDocument(file, selectedKnowledgeBase.id);
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

  // 搜索文档
  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      const results = await searchDocuments(
        query,
        10,
        selectedKnowledgeBase?.id || null
      );
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

  // 删除文档
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
  
  // 关闭所有模态框
  const closeAllModals = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setShowDeleteModal(false);
    setShowDocumentDetail(false);
    setEditingKnowledgeBase(null);
    setDeletingKnowledgeBase(null);
    setSelectedDocument(null);
    setFormData({ name: '', description: '' });
    setError('');
  };

  const displayResults = searchQuery ? searchResults : documents;

  return (
    <div className="knowledge-container">
      <div className="content-header">
        <h2>知识库管理</h2>
        <p>管理和查询您的知识库文档</p>
        {stats.total_documents !== undefined && (
          <div className="stats-info">
            文档总数: {stats.total_documents} | 向量文档: {stats.vector_documents} | 知识库: {stats.knowledge_bases_count}
          </div>
        )}
      </div>
      
      {/* 知识库导航栏 */}
      <div className="knowledge-nav">
        <div className="knowledge-nav-header">
          <div className="knowledge-nav-title">知识库</div>
          <button className="create-btn" onClick={() => setShowCreateModal(true)}>
            + 新建知识库
          </button>
        </div>
        
        <div className="knowledge-nav-list">
          {knowledgeBases.map(kb => (
            <div
              key={kb.id}
              className={`knowledge-nav-item ${selectedKnowledgeBase?.id === kb.id ? 'active' : ''}`}
              onClick={() => setSelectedKnowledgeBase(kb)}
            >
              <span>{kb.name}</span>
              <button
                className="close-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  openDeleteModal(kb);
                }}
                title="删除知识库"
              >
                ×
              </button>
            </div>
          ))}
        </div>
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
              disabled={uploading || !selectedKnowledgeBase}
              accept=".pdf,.docx,.doc,.txt"
              style={{ display: 'none' }}
            />
            <label htmlFor="file-upload" className="import-btn">
              {uploading ? '上传中...' : !selectedKnowledgeBase ? '请选择知识库' : '导入文档'}
            </label>
            
            {selectedKnowledgeBase && (
              <button 
                className="create-btn"
                onClick={() => openEditModal(selectedKnowledgeBase)}
                disabled={uploading}
              >
                编辑知识库
              </button>
            )}
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="similarity-score">相似度: {result.score.toFixed(2)}</span>
                  <button 
                    className="btn-secondary"
                    onClick={() => openDocumentDetail(result.id)}
                    style={{ fontSize: '12px', padding: '4px 8px' }}
                  >
                    查看详情
                  </button>
                </div>
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
            {selectedKnowledgeBase ? (
              documents.map(document => (
                <div key={document.id} className="knowledge-item">
                  <div className="knowledge-icon">
                    {document.file_type === '.pdf' ? '📄' : 
                     document.file_type === '.docx' || document.file_type === '.doc' ? '📝' : '📄'}
                  </div>
                  <div className="knowledge-info">
                    <h3 className="knowledge-title" onClick={() => openDocumentDetail(document.id)}>
                      {document.title}
                    </h3>
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
                      title="查看详情"
                      onClick={() => openDocumentDetail(document.id)}
                    >
                      👁️
                    </button>
                    <button 
                      className="action-btn" 
                      title="删除"
                      onClick={() => handleDeleteDocument(document.id)}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <p>请选择或创建一个知识库</p>
              </div>
            )}
            
            {selectedKnowledgeBase && documents.length === 0 && (
              <div className="empty-state">
                <p>当前知识库暂无文档，请点击"导入文档"开始使用</p>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* 创建知识库模态框 */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={closeAllModals}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">创建知识库</h3>
              <button className="modal-close" onClick={closeAllModals}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">知识库名称</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="请输入知识库名称"
                />
              </div>
              <div className="form-group">
                <label className="form-label">描述</label>
                <textarea
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="请输入知识库描述（可选）"
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeAllModals}>取消</button>
              <button className="btn-primary" onClick={handleCreateKnowledgeBase}>创建</button>
            </div>
          </div>
        </div>
      )}
      
      {/* 编辑知识库模态框 */}
      {showEditModal && editingKnowledgeBase && (
        <div className="modal-overlay" onClick={closeAllModals}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">编辑知识库</h3>
              <button className="modal-close" onClick={closeAllModals}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">知识库名称</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="请输入知识库名称"
                />
              </div>
              <div className="form-group">
                <label className="form-label">描述</label>
                <textarea
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="请输入知识库描述（可选）"
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeAllModals}>取消</button>
              <button className="btn-primary" onClick={handleUpdateKnowledgeBase}>保存</button>
            </div>
          </div>
        </div>
      )}
      
      {/* 删除知识库确认模态框 */}
      {showDeleteModal && deletingKnowledgeBase && (
        <div className="modal-overlay" onClick={closeAllModals}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">确认删除</h3>
              <button className="modal-close" onClick={closeAllModals}>×</button>
            </div>
            <div className="modal-body">
              <p>确定要删除知识库 "{deletingKnowledgeBase.name}" 吗？</p>
              <p style={{ color: '#e74c3c', fontSize: '14px', marginTop: '8px' }}>
                注意：删除知识库将同时删除其中的所有文档。
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeAllModals}>取消</button>
              <button className="btn-primary" onClick={handleDeleteKnowledgeBase} style={{ backgroundColor: '#e74c3c' }}>
                删除
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 文档详情模态框 */}
      {showDocumentDetail && selectedDocument && (
        <div className="modal-overlay" onClick={closeAllModals}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}> 
            <div className="modal-header">
              <h3 className="modal-title">文档详情</h3>
              <button className="modal-close" onClick={closeAllModals}>×</button>
            </div>
            <div className="modal-body">
              <div className="document-detail">
                <div className="document-detail-header">
                  <h1 className="document-detail-title">{selectedDocument.title}</h1>
                  <div className="document-detail-meta">
                    <span>文件类型: {selectedDocument.file_type.toUpperCase()}</span>
                    <span>创建时间: {new Date(selectedDocument.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <div className="document-detail-content">
                  {selectedDocument.content || '文档内容为空'}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-primary" onClick={closeAllModals}>关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Knowledge;