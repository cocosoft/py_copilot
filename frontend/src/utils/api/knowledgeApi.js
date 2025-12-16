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

export const searchDocuments = async (query, limit = 10, knowledgeBaseId = null) => {
    const response = await request('/v1/knowledge/search', {
        method: 'GET',
        params: { query, limit, knowledge_base_id: knowledgeBaseId }
    });
    
    return response.results;
};

export const listDocuments = async (skip = 0, limit = 10, knowledgeBaseId = null) => {
    const response = await request('/v1/knowledge/documents', {
        method: 'GET',
        params: { skip, limit, knowledge_base_id: knowledgeBaseId }
    });
    
    return response.documents;
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

export const getKnowledgeStats = async () => {
    const response = await request('/v1/knowledge/stats', {
        method: 'GET'
    });
    return response;
};