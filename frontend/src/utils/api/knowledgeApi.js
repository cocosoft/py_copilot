import { request } from '../apiUtils';

// Knowledge Base API
export const createKnowledgeBase = async (name, description) => {
    const response = await request('/v1/knowledge/knowledge-bases', {
        method: 'POST',
        data: { name, description }
    });
    return response;
};

export const getKnowledgeBases = async (skip = 0, limit = 10) => {
    const response = await request('/v1/knowledge/knowledge-bases', {
        method: 'GET',
        params: { skip, limit }
    });
    return response;
};

export const getKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}`, {
        method: 'GET'
    });
    return response;
};

export const updateKnowledgeBase = async (knowledgeBaseId, name, description) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}`, {
        method: 'PUT',
        data: { name, description }
    });
    return response;
};

export const deleteKnowledgeBase = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}`, {
        method: 'DELETE'
    });
    return response;
};

// Knowledge Document API
export const uploadDocument = async (file, knowledgeBaseId) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await request('/v1/knowledge/documents', {
        method: 'POST',
        params: { knowledge_base_id: knowledgeBaseId },
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    
    return response;
};

export const searchDocuments = async (query, limit = 10, knowledgeBaseId = null, sortBy = 'relevance', sortOrder = 'desc', fileTypes = [], startDate = null, endDate = null) => {
    const response = await request('/v1/knowledge/search', {
        method: 'GET',
        params: {
            query,
            limit,
            knowledge_base_id: knowledgeBaseId,
            sort_by: sortBy,
            sort_order: sortOrder,
            file_types: fileTypes.join(','),
            start_date: startDate,
            end_date: endDate
        }
    });
    
    return response.results;
};

export const listDocuments = async (skip = 0, limit = 10, knowledgeBaseId = null) => {
    const response = await request('/v1/knowledge/documents', {
        method: 'GET',
        params: { skip, limit, knowledge_base_id: knowledgeBaseId }
    });
    
    return response;
};

export const getDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'GET'
    });
    return response;
};

export const deleteDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'DELETE'
    });
    return response;
};

export const updateDocument = async (documentId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await request(`/v1/knowledge/documents/${documentId}`, {
        method: 'PUT',
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    
    return response;
};

export const downloadDocument = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/download`, {
        method: 'GET',
        responseType: 'blob'
    });
    return response;
};

export const getKnowledgeStats = async () => {
    const response = await request('/v1/knowledge/stats', {
        method: 'GET'
    });
    return response;
};

// Knowledge Base Permission API
export const getKnowledgeBasePermissions = async (knowledgeBaseId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'GET'
    });
    return response;
};

export const updateKnowledgeBasePermissions = async (knowledgeBaseId, permissions) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'PUT',
        data: { permissions }
    });
    return response;
};

export const addKnowledgeBasePermission = async (knowledgeBaseId, userId, role) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions`, {
        method: 'POST',
        data: { user_id: userId, role }
    });
    return response;
};

export const removeKnowledgeBasePermission = async (knowledgeBaseId, permissionId) => {
    const response = await request(`/v1/knowledge/knowledge-bases/${knowledgeBaseId}/permissions/${permissionId}`, {
        method: 'DELETE'
    });
    return response;
};

// Document Tag API
export const getDocumentTags = async (documentId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags`, {
        method: 'GET'
    });
    return response;
};

export const addDocumentTag = async (documentId, tagName) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags`, {
        method: 'POST',
        data: { tag_name: tagName }
    });
    return response;
};

export const removeDocumentTag = async (documentId, tagId) => {
    const response = await request(`/v1/knowledge/documents/${documentId}/tags/${tagId}`, {
        method: 'DELETE'
    });
    return response;
};

export const getAllTags = async (knowledgeBaseId = null) => {
    const response = await request('/v1/knowledge/tags', {
        method: 'GET',
        params: { knowledge_base_id: knowledgeBaseId }
    });
    return response;
};

export const searchDocumentsByTag = async (tagId, knowledgeBaseId = null) => {
    const response = await request(`/v1/knowledge/tags/${tagId}/documents`, {
        method: 'GET',
        params: { knowledge_base_id: knowledgeBaseId }
    });
    return response;
};