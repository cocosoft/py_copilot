/**
 * 模型数据管理服务
 * 用于集中管理模型数据，提供统一的数据访问接口
 */
import { API_BASE_URL } from '../utils/apiUtils';

class ModelDataManager {
  static instance = null;
  static models = [];
  static isLoaded = false;
  static loadPromise = null;

  /**
   * 获取单例实例
   * @returns {ModelDataManager}
   */
  static getInstance() {
    if (!ModelDataManager.instance) {
      ModelDataManager.instance = new ModelDataManager();
    }
    return ModelDataManager.instance;
  }

  /**
   * 加载模型数据
   * @param {string} scene - 使用场景
   * @returns {Promise<Array>}
   */
  static async loadModels(scene = 'all') {
    // 如果已经有加载中的请求，返回同一个Promise
    if (ModelDataManager.loadPromise) {
      return ModelDataManager.loadPromise;
    }

    // 如果已经加载过数据，直接返回
    if (ModelDataManager.isLoaded && ModelDataManager.models.length > 0) {
      return ModelDataManager.models;
    }

    try {
      ModelDataManager.loadPromise = ModelDataManager.fetchModels(scene);
      const models = await ModelDataManager.loadPromise;
      ModelDataManager.models = models;
      ModelDataManager.isLoaded = true;
      return models;
    } catch (error) {
      console.error('加载模型数据失败:', error);
      return [];
    } finally {
      ModelDataManager.loadPromise = null;
    }
  }

  /**
   * 从API获取模型数据
   * @param {string} scene - 使用场景
   * @returns {Promise<Array>}
   */
  static async fetchModels(scene = 'all') {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/model-management/models/select?scene=${encodeURIComponent(scene)}`);

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();
      return data.data || [];
    } catch (error) {
      console.error('获取模型数据失败:', error);
      return [];
    }
  }

  /**
   * 根据ID获取模型
   * @param {number} modelId - 模型ID
   * @returns {Promise<Object|null>}
   */
  static async getModelById(modelId) {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/model-management/models/select/${modelId}`);

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();
      return data.data || null;
    } catch (error) {
      console.error('获取模型详情失败:', error);
      return null;
    }
  }

  /**
   * 获取默认模型
   * @param {string} scene - 使用场景
   * @returns {Promise<Object|null>}
   */
  static async getDefaultModel(scene = 'chat') {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/model-management/models/select/default/${encodeURIComponent(scene)}`);

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();
      return data.data || null;
    } catch (error) {
      console.error('获取默认模型失败:', error);
      return null;
    }
  }

  /**
   * 按供应商分组模型
   * @param {Array} models - 模型列表
   * @returns {Array} 分组后的模型数据
   */
  static groupModelsBySupplier(models) {
    const grouped = {};
    
    models.forEach(model => {
      // 确定供应商ID
      const supplierKey = model.supplier_id;
      
      if (!grouped[supplierKey]) {
        // 尝试从多个来源获取供应商信息
        let supplierName = '未知供应商';
        let supplierLogo = '';
        
        // 优先从supplier对象获取
        if (model.supplier) {
          supplierName = model.supplier.display_name || model.supplier.name || supplierName;
          supplierLogo = model.supplier.logo || '';
        }
        
        // 其次从模型直接属性获取
        supplierName = model.supplier_display_name || model.supplier_name || supplierName;
        supplierLogo = model.supplier_logo || supplierLogo;
        
        // 如果supplier_logo包含路径前缀，提取纯文件名
        if (supplierLogo && supplierLogo.includes('logos/providers/')) {
          const parts = supplierLogo.split('logos/providers/');
          const lastPart = parts[parts.length - 1];
          // 如果最后一部分仍然包含logos/providers/，说明路径重复了
          if (lastPart.includes('logos/providers/')) {
            const subParts = lastPart.split('logos/providers/');
            supplierLogo = subParts[subParts.length - 1];
          } else {
            supplierLogo = lastPart;
          }
        }
        
        grouped[supplierKey] = {
          id: supplierKey,
          name: supplierName,
          logo: supplierLogo,
          models: []
        };
      }
      grouped[supplierKey].models.push(model);
    });
    
    // 转换为数组并排序
    return Object.values(grouped).sort((a, b) => a.name.localeCompare(b.name));
  }

  /**
   * 重置数据
   */
  static reset() {
    ModelDataManager.models = [];
    ModelDataManager.isLoaded = false;
    ModelDataManager.loadPromise = null;
  }

  /**
   * 刷新数据
   * @param {string} scene - 使用场景
   * @returns {Promise<Array>}
   */
  static async refresh(scene = 'all') {
    ModelDataManager.reset();
    return ModelDataManager.loadModels(scene);
  }
}

// 导出服务
export default ModelDataManager;