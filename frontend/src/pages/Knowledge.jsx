import React, { useState, useEffect } from 'react';
import './knowledge.css';
import * as pdfjsLib from 'pdfjs-dist';
import mammoth from 'mammoth';
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
  getDocument,
  downloadDocument
} from '../utils/api/knowledgeApi';

// 设置PDF.js工作路径
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

const Knowledge = () => {
  // 状态管理
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [searchResults, setSearchResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({});
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [loadingKnowledgeBases, setLoadingKnowledgeBases] = useState(false);
  const [searching, setSearching] = useState(false);
  
  // 知识库相关状态
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState(null);
  
  // 分页相关状态
  const [currentPage, setCurrentPage] = useState(1);
  const [documentsPerPage, setDocumentsPerPage] = useState(20);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  
  // 知识库分页相关状态
  const [kbCurrentPage, setKbCurrentPage] = useState(1);
  const [kbPerPage, setKbPerPage] = useState(10);
  const [totalKbs, setTotalKbs] = useState(0);
  const [totalKbPages, setTotalKbPages] = useState(1);
  
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
  
  // 预览相关状态
  const [previewContent, setPreviewContent] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  
  // 搜索排序相关状态
  const [sortBy, setSortBy] = useState('relevance');
  const [sortOrder, setSortOrder] = useState('desc');
  
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

  // 当排序方式或顺序变化时，重新执行搜索
  useEffect(() => {
    if (searchQuery) {
      handleSearch(searchQuery);
    }
  }, [sortBy, sortOrder]);
  
  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    setLoadingKnowledgeBases(true);
    try {
      const skip = (kbCurrentPage - 1) * kbPerPage;
      const response = await getKnowledgeBases(skip, kbPerPage);
      setKnowledgeBases(response.knowledge_bases || response);
      setTotalKbs(response.total || (response.knowledge_bases ? response.knowledge_bases.length : response.length));
      setTotalKbPages(Math.ceil((response.total || (response.knowledge_bases ? response.knowledge_bases.length : response.length)) / kbPerPage));
      if ((response.knowledge_bases ? response.knowledge_bases.length : response.length) > 0 && !selectedKnowledgeBase) {
        setSelectedKnowledgeBase(response.knowledge_bases ? response.knowledge_bases[0] : response[0]);
      }
    } catch (error) {
      setError(`加载知识库列表失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoadingKnowledgeBases(false);
    }
  };

  // 加载文档列表
  const loadDocuments = async () => {
    setLoadingDocuments(true);
    try {
      const skip = (currentPage - 1) * documentsPerPage;
      const response = await listDocuments(skip, documentsPerPage, selectedKnowledgeBase?.id || null);
      setDocuments(response.documents);
      setTotalDocuments(response.total || response.documents.length);
      setTotalPages(Math.ceil((response.total || response.documents.length) / documentsPerPage));
    } catch (error) {
      setError(`加载文档列表失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoadingDocuments(false);
    }
  };

  // 加载统计信息
  const loadStats = async () => {
    try {
      const statsData = await getKnowledgeStats();
      setStats(statsData);
    } catch (error) {
      console.error('加载统计信息失败:', error);
      // 可以考虑向用户显示错误
      // setError(`加载统计信息失败: ${error.response?.data?.detail || error.message}`);
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
      setPreviewLoading(true);
      setPreviewError('');
      setPreviewContent(null);
      
      const doc = await getDocument(documentId);
      setSelectedDocument(doc);
      
      // 根据文件类型生成预览内容
      if (doc.file_type === '.pdf') {
        // PDF文件预览
        try {
          const response = await fetch(doc.file_path);
          const arrayBuffer = await response.arrayBuffer();
          const pdf = await pdfjsLib.getDocument({
            data: arrayBuffer,
            cMapUrl: `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/cmaps/`,
            cMapPacked: true
          }).promise;
          
          const page = await pdf.getPage(1);
          const viewport = page.getViewport({ scale: 1 });
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          
          canvas.height = viewport.height;
          canvas.width = viewport.width;
          
          await page.render({
            canvasContext: context,
            viewport: viewport
          }).promise;
          
          setPreviewContent(<canvas ref={(el) => el && el.getContext('2d').drawImage(canvas, 0, 0)} width={viewport.width} height={viewport.height} className="pdf-preview" />);
        } catch (pdfError) {
          setPreviewError('PDF预览失败，显示文本内容');
          setPreviewContent(doc.content || '文档内容为空');
        }
      } else if (doc.file_type === '.docx' || doc.file_type === '.doc') {
        // Word文档预览
        try {
          const response = await fetch(doc.file_path);
          const arrayBuffer = await response.arrayBuffer();
          const result = await mammoth.convertToHtml({ arrayBuffer });
          setPreviewContent(<div dangerouslySetInnerHTML={{ __html: result.value }} className="word-preview" />);
        } catch (wordError) {
          setPreviewError('Word文档预览失败，显示文本内容');
          setPreviewContent(doc.content || '文档内容为空');
        }
      } else {
        // 其他文件类型，直接显示文本内容
        setPreviewContent(doc.content || '文档内容为空');
      }
      
      setShowDocumentDetail(true);
    } catch (error) {
      setError(`加载文档详情失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  // 上传文档
  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    if (!selectedKnowledgeBase) {
      setError('请先选择或创建一个知识库');
      return;
    }
    
    // 检查文件格式和大小
    const supportedFormats = ['.pdf', '.docx', '.doc', '.txt'];
    const validFiles = [];
    const invalidFiles = [];
    
    files.forEach(file => {
      const fileExt = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
      const isValidFormat = supportedFormats.includes(fileExt);
      const isValidSize = file.size <= 50 * 1024 * 1024; // 50MB限制
      
      if (!isValidFormat) {
        invalidFiles.push({ name: file.name, reason: `不支持的文件格式: ${fileExt}` });
      } else if (!isValidSize) {
        invalidFiles.push({ name: file.name, reason: '文件大小超过50MB限制' });
      } else {
        validFiles.push(file);
      }
    });
    
    // 显示无效文件信息
    if (invalidFiles.length > 0) {
      const errorMsg = `以下文件无法上传:\n${invalidFiles.map(f => `- ${f.name}: ${f.reason}`).join('\n')}`;
      setError(errorMsg);
      
      // 如果没有有效文件，直接返回
      if (validFiles.length === 0) {
        event.target.value = ''; // 清空文件选择
        return;
      }
    }
    
    if (validFiles.length === 0) {
      setError('没有有效文件可以上传');
      event.target.value = '';
      return;
    }
    
    setUploading(true);
    setUploadProgress(0);
    setError('');
    setSuccess('');
    
    try {
      // 模拟总上传进度
      let currentFileIndex = 0;
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const fileProgress = (currentFileIndex / validFiles.length) * 100;
          const fileCurrentProgress = (prev % (100 / validFiles.length));
          return Math.min(fileProgress + fileCurrentProgress, 95);
        });
      }, 300);
      
      // 上传所有有效文件
      const uploadResults = [];
      for (const file of validFiles) {
        try {
          const result = await uploadDocument(file, selectedKnowledgeBase.id);
          uploadResults.push({ success: true, name: file.name, document_id: result.document_id });
        } catch (fileError) {
          uploadResults.push({ success: false, name: file.name, error: fileError.response?.data?.detail || fileError.message });
        }
        currentFileIndex++;
      }
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      // 短暂显示100%进度后重置
      setTimeout(() => {
        setUploadProgress(0);
      }, 500);
      
      // 统计上传结果
      const successCount = uploadResults.filter(r => r.success).length;
      const failedCount = uploadResults.filter(r => !r.success).length;
      
      let successMsg = `成功上传 ${successCount} 个文档`;
      if (failedCount > 0) {
        const failedFiles = uploadResults.filter(r => !r.success).map(r => `- ${r.name}: ${r.error}`).join('\n');
        setError(`以下文件上传失败:\n${failedFiles}`);
      }
      
      setSuccess(successMsg);
      event.target.value = ''; // 清空文件选择
      loadDocuments(); // 重新加载文档列表
      loadStats(); // 重新加载统计信息
    } catch (error) {
      setError(`上传失败: ${error.response?.data?.detail || error.message}`);
      setUploadProgress(0);
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
    
    setSearching(true);
    try {
      const results = await searchDocuments(
        query,
        10,
        selectedKnowledgeBase?.id || null,
        sortBy,
        sortOrder
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
    } finally {
      setSearching(false);
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
  
  // 处理文档下载
  const handleDownloadDocument = async () => {
    if (!selectedDocument) return;
    
    try {
      setPreviewLoading(true);
      const blob = await downloadDocument(selectedDocument.id);
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = selectedDocument.title;
      document.body.appendChild(a);
      a.click();
      
      // 清理
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setSuccess('文件下载成功');
    } catch (error) {
      setError(`下载失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setPreviewLoading(false);
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
    // 重置预览状态
    setPreviewContent(null);
    setPreviewLoading(false);
    setPreviewError('');
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
          {loadingKnowledgeBases ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <span>加载知识库...</span>
            </div>
          ) : knowledgeBases.length > 0 ? (
            knowledgeBases.map(kb => (
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
            ))
          ) : (
            <div className="empty-nav">
              <span>暂无知识库，请创建新的知识库</span>
            </div>
          )}
        </div>
        
        {/* 知识库列表分页控件 */}
        {totalKbs > 0 && (
          <div className="knowledge-pagination">
            <div className="pagination-info">
              共 {totalKbs} 个知识库
            </div>
            <div className="pagination-controls">
              <button 
                className="pagination-btn" 
                onClick={() => setKbCurrentPage(1)}
                disabled={kbCurrentPage === 1}
              >
                首页
              </button>
              <button 
                className="pagination-btn" 
                onClick={() => setKbCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={kbCurrentPage === 1}
              >
                上一页
              </button>
              
              {/* 页码按钮 */}
              {Array.from({ length: totalKbPages }, (_, i) => i + 1).map(page => (
                <button 
                  key={page}
                  className={`pagination-btn ${kbCurrentPage === page ? 'active' : ''}`} 
                  onClick={() => setKbCurrentPage(page)}
                >
                  {page}
                </button>
              ))}
              
              <button 
                className="pagination-btn" 
                onClick={() => setKbCurrentPage(prev => Math.min(totalKbPages, prev + 1))}
                disabled={kbCurrentPage === totalKbPages}
              >
                下一页
              </button>
              <button 
                className="pagination-btn" 
                onClick={() => setKbCurrentPage(totalKbPages)}
                disabled={kbCurrentPage === totalKbPages}
              >
                末页
              </button>
            </div>
          </div>
        )}
      </div>
      
      <div className="knowledge-content">
        {/* 错误和成功提示 */}
        {error && (
          <div className="notification error">
            <span className="notification-icon">❌</span>
            <span className="notification-text">{error}</span>
            <button className="notification-close" onClick={() => setError('')}>×</button>
          </div>
        )}
        {success && (
          <div className="notification success">
            <span className="notification-icon">✅</span>
            <span className="notification-text">{success}</span>
            <button className="notification-close" onClick={() => setSuccess('')}>×</button>
          </div>
        )}
        
        {/* 上传进度显示 */}
        {uploading && uploadProgress > 0 && (
          <div className="notification warning">
            <span className="notification-icon">📤</span>
            <div className="notification-text">
              <div>上传进度: {Math.round(uploadProgress)}%</div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}
        
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
              multiple
              style={{ display: 'none' }}
            />
            <label htmlFor="file-upload" className="import-btn">
              {uploading ? '上传中...' : !selectedKnowledgeBase ? '请选择知识库' : '选择文档'}
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
            {searching ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <span>搜索中...</span>
              </div>
            ) : (
              <>
                {searchResults.length > 0 && (
                  <div className="search-results-header">
                    <p className="results-count">找到 {searchResults.length} 个相关文档</p>
                    <div className="search-sort-controls">
                      <div className="sort-control">
                        <label htmlFor="sortBy">排序方式:</label>
                        <select 
                          id="sortBy" 
                          value={sortBy} 
                          onChange={(e) => setSortBy(e.target.value)}
                        >
                          <option value="relevance">相关性</option>
                          <option value="created_at">创建时间</option>
                          <option value="title">文档标题</option>
                        </select>
                      </div>
                      <div className="sort-control">
                        <label htmlFor="sortOrder">排序顺序:</label>
                        <select 
                          id="sortOrder" 
                          value={sortOrder} 
                          onChange={(e) => setSortOrder(e.target.value)}
                        >
                          <option value="desc">降序</option>
                          <option value="asc">升序</option>
                        </select>
                      </div>
                    </div>
                  </div>
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
              </>
            )}
          </div>
        )}
        
        {/* 文档列表 */}
        {!searchQuery && (
          <>
            <div className="knowledge-grid">
              {selectedKnowledgeBase ? (
                loadingDocuments ? (
                  <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <span>加载文档列表...</span>
                  </div>
                ) : documents.map(document => (
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
            
            {/* 文档列表分页控件 */}
            {selectedKnowledgeBase && totalDocuments > 0 && (
              <div className="pagination-container">
                <div className="pagination-info">
                  共 {totalDocuments} 条文档，第 {currentPage} / {totalPages} 页
                </div>
                <div className="pagination-controls">
                  <button 
                    className="pagination-btn" 
                    onClick={() => setCurrentPage(1)}
                    disabled={currentPage === 1}
                  >
                    首页
                  </button>
                  <button 
                    className="pagination-btn" 
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                  >
                    上一页
                  </button>
                  
                  {/* 页码按钮 */}
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button 
                      key={page}
                      className={`pagination-btn ${currentPage === page ? 'active' : ''}`} 
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </button>
                  ))}
                  
                  <button 
                    className="pagination-btn" 
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                  >
                    下一页
                  </button>
                  <button 
                    className="pagination-btn" 
                    onClick={() => setCurrentPage(totalPages)}
                    disabled={currentPage === totalPages}
                  >
                    末页
                  </button>
                  
                  {/* 每页显示数量选择 */}
                  <div className="page-size-selector">
                    <label htmlFor="pageSize">每页：</label>
                    <select 
                      id="pageSize" 
                      value={documentsPerPage} 
                      onChange={(e) => {
                        setDocumentsPerPage(Number(e.target.value));
                        setCurrentPage(1); // 重置到第一页
                      }}
                    >
                      <option value={10}>10条</option>
                      <option value={20}>20条</option>
                      <option value={50}>50条</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </>
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
          <div className="modal-content document-detail-modal" onClick={(e) => e.stopPropagation()}> 
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
                  {previewLoading ? (
                    <div className="loading-container">
                      <div className="loading-spinner"></div>
                      <span>加载文档预览...</span>
                    </div>
                  ) : (
                    <>
                      {previewError && (
                        <div className="preview-error">
                          <span className="error-icon">⚠️</span>
                          <span>{previewError}</span>
                        </div>
                      )}
                      {previewContent}
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-primary" onClick={handleDownloadDocument} disabled={previewLoading}>
                {previewLoading ? '下载中...' : '下载文档'}
              </button>
              <button className="btn-secondary" onClick={closeAllModals}>关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Knowledge;