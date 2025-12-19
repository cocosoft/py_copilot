import { request } from '../utils/apiUtils';

class WorkflowService {
  async getWorkflows(skip = 0, limit = 100) {
    try {
      const response = await request('/v1/workflows', {
        method: 'GET',
        params: { skip, limit }
      });
      return response;
    } catch (error) {
      console.error('获取工作流列表失败:', error);
      throw error;
    }
  }

  async getWorkflow(workflowId) {
    try {
      const response = await request(`/v1/workflows/${workflowId}`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('获取工作流详情失败:', error);
      throw error;
    }
  }

  async createWorkflow(workflowData) {
    try {
      const response = await request('/v1/workflows', {
        method: 'POST',
        data: workflowData
      });
      return response;
    } catch (error) {
      console.error('创建工作流失败:', error);
      throw error;
    }
  }

  async updateWorkflow(workflowId, workflowData) {
    try {
      const response = await request(`/v1/workflows/${workflowId}`, {
        method: 'PUT',
        data: workflowData
      });
      return response;
    } catch (error) {
      console.error('更新工作流失败:', error);
      throw error;
    }
  }

  async deleteWorkflow(workflowId) {
    try {
      const response = await request(`/v1/workflows/${workflowId}`, {
        method: 'DELETE'
      });
      return response;
    } catch (error) {
      console.error('删除工作流失败:', error);
      throw error;
    }
  }

  async executeWorkflow(workflowId, inputData = {}) {
    try {
      const response = await request(`/v1/workflows/${workflowId}/execute`, {
        method: 'POST',
        data: { input_data: inputData }
      });
      return response;
    } catch (error) {
      console.error('执行工作流失败:', error);
      throw error;
    }
  }

  async getWorkflowExecutions() {
    try {
      const response = await request('/v1/executions', {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('获取工作流执行历史失败:', error);
      throw error;
    }
  }

  async getWorkflowExecution(executionId) {
    try {
      const response = await request(`/v1/executions/${executionId}`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('获取工作流执行详情失败:', error);
      throw error;
    }
  }

  async testKnowledgeSearch(query, knowledgeBaseId = null) {
    try {
      const response = await request('/v1/workflows/knowledge-search/test', {
        method: 'POST',
        data: {
          query,
          knowledge_base_id: knowledgeBaseId
        }
      });
      return response;
    } catch (error) {
      console.error('测试知识搜索失败:', error);
      throw error;
    }
  }

  async testEntityExtraction(text, entityTypes = null) {
    try {
      const response = await request('/v1/workflows/entity-extraction/test', {
        method: 'POST',
        data: {
          text,
          entity_types: entityTypes
        }
      });
      return response;
    } catch (error) {
      console.error('测试实体抽取失败:', error);
      throw error;
    }
  }

  async testRelationshipAnalysis(entityIds, relationshipTypes = null) {
    try {
      const response = await request('/v1/workflows/relationship-analysis/test', {
        method: 'POST',
        data: {
          entity_ids: entityIds,
          relationship_types: relationshipTypes
        }
      });
      return response;
    } catch (error) {
      console.error('测试关系分析失败:', error);
      throw error;
    }
  }
}

export default new WorkflowService();