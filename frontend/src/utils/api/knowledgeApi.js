import { request } from '../apiUtils';

export const uploadDocument = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await request('/v1/knowledge/upload', {
        method: 'POST',
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    
    return response;
};

export const searchDocuments = async (query, limit = 10) => {
    const response = await request('/v1/knowledge/search', {
        method: 'GET',
        params: { query, limit }
    });
    
    return response.results;
};

export const listDocuments = async (skip = 0, limit = 10) => {
    const response = await request('/v1/knowledge/documents', {
        method: 'GET',
        params: { skip, limit }
    });
    
    return response.documents;
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